"""One-time, explicitly authorized public-gallery curation. No public admin endpoint."""
import logging
import os
import hashlib
import json
import uuid
from threading import Thread

from report_auth import SessionUser

JOB = "public-gallery-2026-10-19-petrobras"
WEG_REPORT_ID = "a206fa64-3ac6-471d-9182-c2b29258580e"
logger = logging.getLogger("uvicorn.error")


def curate():
    from full_reports import connection, open_company_report, OpenCompanyReport
    conn = connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_lock(20261019, 9341)")
            if not cur.fetchone()[0]:
                return
            cur.execute("""CREATE TABLE IF NOT EXISTS maintenance_tasks (
                id TEXT PRIMARY KEY, state TEXT NOT NULL, report_id TEXT, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
            cur.execute("SELECT state FROM maintenance_tasks WHERE id=%s", (JOB,))
            previous = cur.fetchone()
            if previous and previous[0] == "completed":
                return
            cur.execute("""INSERT INTO maintenance_tasks(id,state) VALUES (%s,'running')
                ON CONFLICT(id) DO UPDATE SET state='running',updated_at=NOW()""", (JOB,))
            cur.execute("""DELETE FROM full_reports WHERE id=%s AND company='WEGE3'
                AND (created_at AT TIME ZONE 'America/Sao_Paulo')::date=DATE '2026-10-19'""", (WEG_REPORT_ID,))
            logger.info("curated_reports_job weg_deleted=%d", cur.rowcount)
            public_key = hashlib.sha256(JOB.encode()).hexdigest()
            cur.execute("SELECT id FROM full_reports WHERE cache_key=%s AND is_public", (public_key,))
            public = cur.fetchone()
            if public:
                report_id = public[0]
            else:
                result = open_company_report(OpenCompanyReport(company="PETR4", locale="pt"),
                                             SessionUser("public-demo-curator", plan="premium"))
                report_id = str(uuid.uuid4())
                # Publish a separate curated copy; never change another user's private report visibility.
                report = {**result["report"], "id": report_id, "is_public": True}
                cur.execute("""INSERT INTO full_reports(id,cache_key,company,period,locale,kind,is_public,content)
                    VALUES (%s,%s,'PETR4',%s,'pt','company',TRUE,%s::jsonb)""",
                            (report_id, public_key, report["period"], json.dumps(report)))
            cur.execute("UPDATE maintenance_tasks SET state='completed',report_id=%s,updated_at=NOW() WHERE id=%s", (report_id, JOB))
            logger.info("curated_reports_job completed report_id=%s company=PETR4", report_id)
    except Exception as exc:
        logger.error("curated_reports_job failed error_type=%s", type(exc).__name__)
        with conn.cursor() as cur:
            cur.execute("UPDATE maintenance_tasks SET state='failed',updated_at=NOW() WHERE id=%s", (JOB,))
    finally:
        conn.close()


def start_if_enabled():
    if os.getenv("VALIDATE_APPLE_REPORT_20261020") == "1":
        Thread(target=validate_apple_report, name="validate-apple-report", daemon=True).start()
    if os.getenv("REPAIR_REPORT_COVERAGE_20261019") == "1":
        Thread(target=repair_reports, name="repair-report-coverage", daemon=True).start()
    if os.getenv("CURATE_PUBLIC_REPORTS_20261019") == "1":
        Thread(target=curate, name="curated-public-reports", daemon=True).start()


def validate_apple_report():
    """One private, metered-cost validation of the user-reported failure; never publish it."""
    from full_reports import connection, open_company_report, OpenCompanyReport
    conn = connection()
    conn.autocommit = True
    task = "report-agents-AAPL-20261020-2"
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (task,))
            if not cur.fetchone()[0]:
                return
            cur.execute("CREATE TABLE IF NOT EXISTS maintenance_tasks (id TEXT PRIMARY KEY, state TEXT NOT NULL, report_id TEXT, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            cur.execute("SELECT state FROM maintenance_tasks WHERE id=%s", (task,))
            if cur.fetchone():
                return  # One attempt only, including failures; restarting must not repeat paid calls.
            cur.execute("INSERT INTO maintenance_tasks(id,state) VALUES (%s,'running')", (task,))
            result = open_company_report(OpenCompanyReport(company="AAPL", locale="en"), SessionUser("public-demo-curator", plan="premium"))
            cur.execute("UPDATE maintenance_tasks SET state='completed',report_id=%s,updated_at=NOW() WHERE id=%s", (result["report"]["id"], task))
            logger.info("apple_report_validation completed report_id=%s", result["report"]["id"])
    except Exception as exc:
        logger.error("apple_report_validation failed error_type=%s", type(exc).__name__)
        with conn.cursor() as cur:
            cur.execute("UPDATE maintenance_tasks SET state='failed',updated_at=NOW() WHERE id=%s", (task,))
    finally:
        conn.close()


def repair_reports():
    """Replace the two user-reported incomplete demos only after validated regeneration."""
    from full_reports import connection, open_company_report, OpenCompanyReport
    for target, company, locale in (
        ("4d25c3c1-3e7d-4685-b9c1-13a2a2495192", "NKE", "en"),
        ("d1173bb0-25b4-409c-a5a1-544cdad232c7", "PETR4", "pt"),
    ):
        conn = connection()
        conn.autocommit = True
        job = "repair-financial-coverage-20261019:" + target
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (job,))
                if not cur.fetchone()[0]:
                    continue
                cur.execute("CREATE TABLE IF NOT EXISTS maintenance_tasks (id TEXT PRIMARY KEY, state TEXT NOT NULL, report_id TEXT, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
                cur.execute("SELECT state FROM maintenance_tasks WHERE id=%s", (job,))
                previous = cur.fetchone()
                if previous and previous[0] == "completed":
                    continue
                cur.execute("INSERT INTO maintenance_tasks(id,state) VALUES (%s,'running') ON CONFLICT(id) DO UPDATE SET state='running',updated_at=NOW()", (job,))
                result = open_company_report(OpenCompanyReport(company=company, locale=locale), SessionUser("public-demo-curator", plan="premium"))
                report = {**result["report"], "id": target, "is_public": True}
                cur.execute("UPDATE full_reports SET content=%s::jsonb WHERE id=%s AND is_public", (json.dumps(report), target))
                if cur.rowcount != 1:
                    raise ValueError("Expected public report was not found")
                cur.execute("UPDATE maintenance_tasks SET state='completed',report_id=%s,updated_at=NOW() WHERE id=%s", (target, job))
                logger.info("report_coverage_repair completed company=%s report_id=%s", company, target)
        except Exception as exc:
            logger.error("report_coverage_repair failed company=%s error_type=%s", company, type(exc).__name__)
            with conn.cursor() as cur:
                cur.execute("UPDATE maintenance_tasks SET state='failed',updated_at=NOW() WHERE id=%s", (job,))
        finally:
            conn.close()
