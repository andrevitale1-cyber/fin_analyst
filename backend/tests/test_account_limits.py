import json
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import sqlite3
import sys
import threading
from unittest.mock import Mock

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import account_limits as limits
import full_reports as reports
from report_auth import SessionUser, require_report_user
from openai_client import OpenAIError
from test_company_report_content import valid_report


@pytest.fixture
def database(monkeypatch):
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript("""CREATE TABLE account_usage(id TEXT PRIMARY KEY,user_id TEXT,kind TEXT,usage_day DATE,state TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,expires_at TEXT DEFAULT (datetime('now','+15 minutes')));
        CREATE TABLE full_reports(id TEXT PRIMARY KEY,cache_key TEXT UNIQUE,company TEXT,period TEXT,locale TEXT,kind TEXT,
            is_public BOOLEAN,content TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE full_report_access(user_id TEXT,report_id TEXT,analysis_id INTEGER,PRIMARY KEY(user_id,report_id));""")
    lock = threading.RLock()
    class Connection:
        held = False
        @contextmanager
        def cursor(self):
            if not self.held: lock.acquire(); self.held = True
            class Cursor:
                def execute(self, sql, params=()):
                    if sql.startswith("SET LOCAL") or "pg_advisory_xact_lock" in sql: return
                    self.cursor = db.execute(sql.replace("%s", "?").replace("::jsonb", "").replace("NOW()", "CURRENT_TIMESTAMP"),
                                             tuple(value.isoformat() if hasattr(value, "isoformat") else value for value in params))
                def fetchone(self): return self.cursor.fetchone()
                def fetchall(self): return self.cursor.fetchall()
            yield Cursor()
        def commit(self): db.commit()
        def rollback(self): db.rollback()
        def close(self):
            if self.held: self.held = False; lock.release()
    monkeypatch.setattr(limits, "connection", Connection)
    monkeypatch.setattr(reports, "connection", Connection)
    limits._plans.clear()
    yield db, Connection
    db.close()


def finish(factory, ticket):
    conn = factory()
    try:
        with conn.cursor() as cur: limits.complete_usage(cur, ticket)
        conn.commit()
    finally: conn.close()


def test_shared_three_analysis_daily_allowance_and_independent_full_report_limit(database):
    db, factory = database; user = SessionUser("user_free", plan="free")
    for _ in range(3): finish(factory, limits.reserve_usage(user, "analysis"))
    with pytest.raises(HTTPException) as exc: limits.reserve_usage(user, "analysis")
    assert exc.value.status_code == 429
    finish(factory, limits.reserve_usage(user, "full_report"))
    with pytest.raises(HTTPException): limits.reserve_usage(user, "full_report")
    assert db.execute("SELECT COUNT(*) FROM account_usage WHERE state='completed'").fetchone()[0] == 4
    assert limits.access_snapshot(user)["analysis_remaining"] == 0


def test_failure_does_not_consume_allowance_and_stale_pending_reservations_expire(database):
    db, _ = database; user = SessionUser("user_free", plan="free")
    ticket = limits.reserve_usage(user, "full_report"); limits.cancel_usage(ticket)
    assert db.execute("SELECT state FROM account_usage WHERE id=?", (ticket,)).fetchone()[0] == "failed"
    pending = limits.reserve_usage(user, "full_report")
    with pytest.raises(HTTPException): limits.reserve_usage(user, "full_report")
    db.execute("UPDATE account_usage SET expires_at='2000-01-01' WHERE id=?", (pending,)); db.commit()
    assert limits.reserve_usage(user, "full_report")


def test_parallel_requests_cannot_exceed_one_daily_full_report(database):
    user = SessionUser("user_free", plan="free"); gate = threading.Barrier(2)
    def run(_):
        gate.wait()
        try: return limits.reserve_usage(user, "full_report")
        except HTTPException as exc: return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool: outcomes = list(pool.map(run, range(2)))
    assert sum(isinstance(item, str) for item in outcomes) == 1 and 429 in outcomes


def test_allowance_renews_on_sao_paulo_day_not_utc_day(database, monkeypatch):
    _, factory = database; user = SessionUser("user_free", plan="free")
    class Clock(datetime):
        instant = datetime.fromisoformat("2026-10-20T02:59:00+00:00")
        @classmethod
        def now(cls, tz=None): return cls.instant.astimezone(tz)
    monkeypatch.setattr(limits, "datetime", Clock)
    finish(factory, limits.reserve_usage(user, "full_report"))
    with pytest.raises(HTTPException): limits.reserve_usage(user, "full_report")
    Clock.instant = datetime.fromisoformat("2026-10-20T03:00:00+00:00")
    assert limits.reserve_usage(user, "full_report")


def test_premium_is_unlimited_and_client_cannot_self_declare_plan(monkeypatch):
    connection = Mock(side_effect=AssertionError("Premium needs no free reservation"))
    monkeypatch.setattr(limits, "connection", connection)
    assert limits.reserve_usage(SessionUser("user_paid", plan="premium"), "full_report") is None
    with pytest.raises(HTTPException) as exc: limits.plan_for("user_paid")
    assert exc.value.status_code == 401


