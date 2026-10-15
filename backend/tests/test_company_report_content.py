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


def test_duplicate_or_incomplete_section_scorecard_and_signal_ids_reject():
    source = {"id": "S1", "basis": "primary", "text": "Full-year EPS was USD 2.50."}
    raw = valid_report()
    raw["sections"][0] = raw["sections"][1]
    with pytest.raises(ValueError, match="section exactly once"):
        validate_company_report(raw, [source])

    raw = valid_report()
    raw["scorecard"].pop()
    with pytest.raises(ValueError, match="scorecard"):
        validate_company_report(raw, [source])

    raw = valid_report()
    raw["signals"].pop()
    with pytest.raises(ValueError, match="signals"):
        validate_company_report(raw, [source])


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
