import json
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
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
from test_company_report_content import complete_report as valid_report


@pytest.fixture
def database(monkeypatch):
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript("""CREATE TABLE account_usage(id TEXT PRIMARY KEY,user_id TEXT,kind TEXT,usage_day DATE,state TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,expires_at TEXT DEFAULT (datetime('now','+15 minutes')));
        CREATE TABLE trial_users(user_id TEXT PRIMARY KEY,trial_start TEXT NOT NULL);
        CREATE TABLE historico(id INTEGER,user_id TEXT,data_criacao TEXT);
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
                                             tuple(value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime) else value.isoformat() if hasattr(value, "isoformat") else value for value in params))
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


def test_trial_has_ten_shared_analyses_and_no_full_report_generation(database):
    db, factory = database; user = SessionUser("user_free", plan="free")
    for _ in range(10): finish(factory, limits.reserve_usage(user, "analysis"))
    with pytest.raises(HTTPException) as exc: limits.reserve_usage(user, "analysis")
    assert exc.value.status_code == 429
    with pytest.raises(HTTPException) as exc: limits.reserve_usage(user, "full_report")
    assert exc.value.status_code == 403
    snapshot = limits.access_snapshot(user)
    assert snapshot["analysis_remaining"] == 0 and snapshot["has_access"]
    assert not snapshot["can_analyze"] and snapshot["resets_at"] is None


def test_failure_releases_trial_allowance_and_pending_reservations_count(database):
    db, factory = database; user = SessionUser("user_free", plan="free")
    for _ in range(9): finish(factory, limits.reserve_usage(user, "analysis"))
    ticket = limits.reserve_usage(user, "analysis")
    with pytest.raises(HTTPException): limits.reserve_usage(user, "analysis")
    limits.cancel_usage(ticket)
    pending = limits.reserve_usage(user, "analysis")
    db.execute("UPDATE account_usage SET expires_at='2000-01-01' WHERE id=?", (pending,)); db.commit()
    assert limits.reserve_usage(user, "analysis")


def test_parallel_requests_cannot_exceed_trial_allowance(database):
    _, factory = database; user = SessionUser("user_free", plan="free")
    for _ in range(9): finish(factory, limits.reserve_usage(user, "analysis"))
    gate = threading.Barrier(2)
    def run(_):
        gate.wait()
        try: return limits.reserve_usage(user, "analysis")
        except HTTPException as exc: return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool: outcomes = list(pool.map(run, range(2)))
    assert sum(isinstance(item, str) for item in outcomes) == 1 and 429 in outcomes


def test_expired_trial_cannot_read_or_generate_and_does_not_restart(database):
    db, _ = database; user = SessionUser("user_old", plan="free")
    start = (datetime.now(timezone.utc) - timedelta(days=7, seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("INSERT INTO trial_users VALUES (?,?)", (str(user),start)); db.commit()
    for operation in (lambda: limits.require_active_user(user), lambda: limits.reserve_usage(user,"analysis")):
        with pytest.raises(HTTPException) as exc: operation()
        assert exc.value.status_code == 403
    assert limits.access_snapshot(user)["has_access"] is False
    assert db.execute("SELECT trial_start FROM trial_users").fetchone()[0] == start


def test_legacy_usage_preserves_original_trial_start(database):
    db, _ = database; user = SessionUser("user_legacy", plan="free")
    db.execute("INSERT INTO account_usage(id,user_id,kind,usage_day,state,created_at) VALUES ('old',?,'analysis','2026-01-01','completed','2026-01-01 00:00:00')", (str(user),)); db.commit()
    assert limits.access_snapshot(user)["has_access"] is False


def test_legacy_analysis_history_does_not_receive_a_new_trial(database):
    db,_ = database; user = SessionUser('user_legacy_history',plan='free')
    db.execute("INSERT INTO historico VALUES (1,?,'2026-01-01 00:00:00')",(str(user),)); db.commit()
    assert not limits.access_snapshot(user)['has_access']


def test_premium_has_fifty_analyses_per_month_and_can_generate_reports(database):
    _, factory = database; user = SessionUser("user_paid", plan="premium")
    for _ in range(50): finish(factory, limits.reserve_usage(user,"analysis"))
    with pytest.raises(HTTPException) as exc: limits.reserve_usage(user,"analysis")
    assert exc.value.status_code == 429
    assert limits.reserve_usage(user,"full_report") is None
    assert limits.access_snapshot(user)["analysis_remaining"] == 0
    with pytest.raises(HTTPException) as exc: limits.plan_for("user_paid")
    assert exc.value.status_code == 401


def test_previous_month_usage_does_not_reduce_current_premium_allowance(database):
    db, _ = database; user = SessionUser("user_paid", plan="premium")
    previous = datetime.now(limits.TIMEZONE).replace(day=1,hour=0,minute=0,second=0,microsecond=0) - timedelta(days=1)
    db.execute("INSERT INTO account_usage(id,user_id,kind,usage_day,state,created_at) VALUES ('old',?,'analysis',?,'completed',?)", (str(user),previous.date().isoformat(),previous.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))); db.commit()
    assert limits.access_snapshot(user)["analysis_remaining"] == 50


def test_monthly_allowance_renews_at_sao_paulo_month_boundary(database, monkeypatch):
    db, _ = database; user = SessionUser('user_paid', plan='premium')
    class Clock(datetime):
        instant = datetime.fromisoformat('2026-11-01T02:59:00+00:00')
        @classmethod
        def now(cls, tz=None): return cls.instant.astimezone(tz)
    monkeypatch.setattr(limits,'datetime',Clock)
    for i in range(50):
        db.execute("INSERT INTO account_usage(id,user_id,kind,usage_day,state,created_at) VALUES (?,?,'analysis','2026-10-31','completed','2026-10-31 20:00:00')",(str(i),str(user)))
    db.commit()
    assert limits.access_snapshot(user)['analysis_remaining'] == 0
    Clock.instant = datetime.fromisoformat('2026-11-01T03:00:00+00:00')
    assert limits.access_snapshot(user)['analysis_remaining'] == 50


def test_expired_trial_is_rejected_by_real_read_endpoints(database, monkeypatch):
    monkeypatch.setattr('psycopg2.connect', Mock())
    import main
    db,_ = database
    user = SessionUser('user_expired',plan='free')
    db.execute("INSERT INTO trial_users VALUES (?,?)",(str(user),(datetime.now(timezone.utc)-timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S'))); db.commit()
    main.app.dependency_overrides[require_report_user] = lambda: user
    try:
        with TestClient(main.app) as client:
            for path in ('/api/history?user_id=user_expired','/api/table-data?user_id=user_expired','/api/recent-analyses','/api/market-data?symbol=PETR4','/api/full-reports'):
                assert client.get(path).status_code == 403, path
            assert client.post('/api/thesis-library/resolve',json={'company':'AAPL'}).status_code == 403
    finally: main.app.dependency_overrides.pop(require_report_user,None)


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
        for _ in range(10): assert client.post("/analysis", data={"user_id": "user_free"}).status_code == 200
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
    from test_company_report_content import stub_pipeline
    monkeypatch.setattr(reports, "company_facts", lambda *a, **kw: {})
    monkeypatch.setattr(reports, "generate_report", stub_pipeline)
    sources = [{"id": "S1", "title": "Annual results", "url": "https://example.com/annual", "text": "Annual EPS USD 2.50.", "basis": "primary"}]
    monkeypatch.setattr(reports, "company_evidence", lambda *args: {"as_of": "2026-10-19", "sources": sources})
    ai = Mock(analyze_full_report=Mock(return_value=valid_report()))
    monkeypatch.setattr(reports, "OpenAIClient", lambda **kwargs: ai)
    return ai


def test_premium_reports_stay_private_and_other_users_cannot_read(database, company_ai):
    _, _ = database; a = SessionUser("user_a", plan="premium"); b = SessionUser("user_b", plan="premium")
    first = reports.open_company_report(reports.OpenCompanyReport(company="META"), a)
    assert first["report"]["is_public"] is False
    assert reports.list_reports(b)["reports"] == []
    with pytest.raises(HTTPException) as exc: reports.get_report(first["report"]["id"], b)
    assert exc.value.status_code == 404
    free = SessionUser("user_free", plan="free")
    with pytest.raises(HTTPException) as exc: reports.open_company_report(reports.OpenCompanyReport(company="META"), free)
    assert exc.value.status_code == 403
    assert reports.open_company_report(reports.OpenCompanyReport(company="META"), a)["reused"]
    assert company_ai.analyze_full_report.call_count == 1


def test_trial_can_read_public_reports_without_spending_analyses(database, company_ai):
    db, _ = database; premium = SessionUser("user_paid", plan="premium")
    report = reports.open_company_report(reports.OpenCompanyReport(company="META"), premium)["report"]
    free = SessionUser("user_free", plan="free")
    db.execute("INSERT INTO full_report_access VALUES (?,?,NULL)",(str(free),report['id'])); db.commit()
    with pytest.raises(HTTPException) as exc: reports.get_report(report['id'],free)
    assert exc.value.status_code == 403
    assert reports.list_reports(free)["reports"] == []
    db.execute("UPDATE full_reports SET is_public=TRUE WHERE id=?", (report["id"],)); db.commit()
    assert reports.get_report(report['id'],free)["report"]["is_public"]
    assert limits.access_snapshot(free)["analysis_remaining"] == 10
