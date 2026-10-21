"""Ready company theses and editorial coverage requests. Browsing never runs an LLM."""
from datetime import datetime, timezone
import hashlib
import json
from urllib.parse import urlsplit
import uuid

from fastapi import APIRouter, Depends, HTTPException

from full_reports import (canonical_company, canonical_period, stored_report,
                          OpenCompanyReport, OpenReport)
from report_auth import require_report_user

router = APIRouter(prefix="/api/thesis-library", tags=["Thesis library"])
INITIAL_COMPANIES = ("MSFT", "NVDA", "AAPL", "GOOGL", "AMZN", "META", "PETR4", "WEGE3", "VIVA3")
EDITOR = "thesis-library-editor"


def connection():
    from full_reports import connection as connect
    return connect()


def create_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS thesis_coverage (
        company TEXT NOT NULL,locale TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'planned',draft_id TEXT,published_id TEXT,
        latest_year INTEGER,latest_quarter INTEGER,covered_year INTEGER,covered_quarter INTEGER,
        draft_year INTEGER,draft_quarter INTEGER,result_url TEXT,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),PRIMARY KEY(company,locale))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS thesis_requests (
        user_id TEXT NOT NULL,company TEXT NOT NULL,locale TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),PRIMARY KEY(user_id,company,locale))""")
    for company in INITIAL_COMPANIES:
        cur.execute("INSERT INTO thesis_coverage(company,locale) VALUES (%s,'pt') ON CONFLICT DO NOTHING", (company,))


def available(cur, company, locale, user):
    cur.execute("""SELECT r.content,r.is_public FROM full_reports r
        WHERE r.company=%s AND r.kind='company' AND (r.is_public OR EXISTS (
            SELECT 1 FROM full_report_access a WHERE a.report_id=r.id AND a.user_id=%s))
        ORDER BY r.is_public DESC,(r.locale=%s) DESC,r.created_at DESC,r.id DESC LIMIT 1""", (company, str(user), locale))
    row = cur.fetchone()
    return annotate(cur, stored_report(row)) if row else None


def annotate(cur, report):
    if report.get("is_public") and report.get("publication", {}).get("reviewed"):
        cur.execute("SELECT state,published_id,latest_year,latest_quarter FROM thesis_coverage WHERE company=%s AND locale=%s", (report["company"], report["locale"]))
        row = cur.fetchone()
        if row:
            report["editorial_status"] = {"state": row[0] if row[1] == report["id"] else "superseded",
                                          "latest_year": row[2], "latest_quarter": row[3]}
    return report


def resolve_company(body, user):
    company = canonical_company(body.company)
    conn = connection()
    try:
        with conn.cursor() as cur:
            report = available(cur, company, body.locale, user)
            if report:
                return {"state": "completed", "company": company, "report": report, "reused": True}
            cur.execute("SELECT 1 FROM thesis_requests WHERE user_id=%s AND company=%s AND locale=%s", (str(user), company, body.locale))
            requested = bool(cur.fetchone())
        return {"state": "requested" if requested else "unavailable", "company": company, "locale": body.locale}
    finally:
        conn.close()


def resolve_analysis(body, user):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT empresa FROM historico WHERE id=%s AND CAST(user_id AS TEXT)=%s", (body.analysis_id, str(user)))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Analysis not found.")
    finally:
        conn.close()
    return resolve_company(OpenCompanyReport(company=row[0], locale=body.locale), user)


@router.post("/resolve")
def resolve(body: OpenCompanyReport, user=Depends(require_report_user)):
    return resolve_company(body, user)


@router.post("/requests")
def request_coverage(body: OpenCompanyReport, user=Depends(require_report_user)):
    company = canonical_company(body.company)
    conn = connection()
    try:
        with conn.cursor() as cur:
            # Serialize a user's requests: the library does not spend their analysis allowance.
            lock = int.from_bytes(hashlib.sha256(f"coverage:{user}".encode()).digest()[:8], "big", signed=True)
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (lock,))
            report = available(cur, company, body.locale, user)
            if report:
                return {"state": "completed", "company": company, "report": report, "reused": True}
            cur.execute("SELECT 1 FROM thesis_requests WHERE user_id=%s AND company=%s AND locale=%s", (str(user), company, body.locale))
            if not cur.fetchone():
                cur.execute("SELECT COUNT(*) FROM thesis_requests WHERE user_id=%s AND created_at>NOW()-INTERVAL '24 hours'", (str(user),))
                if cur.fetchone()[0] >= 10:
                    raise HTTPException(429, "Coverage request limit reached. / Limite de solicitações de cobertura atingido.")
                cur.execute("INSERT INTO thesis_requests(user_id,company,locale) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING", (str(user), company, body.locale))
                cur.execute("INSERT INTO thesis_coverage(company,locale) VALUES (%s,%s) ON CONFLICT DO NOTHING", (company, body.locale))
        conn.commit()
        return {"state": "requested", "company": company, "locale": body.locale}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def note_official_result(cur, company, year, quarter, url):
    """Only the verified automatic-document flow calls this; uploads never trigger publication."""
    company = canonical_company(company)
    year, quarter = canonical_period(year, quarter)
    if urlsplit(url or "").scheme != "https":
        return
    cur.execute("""UPDATE thesis_coverage SET latest_year=%s,latest_quarter=%s,result_url=%s,
        state=CASE WHEN published_id IS NOT NULL AND (covered_year IS NULL OR (covered_year,covered_quarter)<(%s,%s))
                   THEN 'needs_update' ELSE state END,updated_at=NOW()
        WHERE company=%s AND (latest_year IS NULL OR (latest_year,latest_quarter)<(%s,%s))""",
        (year, quarter, url, year, quarter, company, year, quarter))


def validate_publication(report, company, locale):
    model = report.get("investment_model") or {}
    if (report.get("scope") != "company" or report.get("company") != company or report.get("locale") != locale
        or report.get("is_public") or report.get("research_profile") != "editorial-v1"
        or not report.get("pipeline", {}).get("verification", {}).get("passed")
        or len(report.get("sections", [])) != 10 or len(report.get("financial_history", [])) < 3
        or not model.get("available") or len(model.get("cases", [])) != 3 or not model.get("cross_check_methods")):
        raise ValueError("Only an audited editorial company draft with history and three scenarios can be published")


def publish(company, locale, draft_id):
    """Operator-only Python/CLI action. Never promote an existing user's private record."""
    company = canonical_company(company)
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT draft_id,draft_year,draft_quarter,latest_year,latest_quarter,published_id,state FROM thesis_coverage WHERE company=%s AND locale=%s FOR UPDATE", (company, locale))
            coverage = cur.fetchone()
            if not coverage or coverage[0] != draft_id:
                raise ValueError("The selected draft is no longer the current editorial candidate")
            if coverage[3] and (coverage[1], coverage[2]) < (coverage[3], coverage[4]):
                raise ValueError("A newer official result requires a new draft")
            if coverage[6] == "published" and coverage[5]:
                return coverage[5]
            cur.execute("""SELECT r.content,r.is_public FROM full_reports r WHERE r.id=%s AND EXISTS
                (SELECT 1 FROM full_report_access a WHERE a.report_id=r.id AND a.user_id=%s) FOR UPDATE""", (draft_id, EDITOR))
            row = cur.fetchone()
            if not row:
                raise ValueError("Editorial draft not found")
            report = stored_report(row)
            validate_publication(report, company, locale)
            public_id = str(uuid.uuid4())
            report = {**report, "id": public_id, "is_public": True,
                      "created_at": datetime.now(timezone.utc).isoformat(),
                      "publication": {"reviewed": True, "covered_year": coverage[1], "covered_quarter": coverage[2]}}
            cur.execute("""INSERT INTO full_reports(id,cache_key,company,period,locale,kind,is_public,content)
                VALUES (%s,%s,%s,'Company overview',%s,'company',TRUE,%s::jsonb)""",
                (public_id, "library:" + public_id, company, locale, json.dumps(report)))
            cur.execute("""UPDATE thesis_coverage SET published_id=%s,covered_year=draft_year,covered_quarter=draft_quarter,
                state='published',updated_at=NOW() WHERE company=%s AND locale=%s""", (public_id, company, locale))
        conn.commit()
        return public_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def prepare(company, locale, year, quarter):
    from full_reports import open_company_report
    from report_auth import SessionUser
    from report_runtime import editorial_preparation
    company = canonical_company(company)
    year, quarter = canonical_period(year, quarter)
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT latest_year,latest_quarter FROM thesis_coverage WHERE company=%s AND locale=%s", (company, locale))
            latest = cur.fetchone()
            if latest and latest[0] and (year, quarter) < tuple(latest):
                raise ValueError("A newer official result must be included before preparation")
    finally:
        conn.close()
    token = editorial_preparation.set(f"{year}Q{quarter}")
    try:
        result = open_company_report(OpenCompanyReport(company=company, locale=locale), SessionUser(EDITOR, plan="premium"))
    finally:
        editorial_preparation.reset(token)
    report = result["report"]
    validate_publication(report, company, locale)
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO thesis_coverage(company,locale,state,draft_id,draft_year,draft_quarter)
                VALUES (%s,%s,'review',%s,%s,%s) ON CONFLICT(company,locale) DO UPDATE
                SET draft_id=EXCLUDED.draft_id,draft_year=EXCLUDED.draft_year,draft_quarter=EXCLUDED.draft_quarter,
                    state='review',updated_at=NOW()
                WHERE (thesis_coverage.draft_year IS NULL OR
                    (thesis_coverage.draft_year,thesis_coverage.draft_quarter)<=(EXCLUDED.draft_year,EXCLUDED.draft_quarter))
                AND (thesis_coverage.latest_year IS NULL OR
                    (thesis_coverage.latest_year,thesis_coverage.latest_quarter)<=(EXCLUDED.draft_year,EXCLUDED.draft_quarter))""", (company, locale, report["id"], year, quarter))
            if cur.rowcount != 1:
                raise ValueError("A more recent editorial draft already exists")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"report_id": report["id"], "reused": result["reused"], "state": "review"}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Prepare and review company theses outside the user request path")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status")
    for action in ("prepare", "publish", "review"):
        item = sub.add_parser(action)
        item.add_argument("company")
        item.add_argument("--locale", choices=("pt", "en"), default="pt")
        if action == "prepare":
            item.add_argument("--year", type=int, required=True)
            item.add_argument("--quarter", choices=(1, 2, 3, 4), type=int, required=True)
        else:
            item.add_argument("--draft-id", required=True)
    args = parser.parse_args()
    # A CLI process must not import main or launch the API's startup maintenance jobs.
    import os
    import psycopg2
    from dotenv import load_dotenv
    import full_reports
    load_dotenv()
    dsn = os.getenv("DATABASE_URL", "").split("?schema=")[0]
    if not dsn:
        parser.error("DATABASE_URL must be configured for the editorial CLI")
    full_reports.connection = lambda: psycopg2.connect(dsn)
    if args.action == "prepare":
        result = prepare(args.company, args.locale, args.year, args.quarter)
    elif args.action == "publish":
        result = {"published_id": publish(args.company, args.locale, args.draft_id)}
    elif args.action == "review":
        conn = connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""SELECT r.content,r.is_public FROM full_reports r WHERE r.id=%s AND r.company=%s AND r.locale=%s
                    AND EXISTS (SELECT 1 FROM full_report_access a WHERE a.report_id=r.id AND a.user_id=%s)""",
                    (args.draft_id, canonical_company(args.company), args.locale, EDITOR))
                row = cur.fetchone()
                if not row:
                    raise ValueError("Editorial draft not found")
                result = stored_report(row)
        finally:
            conn.close()
    else:
        conn = connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""SELECT c.company,c.locale,c.state,c.draft_id,c.published_id,c.latest_year,c.latest_quarter,c.covered_year,c.covered_quarter,
                    (SELECT COUNT(*) FROM thesis_requests r WHERE r.company=c.company AND r.locale=c.locale)
                    FROM thesis_coverage c ORDER BY (c.state='needs_update') DESC,c.company,c.locale""")
                columns = ("company", "locale", "state", "draft_id", "published_id", "latest_year", "latest_quarter", "covered_year", "covered_quarter", "requests")
                result = [dict(zip(columns, row)) for row in cur.fetchall()]
        finally:
            conn.close()
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
