import copy
import json
import sys
from pathlib import Path
from time import perf_counter
from unittest.mock import MagicMock, Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.report_facts import validate_dossier, extract_facts, writing_sources
from agents.report_pipeline import generate_report
from agents.report_verifier import check_consistency
from company_research import collect_transcript_sources
from full_report_content import ReportValidationError
from test_company_report_content import complete_report
import full_reports as reports


SOURCES = [{"id": "S1", "basis": "primary", "title": "Annual results", "url": "https://example.com/annual",
            "text": "Annual EPS USD 2.50. Revenue was USD 10 billion in FY2025. Operating cash flow was positive in FY2025."}]


def facts():
    return {"facts": [{"statement": quote, "quote": quote, "source_id": "S1", "period": "FY2025",
                       "numeric_value": amount, "unit": "USD/share" if amount else None, "currency": "USD" if amount else None,
                       "sections": ["financials", "valuation", "thesis"]}
                      for quote, amount in [("Annual EPS USD 2.50.", 2.5), ("Revenue was USD 10 billion in FY2025.", None),
                                            ("Operating cash flow was positive in FY2025.", None)]], "gaps": []}


def test_annual_tables_survive_extraction_budget_without_inventing_facts():
    table = "| Year | Revenue | Net income |\n|2023|100|10|\n|2024|120|12|\n|2025|150|15|"
    sources = [{"id": "S1", "text": table, "basis": "web_research"},
               {"id": "IR2025", "text": "Original Vivara annual financial statements", "basis": "primary", "document_type": "filing"},
               {"id": "S2", "text": "Unrelated prose", "basis": "web_research"}]
    compact = writing_sources({"facts": []}, sources)
    assert [s["id"] for s in compact] == ["S1", "IR2025"]
    assert compact[0]["text"] == table
    primary = {"id": "IR2024", "text": "x" * 21000 + "ANNUAL INCOME TABLE" + "x" * 10000,
               "basis": "primary", "document_type": "filing"}
    assert "ANNUAL INCOME TABLE" in writing_sources({"facts": []}, [primary])[0]["text"]


def test_original_financial_tables_reach_writer_repair_and_independent_review():
    from agents.report_writer import write_report, repair_report
    from agents.report_verifier import verify_report
    from agents.report_valuation import calculate_valuation
    marker = "|2023|100|10|"
    sources = SOURCES + [{"id": "S2", "basis": "web_research", "title": "Financial table", "url": "https://example.com/table",
                          "text": "|Year|Revenue|Net income|\n" + marker + "\n|2024|120|12|\n|2025|150|15|"}]
    dossier = validate_dossier(facts(), sources)
    compact = writing_sources(dossier, sources)
    client = Mock()
    write_report(client, "META", "2026-10-20", "en", dossier, compact)
    assert marker in client.analyze_full_report.call_args.args[0]
    client.analyze_full_report.return_value = {"metrics": []}
    repair_report(client, "META", "2026-10-20", "en", complete_report(),
                  [{"target": "metrics", "reason": "Check figure", "source_ids": ["S2"]}], dossier, compact)
    assert marker in client.analyze_full_report.call_args.args[0]
    client.analyze_full_report.return_value = {"passed": True, "issues": []}
    verify_report(client, calculate_valuation(complete_report()), dossier, sources, "2026-10-20")
    assert marker in client.analyze_full_report.call_args.args[0]


class AgentClient:
    model = "test-model"

    def __init__(self, *, reject=False):
        self.calls = []
        self.reject = reject

    def analyze_full_report(self, prompt, schema, **kwargs):
        self.calls.append((prompt.split("\n", 1)[0], schema, kwargs))
        properties = schema["properties"]
        if "facts" in properties:
            return facts()
        if "passed" in properties:
            return {"passed": not self.reject, "issues": [{"target": "thesis", "reason": "Unsupported claim", "source_ids": ["S1"]}] if self.reject else []}
        report = complete_report()
        if prompt.startswith("AGENT 2 — repair"):
            result = {key: report[key] for key in properties}
            if "sections" in result:
                allowed = properties["sections"]["items"]["properties"]["id"]["enum"]
                result["sections"] = [section for section in result["sections"] if section["id"] in allowed]
            return result
        section = next(s for s in report["sections"] if s["id"] == "valuation")
        if "section" in properties:
            return {"section": section, "valuation": report["valuation"]}
        report.pop("valuation")
        report["sections"] = [s for s in report["sections"] if s["id"] != "valuation"]
        return report


def test_real_four_agent_contracts_preserve_sources_and_calculate_scenarios():
    client = AgentClient()
    dossier = extract_facts(client, "META", "2026-10-19", SOURCES)
    report = generate_report(client, "META", "2026-10-19", "en", SOURCES, dossier, deadline=perf_counter() + 300)
    assert len(client.calls) == 4
    assert len(report["sections"]) == 10 and report["pipeline"]["verification"]["passed"]
    assert report["valuation"]["fair_value"] == round(2.5 * 1.1 ** 5 * 20 / 1.15 ** 5, 2)
    assert all(s["upside_percent"] is None for s in report["valuation"]["scenarios"])
    writer = next(c for c in client.calls if "company_name" in c[1]["properties"])
    assert "valuation" not in writer[1]["properties"]
    assert writer[1]["properties"]["sections"]["minItems"] == 9
    assert dossier["facts"][0]["id"] == "E1"


