import copy
from contextlib import contextmanager
import json
import sqlite3
from unittest.mock import Mock

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

import full_reports
import thesis_library as library
from report_runtime import editorial_preparation


@pytest.fixture
def database(monkeypatch):
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript("""CREATE TABLE full_reports(id TEXT PRIMARY KEY,cache_key TEXT UNIQUE,company TEXT,period TEXT,
        locale TEXT,kind TEXT,is_public BOOLEAN,content JSON,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE full_report_access(user_id TEXT,report_id TEXT);
        CREATE TABLE historico(id INTEGER,empresa TEXT,user_id TEXT);""")
    class Connection:
        @contextmanager
        def cursor(self):
            class Cursor:
                def execute(self, sql, args=()):
                    sql = sql.replace("%s", "?").replace("::jsonb", "").replace(" FOR UPDATE", "")
                    sql = sql.replace("NOW()-INTERVAL '24 hours'", "datetime('now','-24 hours')").replace("NOW()", "CURRENT_TIMESTAMP")
                    if "pg_advisory" not in sql:
                        self.current = db.execute(sql, args)
                def fetchone(self): return self.current.fetchone()
                def fetchall(self): return self.current.fetchall()
                @property
                def rowcount(self): return self.current.rowcount
            yield Cursor()
        def commit(self): db.commit()
        def rollback(self): db.rollback()
        def close(self): pass
    with Connection().cursor() as cur:
        library.create_tables(cur)
    db.commit()
    monkeypatch.setattr(library, "connection", Connection)
    monkeypatch.setattr(full_reports, "connection", Connection)
    monkeypatch.setattr(full_reports, "OpenAIClient", Mock(side_effect=AssertionError("No model calls in the library")))
    yield db
    db.close()


def add_report(db, report_id, *, public=True, locale="pt", company="MSFT", date="2026-10-20"):
    report = {"id": report_id, "company": company, "scope": "company", "locale": locale,
              "research_profile": "editorial-v1", "sections": [{}] * 10, "financial_history": [{}] * 5,
              "pipeline": {"verification": {"passed": True}}, "investment_model": {"available": True, "cases": [{}] * 3, "cross_check_methods": ["pe"]}}
    db.execute("INSERT INTO full_reports(id,company,locale,kind,content,is_public,created_at) VALUES (?,?,?,'company',?,?,?)",
               (report_id, company, locale, json.dumps(report), public, date))
    db.commit()
    return report


def test_initial_collection_and_resolve_choose_public_locale_without_spending_quota(database):
    assert database.execute("SELECT COUNT(*) FROM thesis_coverage").fetchone()[0] == 9
    add_report(database, "old-pt", date="2026-10-19")
    add_report(database, "new-en", locale="en")
    add_report(database, "private", public=False, date="2026-10-21")
    database.execute("INSERT INTO full_report_access VALUES ('other','private')")
    database.commit()
    before = database.total_changes
    result = library.resolve_company(full_reports.OpenCompanyReport(company="Microsoft", locale="pt"), "reader")
    assert result["report"]["id"] == "old-pt" and result["report"]["is_public"]
    assert database.total_changes == before
    assert library.resolve_company(full_reports.OpenCompanyReport(company="VIVA3"), "reader")["state"] == "unavailable"


def test_own_private_reports_remain_readable_and_history_ownership_is_checked(database):
    add_report(database, "own", company="VIVA3", public=False)
    database.execute("INSERT INTO full_report_access VALUES ('owner','own')")
    database.execute("INSERT INTO historico VALUES (1,'Vivara','owner')")
    database.commit()
    assert library.resolve_analysis(full_reports.OpenReport(analysis_id=1), "owner")["report"]["id"] == "own"
    with pytest.raises(HTTPException): library.resolve_analysis(full_reports.OpenReport(analysis_id=1), "other")
    assert library.resolve_company(full_reports.OpenCompanyReport(company="VIVA3"), "other")["state"] == "unavailable"


def test_request_is_private_deduplicated_and_does_not_create_a_report(database):
    body = full_reports.OpenCompanyReport(company="Vivara")
    assert library.request_coverage(body, "reader")["state"] == "requested"
    library.request_coverage(body, "reader")
    assert database.execute("SELECT COUNT(*) FROM thesis_requests").fetchone()[0] == 1
    assert database.execute("SELECT COUNT(*) FROM full_reports").fetchone()[0] == 0
    assert library.resolve_company(body, "reader")["state"] == "requested"
    assert library.resolve_company(body, "other")["state"] == "unavailable"


def test_new_result_marks_revision_but_does_not_replace_the_published_thesis(database):
    database.execute("UPDATE thesis_coverage SET published_id='approved',covered_year=2026,covered_quarter=1,state='published' WHERE company='VIVA3'")
    class Cursor:
        def execute(self, sql, args): database.execute(sql.replace("%s", "?").replace("NOW()", "CURRENT_TIMESTAMP"), args)
    library.note_official_result(Cursor(), "Vivara", 2026, 2, "https://issuer.example/release.pdf")
    library.note_official_result(Cursor(), "Vivara", 2025, 4, "https://issuer.example/older.pdf")
    row = database.execute("SELECT state,latest_year,latest_quarter,published_id FROM thesis_coverage WHERE company='VIVA3'").fetchone()
    assert row == ("needs_update", 2026, 2, "approved")


