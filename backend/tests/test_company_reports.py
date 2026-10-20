import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from unittest.mock import MagicMock, Mock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import full_reports as reports
import company_research as research
from openai_client import OpenAIClient, OpenAIError
from test_company_report_content import complete_report as valid_report


@pytest.fixture(autouse=True)
def isolate_usage_service(monkeypatch):
    from test_company_report_content import stub_pipeline
    monkeypatch.setattr(reports, "company_facts", lambda *a, **kw: {})
    monkeypatch.setattr(reports, "generate_report", stub_pipeline)
    monkeypatch.setattr(reports, "reserve_usage", lambda *args: None)
    monkeypatch.setattr(reports, "cancel_usage", lambda *args: None)
    monkeypatch.setattr(research, "collect_transcript_sources", lambda *a: [])
    monkeypatch.setattr(research, "hydrate_company_documents", lambda company, sources: sources)


SOURCES = [{"id": "S1", "title": "SEC annual facts", "url": "https://data.sec.gov/example",
            "text": "Full-year EPS was USD 2.50.", "basis": "primary"}]


def test_company_cache_scopes_week_model_language_and_canonical_names():
    assert reports.canonical_company("Microsoft") == "MSFT"
    assert reports.canonical_company("Micron") == "MU"
    assert reports.canonical_company("Nike") == reports.canonical_company("NIKE, Inc.") == reports.canonical_company("NKE") == "NKE"
    assert reports.canonical_company("GOOG") == reports.canonical_company("Alphabet") == "GOOGL"
    key = reports.company_cache_key("META", "model-a", "2026-10-12", "en")
    assert key == reports.company_cache_key("META", "model-a", "2026-10-18", "en")
    assert key != reports.company_cache_key("META", "model-a", "2026-10-19", "en")
    assert key != reports.company_cache_key("META", "model-a", "2026-10-12", "pt")
    assert key != reports.company_cache_key("META", "model-b", "2026-10-12", "en")
    assert key != reports.company_cache_key("TSLA", "model-a", "2026-10-12", "en")
    for value in ("https://evil.example", "META;DROP TABLE", "", "<script>"):
        with pytest.raises(HTTPException): reports.canonical_company(value)
    with pytest.raises(ValidationError): reports.OpenCompanyReport(company="META", is_public=False)


def test_company_report_and_research_cache_version_invalidate_old_outputs(monkeypatch):
    current = reports.company_cache_key("MSFT", "model", "2026-10-12", "pt")
    research_current = reports.company_cache_key("MSFT", "model", "2026-10-12")
    monkeypatch.setattr(reports, "COMPANY_REPORT_VERSION", "company-v1")
    assert current != reports.company_cache_key("MSFT", "model", "2026-10-12", "pt")
    assert research_current != reports.company_cache_key("MSFT", "model", "2026-10-12")


