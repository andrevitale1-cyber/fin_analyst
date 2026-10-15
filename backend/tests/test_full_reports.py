import copy
import importlib
import json
from pathlib import Path
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, MagicMock

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import full_reports as reports
import report_auth
from openai_client import OpenAIClient, OpenAIError


SOURCES = [{"id": "S1", "title": "Official release", "url": "https://www.sec.gov/release", "text": "Revenue grew.", "basis": "primary"}]


def content():
    return {"coverage": "One release.", "score": 4,
            "sections": [{"id": key, "title": key, "summary": "Evidence.", "paragraphs": [], "bullets": [], "source_ids": ["S1"]}
                         for key in ("thesis", "business", "financials", "moat", "management", "risks", "valuation")],
            "metrics": [], "watchpoints": [],
            "valuation": {"available": False, "base_eps": None, "currency": None, "source_id": None, "reason": "Annual EPS missing."}}


def arguments(user="user_first"):
    return dict(user_id=user, analysis_id=1, company="AAPL", period="1Q/2026", locale="en", kind="report", sources=SOURCES,
                client=Mock(analyze_full_report=Mock(return_value=content())))


def test_cache_dimensions_and_private_upload_isolation():
    args = ["AAPL", 2026, 1, "en", "report", SOURCES, "model-a"]
    key = reports.cache_key(*args)
    assert key == reports.cache_key(*copy.deepcopy(args))
    for index, replacement in [(0, "MSFT"), (1, 2025), (2, 2), (3, "pt"), (4, "transcript"), (6, "model-b")]:
        changed = copy.deepcopy(args); changed[index] = replacement
        assert key != reports.cache_key(*changed)
    changed = copy.deepcopy(args); changed[5][0]["text"] += " Revised filing."
    assert key != reports.cache_key(*changed)
    assert reports.cache_key(*args, private_user="user_one") != reports.cache_key(*args, private_user="user_two")


def test_shared_hit_links_the_second_user_without_ai():
    cur = Mock()
    report = {**content(), "id": "shared-id"}
    cur.fetchone.return_value = (report,)
    args = arguments("user_second")
    result = reports.generate_or_reuse(cur, "a" * 64, **args)
    assert result == {"report": report, "reused": True}
    args["client"].analyze_full_report.assert_not_called()
    assert cur.execute.call_args.args[1] == ("user_second", "shared-id", 1)


def test_failed_generation_cannot_be_saved():
    cur = Mock(); cur.fetchone.return_value = None
    args = arguments(); args["client"].analyze_full_report.side_effect = OpenAIError("failure")
    with pytest.raises(OpenAIError):
        reports.generate_or_reuse(cur, "b" * 64, **args)
    assert not any("INSERT INTO" in call.args[0] for call in cur.execute.call_args_list)


def test_simultaneous_requests_generate_once_after_transaction_lock():
    lock, contents, links = threading.Lock(), {}, set()
    ai = Mock(return_value=content())
    ready = threading.Barrier(2)

    class Cursor:
        def execute(self, sql, params=None):
            if "pg_advisory_xact_lock" in sql: lock.acquire()
            elif "SELECT content" in sql: self.row = (contents[params[0]],) if params[0] in contents else None
            elif "INSERT INTO full_reports " in sql: contents[params[1]] = json.loads(params[-1])
            elif "INSERT INTO full_report_access" in sql: links.add(params[0])
        def fetchone(self): return self.row

    def run(user):
        cur = Cursor(); args = arguments(user); args["client"].analyze_full_report = ai
        ready.wait()
        try: return reports.generate_or_reuse(cur, "c" * 64, **args)
        finally: lock.release()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run, ["user_one", "user_two"]))
    assert ai.call_count == 1
    assert results[0]["report"]["id"] == results[1]["report"]["id"]
    assert sorted(result["reused"] for result in results) == [False, True]
    assert links == {"user_one", "user_two"}


@pytest.fixture
def rsa_key(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(report_auth, "signing_keys", lambda _: Mock(get_signing_key_from_jwt=lambda token: Mock(key=key.public_key())))
    monkeypatch.setenv("CLERK_ISSUER", "https://clerk.example.com")
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "https://app.example.com")
    return key


def session_token(key, **overrides):
    now = int(time.time())
    claims = {"sub": "user_one", "iss": "https://clerk.example.com", "azp": "https://app.example.com", "exp": now + 60, "iat": now, "nbf": now}
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


