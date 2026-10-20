import copy
import importlib
import json
import sqlite3
from contextlib import contextmanager
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


@pytest.fixture(autouse=True)
def isolate_usage_service(monkeypatch):
    from test_company_report_content import stub_pipeline
    monkeypatch.setattr(reports, "company_facts", lambda *a, **kw: {})
    monkeypatch.setattr(reports, "generate_report", stub_pipeline)
    monkeypatch.setattr(reports, "reserve_usage", lambda *args: None)
    monkeypatch.setattr(reports, "cancel_usage", lambda *args: None)


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
    report = {**content(), "id": "shared-id", "is_public": True}
    cur.fetchone.return_value = (report, True)
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
            elif "SELECT content" in sql: self.row = (contents[params[0]], contents[params[0]]["is_public"]) if params[0] in contents else None
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


@pytest.mark.parametrize("company", ["Apple", "WEGE3", "NIKE"])
def test_history_full_report_uses_company_scope_without_loading_private_or_quarterly_evidence(monkeypatch, company):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI(); app.include_router(reports.router)
    app.dependency_overrides[report_auth.require_report_user] = lambda: "user_one"
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = (company,)
    monkeypatch.setattr(reports, "connection", lambda: conn)
    company_report = Mock(return_value={"report": {"company": reports.canonical_company(company), "scope": "company"}, "reused": True})
    monkeypatch.setattr(reports, "open_company_report", company_report)
    monkeypatch.setattr(reports, "generate_or_reuse", Mock(side_effect=AssertionError("No quarterly expansion")))
    response = TestClient(app).post("/api/full-reports", json={"analysis_id": 1, "locale": "en"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["reused"] is True and result["report"]["scope"] == "company"
    assert result["report"]["company"] == reports.canonical_company(company)
    body, user = company_report.call_args.args
    assert body.company == company and body.locale == "en" and user == "user_one"
    cur.execute.assert_called_once()
    assert "SELECT empresa FROM historico" in cur.execute.call_args.args[0]
    assert cur.execute.call_args.args[1] == (1, "user_one")
    conn.close.assert_called_once()


def test_private_report_detail_requires_user_link(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    with pytest.raises(HTTPException) as exc: reports.get_report("known-shared-id", "user_other")
    assert exc.value.status_code == 404
    assert cur.execute.call_args.args[1] == ("known-shared-id", "user_other")


@pytest.fixture
def gallery_database(monkeypatch):
    db = sqlite3.connect(":memory:")
    db.executescript("""CREATE TABLE full_reports (id TEXT, content TEXT, is_public BOOLEAN, created_at TEXT);
        CREATE TABLE full_report_access (user_id TEXT, report_id TEXT);""")
    for report_id, public in [("demo", True), ("own", False), ("other", False)]:
        report = {**content(), "id": report_id, "company": "AAPL", "period": "1Q/2026",
                  "locale": "en", "kind": "report", "created_at": "2026-10-14", "is_public": not public}
        # Deliberately conflicting JSON proves the stored server flag governs visibility metadata.
        db.execute("INSERT INTO full_reports VALUES (?,?,?,?)", (report_id, json.dumps(report), public, report["created_at"]))
    db.executemany("INSERT INTO full_report_access VALUES (?,?)", [
        ("user_one", "demo"), ("user_two", "demo"), ("user_one", "own"), ("user_two", "other")])
    db.commit()

    class Connection:
        @contextmanager
        def cursor(self):
            class Cursor:
                def execute(self, sql, params): self.cursor = db.execute(sql.replace("%s", "?").replace("FOR UPDATE", ""), params)
                def fetchone(self): return self.cursor.fetchone()
                def fetchall(self): return self.cursor.fetchall()
            yield Cursor()
        def close(self): pass
        def commit(self): db.commit()
        def rollback(self): db.rollback()

    monkeypatch.setattr(reports, "connection", Connection)
    monkeypatch.setattr(reports, "OpenAIClient", Mock(side_effect=AssertionError("Browsing must never generate")))
    yield db
    db.close()


def test_gallery_includes_public_demos_and_only_own_private_reports_without_duplicates(gallery_database):
    before = gallery_database.total_changes
    result = reports.list_reports("user_one")["reports"]
    assert [(r["id"], r["is_public"]) for r in result] == [("demo", True), ("own", False)]
    assert [r["id"] for r in reports.list_reports("user_new")["reports"]] == ["demo"]
    assert gallery_database.total_changes == before


def test_gallery_shows_only_latest_public_microsoft_across_languages_and_keeps_saved_links(gallery_database):
    db = gallery_database
    for report_id, company, locale, date, public in [
        ("ms-old", "Microsoft Corporation", "en", "2026-10-15", True),
        ("ms-new", "MSFT", "pt", "2026-10-17", True),
        ("ms-mid", "MSFT", "en", "2026-10-16", True),
        ("ms-private", "MSFT", "en", "2026-10-18", False),
    ]:
        report = {**content(), "id": report_id, "company": company, "period": "Company overview", "scope": "company",
                  "locale": locale, "kind": "company", "created_at": date}
        db.execute("INSERT INTO full_reports VALUES (?,?,?,?)", (report_id, json.dumps(report), public, date))
    db.execute("INSERT INTO full_report_access VALUES (?,?)", ("user_one", "ms-private"))
    db.commit()
    before = db.total_changes
    assert {r["id"] for r in reports.list_reports("user_one")["reports"]} == {"demo", "own", "ms-new", "ms-private"}
    assert reports.get_report("ms-old", "user_new")["report"]["id"] == "ms-old"
    assert db.total_changes == before


def test_owner_can_delete_private_report_without_removing_other_reports(gallery_database):
    assert reports.delete_report("own", "user_one").status_code == 204
    assert gallery_database.execute("SELECT id FROM full_reports WHERE id='own'").fetchone() is None
    assert gallery_database.execute("SELECT * FROM full_report_access WHERE report_id='own'").fetchone() is None
    assert {r["id"] for r in reports.list_reports("user_one")["reports"]} == {"demo"}
    assert reports.get_report("other", "user_two")["report"]["id"] == "other"


@pytest.mark.parametrize("report_id", ["demo", "other", "missing"])
def test_deletion_rejects_public_other_users_and_unknown_reports(gallery_database, report_id):
    before = gallery_database.total_changes
    with pytest.raises(HTTPException) as error:
        reports.delete_report(report_id, "user_one")
    assert error.value.status_code == 404
    assert gallery_database.total_changes == before
    assert len(reports.list_reports("user_one")["reports"]) == 2


def test_deleting_shared_private_access_preserves_other_users_copy(gallery_database):
    gallery_database.execute("INSERT INTO full_report_access VALUES (?,?)", ("user_two", "own"))
    gallery_database.commit()
    reports.delete_report("own", "user_one")
    assert reports.get_report("own", "user_two")["report"]["id"] == "own"
    with pytest.raises(HTTPException): reports.get_report("own", "user_one")
    reports.delete_report("own", "user_two")
    assert gallery_database.execute("SELECT id FROM full_reports WHERE id='own'").fetchone() is None


def test_deletion_rolls_back_on_database_failure(monkeypatch):
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value.fetchone.return_value = ("own",)
    conn.commit.side_effect = RuntimeError("database unavailable")
    monkeypatch.setattr(reports, "connection", lambda: conn)
    with pytest.raises(RuntimeError): reports.delete_report("own", "user_one")
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.parametrize("report_id,user,allowed", [
    ("demo", "user_new", True), ("own", "user_one", True),
    ("own", "user_new", False), ("other", "user_one", False), ("missing", "user_one", False),
])
def test_saved_report_reads_enforce_public_or_owner_access_without_generation(gallery_database, report_id, user, allowed):
    before = gallery_database.total_changes
    if allowed:
        result = reports.get_report(report_id, user)["report"]
        assert result["id"] == report_id and result["is_public"] is (report_id == "demo")
    else:
        with pytest.raises(HTTPException) as exc: reports.get_report(report_id, user)
        assert exc.value.status_code == 404
    assert gallery_database.total_changes == before


def test_clients_cannot_publish_reports_or_override_visibility():
    from pydantic import ValidationError
    with pytest.raises(ValidationError): reports.OpenReport(analysis_id=1, is_public=True)


def test_retained_public_source_promotes_cached_report_without_regeneration():
    cur = Mock(); cur.fetchone.return_value = ({**content(), "id": "existing"}, False)
    args = arguments()
    result = reports.generate_or_reuse(cur, "d" * 64, **args, is_public=True)
    assert result["reused"] and result["report"]["is_public"]
    args["client"].analyze_full_report.assert_not_called()
    assert any(call.args == ("UPDATE full_reports SET is_public=TRUE WHERE id=%s", ("existing",)) for call in cur.execute.call_args_list)


def test_schema_creation_never_automatically_publishes_private_reports():
    cur = Mock()
    reports.create_tables(cur)
    assert not any("SET is_public=TRUE" in call.args[0] for call in cur.execute.call_args_list)


def test_new_endpoints_require_authentication(monkeypatch):
    monkeypatch.setattr("psycopg2.connect", Mock())
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kw: False)
    main = importlib.import_module("main")
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    for path in ("/api/full-reports", "/api/full-reports/known-id"):
        assert client.get(path).status_code == 401
    assert client.post("/api/full-reports", json={"analysis_id": 1, "locale": "en"}).status_code == 401
    assert client.post("/api/full-reports/company", json={"company": "META", "locale": "en"}).status_code == 401
    assert client.delete("/api/full-reports/known-id").status_code == 401


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


def test_provider_error_keeps_safe_identifiers_without_document_or_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-api-key")
    original = httpx.Client
    def handler(request):
        return httpx.Response(400, headers={"x-request-id": "req_test123"}, json={"error": {
            "message": "PRIVATE_DOCUMENT_TEXT secret-api-key", "code": "invalid_json_schema", "param": "text.format.schema"}})
    monkeypatch.setattr(httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(OpenAIError) as error:
        OpenAIClient().analyze_full_report("Evidence", reports.report_schema())
    assert error.value.status_code == 400 and error.value.code == "invalid_json_schema"
    assert error.value.param == "text.format.schema" and error.value.request_id == "req_test123"
    assert "PRIVATE_DOCUMENT_TEXT" not in str(error.value) and "secret-api-key" not in str(error.value)
    assert OpenAIError("error", code="unsafe\nlog text", param="document text").code is None


@pytest.mark.parametrize("response,code", [
    ({"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}}, "output_token_limit"),
    ({"status": "incomplete"}, "response_incomplete"),
    ({"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "PRIVATE_REASON"}]}]}, "response_refusal"),
    ({"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "invalid"}]}]}, "invalid_json"),
])
def test_full_report_provider_failures_have_distinct_codes_without_retries(monkeypatch, response, code):
    client = OpenAIClient(); client._client = MagicMock()
    client._request = Mock(return_value=response)
    with pytest.raises(OpenAIError) as error: client.analyze_full_report("Evidence", reports.report_schema())
    assert error.value.code == code and "PRIVATE_REASON" not in str(error.value)
    client._request.assert_called_once()


@pytest.mark.parametrize("locale", ["en", "pt"])
@pytest.mark.parametrize("failure", ["provider", "validation"])
def test_company_generation_failure_is_logged_without_sensitive_content_and_rolls_back(monkeypatch, caplog, locale, failure):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    monkeypatch.setattr(reports, "company_evidence", lambda *args: {"as_of": "2026-10-19", "sources": SOURCES})
    ai = Mock(model="test-model")
    if failure == "provider":
        ai.analyze_full_report.side_effect = OpenAIError("PRIVATE_EXCEPTION_TEXT", status_code=400,
                                                       code="invalid_json_schema", request_id="req_123")
    else:
        from test_company_report_content import valid_report
        invalid = valid_report(); invalid["coverage"] = "PRIVATE_GENERATED_TEXT" * 30
        ai.analyze_full_report.return_value = invalid
    monkeypatch.setattr(reports, "OpenAIClient", lambda **kwargs: ai)
    with pytest.raises(HTTPException) as error:
        reports.open_company_report(reports.OpenCompanyReport(company="META", locale=locale), "user_one")
    assert error.value.status_code == 502
    assert ("We could not generate" in error.value.detail) == (locale == "en")
    conn.rollback.assert_called_once(); conn.commit.assert_not_called()
    assert not any("INSERT INTO full_reports" in call.args[0] for call in cur.execute.call_args_list)
    assert "full_report_failed analysis_id=None company=META" in caplog.text
    assert "invalid_json_schema" in caplog.text if failure == "provider" else "string_too_long" in caplog.text
    assert not any(value in caplog.text for value in ("PRIVATE_SOURCE_TEXT", "PRIVATE_EXCEPTION_TEXT", "PRIVATE_GENERATED_TEXT"))


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
