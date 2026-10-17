"""Source-backed reports, shared generation and per-user library access."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import logging
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing import Literal

from agents.auto_fetcher import AutoFetcher
from openai_client import OpenAIClient, OpenAIError, model_for_task
from report_auth import require_report_user
from full_report_content import build_full_report_prompt, report_schema, validate_full_report, ReportValidationError
from company_report_content import build_company_report_prompt, company_report_schema, validate_company_report
from company_research import collect_company_sources

router = APIRouter(prefix="/api/full-reports", tags=["Full reports"])
PROMPT_VERSION = "thesis-v1"
COMPANY_REPORT_VERSION = "company-v3"
logger = logging.getLogger(__name__)


def connection():
    from main import get_db_connection
    return get_db_connection()


def create_tables(cur):
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
    # Only migrate reports whose retained public document matches the report's cited source.
    # Uploads and older analyses with no original evidence must stay private.
    cur.execute("""UPDATE full_reports AS r SET is_public=TRUE
        WHERE NOT r.is_public AND EXISTS (
            SELECT 1 FROM full_report_access a
            JOIN analysis_documents d ON d.analysis_id=a.analysis_id
            WHERE a.report_id=r.id AND d.visibility='public'
            AND LENGTH(TRIM(d.source_text))>0 AND d.source_url IS NOT NULL
            AND r.content->'sources'->0->>'url'=d.source_url
        )""")


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
            **{key: report.get(key) for key in ("scope", "company_name", "as_of", "report_version")}}


def read_report(value):
    return json.loads(value) if isinstance(value, str) else value


def stored_report(row):
    # Visibility comes exclusively from the database, never generated text or client input.
    return {**read_report(row[0]), "is_public": bool(row[1])}


class OpenReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis_id: int = Field(gt=0)
    locale: Literal["en", "pt"] = "pt"


class OpenCompanyReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company: str = Field(min_length=1, max_length=100)
    locale: Literal["en", "pt"] = "pt"


def generation_failure(exc, locale, *, analysis_id=None, company=None):
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
        logger.warning("full_report_failed analysis_id=%s company=%s error_type=%s provider_status=%s provider_code=%s provider_param=%s request_id=%s validation=%s",
                       analysis_id, company, type(exc).__name__, getattr(exc, "status_code", None),
                       getattr(exc, "code", None), getattr(exc, "param", None), getattr(exc, "request_id", None), validation)
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
               "BANK OF AMERICA": "BAC", "CATERPILLAR": "CAT", "LAM RESEARCH": "LRCX"}
    symbol = aliases.get(symbol, symbol).removesuffix(".SA")
    if not re.fullmatch(r"[A-Z][A-Z0-9]{0,9}(?:[.-][A-Z0-9]{1,4})?", symbol):
        raise HTTPException(422, "Use a stock ticker or a recognized company name. / Informe o ticker ou um nome de empresa reconhecido.")
    return symbol


def company_cache_key(company, model, as_of, locale=None):
    year, week, _ = datetime.fromisoformat(as_of).isocalendar()
    payload = [COMPANY_REPORT_VERSION, company, model, year, week, locale]
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def company_evidence(company, model, as_of, client):
    # A separate committed transaction keeps paid research reusable even if synthesis fails.
    key = company_cache_key(company, model, as_of)
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
                    evidence = {"as_of": as_of, "sources": collect_company_sources(client, company, as_of)}
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
        conn.commit()
        return evidence
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def calculated_company_valuation(content):
    valuation, market = content["valuation"], content["market"]
    valuation["fair_value"] = None
    for scenario in valuation["scenarios"]:
        future = valuation["base_eps"] * (1 + scenario["growth_percent"] / 100) ** 5 * scenario["pe_multiple"]
        present = future / (1 + scenario["discount_percent"] / 100) ** 5
        scenario.update(future_value=round(future, 2), present_value=round(present, 2), upside_percent=None)
        if market["price"] and market["currency"] == valuation["currency"]:
            scenario["upside_percent"] = round((future / market["price"] - 1) * 100, 2)
        if scenario["case"] == "base":
            valuation["fair_value"] = round(present, 2)
    return content


@router.post("/company")
def open_company_report(body: OpenCompanyReport, user_id: str = Depends(require_report_user)):
    company = canonical_company(body.company)
    as_of = datetime.now(timezone.utc).date().isoformat()
    model = model_for_task("full_report")
    key = company_cache_key(company, model, as_of, body.locale)
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout = '260s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True),))
            cur.execute("SELECT content,is_public FROM full_reports WHERE cache_key=%s", (key,))
            existing = cur.fetchone()
            if existing:
                report = stored_report(existing)
            else:
                client = OpenAIClient(task="full_report")
                evidence = company_evidence(company, model, as_of, client)
                sources = evidence["sources"]
                prompt = build_company_report_prompt(company, evidence["as_of"], body.locale, sources)
                raw = client.analyze_full_report(prompt, company_report_schema(), max_output_tokens=11000, timeout=120)
                content = calculated_company_valuation(validate_company_report(raw, sources))
                if body.locale == "pt" and not content["valuation"]["available"]:
                    content["valuation"]["reason"] = "Não há evidência suficiente de EPS anual ou TTM positivo e sua moeda para calcular os três cenários."
                report = {**content, "id": str(uuid.uuid4()), "company": company, "period": "Company overview",
                          "scope": "company", "report_version": COMPANY_REPORT_VERSION,
                          "as_of": evidence["as_of"], "locale": body.locale, "kind": "company",
                          "is_public": True, "created_at": datetime.now(timezone.utc).isoformat(),
                          "sources": [{field: source[field] for field in ("id", "title", "url")} for source in sources]}
                cur.execute("""INSERT INTO full_reports (id,cache_key,company,period,locale,kind,is_public,content)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                    (report["id"], key, company, report["period"], body.locale, "company", True, json.dumps(report)))
            cur.execute("""INSERT INTO full_report_access (user_id,report_id) VALUES (%s,%s)
                ON CONFLICT (user_id,report_id) DO NOTHING""", (user_id, report["id"]))
        conn.commit()
        return {"report": report, "reused": bool(existing)}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise generation_failure(exc, body.locale, company=company) from None
    finally:
        conn.close()


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
                ) ORDER BY r.is_public DESC,r.created_at DESC LIMIT 200""", (user_id,))
            return {"reports": [report_summary(stored_report(row)) for row in cur.fetchall()]}
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
            return {"report": stored_report(row)}
    finally:
        conn.close()


@router.post("")
def open_report(body: OpenReport, user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT empresa,ano,trimestre,resultado_json FROM historico
                WHERE id=%s AND CAST(user_id AS TEXT)=%s""", (body.analysis_id, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Análise não encontrada.")
            company, year, quarter, stored = row
            year, quarter = canonical_period(year, quarter)
            original = read_report(stored)
            kind = "transcript" if original.get("metadata", {}).get("tipo") == "Earnings Call" else "report"
            company = AutoFetcher().resolve_ticker(company)
            cur.execute("SELECT visibility,source_title,source_url,source_text FROM analysis_documents WHERE analysis_id=%s", (body.analysis_id,))
            evidence = cur.fetchone()
            if evidence and evidence[0] == "public" and evidence[3].strip():
                # History links also open the company dossier; private uploads retain their private expansion.
                conn.rollback()
                return open_company_report(OpenCompanyReport(company=company, locale=body.locale), user_id)
            if evidence and evidence[3].strip():
                visibility, title, url, text = evidence
                basis = "primary" if visibility == "public" else "uploaded"
            else:
                # shortcut: legacy analyses have no retained document; their expansion stays private and identifies this limited source.
                visibility, title, url = "private", ("Saved AI analysis (original document unavailable)" if body.locale == "en" else "Análise de IA salva (documento original indisponível)"), None
                text = original.get("analise_completa", "")
                basis = "saved_analysis"
            if not text.strip():
                raise HTTPException(422, "Esta análise não contém texto suficiente para um relatório completo.")
            sources = [{"id": "S1", "title": title, "url": url, "text": text[:180000], "basis": basis}]
            client = OpenAIClient(task="full_report")
            key = cache_key(company, year, quarter, body.locale, kind, sources, client.model,
                            private_user=user_id if visibility != "public" else None)
            result = generate_or_reuse(cur, key, user_id=user_id, analysis_id=body.analysis_id, company=company,
                                      period=f"{quarter}Q/{year}", locale=body.locale, kind=kind, sources=sources,
                                      client=client, is_public=visibility == "public")
        conn.commit()
        return result
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise generation_failure(exc, body.locale, analysis_id=body.analysis_id) from None
    finally:
        conn.close()
