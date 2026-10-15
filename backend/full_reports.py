"""Source-backed reports, shared generation and per-user library access."""
from datetime import datetime, timezone
import hashlib
import json
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from agents.auto_fetcher import AutoFetcher
from openai_client import OpenAIClient, OpenAIError
from report_auth import require_report_user
from full_report_content import build_full_report_prompt, report_schema, validate_full_report

router = APIRouter(prefix="/api/full-reports", tags=["Full reports"])
PROMPT_VERSION = "thesis-v1"


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
        content JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS full_report_access (
        user_id TEXT NOT NULL, report_id TEXT NOT NULL REFERENCES full_reports(id) ON DELETE CASCADE,
        analysis_id INTEGER REFERENCES historico(id) ON DELETE SET NULL,
        PRIMARY KEY (user_id, report_id)
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
    return {key: report[key] for key in ("id", "company", "period", "locale", "kind", "created_at", "score")}


def read_report(value):
    return json.loads(value) if isinstance(value, str) else value


class OpenReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis_id: int = Field(gt=0)
    locale: Literal["en", "pt"] = "pt"


def generate_or_reuse(cur, key, *, user_id, analysis_id, company, period, locale, kind, sources, client):
    # A transaction-scoped lock also deduplicates requests across server processes.
    cur.execute("SET LOCAL lock_timeout = '190s'")
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True),))
    cur.execute("SELECT content FROM full_reports WHERE cache_key=%s", (key,))
    existing = cur.fetchone()
    if existing:
        report = read_report(existing[0])
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
                  "locale": locale, "kind": kind, "created_at": datetime.now(timezone.utc).isoformat(),
                  "sources": [{key: source[key] for key in ("id", "title", "url")} for source in sources]}
        cur.execute("""INSERT INTO full_reports (id,cache_key,company,period,locale,kind,content)
            VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)""",
            (report["id"], key, company, period, locale, kind, json.dumps(report)))
    cur.execute("""INSERT INTO full_report_access (user_id,report_id,analysis_id) VALUES (%s,%s,%s)
        ON CONFLICT (user_id,report_id) DO NOTHING""", (user_id, report["id"], analysis_id))
    return {"report": report, "reused": bool(existing)}


@router.get("")
def list_reports(user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT r.content FROM full_reports r JOIN full_report_access a ON a.report_id=r.id
                WHERE a.user_id=%s ORDER BY r.created_at DESC LIMIT 200""", (user_id,))
            return {"reports": [report_summary(read_report(row[0])) for row in cur.fetchall()]}
    finally:
        conn.close()


@router.get("/{report_id}")
def get_report(report_id: str, user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT r.content FROM full_reports r JOIN full_report_access a ON a.report_id=r.id
                WHERE r.id=%s AND a.user_id=%s""", (report_id, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Relatório não encontrado.")
            return {"report": read_report(row[0])}
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
            client = OpenAIClient()
            key = cache_key(company, year, quarter, body.locale, kind, sources, client.model,
                            private_user=user_id if visibility != "public" else None)
            result = generate_or_reuse(cur, key, user_id=user_id, analysis_id=body.analysis_id, company=company,
                                      period=f"{quarter}Q/{year}", locale=body.locale, kind=kind, sources=sources, client=client)
        conn.commit()
        return result
    except HTTPException:
        conn.rollback()
        raise
    except (OpenAIError, ValueError, TimeoutError):
        conn.rollback()
        raise HTTPException(502, "Não foi possível gerar o relatório completo. Tente novamente; nenhuma versão incompleta foi salva.") from None
    except Exception:
        conn.rollback()
        raise HTTPException(503, "O serviço de relatórios está temporariamente indisponível. Tente novamente.") from None
    finally:
        conn.close()