def test_company_report_cache_hit_skips_research_and_ai_for_another_user(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    report = {"id": "shared-company", "scope": "company", "company": "META"}
    cur.fetchone.return_value = (report, True)
    monkeypatch.setattr(reports, "connection", lambda: conn)
    monkeypatch.setattr(reports, "OpenAIClient", Mock(side_effect=AssertionError("No AI on a cache hit")))
    result = reports.open_company_report(reports.OpenCompanyReport(company="META", locale="en"), "user_second")
    assert result["reused"] is True and result["report"]["is_public"]
    assert cur.execute.call_args.args[1] == ("user_second", "shared-company")
    conn.commit.assert_called_once()


def test_nike_ticker_fix_reuses_a_ready_legacy_report_without_paid_generation(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    report = {"id": "nike-ready", "scope": "company", "company": "NIKE"}
    cur.fetchone.side_effect = [None, (report, True)]
    monkeypatch.setattr(reports, "connection", lambda: conn)
    monkeypatch.setattr(reports, "OpenAIClient", Mock(side_effect=AssertionError("Do not regenerate Nike")))
    result = reports.open_company_report(reports.OpenCompanyReport(company="Nike", locale="en"), "another_user")
    assert result["reused"] is True and result["report"]["id"] == "nike-ready"
    assert cur.execute.call_args.args[1] == ("another_user", "nike-ready")
    conn.commit.assert_called_once()


def test_history_link_reuses_the_same_general_report_as_the_full_reports_tab(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    ready = {"id": "weg-company", "company": "WEGE3", "scope": "company"}
    cur.fetchone.side_effect = [("WEGE3",), (ready, True), (ready, True)]
    monkeypatch.setattr(reports, "connection", lambda: conn)
    monkeypatch.setattr(reports, "OpenAIClient", Mock(side_effect=AssertionError("Do not regenerate a ready company report")))
    history = reports.open_report(reports.OpenReport(analysis_id=7, locale="en"), "user_one")
    direct = reports.open_company_report(reports.OpenCompanyReport(company="WEGE3", locale="en"), "user_two")
    assert history == direct and history["reused"] is True
    assert history["report"]["scope"] == "company" and history["report"]["symbol"] == "WEGE3"
    assert cur.execute.call_args_list[0].args[1] == (7, "user_one")
    access = [call.args[1] for call in cur.execute.call_args_list if "INSERT INTO full_report_access" in call.args[0]]
    assert access == [("user_one", "weg-company"), ("user_two", "weg-company")]


def test_saved_company_report_uses_canonical_identity_instead_of_exchange_code():
    original = {"id": "weg", "scope": "company", "company": "WEGE3", "symbol": "BVMF"}
    assert reports.stored_report((original, True))["symbol"] == "WEGE3"
    assert original["symbol"] == "BVMF"


def test_general_company_report_uses_public_dossier_without_user_history(monkeypatch):
    timing = Mock()
    monkeypatch.setattr(reports.timing_logger, "info", timing)
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    evidence = Mock(return_value={"as_of": "2026-10-12", "sources": SOURCES})
    monkeypatch.setattr(reports, "company_evidence", evidence)
    ai = Mock(model="test-model", analyze_full_report=Mock(return_value=valid_report()))
    factory = Mock(return_value=ai)
    monkeypatch.setattr(reports, "OpenAIClient", factory)
    result = reports.open_company_report(reports.OpenCompanyReport(company="META", locale="en"), "user_one")
    report = result["report"]
    assert report["scope"] == report["kind"] == "company"
    assert report["symbol"] == "META"
    assert report["as_of"] == "2026-10-12" and report["is_public"] is False
    assert report["report_version"] == reports.report_summary(report)["report_version"] == "company-v7"
    assert report["score"] == 4 and len(report["sections"]) == 10
    assert report["valuation"]["fair_value"] > 0
    assert all("text" not in source for source in report["sources"])
    assert not any("historico" in call.args[0] or "analysis_documents" in call.args[0] for call in cur.execute.call_args_list)
    assert ai.analyze_full_report.call_args.kwargs == {"max_output_tokens": 11000, "timeout": 120}
    assert [call.kwargs for call in factory.call_args_list] == [{"task": "full_report"}, {"task": "analysis"}]
    assert evidence.call_args.args[1] == reports.model_for_task("full_report")
    conn.commit.assert_called_once()
    _, company, _, stage, duration, timings = timing.call_args.args
    assert company == "META" and stage == "complete" and duration >= 0
    assert set(timings) == {"cache_ms", "research_ms", "extraction_ms", "synthesis_ms"}
    assert "Full-year EPS" not in str(timing.call_args)


def test_company_generation_accepts_supported_subsets_without_retry_or_fake_categories(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    monkeypatch.setattr(reports, "company_evidence", lambda *args: {"as_of": "2026-10-12", "sources": SOURCES})
    raw = valid_report()
    raw["signals"] = raw["signals"][:2]
    raw["scorecard"] = raw["scorecard"][:3]
    ai = Mock(analyze_full_report=Mock(return_value=raw))
    monkeypatch.setattr(reports, "OpenAIClient", lambda **kwargs: ai)
    report = reports.open_company_report(reports.OpenCompanyReport(company="GOOGL"), "user_one")["report"]
    assert len(report["signals"]) == 2 and len(report["scorecard"]) == 3
    assert report["score"] == 4
    ai.analyze_full_report.assert_called_once()
    conn.commit.assert_called_once()


@pytest.mark.parametrize("stage", ["research", "synthesis"])
def test_company_timeout_reports_stage_without_retries_or_partial_reports(monkeypatch, caplog, stage):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    evidence = Mock(return_value={"as_of": "2026-10-17", "sources": SOURCES})
    ai = Mock(analyze_full_report=Mock(return_value=valid_report()))
    if stage == "research": evidence.side_effect = TimeoutError("PRIVATE_PROVIDER_TEXT")
    else: ai.analyze_full_report.side_effect = TimeoutError("PRIVATE_PROVIDER_TEXT")
    monkeypatch.setattr(reports, "company_evidence", evidence)
    monkeypatch.setattr(reports, "OpenAIClient", lambda **kwargs: ai)
    with pytest.raises(HTTPException) as error:
        reports.open_company_report(reports.OpenCompanyReport(company="AMZN", locale="pt"), "user_one")
    assert error.value.status_code == 504
    assert "Tente novamente" in error.value.detail
    assert f"stage={stage}" in caplog.text and "company=AMZN" in caplog.text
    assert "PRIVATE_PROVIDER_TEXT" not in caplog.text
    assert ai.analyze_full_report.call_count == (1 if stage == "synthesis" else 0)
    assert evidence.call_count == 1
    conn.rollback.assert_called_once(); conn.commit.assert_not_called()
    assert not any("INSERT INTO full_reports" in call.args[0] for call in cur.execute.call_args_list)


def test_research_is_committed_independently_and_cache_hit_never_repeats_search(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    collect = Mock(return_value=SOURCES); monkeypatch.setattr(reports, "collect_company_sources", collect)
    first = reports.company_evidence("META", "model", "2026-10-12", Mock())
    conn.commit.assert_called_once()
    cur.fetchone.return_value = (json.dumps(first),)
    second = reports.company_evidence("META", "model", "2026-10-13", Mock())
    assert second == first and collect.call_count == 1
    assert conn.commit.call_count == 2


def test_unsupported_company_research_has_shared_cooldown_instead_of_repeated_paid_search(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    collect = Mock(side_effect=OpenAIError("No citations", code="insufficient_company_sources"))
    monkeypatch.setattr(reports, "collect_company_sources", collect)
    with pytest.raises(OpenAIError): reports.company_evidence("NONE", "model", "2026-10-12", Mock())
    cached = json.loads(next(call.args[1][1] for call in cur.execute.call_args_list if "INSERT INTO company_research_cache" in call.args[0]))
    cur.fetchone.return_value = (cached,)
    with pytest.raises(OpenAIError): reports.company_evidence("NONE", "model", "2026-10-12", Mock())
    assert collect.call_count == 1
    conn.commit.assert_called_once()


def test_concurrent_company_requests_generate_and_research_once_across_users(monkeypatch):
    locks, report_cache, evidence_cache = {}, {}, {}
    registry_lock = threading.Lock()
    class Connection:
        def __init__(self): self.held = None
        def cursor(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql, params=None):
            if "pg_advisory_xact_lock" in sql:
                with registry_lock: lock = locks.setdefault(params[0], threading.Lock())
                lock.acquire(); self.held = lock
            elif "SELECT content,is_public" in sql:
                self.row = (report_cache[params[0]], True) if params[0] in report_cache else None
            elif "SELECT content FROM company_research_cache" in sql:
                self.row = (evidence_cache[params[0]],) if params[0] in evidence_cache else None
            elif "INSERT INTO full_reports " in sql: report_cache[params[1]] = json.loads(params[-1])
            elif "INSERT INTO company_research_cache" in sql: evidence_cache[params[0]] = json.loads(params[1])
        def fetchone(self): return self.row
        def commit(self):
            if self.held: self.held.release(); self.held = None
        rollback = close = commit
    monkeypatch.setattr(reports, "connection", Connection)
    collect = Mock(return_value=SOURCES); monkeypatch.setattr(reports, "collect_company_sources", collect)
    ai = Mock(analyze_full_report=Mock(side_effect=lambda *args, **kwargs: valid_report()))
    monkeypatch.setattr(reports, "OpenAIClient", lambda **kwargs: ai)
    barrier = threading.Barrier(2)
    def run(user):
        barrier.wait()
        return reports.open_company_report(reports.OpenCompanyReport(company="META", locale="en"), user)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ["user_one", "user_two"]))
    assert results[0]["report"]["id"] == results[1]["report"]["id"]
    assert sorted(result["reused"] for result in results) == [False, True]
    assert collect.call_count == ai.analyze_full_report.call_count == 1


def test_invalid_company_synthesis_rolls_back_without_discarding_research(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    evidence = Mock(return_value={"as_of": "2026-10-12", "sources": SOURCES})
    monkeypatch.setattr(reports, "company_evidence", evidence)
    ai = Mock(); ai.analyze_full_report.side_effect = OpenAIError("Failure", code="response_incomplete")
    monkeypatch.setattr(reports, "OpenAIClient", lambda **kwargs: ai)
    with pytest.raises(HTTPException) as exc:
        reports.open_company_report(reports.OpenCompanyReport(company="META"), "user_one")
    assert exc.value.status_code == 502 and evidence.call_count == 1
    assert not any("INSERT INTO full_reports" in call.args[0] for call in cur.execute.call_args_list)
    conn.rollback.assert_called_once(); conn.commit.assert_not_called()


def test_scenario_values_are_calculated_without_assuming_adr_or_share_equivalence():
    content = reports.validate_company_report(valid_report(), SOURCES)
    content["market"].update(price=40, currency="USD", as_of="2026-10-12", source_id="S1")
    result = reports.calculated_company_valuation(content)
    base = next(s for s in result["valuation"]["scenarios"] if s["case"] == "base")
    assert base["future_value"] == round(2.5 * 1.1 ** 5 * 20, 2)
    assert result["valuation"]["fair_value"] == round(2.5 * 1.1 ** 5 * 20 / 1.15 ** 5, 2)
    assert base["upside_percent"] is None
    content["market"]["currency"] = "BRL"
    assert all(s["upside_percent"] is None for s in reports.calculated_company_valuation(content)["valuation"]["scenarios"])


def cited_response():
    text = "Reported revenue grew in FY2025 [1].\n\nManagement described competition [2].\n\nDated market consensus [3]."
    annotations = [{"type": "url_citation", "url": f"https://source{i}.example/report", "title": f"Source {i}",
                    "start_index": text.index(f"[{i}]"), "end_index": text.index(f"[{i}]") + 3} for i in (1, 2, 3)]
    return {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": text, "annotations": annotations}]}]}


def test_only_cited_fragments_become_evidence_and_uncited_text_is_not_reused():
    response = cited_response()
    sources = research.cited_sources(response)
    assert len(sources) == 3 and all(source["basis"] == "web_research" for source in sources)
    assert "Reported revenue" in sources[0]["text"] and "market consensus" not in sources[0]["text"]
    response["output"][0]["content"][0]["annotations"][1]["url"] = "javascript:alert(1)"
    with pytest.raises(OpenAIError) as exc: research.cited_sources(response)
    assert exc.value.code == "insufficient_company_sources"
    with pytest.raises(OpenAIError): research.cited_sources({"status": "incomplete"})


def test_company_research_request_is_bounded_and_uses_only_public_company_name():
    client = OpenAIClient(); client._client = MagicMock(); client._request = Mock(return_value=cited_response())
    client.research_company(research.research_prompt("META", "2026-10-12"))
    request = client._request.call_args.kwargs
    assert request["json"]["max_tool_calls"] == 4 and request["json"]["max_output_tokens"] == 4000
    assert request["json"]["tools"][0]["type"] == "web_search" and request["json"]["store"] is False
    assert "META" in request["json"]["input"] and "2026-10-12" in request["json"]["input"]

    client.research_company(research.market_research_prompt("META", "2026-10-12"),
                            max_tool_calls=2, max_output_tokens=2000, timeout=35)
    request = client._request.call_args.kwargs
    assert request["json"]["max_tool_calls"] == 2 and request["json"]["max_output_tokens"] == 2000
    assert request["timeout"] == 35