def test_signed_clerk_session_is_accepted(rsa_key):
    assert report_auth.require_report_user("Bearer " + session_token(rsa_key)) == "user_one"


@pytest.mark.parametrize("overrides", [{"azp": "https://untrusted.example.com"}, {"iss": "https://wrong.example.com"}, {"exp": 1}, {"nbf": 9999999999}, {"sub": "other"}])
def test_invalid_session_claims_are_rejected(rsa_key, overrides):
    with pytest.raises(HTTPException) as exc:
        report_auth.require_report_user("Bearer " + session_token(rsa_key, **overrides))
    assert exc.value.status_code == 401


def test_missing_and_forged_token_rejected(rsa_key):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    for value in ("", "Bearer " + session_token(other), "Bearer broken"):
        with pytest.raises(HTTPException) as exc: report_auth.require_report_user(value)
        assert exc.value.status_code == 401


def test_owner_check_precedes_source_and_shared_cache(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    with pytest.raises(HTTPException) as exc:
        reports.open_report(reports.OpenReport(analysis_id=5), user_id="user_other")
    assert exc.value.status_code == 404
    assert cur.execute.call_count == 1
    assert cur.execute.call_args.args[1] == (5, "user_other")
    conn.rollback.assert_called_once()


@pytest.mark.parametrize("evidence", [
    ("public", "SEC release", "https://www.sec.gov/release", "Source revenue grew."),
    ("private", "Uploaded document", None, "Private source revenue grew."),
    None,
])
def test_open_report_route_retains_source_scope_and_never_returns_source_body(monkeypatch, evidence):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI(); app.include_router(reports.router)
    app.dependency_overrides[report_auth.require_report_user] = lambda: "user_one"
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    original = {"metadata": {}, "analise_completa": "Prior saved analysis."}
    cur.fetchone.side_effect = [("Apple", "2026", "1T", json.dumps(original)), evidence, None]
    monkeypatch.setattr(reports, "connection", lambda: conn)
    ai = Mock(model="test-model", analyze_full_report=Mock(return_value=content()))
    monkeypatch.setattr(reports, "OpenAIClient", lambda: ai)
    response = TestClient(app).post("/api/full-reports", json={"analysis_id": 1, "locale": "en"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["reused"] is False and result["report"]["company"] == "AAPL"
    assert result["report"]["period"] == "1Q/2026" and result["report"]["score"] is None
    assert all("text" not in source for source in result["report"]["sources"])
    if evidence is None: assert "original document was not retained" in result["report"]["coverage"]
    elif evidence[0] == "private": assert "uploaded" in result["report"]["coverage"]
    else: assert "Source document" in result["report"]["coverage"]
    conn.commit.assert_called_once()


def test_report_detail_requires_user_link(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    with pytest.raises(HTTPException) as exc: reports.get_report("known-shared-id", "user_other")
    assert exc.value.status_code == 404
    assert cur.execute.call_args.args[1] == ("known-shared-id", "user_other")


def test_new_endpoints_require_authentication(monkeypatch):
    monkeypatch.setattr("psycopg2.connect", Mock())
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kw: False)
    main = importlib.import_module("main")
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    for path in ("/api/full-reports", "/api/full-reports/known-id"):
        assert client.get(path).status_code == 401
    assert client.post("/api/full-reports", json={"analysis_id": 1, "locale": "en"}).status_code == 401


def test_structured_output_is_requested_and_truncated_response_rejected(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    original = httpx.Client
    seen = []
    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"status": "incomplete", "output": []})
    monkeypatch.setattr(httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(OpenAIError): OpenAIClient().analyze_full_report("Source evidence", reports.report_schema())
    assert seen[0]["text"]["format"]["type"] == "json_schema"
    assert seen[0]["text"]["format"]["strict"] is True and seen[0]["store"] is False


def test_schema_failure_prevents_serving_a_half_migrated_application(monkeypatch):
    monkeypatch.setattr("psycopg2.connect", Mock())
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kw: False)
    main = importlib.import_module("main")
    conn = Mock()
    monkeypatch.setattr(main, "get_db_connection", lambda: conn)
    monkeypatch.setattr(main, "create_full_report_tables", Mock(side_effect=RuntimeError("DDL failed")))
    with pytest.raises(RuntimeError, match="DDL failed"):
        main.init_db()
    conn.commit.assert_not_called()
    conn.close.assert_called_once()
