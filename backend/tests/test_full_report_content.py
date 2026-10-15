from pathlib import Path
from copy import deepcopy
import json
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
    json.dumps(schema)

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
    properties = schema["properties"]
    assert properties["coverage"]["pattern"] == r"^[\s\S]{1,300}$"
    assert properties["sections"]["minItems"] == properties["sections"]["maxItems"] == 7
    assert properties["metrics"]["maxItems"] == 30
    assert properties["watchpoints"]["maxItems"] == 10
    section = properties["sections"]["items"]["properties"]
    assert section["title"]["pattern"] == r"^[\s\S]{1,100}$"
    assert section["summary"]["pattern"] == r"^[\s\S]{0,700}$"
    assert section["paragraphs"]["maxItems"] == 5
    assert section["paragraphs"]["items"]["pattern"] == r"^[\s\S]{0,1200}$"
    assert section["bullets"]["maxItems"] == 8
    assert section["bullets"]["items"]["pattern"] == r"^[\s\S]{0,300}$"
    assert section["source_ids"]["maxItems"] == 12
    assert section["source_ids"]["items"]["pattern"] == r"^[\s\S]{1,40}$"
    metric = properties["metrics"]["items"]["properties"]
    assert all(metric[key]["pattern"] == r"^[\s\S]{1,100}$" for key in ("label", "value"))
    assert metric["source_id"]["pattern"] == r"^[\s\S]{1,40}$"
    assert properties["watchpoints"]["items"]["pattern"] == r"^[\s\S]{0,300}$"
    assert properties["valuation"]["properties"]["reason"]["pattern"] == r"^[\s\S]{0,500}$"
    assert properties["valuation"]["properties"]["source_id"]["anyOf"][0]["pattern"] == r"^[\s\S]{1,40}$"


def test_rejects_unknown_source_and_duplicate_sections_and_normalizes_order():
    source = {"id": "S1", "text": "Quarterly release", "title": "Release", "url": None}
    report = valid_report()
    report["sections"][0]["source_ids"] = ["FAKE"]
    with pytest.raises(ValueError, match="unknown source"):
        validate_full_report(report, [source])

    report = valid_report()
    report["sections"][0], report["sections"][1] = report["sections"][1], report["sections"][0]
    assert [section["id"] for section in validate_full_report(report, [source])["sections"]] == list(SECTION_IDS)

    report["sections"][0] = report["sections"][1]
    with pytest.raises(ValueError, match="exactly once"):
        validate_full_report(report, [source])


def test_limit_boundaries_pass_and_oversize_values_fail():
    report = valid_report()
    report["coverage"] = "c" * 300
    section = report["sections"][0]
    section.update(title="t" * 100, summary="s" * 700,
                   paragraphs=["p" * 1200] * 5, bullets=["b" * 300] * 8,
                   source_ids=["S1"] * 12)
    report["metrics"] = [{"label": "l" * 100, "value": "v" * 100, "source_id": "S1"}] * 30
    report["watchpoints"] = ["w" * 300] * 10
    report["valuation"]["reason"] = "r" * 500
    assert len(validate_full_report(report, [{"id": "S1", "text": "Quarterly release"}])["metrics"]) == 30

    oversize = [
        lambda r: r["sections"][0].update(title="t" * 101),
        lambda r: r["sections"][0].update(summary="s" * 701),
        lambda r: r["sections"][0].update(paragraphs=["p"] * 6),
        lambda r: r["sections"][0].update(paragraphs=["p" * 1201]),
        lambda r: r["sections"][0].update(bullets=["b"] * 9),
        lambda r: r["sections"][0].update(bullets=["b" * 301]),
        lambda r: r["sections"][0].update(source_ids=["S1"] * 13),
        lambda r: r.update(metrics=r["metrics"] * 31),
        lambda r: r["metrics"][0].update(value="v" * 101),
        lambda r: r.update(watchpoints=["w"] * 11),
        lambda r: r.update(watchpoints=["w" * 301]),
        lambda r: r["valuation"].update(reason="r" * 501),
    ]
    for make_oversize in oversize:
        candidate = deepcopy(valid_report())
        make_oversize(candidate)
        with pytest.raises(ValueError):
            validate_full_report(candidate, [{"id": "S1", "text": "Quarterly release"}])


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
