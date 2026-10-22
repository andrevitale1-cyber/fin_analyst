"""Source-backed reports, shared generation and per-user library access."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import logging
import re
import uuid
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing import Literal

from agents.auto_fetcher import AutoFetcher
from openai_client import OpenAIClient, OpenAIError, model_for_task
from report_auth import require_report_user
from full_report_content import build_full_report_prompt, report_schema, validate_full_report, ReportValidationError
from company_report_content import company_report_schema, validate_company_report
from agents.report_facts import extract_facts, validate_dossier
from agents.report_pipeline import generate_report, remaining
from agents.report_model import baseline_from_sources, model_assumptions, calculate_model, VERSION as MODEL_VERSION
from sector_research import is_petrobras, VERSION as SECTOR_VERSION
from agents.report_valuation import calculate_valuation as calculated_company_valuation, VALUATION_METHODS
from company_research import collect_deep_company_sources as collect_company_sources, evidence_manifest, recover_market_sources
from report_runtime import checkpoint, progress, record_run, editorial_preparation
from agents.company_documents import collect_issuer_annual_sources
from account_limits import reserve_usage, complete_usage, cancel_usage, TIMEZONE

router = APIRouter(prefix="/api/full-reports", tags=["Full reports"])
PROMPT_VERSION = "thesis-v1"
COMPANY_REPORT_VERSION = "company-v11"
RESEARCH_VERSION = "company-v7"
logger = logging.getLogger(__name__)
timing_logger = logging.getLogger("uvicorn.error")


def connection():
    from main import get_db_connection
    return get_db_connection()


def create_tables(cur):
    from thesis_library import create_tables as create_library_tables
    cur.execute("""CREATE TABLE IF NOT EXISTS report_runs (
        id TEXT PRIMARY KEY,company TEXT NOT NULL,model TEXT NOT NULL,stage TEXT NOT NULL,
        elapsed_ms INTEGER NOT NULL,error_type TEXT,diagnostics JSONB NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS analysis_documents (
        analysis_id INTEGER PRIMARY KEY REFERENCES historico(id) ON DELETE CASCADE,
        visibility TEXT NOT NULL CHECK (visibility IN ('public','private')),
        source_title TEXT NOT NULL, source_url TEXT, source_text TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS full_reports (
        id TEXT PRIMARY KEY, cache_key TEXT UNIQUE NOT NULL, company TEXT NOT NULL,
        period TEXT NOT NULL, locale TEXT NOT NULL, kind TEXT NOT NULL,
        content JSONB NOT NULL, is_public BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("ALTER TABLE full_reports ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT FALSE")
    cur.execute("""CREATE TABLE IF NOT EXISTS company_research_cache (
        cache_key TEXT PRIMARY KEY, content JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS full_report_access (
        user_id TEXT NOT NULL, report_id TEXT NOT NULL REFERENCES full_reports(id) ON DELETE CASCADE,
        analysis_id INTEGER REFERENCES historico(id) ON DELETE SET NULL,
        PRIMARY KEY (user_id, report_id)
    )""")
    create_library_tables(cur)


def save_analysis_document(cur, analysis_id, *, visibility, title, url=None, text="", pdf_bytes=b""):
    if not text.strip() and pdf_bytes:
        try:
            text = OpenAIClient.extract_text(pdf_bytes)
        except OpenAIError:
            text = ""
    cur.execute("""INSERT INTO analysis_documents
        (analysis_id,visibility,source_title,source_url,source_text) VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (analysis_id) DO NOTHING""",
        (analysis_id, visibility, title, url, text[:180000]))


def cache_key(company, year, quarter, locale, kind, sources, model, private_user=None):
    # The user ID scopes uploads; public source content never incorporates a user's earlier AI response.
    payload = {"company": company, "year": year, "quarter": quarter, "locale": locale, "kind": kind,
               "sources": sources,
               "model": model, "version": PROMPT_VERSION, "private_user": private_user}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def canonical_period(year, quarter):
    match = re.fullmatch(r"(?:([1-4])[TQ]?|[TQ]([1-4]))", str(quarter).upper())
    if not match or not re.fullmatch(r"\d{4}", str(year)) or not 1900 <= int(year) <= 2100:
        raise HTTPException(422, "Período da análise inválido.")
    return int(year), int(match.group(1) or match.group(2))


def report_summary(report):
    return {**{key: report[key] for key in ("id", "company", "period", "locale", "kind", "created_at", "score", "is_public")},
            **{key: report.get(key) for key in ("scope", "company_name", "symbol", "as_of", "report_version")}}


def read_report(value):
    return json.loads(value) if isinstance(value, str) else value


def stored_report(row):
    # Visibility comes exclusively from the database, never generated text or client input.
    report = {**read_report(row[0]), "is_public": bool(row[1])}
    if report.get("scope") == "company":
        report["symbol"] = report["company"]
        if report.get("valuation") and not report.get("investment_model"):
            report["valuation"] = {**report["valuation"], "method": VALUATION_METHODS.get(report.get("locale"), VALUATION_METHODS["en"])}
    return report


class OpenReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis_id: int = Field(gt=0)
    locale: Literal["en", "pt"] = "pt"


class OpenCompanyReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company: str = Field(min_length=1, max_length=100)
    locale: Literal["en", "pt"] = "pt"


def generation_failure(exc, locale, *, analysis_id=None, company=None, stage=None, model=None):
    # Record diagnostic identifiers, never source text or Pydantic input values.
    validation = []
    if isinstance(exc, ValidationError):
        fields = {"coverage", "score", "sections", "metrics", "watchpoints", "valuation", "market",
                  "signals", "scorecard", "tracking_metrics", "breakdowns", "financial_history", "projections", "analyst_consensus"}
        validation = [{"field": item["loc"][0] if item["loc"] and item["loc"][0] in fields else "other",
                       "type": item["type"]} for item in exc.errors(include_input=False, include_url=False)]
    elif isinstance(exc, ReportValidationError):
        validation = [{"type": str(exc)}]
    if isinstance(exc, (OpenAIError, ValueError, TimeoutError)):
        logger.warning("full_report_failed analysis_id=%s company=%s error_type=%s provider_status=%s provider_code=%s provider_param=%s request_id=%s validation=%s stage=%s model=%s",
                       analysis_id, company, type(exc).__name__, getattr(exc, "status_code", None),
                       getattr(exc, "code", None), getattr(exc, "param", None), getattr(exc, "request_id", None), validation, stage, model or model_for_task("full_report"))
        if isinstance(exc, TimeoutError):
            return HTTPException(504, "Researching this company took longer than expected. Please try again in a moment." if locale == "en" else
                                 "A pesquisa desta empresa demorou mais que o esperado. Tente novamente em instantes.")
        if getattr(exc, "code", None) == "insufficient_company_sources":
            return HTTPException(422, "Not enough cited public information was found for this company. Check the ticker and try again." if locale == "en" else
                                 "Não foram encontradas fontes públicas citadas suficientes para esta companhia. Confira o ticker e tente novamente.")
        return HTTPException(502, "We could not generate the full report. Please try again; no incomplete report was saved." if locale == "en" else
                             "Não foi possível gerar o relatório completo. Tente novamente; nenhuma versão incompleta foi salva.")
    logger.error("full_report_unavailable analysis_id=%s company=%s error_type=%s", analysis_id, company, type(exc).__name__)
    return HTTPException(503, "The report service is temporarily unavailable. Please try again." if locale == "en" else
                         "O serviço de relatórios está temporariamente indisponível. Tente novamente.")


def canonical_company(company):
    symbol = AutoFetcher().resolve_ticker(company)
    aliases = {"MICRON": "MU", "MICRON TECHNOLOGY": "MU", "SERVICENOW": "NOW", "SERVICE NOW": "NOW",
               "ADVANCED MICRO DEVICES": "AMD", "BROADCOM": "AVGO", "GOOG": "GOOGL",
               "META PLATFORMS": "META", "NVIDIA CORPORATION": "NVDA", "APPLE INC": "AAPL",
               "COCA COLA": "KO", "COCA-COLA": "KO", "BERKSHIRE HATHAWAY": "BRK-B",
               "JPMORGAN": "JPM", "JOHNSON & JOHNSON": "JNJ", "ELI LILLY": "LLY",
               "WALMART": "WMT", "VISA": "V", "MASTERCARD": "MA", "COSTCO": "COST",
               "ORACLE": "ORCL", "EXXON MOBIL": "XOM", "CHEVRON": "CVX", "ABBVIE": "ABBV",
               "BANK OF AMERICA": "BAC", "CATERPILLAR": "CAT", "LAM RESEARCH": "LRCX",
               "NIKE": "NKE", "NIKE INC": "NKE", "NIKE, INC.": "NKE"}
    symbol = AutoFetcher().resolve_ticker(aliases.get(symbol, symbol).removesuffix(".SA"))
    if not re.fullmatch(r"[A-Z][A-Z0-9]{0,9}(?:[.-][A-Z0-9]{1,4})?", symbol):
        raise HTTPException(422, "Use a stock ticker or a recognized company name. / Informe o ticker ou um nome de empresa reconhecido.")
    return symbol


def company_cache_key(company, model, as_of, locale=None, *, version=None):
    year, week, _ = datetime.fromisoformat(as_of).isocalendar()
    payload = [version or COMPANY_REPORT_VERSION, company, model, year, week, locale]
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def company_evidence(company, model, as_of, client):
    # A separate committed transaction keeps paid research reusable even if synthesis fails.
    revision = editorial_preparation.get()
    research_version = f"editorial-v1:{revision}" if revision else RESEARCH_VERSION
    if is_petrobras(company):
        research_version += ":" + SECTOR_VERSION
    key = company_cache_key(company, model, as_of, version=research_version)
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout = '260s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True),))
            cur.execute("SELECT content FROM company_research_cache WHERE cache_key=%s", (key,))
            existing = cur.fetchone()
            if existing:
                evidence = read_report(existing[0])
                if evidence.get("error") and evidence["retry_after"] > datetime.now(timezone.utc).isoformat():
                    raise OpenAIError("Recent company research did not find sufficient evidence.", code=evidence["error"])
            if not existing or evidence.get("error"):
                try:
                    sources = collect_company_sources(client, company, as_of)
                    evidence = {"as_of": as_of, "sources": sources, "coverage": evidence_manifest(sources), "issuer_documents_version": 2}
                except OpenAIError as exc:
                    if exc.code not in ("insufficient_company_sources", "research_incomplete"):
                        raise
                    failed = {"error": exc.code, "retry_after": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()}
                    cur.execute("""INSERT INTO company_research_cache (cache_key,content) VALUES (%s,%s::jsonb)
                        ON CONFLICT (cache_key) DO UPDATE SET content=EXCLUDED.content,created_at=NOW()""", (key, json.dumps(failed)))
                    conn.commit()
                    raise
                cur.execute("""INSERT INTO company_research_cache (cache_key,content) VALUES (%s,%s::jsonb)
                    ON CONFLICT (cache_key) DO UPDATE SET content=EXCLUDED.content,created_at=NOW()""", (key, json.dumps(evidence)))
            if company in AutoFetcher.mziq_catalogs and evidence.get("issuer_documents_version") != 2:
                annuals = collect_issuer_annual_sources(company, as_of)
                ids = {s["id"] for s in annuals}
                evidence["sources"] = annuals + [s for s in evidence["sources"] if s["id"] not in ids]
                evidence["issuer_documents_version"] = 2
                cur.execute("UPDATE company_research_cache SET content=%s::jsonb WHERE cache_key=%s", (json.dumps(evidence), key))
            if evidence.get("coverage", {}).get("has_market_consensus") is False and not evidence.get("market_recovery_version"):
                snapshot_date = evidence["as_of"]
                extra = recover_market_sources(client, company, snapshot_date)
                by_url = {s["url"]: s for s in evidence["sources"]}
                for source in extra:
                    if source["url"] in by_url:
                        existing_source = by_url[source["url"]]
                        if existing_source.get("basis") != "primary":
                            existing_source["text"] = (source["text"] + "\n\n" + existing_source["text"])[:24000]
                    else:
                        source = {**source, "id": f"M{len(by_url) + 1}", "retrieved_at": snapshot_date}
                        evidence["sources"].append(source)
                        by_url[source["url"]] = source
                evidence["coverage"] = evidence_manifest(evidence["sources"])
                evidence["market_recovery_version"] = 1
                cur.execute("UPDATE company_research_cache SET content=%s::jsonb WHERE cache_key=%s", (json.dumps(evidence), key))
            if is_petrobras(company) and not evidence.get("petrobras_documents_version"):
                from agents.company_documents import collect_petrobras_filings, collect_petrobras_market_sources, hydrate_company_documents
                discovered = collect_petrobras_filings(evidence["as_of"])
                if not discovered:
                    raise ReportValidationError("Original Petrobras statement catalogue is unavailable")
                from urllib.parse import urlsplit, urlunsplit
                def identity(source):
                    url = urlsplit(source["url"])
                    return urlunsplit((url.scheme, url.netloc, url.path, "", ""))
                new_urls = {identity(s) for s in discovered}
                kept = [s for s in evidence["sources"] if identity(s) not in new_urls]
                original = [s for s in kept if s.get("id") == "F1"]
                rest = [s for s in kept if s.get("id") != "F1"]
                evidence["sources"] = hydrate_company_documents(company, original + discovered + rest)
                if any(s.get("basis") != "primary" for s in evidence["sources"] if s["id"].startswith("IRSEC")):
                    raise ReportValidationError("Original Petrobras filings could not be downloaded")
                market_sources = collect_petrobras_market_sources()
                market_urls = {identity(s) for s in market_sources}
                evidence["sources"] = [s for s in evidence["sources"] if identity(s) not in market_urls] + market_sources
                evidence["coverage"] = evidence_manifest(evidence["sources"])
                evidence["petrobras_documents_version"] = 1
                cur.execute("UPDATE company_research_cache SET content=%s::jsonb WHERE cache_key=%s", (json.dumps(evidence), key))
        conn.commit()
        return evidence
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def company_facts(company, model, evidence, client, *, deadline):
    # Shared across languages/users; failed writing/audits never require another paid extraction.
    payload = ["facts-v7", company, model, evidence]
    key = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout = '45s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True),))
            cur.execute("SELECT content FROM company_research_cache WHERE cache_key=%s", (key,))
            cached = cur.fetchone()
            if cached:
                # Cached IDs are assigned again after matching evidence quotes to current source content.
                raw = read_report(cached[0])
                raw = {**raw, "facts": [{k: v for k, v in fact.items() if k != "id"} for fact in raw["facts"]]}
                dossier = validate_dossier(raw, evidence["sources"])
            else:
                dossier = extract_facts(client, company, evidence["as_of"], evidence["sources"], timeout=remaining(deadline, 120 if editorial_preparation.get() else 60))
                cur.execute("INSERT INTO company_research_cache(cache_key,content) VALUES (%s,%s::jsonb)", (key, json.dumps(dossier)))
        conn.commit()
        return dossier
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def company_model(company, client, evidence, dossier, locale, *, deadline):
    baseline = baseline_from_sources(evidence["sources"])
    if baseline is None:
        return None
    if is_petrobras(company):
        from agents import petrobras_model
        identity = [petrobras_model.VERSION, company, evidence["as_of"], locale, client.model, baseline, dossier, evidence["sources"]]
        raw = checkpoint("petrobras-proposal-v2", identity,
                         lambda: petrobras_model.propose(client, company, evidence["as_of"], locale, dossier,
                             baseline, evidence["sources"], timeout=remaining(deadline, 240)))
        return petrobras_model.calculate(baseline, raw, evidence["sources"])
    identity = [MODEL_VERSION, company, evidence["as_of"], locale, client.model, baseline, dossier]
    raw = checkpoint("operating-assumptions", identity,
                     lambda: model_assumptions(client, company, evidence["as_of"], locale, dossier, baseline, timeout=remaining(deadline, 90)))
    result = calculate_model(baseline, raw, {s["id"] for s in evidence["sources"]})
    return result if result["available"] else None


def reserve_report_usage(user, locale):
    from report_jobs import reserved_ticket
    reserved = reserved_ticket.get()
    return reserved["ticket"] if reserved is not None else reserve_usage(user, "full_report", locale)


def cancel_report_usage(ticket):
    from report_jobs import reserved_ticket
    # The job owner handles cleanup. A replaced worker must not cancel its successor's lease.
    if reserved_ticket.get() is None:
        cancel_usage(ticket)


@router.post("/company")
def open_library_company(body: OpenCompanyReport, user_id: str = Depends(require_report_user)):
    from thesis_library import resolve_company
    return resolve_company(body, user_id)


def open_company_report(body: OpenCompanyReport, user_id: str = Depends(require_report_user)):
    started = perf_counter()
    timings = {}
    company = canonical_company(body.company)
    as_of = datetime.now(TIMEZONE).date().isoformat()
    model = model_for_task("full_report")
    revision = editorial_preparation.get()
    key = company_cache_key(company, model, as_of, body.locale,
                            version=(f"{COMPANY_REPORT_VERSION}:editorial-v1:{revision}" if revision else COMPANY_REPORT_VERSION)
                            + (":" + SECTOR_VERSION if is_petrobras(company) else ""))
    conn = connection()
    stage = "cache"
    ticket = None
    client = facts_client = research_client = None
    error_type = None
    deadline = started + (2400 if revision else 720)
    try:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout = '720s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True),))
            cur.execute("SELECT content,is_public FROM full_reports WHERE cache_key=%s", (key,))
            existing = cur.fetchone()
            if not existing and company == "NKE":
                # Keep reports generated under the old NIKE identifier reusable.
                legacy_key = company_cache_key("NIKE", model, as_of, body.locale)
                cur.execute("SELECT content,is_public FROM full_reports WHERE cache_key=%s", (legacy_key,))
                existing = cur.fetchone()
            timings["cache_ms"] = round((perf_counter() - started) * 1000)
            if existing:
                report = stored_report(existing)
                if not report["is_public"]:
                    cur.execute("SELECT 1 FROM full_report_access WHERE user_id=%s AND report_id=%s", (str(user_id), report["id"]))
                    if not cur.fetchone():
                        ticket = reserve_report_usage(user_id, body.locale)
            else:
                ticket = reserve_report_usage(user_id, body.locale)
                client = OpenAIClient(task="full_report")
                research_client = OpenAIClient(task="analysis")
                stage = "research"
                step = perf_counter()
                evidence = company_evidence(company, model_for_task("analysis"), as_of, research_client)
                timings["research_ms"] = round((perf_counter() - step) * 1000)
                sources = evidence["sources"]
                stage = "extraction"
                progress(stage)
                step = perf_counter()
                facts_client = OpenAIClient(task="analysis")
                dossier = company_facts(company, model_for_task("analysis"), evidence, facts_client, deadline=deadline)
                timings["extraction_ms"] = round((perf_counter() - step) * 1000)
                stage = "model"
                progress(stage)
                step = perf_counter()
                investment_model = company_model(company, client, evidence, dossier, body.locale, deadline=deadline)
                timings["model_ms"] = round((perf_counter() - step) * 1000)
                stage = "synthesis"
                step = perf_counter()
                content = generate_report(client, company, evidence["as_of"], body.locale, sources, dossier,
                                          deadline=deadline, investment_model=investment_model)
                if "pipeline" in content:
                    content["pipeline"]["facts_model"] = model_for_task("analysis")
                timings["synthesis_ms"] = round((perf_counter() - step) * 1000)
                stage = "validation"
                if body.locale == "pt" and not content["valuation"]["available"] and not content.get("investment_model", {}).get("available"):
                    content["valuation"]["reason"] = "Não há evidência suficiente de EPS anual ou TTM positivo e sua moeda para calcular os três cenários."
                report = {**content, "id": str(uuid.uuid4()), "company": company, "symbol": company, "period": "Company overview",
                          "scope": "company", "report_version": COMPANY_REPORT_VERSION,
                          "as_of": evidence["as_of"], "locale": body.locale, "kind": "company",
                          "is_public": False, "created_at": datetime.now(timezone.utc).isoformat(),
                          "research_profile": "editorial-v1" if revision else "standard",
                          "evidence_coverage": evidence.get("coverage", {}),
                          "sources": [{field: source[field] for field in ("id", "title", "url")} for source in sources]}
                cur.execute("""INSERT INTO full_reports (id,cache_key,company,period,locale,kind,is_public,content)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                    (report["id"], key, company, report["period"], body.locale, "company", False, json.dumps(report)))
            cur.execute("""INSERT INTO full_report_access (user_id,report_id) VALUES (%s,%s)
                ON CONFLICT (user_id,report_id) DO NOTHING""", (user_id, report["id"]))
            complete_usage(cur, ticket)
        conn.commit()
        stage = "complete"
        return {"report": report, "reused": bool(existing)}
    except HTTPException:
        error_type = "HTTPException"
        conn.rollback()
        cancel_report_usage(ticket)
        raise
    except Exception as exc:
        error_type = type(exc).__name__
        conn.rollback()
        cancel_report_usage(ticket)
        raise generation_failure(exc, body.locale, company=company, stage=stage,
                                 model=model_for_task("analysis") if stage == "extraction" else model) from None
    finally:
        conn.close()
        record_run(company, model, stage, round((perf_counter() - started) * 1000), timings,
                   [client, facts_client, research_client], error_type)
        timing_logger.info("full_report_timing company=%s model=%s stage=%s total_ms=%d timings=%s",
                    company, model, stage, round((perf_counter() - started) * 1000), timings)


def generate_or_reuse(cur, key, *, user_id, analysis_id, company, period, locale, kind, sources, client, is_public=False):
    # A transaction-scoped lock also deduplicates requests across server processes.
    cur.execute("SET LOCAL lock_timeout = '190s'")
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True),))
    cur.execute("SELECT content,is_public FROM full_reports WHERE cache_key=%s", (key,))
    existing = cur.fetchone()
    if existing:
        report = stored_report(existing)
        if is_public and not report["is_public"]:
            cur.execute("UPDATE full_reports SET is_public=TRUE WHERE id=%s", (report["id"],))
            report["is_public"] = True
    else:
        prompt = build_full_report_prompt(company, period, locale, kind, sources)
        content = validate_full_report(client.analyze_full_report(prompt, report_schema()), sources)
        basis = sources[0]["basis"]
        content["coverage"] = (
            {"primary": "Source document from the selected analysis; comparisons are limited to the information it contains.",
             "uploaded": "Your uploaded document; coverage is limited to its contents.",
             "saved_analysis": "Saved AI analysis; the original document was not retained, so its claims have not been reverified."}
            if locale == "en" else
            {"primary": "Documento de origem da análise selecionada; comparações limitadas às informações nele presentes.",
             "uploaded": "Arquivo enviado por você; a cobertura se limita ao seu conteúdo.",
             "saved_analysis": "Análise de IA salva; o documento original não foi retido e as afirmações não foram verificadas novamente."}
        )[basis]
        content["score"] = None
        if locale == "pt" and content["valuation"]["reason"] == "The source does not explicitly establish positive annual or TTM EPS and its currency.":
            content["valuation"]["reason"] = "A fonte não comprova lucro por ação anual ou dos últimos 12 meses positivo e sua moeda."
        report = {**content, "id": str(uuid.uuid4()), "company": company, "period": period,
                  "locale": locale, "kind": kind, "is_public": is_public,
                  "created_at": datetime.now(timezone.utc).isoformat(),
                  "sources": [{key: source[key] for key in ("id", "title", "url")} for source in sources]}
        cur.execute("""INSERT INTO full_reports (id,cache_key,company,period,locale,kind,is_public,content)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
            (report["id"], key, company, period, locale, kind, is_public, json.dumps(report)))
    cur.execute("""INSERT INTO full_report_access (user_id,report_id,analysis_id) VALUES (%s,%s,%s)
        ON CONFLICT (user_id,report_id) DO NOTHING""", (user_id, report["id"], analysis_id))
    return {"report": report, "reused": bool(existing)}


@router.get("")
def list_reports(user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT r.content,r.is_public FROM full_reports r
                WHERE r.is_public OR EXISTS (
                    SELECT 1 FROM full_report_access a WHERE a.report_id=r.id AND a.user_id=%s
                ) ORDER BY r.is_public DESC,r.created_at DESC,r.id DESC LIMIT 200""", (user_id,))
            items = []
            public_companies_seen = set()
            for row in cur.fetchall():
                report = stored_report(row)
                microsoft = str(report.get("symbol") or report["company"]).strip().upper() in {
                    "MSFT", "MICROSOFT", "MICROSOFT CORPORATION", "MICROSOFT CORPORATION (MSFT)"}
                if report["is_public"] and (microsoft or report.get("scope") == "company"):
                    company_key = "MSFT" if microsoft else report["company"].strip().upper()
                    if company_key in public_companies_seen:
                        continue
                    public_companies_seen.add(company_key)
                items.append(report_summary(report))
            return {"reports": items}
    finally:
        conn.close()


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: str, user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            # Lock the report before removing access so publication or shared access cannot race deletion.
            cur.execute("""SELECT r.id FROM full_reports r WHERE r.id=%s AND NOT r.is_public
                AND EXISTS (SELECT 1 FROM full_report_access a WHERE a.report_id=r.id AND a.user_id=%s)
                FOR UPDATE""", (report_id, user_id))
            if not cur.fetchone():
                raise HTTPException(404, "Relatório privado não encontrado.")
            cur.execute("DELETE FROM full_report_access WHERE report_id=%s AND user_id=%s", (report_id, user_id))
            cur.execute("""DELETE FROM full_reports WHERE id=%s AND NOT is_public
                AND NOT EXISTS (SELECT 1 FROM full_report_access WHERE report_id=%s)""", (report_id, report_id))
        conn.commit()
        return Response(status_code=204)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@router.get("/{report_id}")
def get_report(report_id: str, user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT r.content,r.is_public FROM full_reports r
                WHERE r.id=%s AND (r.is_public OR EXISTS (
                    SELECT 1 FROM full_report_access a WHERE a.report_id=r.id AND a.user_id=%s
                ))""", (report_id, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Relatório não encontrado.")
            from thesis_library import annotate
            return {"report": annotate(cur, stored_report(row))}
    finally:
        conn.close()


@router.post("")
def open_report(body: OpenReport, user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT empresa FROM historico
                WHERE id=%s AND CAST(user_id AS TEXT)=%s""", (body.analysis_id, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Análise não encontrada.")
            company = row[0]
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise generation_failure(exc, body.locale, analysis_id=body.analysis_id) from None
    finally:
        conn.close()
    # Match the Full Reports tab; private documents and the selected quarter never enter the public dossier.
    from thesis_library import resolve_company
    return resolve_company(OpenCompanyReport(company=company, locale=body.locale), user_id)