def test_publish_creates_a_reviewed_public_copy_and_preserves_private_draft(database):
    add_report(database, "draft", public=False)
    database.execute("INSERT INTO full_report_access VALUES (?,?)", (library.EDITOR, "draft"))
    database.execute("UPDATE thesis_coverage SET draft_id='draft',draft_year=2026,draft_quarter=2,state='review' WHERE company='MSFT'")
    database.commit()
    public_id = library.publish("MSFT", "pt", "draft")
    assert library.publish("MSFT", "pt", "draft") == public_id
    assert database.execute("SELECT is_public FROM full_reports WHERE id='draft'").fetchone()[0] == 0
    report = library.resolve_company(full_reports.OpenCompanyReport(company="MSFT"), "new-reader")["report"]
    assert report["id"] == public_id and report["publication"]["reviewed"]
    with pytest.raises(ValueError): library.publish("MSFT", "pt", "another-draft")


def test_publish_refuses_stale_or_unverified_drafts(database):
    draft = add_report(database, "draft", public=False)
    database.execute("INSERT INTO full_report_access VALUES (?,?)", (library.EDITOR, "draft"))
    database.execute("UPDATE thesis_coverage SET draft_id='draft',draft_year=2026,draft_quarter=1,latest_year=2026,latest_quarter=2 WHERE company='MSFT'")
    database.commit()
    with pytest.raises(ValueError, match="newer official result"): library.publish("MSFT", "pt", "draft")
    for change in ("audit", "profile", "scenarios"):
        invalid = copy.deepcopy(draft)
        invalid["is_public"] = False
        if change == "audit": invalid["pipeline"]["verification"]["passed"] = False
        if change == "profile": invalid["research_profile"] = "standard"
        if change == "scenarios": invalid["investment_model"]["cases"] = []
        with pytest.raises(ValueError): library.validate_publication(invalid, "MSFT", "pt")


def test_api_requires_authentication_and_exposes_no_publish_or_prepare_endpoint():
    app = FastAPI(); app.include_router(library.router)
    client = TestClient(app)
    for path in ("resolve", "requests"):
        assert client.post("/api/thesis-library/" + path, json={"company": "MSFT"}).status_code == 401
    for path in ("publish", "prepare"):
        assert client.post("/api/thesis-library/" + path, json={"company": "MSFT"}).status_code == 404


def test_coverage_limit_does_not_block_a_duplicate_request(database):
    for number in range(10):
        library.request_coverage(full_reports.OpenCompanyReport(company=f"AA{number}"), "reader")
    with pytest.raises(HTTPException) as error:
        library.request_coverage(full_reports.OpenCompanyReport(company="EXTRA"), "reader")
    assert error.value.status_code == 429
    assert library.request_coverage(full_reports.OpenCompanyReport(company="AA0"), "reader")["state"] == "requested"


def test_prepare_uses_editorial_context_and_stops_at_private_review(database, monkeypatch):
    draft = add_report(database, "candidate", public=False)
    draft["is_public"] = False
    def generate(body, user):
        assert editorial_preparation.get() == "2026Q2"
        assert str(user) == library.EDITOR and body.company == "MSFT"
        return {"report": draft, "reused": False}
    monkeypatch.setattr(full_reports, "open_company_report", generate)
    result = library.prepare("MSFT", "pt", 2026, 2)
    assert result["state"] == "review" and editorial_preparation.get() is None
    assert database.execute("SELECT state,draft_id,published_id FROM thesis_coverage WHERE company='MSFT'").fetchone() == ("review", "candidate", None)
    assert database.execute("SELECT is_public FROM full_reports WHERE id='candidate'").fetchone()[0] == 0
    database.execute("UPDATE thesis_coverage SET latest_year=2026,latest_quarter=3 WHERE company='MSFT'")
    database.commit()
    generator = Mock(side_effect=AssertionError("Do not pay for a known stale result"))
    monkeypatch.setattr(full_reports, "open_company_report", generator)
    with pytest.raises(ValueError, match="newer official result"):
        library.prepare("MSFT", "pt", 2026, 2)
    generator.assert_not_called()


def test_editorial_writing_budget_is_distinct_without_changing_default_flow():
    from agents.report_writer import write_report
    client = Mock(analyze_full_report=Mock(return_value={}))
    token = editorial_preparation.set("2026Q2")
    try:
        write_report(client, "MSFT", "2026-10-21", "pt", {"facts": []}, [])
    finally:
        editorial_preparation.reset(token)
    assert "2,500–3,500" in client.analyze_full_report.call_args.args[0]
    assert client.analyze_full_report.call_args.kwargs["max_output_tokens"] == 14000
    write_report(client, "MSFT", "2026-10-21", "pt", {"facts": []}, [])
    assert "1,200–1,600" in client.analyze_full_report.call_args.args[0]
    assert client.analyze_full_report.call_args.kwargs["max_output_tokens"] == 8500