@pytest.mark.parametrize("mutation", ["quote", "citation", "number", "section", "unit"])
def test_extractor_rejects_fabricated_support(mutation):
    raw = facts()
    if mutation == "quote": raw["facts"][0]["quote"] = "An invented evidence quotation."
    if mutation == "citation": raw["facts"][0]["source_id"] = "made-up"
    if mutation == "number": raw["facts"][0]["numeric_value"] = 250.0
    if mutation == "section": raw["facts"][0]["sections"] = ["invented"]
    if mutation == "unit": raw["facts"][0]["unit"] = None
    with pytest.raises(ReportValidationError): validate_dossier(raw, SOURCES)


def test_independent_rejection_blocks_report_and_deadline_does_not_start_agents():
    dossier = validate_dossier(facts(), SOURCES)
    with pytest.raises(ReportValidationError, match="audit rejected"):
        generate_report(AgentClient(reject=True), "META", "2026-10-19", "en", SOURCES, dossier, deadline=perf_counter() + 300)
    client = AgentClient()
    with pytest.raises(TimeoutError):
        generate_report(client, "META", "2026-10-19", "en", SOURCES, dossier, deadline=perf_counter() - 1)
    assert client.calls == []


@pytest.mark.parametrize("corrupt", ["duplicate", "shares", "market", "calculation"])
def test_deterministic_verifier_blocks_inconsistent_numbers(corrupt):
    client = AgentClient()
    report = generate_report(client, "META", "2026-10-19", "en", SOURCES, validate_dossier(facts(), SOURCES), deadline=perf_counter() + 300)
    if corrupt == "duplicate": report["financial_history"].append(copy.deepcopy(report["financial_history"][0]))
    if corrupt == "shares": report["breakdowns"] *= 2
    if corrupt == "market": report["market"].update(as_of="2027-01-01", price=10.0, currency="USD", source_id="S1")
    if corrupt == "calculation": report["valuation"]["scenarios"][0]["present_value"] = 99999999
    with pytest.raises(ReportValidationError): check_consistency(report, SOURCES, "2026-10-19")


@pytest.mark.parametrize("rejected", [False, True])
def test_real_pipeline_is_required_before_database_insert_and_preserves_privacy(monkeypatch, rejected):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    monkeypatch.setattr(reports, "reserve_usage", lambda *a: "quota-ticket")
    cancel = Mock(); monkeypatch.setattr(reports, "cancel_usage", cancel)
    monkeypatch.setattr(reports, "company_evidence", lambda *a: {"as_of": "2026-10-19", "sources": SOURCES})
    client = AgentClient(reject=rejected)
    monkeypatch.setattr(reports, "OpenAIClient", lambda **kw: client)
    if rejected:
        from fastapi import HTTPException
        with pytest.raises(HTTPException): reports.open_company_report(reports.OpenCompanyReport(company="META"), "user_one")
        assert not any("INSERT INTO full_reports " in c.args[0] for c in cur.execute.call_args_list)
        cancel.assert_called_with("quota-ticket")
    else:
        report = reports.open_company_report(reports.OpenCompanyReport(company="META"), "user_one")["report"]
        assert report["is_public"] is False and report["pipeline"]["verification"]["passed"]
        assert any("INSERT INTO full_reports " in c.args[0] for c in cur.execute.call_args_list)
    assert len(client.calls) == (6 if rejected else 4)


