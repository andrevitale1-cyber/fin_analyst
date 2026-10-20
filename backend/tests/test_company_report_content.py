from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from company_report_content import (
    COMPANY_SECTION_IDS, SCORECARD_IDS, SIGNAL_IDS, build_company_report_prompt,
    company_report_schema, validate_company_report,
)


def valid_report():
    return {
        "company_name": "Example Co", "coverage": "Limited to supplied reports.", "score": None,
        "sections": [
            {"id": item, "title": item.title(), "summary": "Evidence-limited summary.",
             "paragraphs": [], "bullets": [], "source_ids": ["S1"]}
            for item in COMPANY_SECTION_IDS
        ],
        "metrics": [{"label": "Revenue", "value": "$10 billion", "group": "scale", "as_of": "FY2025", "source_id": "S1"}],
        "signals": [{"id": item, "label": item.title(), "value": "Not enough evidence", "tone": "unknown", "source_ids": []}
                    for item in SIGNAL_IDS],
        "scorecard": [
            {"id": item, "label": item.replace("_", " ").title(), "score": score,
             "reason": "Source-limited AI assessment.", "source_ids": ["S1"]}
            for item, score in zip(SCORECARD_IDS, [5, 4, 3, 4, 2, 3, 4])
        ],
        "tracking_metrics": [{"label": "Margins", "expectation": "Watch for disclosed margins.", "status": "Not reported", "source_ids": ["S1"]}],
        "breakdowns": [{"category": "segment", "label": "Vehicles", "value": "$8 billion", "share": 80, "source_id": "S1"}],
        "financial_history": [{"period": "FY2025", "currency": "USD", "revenue": 10, "net_income": 2,
                               "free_cash_flow": 1, "source_id": "S1"}],
        "projections": [{"period": "FY2026", "currency": "USD", "revenue": None, "eps": None,
                         "basis": "management_guidance", "source_id": "S1"}],
        "market": {"price": None, "change_percent": None, "currency": None, "as_of": None, "source_id": None},
        "watchpoints": ["Check reported deliveries."],
        "valuation": {"available": True, "base_eps": 2.5, "currency": "USD", "source_id": "S1",
                      "reason": "Annual EPS was disclosed.", "method": "Scenario P/E on annual EPS.",
                      "scenarios": [
                          {"case": case, "growth_percent": growth, "pe_multiple": multiple,
                           "discount_percent": 15, "rationale": "Illustrative assumption."}
                          for case, growth, multiple in (("bear", -10, 12), ("base", 10, 20), ("bull", 20, 30))
                      ]},
    }


def test_valuation_cannot_choose_an_older_profitable_sec_year_or_undated_quote():
    source = {"id": "F1", "basis": "primary", "text":
              "For the full year ended 2025-12-31, diluted earnings per share USD/shares -0.5.\n"
              "For the full year ended 2024-12-31, diluted earnings per share USD/shares 2.5."}
    raw = valid_report()
    for section in raw["sections"]: section["source_ids"] = ["F1"]
    for field in ("metrics", "breakdowns", "financial_history", "projections"):
        for item in raw[field]: item["source_id"] = "F1"
    for field in ("scorecard", "tracking_metrics"):
        for item in raw[field]: item["source_ids"] = ["F1"]
    raw["valuation"]["source_id"] = "F1"
    assert validate_company_report(raw, [source])["valuation"]["available"] is False
    raw = valid_report()
    raw["market"].update(price=50, currency="USD", source_id="S1")
    with pytest.raises(ValueError, match="date and currency"):
        validate_company_report(raw, [{"id": "S1", "basis": "primary", "text": "Full-year EPS was USD 2.50."}])


