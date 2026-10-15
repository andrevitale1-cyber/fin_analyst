from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from full_report_content import SECTION_IDS, build_full_report_prompt, report_schema, validate_full_report


def valid_report():
    return {
        "coverage": "Limited to one official quarterly release.",
        "score": None,
        "sections": [
            {"id": section_id, "title": section_id.title(), "summary": "Limited evidence.",
             "paragraphs": [], "bullets": [], "source_ids": ["S1"]}
            for section_id in SECTION_IDS
        ],
        "metrics": [{"label": "Revenue", "value": "R$ 100 million", "source_id": "S1"}],
        "watchpoints": [],
        "valuation": {"available": False, "base_eps": None, "currency": None,
                      "source_id": None, "reason": "No annual EPS evidence."},
    }


def test_schema_requires_every_field_and_forbids_extra_properties():
    schema = report_schema()

    def visit(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
                assert set(node["required"]) == set(node["properties"])
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)


def test_rejects_unknown_source_and_wrong_section_order():
    source = {"id": "S1", "text": "Quarterly release", "title": "Release", "url": None}
    report = valid_report()
    report["sections"][0]["source_ids"] = ["FAKE"]
    with pytest.raises(ValueError, match="unknown source"):
        validate_full_report(report, [source])

    report = valid_report()
    report["sections"][0], report["sections"][1] = report["sections"][1], report["sections"][0]
    with pytest.raises(ValueError, match="prescribed order"):
        validate_full_report(report, [source])


def test_downgrades_quarterly_eps_or_missing_currency_to_unavailable():
    report = valid_report()
    report["valuation"] = {"available": True, "base_eps": 2.5, "currency": "USD",
                           "source_id": "S1", "reason": "Reported EPS."}
    source = {"id": "S1", "text": "Quarterly EPS was USD 2.50.", "title": "Release", "url": None}
    result = validate_full_report(report, [source])
    assert result["valuation"] == {
        "available": False, "base_eps": None, "currency": None, "source_id": None,
        "reason": "The source does not explicitly establish positive annual or TTM EPS and its currency.",
    }

    source["text"] = "Full-year earnings per share were 2.50."
    assert validate_full_report(report, [source])["valuation"]["available"] is False


def test_accepts_positive_annual_eps_only_when_currency_and_basis_are_in_source():
    report = valid_report()
    report["valuation"] = {"available": True, "base_eps": 2.5, "currency": "USD",
                           "source_id": "S1", "reason": "Full-year EPS reported."}
    source = {"id": "S1", "text": "Full-year earnings per share (EPS) were USD 2.50.", "basis": "primary",
              "title": "Annual release", "url": "https://example.test"}
    result = validate_full_report(report, [source])
    assert result["valuation"]["available"] is True

    report["valuation"]["base_eps"] = 999
    assert validate_full_report(report, [source])["valuation"]["available"] is False

    report["valuation"]["base_eps"] = 2.5
    source["basis"] = "saved_analysis"
    assert validate_full_report(report, [source])["valuation"]["available"] is False


def test_prompt_marks_private_fallback_as_limited_and_excludes_fabrication():
    prompt = build_full_report_prompt("Example Co", "Q1 2026", "en", "report", [
        {"id": "S1", "basis": "saved_analysis", "title": "Saved analysis", "url": None, "text": "Summary"}
    ])
    assert "saved AI analysis" in prompt
    assert "limited" in prompt
    assert "Never annualize quarterly EPS" in prompt
    assert "do not fabricate a moat" in prompt.lower()


@pytest.mark.parametrize("eps,text", [
    (250, "Full-year EPS was USD 2.50."),
    (2.5, "Full-year revenue rose; quarterly EPS was USD 2.50."),
    (2.5, "Annual EPS guidance is USD 2.50."),
    (float('inf'), "Full-year EPS was USD 2.50."),
    (2026, "Full-year 2026 EPS was USD 2.50."),
])
def test_valuation_rejects_decimal_misreading_forecasts_and_unrelated_numbers(eps, text):
    raw = valid_report()
    raw["valuation"] = {"available": True, "base_eps": eps, "currency": "USD", "source_id": "S1", "reason": "Annual EPS"}
    result = validate_full_report(raw, [{"id": "S1", "text": text, "basis": "primary"}])
    assert result["valuation"]["available"] is False