def test_fact_cache_survives_later_failures_and_revalidates_quotes(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None
    monkeypatch.setattr(reports, "connection", lambda: conn)
    client = AgentClient(); evidence = {"as_of": "2026-10-19", "sources": SOURCES}
    first = reports.company_facts("META", "model", evidence, client, deadline=perf_counter() + 90)
    saved = next(c.args[1][1] for c in cur.execute.call_args_list if "INSERT INTO company_research_cache" in c.args[0])
    cur.fetchone.return_value = (saved,)
    second = reports.company_facts("META", "model", evidence, client, deadline=perf_counter() + 90)
    assert first == second and len(client.calls) == 1
    assert conn.commit.call_count == 2


def test_transcript_search_is_bounded_and_absence_never_invents_call_content():
    client = Mock(); client.research_company.return_value = {"status": "completed", "output": []}
    assert collect_transcript_sources(client, "META", "2026-10-19") == []
    assert client.research_company.call_args.kwargs == {"max_tool_calls": 1, "max_output_tokens": 900, "timeout": 25}


def test_fact_extraction_omits_editorial_grading_and_bounds_long_transcripts():
    client = AgentClient()
    api = Mock(side_effect=client.analyze_full_report)
    client.analyze_full_report = api
    sources = [*SOURCES, {"id": "T1", "basis": "transcript", "title": "Apple earnings call", "url": "https://example.com/call",
                         "text": "CALL OPENING " + "x" * 30000 + " Q&A END"}]
    extract_facts(client, "AAPL", "2026-10-20", sources)
    prompt = api.call_args.args[0]
    assert "CALL OPENING" in prompt and "Q&A END" in prompt
    assert "x" * 20000 not in prompt and "40/25/20/15" not in prompt
    assert api.call_args.kwargs["max_output_tokens"] == 3600


def test_extraction_discards_bad_fact_without_weakening_remaining_evidence():
    raw = facts()
    invalid = copy.deepcopy(raw["facts"][0])
    invalid["numeric_value"] = 250
    raw["facts"].append(invalid)
    dossier = validate_dossier(raw, SOURCES, drop_invalid=True)
    assert len(dossier["facts"]) == 3
    assert [f["id"] for f in dossier["facts"]] == ["E1", "E2", "E3"]
    raw["facts"] = [invalid] * 3
    with pytest.raises(ReportValidationError, match="Insufficient"):
        validate_dossier(raw, SOURCES, drop_invalid=True)


def test_independent_audit_repairs_once_and_requires_second_approval():
    client = AgentClient()
    original = client.analyze_full_report
    reviews = []
    def analyze(prompt, schema, **kwargs):
        result = original(prompt, schema, **kwargs)
        if "passed" in schema["properties"]:
            reviews.append(prompt)
            if len(reviews) == 1:
                return {"passed": False, "issues": [{"target": "thesis", "reason": "Remove unsupported claim", "source_ids": ["S1"]}]}
        return result
    client.analyze_full_report = analyze
    report = generate_report(client, "META", "2026-10-19", "en", SOURCES, validate_dossier(facts(), SOURCES), deadline=perf_counter() + 300)
    assert len(reviews) == 2 and report["pipeline"]["verification"]["passed"]
    repairs = [call for call in client.calls if call[0].startswith("AGENT 2 — repair")]
    assert len(repairs) == 1
    assert repairs[0][1]["properties"]["sections"]["items"]["properties"]["id"]["enum"] == ["thesis"]
    assert len([call for call in client.calls if call[0].startswith("AGENT 3")]) == 1


@pytest.mark.parametrize("locale, phrase", [("en", "Calculated base fair value"), ("pt", "Valor-base calculado")])
def test_valuation_narrative_uses_actual_python_outputs(locale, phrase):
    from agents.report_valuation import calculate_valuation
    report = complete_report()
    section = next(s for s in report["sections"] if s["id"] == "valuation")
    section["summary"] = "No prices or fair value have been calculated."
    section["paragraphs"] = ["No scenarios populated."]
    result = calculate_valuation(report, locale)
    updated = next(s for s in result["sections"] if s["id"] == "valuation")
    assert phrase in updated["paragraphs"][0]
    assert "No prices" not in json.dumps(updated) and len(updated["bullets"]) == 3
    expected = f"{result['valuation']['fair_value']:,.2f}"
    if locale == "pt":
        expected = expected.replace(",", "_").replace(".", ",").replace("_", ".")
    assert expected in updated["paragraphs"][0]


def test_targeted_repair_preserves_unaffected_fields_and_rejects_unrequested_changes():
    from agents.report_writer import repair_report
    report = complete_report()
    issues = [{"target": "sections[id=thesis].summary", "reason": "Unsupported", "source_ids": ["S1"]}]
    corrected = copy.deepcopy(report["sections"][0]); corrected["summary"] = "Corrected supported summary."
    client = Mock()
    client.analyze_full_report.return_value = {"sections": [corrected]}
    result = repair_report(client, "META", "2026-10-20", "en", report, issues, validate_dossier(facts(), SOURCES), SOURCES)
    assert result["valuation"] == report["valuation"] and result["financial_history"] == report["financial_history"]
    assert result["sections"][1:] == report["sections"][1:]
    assert "Corrected" in result["sections"][0]["summary"] and report["sections"][0] != corrected
    client.analyze_full_report.return_value["market"] = report["market"]
    with pytest.raises(ReportValidationError, match="unexpected fields"):
        repair_report(client, "META", "2026-10-20", "en", report, issues, validate_dossier(facts(), SOURCES), SOURCES)


def test_audit_budget_allows_reasoning_and_structured_findings():
    from agents.report_verifier import verify_report
    client = Mock()
    client.analyze_full_report.return_value = {"passed": True, "issues": []}
    report = complete_report()
    from agents.report_valuation import calculate_valuation
    verify_report(client, calculate_valuation(report), validate_dossier(facts(), SOURCES), SOURCES, "2026-10-20")
    assert client.analyze_full_report.call_args.kwargs["max_output_tokens"] == 4000