def test_schema_is_json_serializable_strict_and_has_all_list_limits():
    schema = company_report_schema()
    json.dumps(schema)

    def check(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for value in node.values():
                check(value)
        elif isinstance(node, list):
            for value in node:
                check(value)

    check(schema)
    props = schema["properties"]
    expected = {"sections": 10, "metrics": 18, "signals": 6, "scorecard": 7,
                "tracking_metrics": 6, "breakdowns": 12, "financial_history": 5,
                "projections": 5, "watchpoints": 10}
    assert {name: props[name]["maxItems"] for name in expected} == expected
    assert props["sections"]["minItems"] == 10
    assert props["valuation"]["properties"]["scenarios"]["maxItems"] == 3
    section = props["sections"]["items"]["properties"]
    assert section["paragraphs"]["maxItems"] == 5
    assert section["paragraphs"]["items"]["pattern"] == r"^[\s\S]{0,1200}$"
    assert section["bullets"]["maxItems"] == 8
    assert section["bullets"]["items"]["pattern"] == r"^[\s\S]{0,300}$"
    assert section["source_ids"]["maxItems"] == 12
    assert props["signals"]["items"]["properties"]["source_ids"]["maxItems"] == 12
    assert props["scorecard"]["items"]["properties"]["source_ids"]["maxItems"] == 12


def test_references_and_canonical_order_are_validated():
    raw = valid_report()
    raw["sections"].reverse()
    source = {"id": "S1", "basis": "primary", "text": "Full-year EPS was USD 2.50."}
    result = validate_company_report(raw, [source])
    assert [item["id"] for item in result["sections"]] == list(COMPANY_SECTION_IDS)
    assert result["score"] == 4

    raw = valid_report()
    raw["metrics"][0]["source_id"] = "OTHER"
    with pytest.raises(ValueError, match="unknown source"):
        validate_company_report(raw, [source])


def test_duplicate_section_scorecard_and_signal_ids_reject():
    source = {"id": "S1", "basis": "primary", "text": "Full-year EPS was USD 2.50."}
    raw = valid_report()
    raw["sections"][0] = raw["sections"][1]
    with pytest.raises(ValueError, match="section exactly once"):
        validate_company_report(raw, [source])

    raw = valid_report()
    raw["scorecard"][0] = raw["scorecard"][1]
    with pytest.raises(ValueError, match="scorecard"):
        validate_company_report(raw, [source])

    raw = valid_report()
    raw["signals"][0] = raw["signals"][1]
    with pytest.raises(ValueError, match="Signals"):
        validate_company_report(raw, [source])


def test_supported_signal_and_scorecard_subsets_do_not_block_the_report():
    raw = valid_report()
    raw["signals"] = raw["signals"][:2]
    raw["scorecard"] = raw["scorecard"][:3]
    result = validate_company_report(raw, [{"id": "S1", "text": "Full-year EPS was USD 2.50."}])
    assert len(result["signals"]) == 2
    assert [item["score"] for item in result["scorecard"]] == [5, 4, 3]
    assert result["score"] == 4


def test_new_synthesis_requires_integer_scores_and_never_fabricates_missing_ratings():
    score_schema = company_report_schema()["properties"]["scorecard"]["items"]["properties"]["score"]
    assert score_schema == {"type": "integer", "minimum": 1, "maximum": 5}
    raw = valid_report()
    for item in raw["scorecard"]:
        item["score"] = None
    result = validate_company_report(raw, [{"id": "S1", "text": "A factual source."}])
    assert result["score"] is None
    assert all(item["score"] is None for item in result["scorecard"])
    for invalid in (0, 6, 2.5, True, "4"):
        raw["scorecard"][0]["score"] = invalid
        with pytest.raises(ValueError):
            validate_company_report(raw, [{"id": "S1", "text": "A factual source."}])


def test_numeric_metrics_keep_exact_amount_currency_and_legacy_display_fallback():
    raw = valid_report()
    source = [{"id": "S1", "text": "Reported revenue USD 331839000000."}]
    legacy = validate_company_report(raw, source)["metrics"][0]
    assert legacy["value"] == "$10 billion" and legacy["numeric_value"] is None
    raw["metrics"][0].update(value="US$ 331,84 bilhões", numeric_value=331839000000, currency="USD", unit="currency")
    metric = validate_company_report(raw, source)["metrics"][0]
    assert metric["numeric_value"] == 331839000000 and metric["currency"] == "USD"
    assert metric["value"] == "US$ 331,84 bilhões"
    for invalid in ({"numeric_value": float("inf")}, {"numeric_value": True}, {"currency": None},
                    {"unit": None}, {"unit": "percent"}, {"numeric_value": None}):
        candidate = valid_report()
        candidate["metrics"][0].update(raw["metrics"][0], **invalid)
        with pytest.raises(ValueError):
            validate_company_report(candidate, source)


def test_sec_units_are_recovered_only_for_known_annual_metrics_with_unique_period():
    source = {"id": "F1", "basis": "primary", "text": "SEC annual facts.", "annual_financials": [
        {"period": "2025-06-30", "currency": "USD", "values": {"Revenue": 331839000000}}]}
    raw = valid_report()
    raw["metrics"][0].update(label="Receita", value="331839000000", as_of="FY2025", source_id="F1")
    sources = [{"id": "S1", "text": "Other supplied facts."}, source]
    result = validate_company_report(raw, sources)["metrics"][0]
    assert result["numeric_value"] == 331839000000
    assert result["unit"] == "currency" and result["currency"] == "USD"
    for as_of in ("TTM 2025", "Q4 2025", "4Q 2025", "3T2025", "2025Q3", "2025-03-31", "2024", "2024–2025"):
        raw["metrics"][0]["as_of"] = as_of
        assert validate_company_report(raw, sources)["metrics"][0]["numeric_value"] is None
    raw["metrics"][0]["as_of"] = "FY2025"
    raw["metrics"][0]["label"] = "Market cap"
    assert validate_company_report(raw, sources)["metrics"][0]["numeric_value"] is None
    raw["metrics"][0].update(label="Receita", source_id="S1")
    assert validate_company_report(raw, sources)["metrics"][0]["numeric_value"] is None
    source["annual_financials"][0]["values"]["Operating margin (calculated)"] = -20
    source["annual_financials"][0]["value_units"] = {"Operating margin (calculated)": "percent"}
    raw["metrics"][0].update(label="Margem operacional", source_id="F1")
    metric = validate_company_report(raw, sources)["metrics"][0]
    assert metric["numeric_value"] == -20 and metric["unit"] == "percent" and metric["currency"] is None


def test_score_is_server_mean_of_at_least_three_supported_ratings():
    raw = valid_report()
    raw["score"] = 1
    for item, score in zip(raw["scorecard"], [5, 4, None, None, None, None, None]):
        item["score"] = score
    source = {"id": "S1", "basis": "primary", "text": "Full-year EPS was USD 2.50."}
    assert validate_company_report(raw, [source])["score"] is None
    raw["scorecard"][2]["score"] = 3
    assert validate_company_report(raw, [source])["score"] == 4


def test_valuation_requires_exact_primary_annual_eps_and_scenarios():
    raw = valid_report()
    primary = {"id": "S1", "basis": "primary", "text": "Full-year earnings per share (EPS) were USD 2.50."}
    assert validate_company_report(raw, [primary])["valuation"]["available"] is True

    for text, basis in (("Quarterly EPS was USD 2.50.", "primary"),
                        ("Full-year EPS was USD 2.50.", "saved_analysis"),
                        ("Full-year EPS was USD 3.50.", "primary")):
        result = validate_company_report(valid_report(), [{"id": "S1", "basis": basis, "text": text}])
        assert result["valuation"]["available"] is False
        assert result["valuation"]["base_eps"] is None
        assert result["valuation"]["scenarios"] == []

    raw = valid_report()
    raw["valuation"]["scenarios"].pop()
    result = validate_company_report(raw, [primary])
    assert result["valuation"]["available"] is False


def test_missing_data_stays_empty_and_source_guidance_is_required_for_projections():
    raw = valid_report()
    raw["scorecard"] = []
    raw["signals"] = []
    raw["projections"] = []
    raw["valuation"].update(available=False, base_eps=None, currency=None, source_id=None, scenarios=[])
    result = validate_company_report(raw, [{"id": "S1", "text": "A sparse quarterly report."}])
    assert result["score"] is None
    assert result["scorecard"] == result["signals"] == result["projections"] == []

    raw = valid_report()
    raw["projections"][0]["basis"] = "model_estimate"
    with pytest.raises(ValueError):
        validate_company_report(raw, [{"id": "S1", "text": "A sparse quarterly report."}])


def test_prompt_covers_broad_dossier_without_inventing_source_data():
    prompt = build_company_report_prompt("Example Co", "2026-10-15", "en", [
        {"id": "S1", "title": "Annual report", "url": None, "text": "Only source facts."}
    ])
    for phrase in ("business model", "customers", "competitors", "management", "capital allocation",
                   "ownership", "growth drivers", "risks", "analyst consensus", "never model estimates",
                   "Never annualize quarterly EPS", "bear/base/bull"):
        assert phrase.lower() in prompt.lower()


def test_localized_prompt_keeps_editorial_coverage_scores_and_numeric_units_explicit():
    for locale, phrases in (
        ("en", ("one complete editorial sentence", "Never put source availability", "Every included scorecard factor",
                "integer score from 1 to 5", "never fill it with a default score", "reader-facing label", "full base units")),
        ("pt", ("frase editorial completa", "Não coloque disponibilidade de fontes", "nota inteira de 1 a 5",
                "nunca preencha com nota padrão", "português brasileiro", "unidades básicas completas")),
    ):
        prompt = build_company_report_prompt("MSFT", "2026-10-15", locale, [])
        assert all(phrase in prompt for phrase in phrases)


def test_report_prompt_preserves_ten_sections_with_a_concise_writing_budget():
    for locale, budget in (("en", "1,000–1,400"), ("pt", "1.000–1.400")):
        prompt = build_company_report_prompt("NKE", "2026-10-19", locale, [])
        assert budget in prompt
        assert "thesis, business, financials, moat, management, sentiment, outlook, risks, valuation, verdict" in prompt


def test_company_report_ticker_requires_evidence_and_legacy_reports_remain_valid():
    raw = valid_report()
    sources = [{"id": "S1", "title": "Nike, Inc. (NKE)", "basis": "primary", "text": "Full-year EPS was USD 2.50."}]
    assert validate_company_report(raw, sources)["symbol"] is None
    raw["symbol"] = "NKE"
    assert validate_company_report(raw, sources)["symbol"] == "NKE"
    raw["symbol"] = "MADEUP"
    assert validate_company_report(raw, sources)["symbol"] is None


def test_scenario_numeric_bounds_and_market_price_are_enforced():
    raw = valid_report()
    raw["valuation"]["scenarios"][0]["growth_percent"] = 101
    with pytest.raises(ValueError):
        validate_company_report(raw, [{"id": "S1", "basis": "primary", "text": "Full-year EPS was USD 2.50."}])

    raw = valid_report()
    raw["market"].update(price=100, currency="USD", as_of="2026-10-15", source_id="S1")
    raw["market"]["price"] = -1
    with pytest.raises(ValueError, match="positive"):
        validate_company_report(raw, [{"id": "S1", "basis": "primary", "text": "Full-year EPS was USD 2.50."}])


def geography_report(shares, *, complete=False):
    raw = valid_report()
    raw["breakdowns"] = [
        {"category": "geography", "label": label, "value": "Reported revenue", "share": share,
         "source_id": "S1", "period": "FY2025", "group_complete": complete}
        for label, share in zip(("Domestic", "International"), shares)]
    return raw


def test_complete_fraction_group_is_normalized_to_percentage_points_only_once():
    source = [{"id": "S1", "text": "Domestic and international exhaust annual revenue."}]
    raw = geography_report([0.515, 0.485], complete=True)
    result = validate_company_report(raw, source)
    assert [row["share"] for row in result["breakdowns"]] == [51.5, 48.5]
    assert [row["share"] for row in validate_company_report(result, source)["breakdowns"]] == [51.5, 48.5]
    for shares, complete in (([0.515, 0.485], False), ([0.5, 10], True), ([0.5], True), ([51.5, 48.5], True)):
        raw = geography_report(shares, complete=complete)
        assert [row["share"] for row in validate_company_report(raw, source)["breakdowns"]] == shares


def test_breakdown_shares_can_be_recovered_from_matching_complete_currency_revenue():
    source = [{"id": "S1", "text": "FY2025 domestic revenue USD 5.15; international USD 4.85; total USD 10."}]
    raw = geography_report([None, None])
    for row, value in zip(raw["breakdowns"], (5.15, 4.85)):
        row.update(numeric_value=value, currency="USD")
    result = validate_company_report(raw, source)
    assert [row["share"] for row in result["breakdowns"]] == [51.5, 48.5]
    for invalid in ({"currency": "CAD"}, {"period": "FY2024"}, {"numeric_value": 1.0}):
        raw["breakdowns"][0].update(invalid)
        assert all(row["share"] is None for row in validate_company_report(raw, source)["breakdowns"])
        raw["breakdowns"][0].update(numeric_value=5.15, currency="USD", period="FY2025")


def test_breakdown_currency_and_amount_are_validated_without_guessing():
    for invalid in ({"numeric_value": float("nan"), "currency": "USD"},
                    {"numeric_value": -5, "currency": "USD"}, {"numeric_value": 5}, {"currency": "USD"}):
        raw = geography_report([51.5, 48.5])
        raw["breakdowns"][0].update(invalid)
        with pytest.raises(ValueError):
            validate_company_report(raw, [{"id": "S1", "text": "Reported facts."}])


def test_dated_cited_analyst_consensus_supports_partial_values_and_no_invented_counts():
    raw = valid_report()
    raw["analyst_consensus"] = {"rating": "Buy", "target_mean": 500, "currency": "USD",
                                "as_of": "2026-10-15", "source_ids": ["S1"]}
    result = validate_company_report(raw, [{"id": "S1", "text": "Dated market provider consensus."}])
    consensus = result["analyst_consensus"]
    assert consensus["target_mean"] == 500 and consensus["analyst_count"] is None
    assert consensus["bullish"] is None and consensus["target_low"] is None
    raw["analyst_consensus"] = {}
    assert validate_company_report(raw, [{"id": "S1", "text": "Annual report."}])["analyst_consensus"] is None


@pytest.mark.parametrize("invalid", [
    {"source_ids": []}, {"source_ids": ["UNKNOWN"]}, {"as_of": None}, {"as_of": "FY2026"},
    {"currency": None}, {"target_mean": float("inf")}, {"target_low": 600},
    {"analyst_count": 10, "bullish": 9, "neutral": 2, "bearish": 0}, {"bullish": -1},
])
def test_analyst_consensus_rejects_uncited_undated_inconsistent_values(invalid):
    raw = valid_report()
    raw["analyst_consensus"] = {"rating": "Buy", "target_mean": 500, "currency": "USD",
                                "as_of": "2026-10-15", "source_ids": ["S1"], **invalid}
    with pytest.raises(ValueError):
        validate_company_report(raw, [{"id": "S1", "text": "Dated market consensus."}])


def complete_report():
    report = valid_report()
    report["financial_history"] = [{**report["financial_history"][0], "period": str(year)} for year in (2023, 2024, 2025)]
    report["metrics"] = [{**report["metrics"][0], "label": label, "numeric_value": 10.0, "unit": "currency", "currency": "USD"} for label in ("Revenue", "Net income", "Operating cash flow", "Gross margin")]
    return report


def test_official_numbers_survive_sparse_synthesis_and_do_not_mutate_model_output():
    from company_report_content import apply_official_financials, ensure_company_completeness
    raw=valid_report()
    source={"id":"F1","basis":"primary","annual_financials":[{"period":str(year)+"-12-31","currency":"USD","values":{
        "Revenue":100+year,"Net income":10,"Operating cash flow":20,"Free cash flow (calculated)":15}} for year in (2022,2023,2024)]}
    merged=apply_official_financials(raw,[source])
    ensure_company_completeness(merged)
    assert len(merged["financial_history"])==3 and len(merged["metrics"])==4
    assert merged["financial_history"][0]["revenue"]==2124
    assert len(raw["financial_history"])==1


def test_thin_financial_report_cannot_be_published_as_complete():
    from company_report_content import ensure_company_completeness
    from full_report_content import ReportValidationError
    with pytest.raises(ReportValidationError):ensure_company_completeness(valid_report())
    report=complete_report();report["valuation"]["available"]=False
    with pytest.raises(ReportValidationError):ensure_company_completeness(report,[{"id":"F1","basis":"primary","annual_financials":[{"period":"2025","values":{"Diluted EPS":2.5}}]}])


def stub_pipeline(client, company, as_of, locale, sources, dossier, *, deadline):
    # Route/quota unit tests isolate the pipeline; its real stages have dedicated contract tests.
    import full_reports as reports
    raw=client.analyze_full_report("Pipeline stub", reports.company_report_schema(), max_output_tokens=11000, timeout=120)
    return reports.calculated_company_valuation(reports.validate_company_report(raw,sources))