def test_plan_comes_from_verified_first_party_server_and_rejects_mismatched_identity(monkeypatch):
    limits._plans.clear(); user = SessionUser("user_real", token="verified-session")
    get = Mock(return_value=Mock(json=lambda: {"user_id": "user_other", "plan": "premium"}))
    monkeypatch.setattr(limits.requests, "get", get)
    with pytest.raises(HTTPException) as exc: limits.plan_for(user)
    assert exc.value.status_code == 503
    get.return_value = Mock(json=lambda: {"user_id": "user_real", "plan": "free"})
    assert limits.plan_for(user) == limits.plan_for(user) == "free"
    assert get.call_count == 2
    assert get.call_args.kwargs["headers"] == {"Authorization": "Bearer verified-session"}


def test_analysis_api_uses_authenticated_owner_and_counts_only_successful_results(database):
    _, factory = database; app = FastAPI()
    app.dependency_overrides[require_report_user] = lambda: SessionUser("user_free", plan="free")
    @app.post("/analysis")
    def analyze(fail: bool = False, ticket=Depends(limits.analysis_access)):
        if fail: raise HTTPException(502, "Provider failed")
        finish(factory, ticket)
        return {"ok": True}
    with TestClient(app) as client:
        assert client.post("/analysis", data={"user_id": "another_user"}).status_code == 403
        assert client.post("/analysis?fail=true", data={"user_id": "user_free"}).status_code == 502
        for _ in range(3): assert client.post("/analysis", data={"user_id": "user_free"}).status_code == 200
        assert client.post("/analysis", data={"user_id": "user_free"}).status_code == 429


def test_all_real_generation_endpoints_require_auth_and_premium_query_flag_is_ignored(database, monkeypatch):
    import importlib
    monkeypatch.setattr("psycopg2.connect", Mock())
    main = importlib.import_module("main")
    with TestClient(main.app) as client:
        for route in ("analyze", "analyze-auto", "analyze-call", "analyze-call-auto"):
            response = client.post("/api/" + route, data={"user_id": "user_free", "company": "META", "ticker": "META", "empresa": "META", "ano": "2026", "trimestre": "1T"},
                                   files={"file": ("release.pdf", b"%PDF-test")})
            assert response.status_code == 401
        main.app.dependency_overrides[require_report_user] = lambda: SessionUser("user_free", plan="free")
        try:
            response = client.get("/api/check-access", params={"user_id": "user_free", "is_premium": "true"})
            assert response.status_code == 200 and response.json()["plan"] == "free"
            assert client.get("/api/check-access", params={"user_id": "user_other"}).status_code == 403
        finally:
            main.app.dependency_overrides.pop(require_report_user, None)


@pytest.fixture
def company_ai(monkeypatch):
    sources = [{"id": "S1", "title": "Annual results", "url": "https://example.com/annual", "text": "Annual EPS USD 2.50.", "basis": "primary"}]
    monkeypatch.setattr(reports, "company_evidence", lambda *args: {"as_of": "2026-10-19", "sources": sources})
    ai = Mock(analyze_full_report=Mock(return_value=valid_report()))
    monkeypatch.setattr(reports, "OpenAIClient", lambda **kwargs: ai)
    return ai


def test_new_reports_stay_private_shared_cache_grants_only_own_access_and_reopening_is_free(database, company_ai):
    db, _ = database; a = SessionUser("user_a", plan="free"); b = SessionUser("user_b", plan="free")
    first = reports.open_company_report(reports.OpenCompanyReport(company="META"), a)
    assert first["report"]["is_public"] is False
    assert reports.list_reports(b)["reports"] == []
    with pytest.raises(HTTPException) as exc: reports.get_report(first["report"]["id"], b)
    assert exc.value.status_code == 404
    second = reports.open_company_report(reports.OpenCompanyReport(company="META"), b)
    assert second["reused"] and second["report"]["is_public"] is False
    assert reports.open_company_report(reports.OpenCompanyReport(company="META"), a)["reused"]
    assert company_ai.analyze_full_report.call_count == 1
    with pytest.raises(HTTPException) as exc: reports.open_company_report(reports.OpenCompanyReport(company="MSFT"), a)
    assert exc.value.status_code == 429 and company_ai.analyze_full_report.call_count == 1
    assert db.execute("SELECT COUNT(*) FROM account_usage WHERE state='completed'").fetchone()[0] == 2


def test_failed_full_report_releases_quota_and_public_report_reads_cost_no_allowance(database, company_ai):
    db, _ = database; user = SessionUser("user_free", plan="free")
    company_ai.analyze_full_report.side_effect = OpenAIError("Provider failed")
    with pytest.raises(HTTPException): reports.open_company_report(reports.OpenCompanyReport(company="META"), user)
    assert limits.access_snapshot(user)["full_report_remaining"] == 1
    company_ai.analyze_full_report.side_effect = None
    report = reports.open_company_report(reports.OpenCompanyReport(company="META"), user)["report"]
    db.execute("UPDATE full_reports SET is_public=TRUE WHERE id=?", (report["id"],)); db.commit()
    another = SessionUser("user_public_reader", plan="free")
    assert reports.open_company_report(reports.OpenCompanyReport(company="META"), another)["report"]["is_public"]
    assert limits.access_snapshot(another)["full_report_remaining"] == 1
