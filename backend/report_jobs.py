"""Durable Postgres jobs; authentication, quota and report access stay server-side."""
from contextvars import ContextVar
import hashlib
import logging
import os
from threading import Event, Thread
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal

from account_limits import reserve_usage, cancel_usage, plan_for
from full_reports import connection, canonical_company, company_cache_key, OpenCompanyReport, open_company_report, get_report, stored_report
from openai_client import model_for_task
from report_auth import SessionUser, require_report_user
from report_runtime import progress_callback

router = APIRouter(prefix="/api/report-jobs", tags=["Report generation"])
reserved_ticket = ContextVar("report_reserved_ticket", default=None)
stop = Event()
logger = logging.getLogger("uvicorn.error")


def create_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS report_jobs (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL, company TEXT NOT NULL, locale TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('queued','running','completed','failed')),
        stage TEXT NOT NULL DEFAULT 'queued', ticket TEXT, report_id TEXT, reused BOOLEAN NOT NULL DEFAULT FALSE,
        error_detail TEXT, owner TEXT, attempts INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS report_jobs_pending ON report_jobs(state,updated_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS report_jobs_user ON report_jobs(user_id,created_at DESC)")


class StartReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company: str | None = Field(default=None, min_length=1, max_length=100)
    analysis_id: int | None = Field(default=None, gt=0)
    locale: Literal["en", "pt"] = "pt"

    @model_validator(mode="after")
    def one_target(self):
        if (self.company is None) == (self.analysis_id is None):
            raise ValueError("Supply exactly one company or analysis")
        return self


@router.post("", status_code=200)
def enqueue(body: StartReport, user=Depends(require_report_user)):
    from thesis_library import resolve_company, resolve_analysis
    if body.analysis_id:
        return resolve_analysis(body, user)
    return resolve_company(OpenCompanyReport(company=body.company, locale=body.locale), user)


@router.get("/{job_id}")
def status(job_id: str, user=Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT state,stage,report_id,reused,error_detail,company FROM report_jobs WHERE id=%s AND user_id=%s", (job_id, str(user)))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Report job not found.")
        result = dict(zip(("state", "stage", "report_id", "reused", "detail", "company"), row))
        if result["state"] == "completed":
            result.update(get_report(result["report_id"], user))
        return result
    finally:
        conn.close()


def claim():
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""UPDATE report_jobs SET state='failed',error_detail='Report interrupted; please request it again.',updated_at=NOW()
                WHERE state='running' AND attempts>=2 AND updated_at<NOW()-INTERVAL '90 seconds' RETURNING ticket""")
            for expired in cur.fetchall():
                cancel_usage(expired[0])
            cur.execute("""SELECT id,user_id,company,locale,ticket FROM report_jobs
                WHERE (state='queued' OR (state='running' AND updated_at<NOW()-INTERVAL '90 seconds')) AND attempts<2
                ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1""")
            row = cur.fetchone()
            if not row:
                conn.commit()  # Commit exhausted leases even when there is no next job.
                return None
            owner = str(uuid.uuid4())
            cur.execute("UPDATE report_jobs SET state='running',stage='research',owner=%s,attempts=attempts+1,updated_at=NOW() WHERE id=%s", (owner, row[0]))
        conn.commit()
        return (*row, owner)
    finally:
        conn.close()


def process(job):
    job_id, user_id, company, locale, ticket, owner = job
    done = Event()
    def update(stage=None):
        conn = connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE report_jobs SET stage=COALESCE(%s,stage),updated_at=NOW() WHERE id=%s AND owner=%s AND state='running'", (stage, job_id, owner))
                if cur.rowcount != 1:
                    raise RuntimeError("Report job lease lost")
                if ticket:
                    cur.execute("UPDATE account_usage SET expires_at=NOW()+INTERVAL '15 minutes' WHERE id=%s AND state='pending'", (ticket,))
            conn.commit()
        finally:
            conn.close()
    def heartbeat():
        while not done.wait(15):
            try:
                update()
            except Exception:
                logger.warning("report_job_heartbeat_unavailable job=%s", job_id)
    lease = Thread(target=heartbeat, daemon=True, name="report-lease")
    lease.start()
    usage_token = reserved_ticket.set({"ticket": ticket})
    progress_token = progress_callback.set(update)
    try:
        if ticket:
            conn = connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE account_usage SET expires_at=NOW()+INTERVAL '15 minutes' WHERE id=%s AND user_id=%s AND state='pending' AND expires_at>NOW() RETURNING 1", (ticket, user_id))
                    if not cur.fetchone():
                        cur.execute("SELECT 1 FROM account_usage WHERE id=%s AND user_id=%s AND state='completed'", (ticket, user_id))
                        if not cur.fetchone():
                            raise HTTPException(429, "The reservation expired; please request the report again." if locale == "en" else "A reserva expirou; solicite o relatório novamente.")
                conn.commit()
            finally:
                conn.close()
        result = open_company_report(OpenCompanyReport(company=company, locale=locale), SessionUser(user_id, plan="premium"))
        conn = connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE report_jobs SET state='completed',stage='complete',report_id=%s,reused=%s,updated_at=NOW() WHERE id=%s AND owner=%s",
                            (result["report"]["id"], result["reused"], job_id, owner))
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        detail = str(exc.detail) if isinstance(exc, HTTPException) and isinstance(exc.detail, str) else ("We could not finish this report. Please try again." if locale == "en" else "Não foi possível concluir o relatório. Tente novamente.")
        conn = connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE report_jobs SET state='failed',error_detail=%s,updated_at=NOW() WHERE id=%s AND owner=%s", (detail, job_id, owner))
            conn.commit()
        finally:
            conn.close()
        logger.warning("report_job_failed job=%s error_type=%s", job_id, type(exc).__name__)
    finally:
        done.set()
        reserved_ticket.reset(usage_token)
        progress_callback.reset(progress_token)
        # A completed analysis owns its completed ticket; unused/failed reservations are released.
        conn = connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT owner FROM report_jobs WHERE id=%s", (job_id,))
                row = cur.fetchone()
                if row and row[0] == owner:
                    cancel_usage(ticket)
        finally:
            conn.close()


def worker():
    while not stop.is_set():
        try:
            job = claim()
            if job:
                process(job)
                continue
        except Exception:
            logger.warning("report_queue_temporarily_unavailable")
        stop.wait(3)


def start_worker():
    if os.getenv("REPORT_JOB_WORKER", "0") != "0":
        stop.clear()
        Thread(target=worker, daemon=True, name="report-worker").start()
