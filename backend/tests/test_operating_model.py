import copy
from time import perf_counter
from unittest.mock import Mock

import pytest

from agents.report_model import baseline_from_sources, calculate_model, verify_model
from agents.report_pipeline import generate_report
from full_report_content import ReportValidationError


def official_source():
    return {"id": "F1", "basis": "primary", "title": "Annual financials", "url": "https://issuer.example/annual",
            "text": "Original consolidated annual statements.", "retrieved_at": "2026-10-20",
            "annual_financials": [{"period": f"{year}-12-31", "currency": "USD", "values": {
                "Revenue": revenue, "Net income": profit, "Net income attributable to parent": profit,
                "Operating income": 150, "Diluted EPS": eps, "Diluted shares": 50,
                "Operating cash flow": 120, "Free cash flow (calculated)": 60,
                "Current long-term debt": 50, "Noncurrent long-term debt": 150,
                "Cash and cash equivalents": 100, "Book equity": 500}}
                for year, revenue, profit, eps in [(2025, 1000, 100, 2), (2024, 900, 75, 1.5),
                                                  (2023, 800, -100, -2), (2022, 700, 60, 1.2), (2021, 600, 50, 1)]]}


def assumptions():
    cases = []
    for name, growth, margin, pe, discount in [("bear", 0, 8, 10, 14), ("base", 5, 12, 15, 10), ("bull", 10, 20, 20, 8)]:
        cases.append({"case": name, "capacity_growth_percent": growth, "productivity_growth_percent": growth,
                      "terminal_revenue_growth_percent": growth / 2, "terminal_net_margin_percent": margin,
                      "terminal_operating_margin_percent": margin + 5, "capex_percent": 6,
                      "depreciation_percent": 4, "incremental_working_capital_percent": 10, "tax_percent": 25,
                      "terminal_pe": pe, "terminal_ev_ebitda": pe / 2, "price_to_book": pe / 5,
                      "discount_percent": discount, "equity_discount_percent": discount + 2, "perpetual_growth_percent": 2,
                      "rationale": "Explicit conditional model assumptions with constant shares and net debt.", "source_ids": ["F1"]})
    return {"profile": "retail", "primary_method": "pe", "capacity_driver": "Productive store equivalents",
            "productivity_driver": "Sales per store", "conviction": "medium", "rationale": "Assumed expansion and profitability drive these conditional outcomes.",
            "counterthesis": "Demand and cash conversion could disappoint against these assumptions.", "scenarios": cases}


def test_python_projects_and_cross_checks_without_treating_assumptions_as_consensus():
    source = official_source()
    base = baseline_from_sources([source])
    result = calculate_model(base, assumptions(), {"F1"})
    assert result["available"] and result["selected_method"] == "pe"
    assert {"dcf", "ev_ebitda", "normalized_pe"}.issubset(result["cross_check_methods"])
    projection = result["cases"][1]["projections"][0]
    assert projection["basis"] == "ai_assumption"
    assert projection["revenue"] == pytest.approx(1000 * 1.05 * 1.05)
    assert 0 < projection["discount_years"] < 1
    assert projection["dcf_period_fraction"] == pytest.approx(72 / 365)
    forecasts = result["cases"][1]["projections"]
    discount = assumptions()["scenarios"][1]["discount_percent"] / 100
    terminal_ev = forecasts[-1]["fcff"] * 1.02 / (discount - .02)
    enterprise = sum(r["fcff"] * r["dcf_period_fraction"] / (1 + discount) ** r["discount_years"] for r in forecasts)
    enterprise += terminal_ev / (1 + discount) ** forecasts[-1]["discount_years"]
    dcf = next(m for m in result["cases"][1]["methods"] if m["method"] == "dcf")
    assert dcf["present_value"] == pytest.approx(round((enterprise - 100) / 50, 2))
    assert projection["ebitda"] == pytest.approx(projection["operating_income"] + projection["depreciation"])
    normalized = next(m for m in result["cases"][1]["methods"] if m["method"] == "normalized_pe")
    assert normalized["present_value"] == pytest.approx((2 + 1.5 - 2 + 1.2 + 1) / 5 * 15)
    verify_model(result, [source])


@pytest.mark.parametrize("change", ["price", "cashflow", "source", "growth"])
def test_independent_recalculation_blocks_mutated_outputs(change):
    source = official_source()
    result = calculate_model(baseline_from_sources([source]), assumptions(), {"F1"})
    if change == "price": result["fair_value"] *= 2
    if change == "cashflow": result["cases"][0]["projections"][0]["fcff"] += 100
    if change == "source": result["baseline"]["values"]["Revenue"] += 1
    if change == "growth": result["cases"][0]["assumptions"]["source_ids"] = ["invented"]
    with pytest.raises(ReportValidationError): verify_model(result, [source])


def test_financial_sector_avoids_industrial_dcf_and_preserves_book_value_method():
    raw = assumptions(); raw.update(profile="financial", primary_method="price_to_book")
    result = calculate_model(baseline_from_sources([official_source()]), raw, {"F1"})
    assert result["selected_method"] == "price_to_book"
    assert not any(m["method"] in ("dcf", "ev_ebitda") for c in result["cases"] for m in c["methods"])


def test_missing_eps_allows_other_valid_methods_but_missing_debt_does_not_imply_zero():
    source = official_source()
    source["annual_financials"][0]["values"].pop("Diluted EPS")
    result = calculate_model(baseline_from_sources([source]), assumptions(), {"F1"})
    assert result["available"] and result["selected_method"] == "dcf"
    source["annual_financials"][0]["values"].pop("Current long-term debt")
    base = baseline_from_sources([source])
    assert base["net_debt"] is None
    result = calculate_model(base, assumptions(), {"F1"})
    assert all(m["method"] not in ("dcf", "ev_ebitda") for c in result["cases"] for m in c["methods"])


def test_zero_spread_unknown_sources_and_reversed_scenarios_are_blocked():
    base = baseline_from_sources([official_source()])
    for mutation in ("spread", "source", "ordering"):
        raw = assumptions()
        if mutation == "spread": raw["scenarios"][0]["discount_percent"] = 2
        if mutation == "source": raw["scenarios"][0]["source_ids"] = ["unknown"]
        if mutation == "ordering": raw["scenarios"][0]["terminal_pe"] = 100
        with pytest.raises(ReportValidationError): calculate_model(base, raw, {"F1"})


def test_new_pipeline_uses_the_model_and_independent_audit_without_an_extra_valuation_call(monkeypatch):
    import agents.report_pipeline as pipeline
    from test_report_agents import AgentClient, facts, SOURCES
    from agents.report_facts import validate_dossier
    source = official_source()
    model = calculate_model(baseline_from_sources([source]), assumptions(), {"F1", "S1"})
    monkeypatch.setattr(pipeline, "checkpoint", lambda stage, identity, compute: compute())
    client = AgentClient()
    report = generate_report(client, "MU", "2026-10-20", "en", [source, *SOURCES], validate_dossier(facts(), SOURCES),
                             deadline=perf_counter() + 700, investment_model=model)
    assert report["investment_model"]["available"] and report["pipeline"]["verification"]["passed"]
    assert len(report["financial_history"]) == 5
    assert len(client.calls) == 2
    assert not report["valuation"]["available"]  # The separate typed model owns these valuations.
    assert report["valuation"]["method"] == "Audited operating model"


def test_normalized_earnings_narrative_matches_its_formula_and_shows_cross_checks():
    from agents.report_model import model_valuation_section
    from agents.report_valuation import calculate_valuation
    raw = assumptions(); raw["primary_method"] = "normalized_pe"
    model = calculate_model(baseline_from_sources([official_source()]), raw, {"F1"})
    content = model_valuation_section(model, "en")
    section = content.pop("section")
    content["sections"] = [section]
    calculate_valuation(content, "en")
    assert "including losses" in section["paragraphs"][0]
    assert "not discounted terminal earnings" in section["paragraphs"][0]
    assert "different bases" in " ".join(section["paragraphs"])
    assert len(section["bullets"]) == 3 and all("normalized_pe" in b and "pe:" in b for b in section["bullets"])
    assert content["valuation"]["method"] == "Audited operating model"


def test_model_copy_keeps_complete_sentences_and_short_driver_labels():
    raw = assumptions()
    raw["rationale"] = "Complete supported conditional assumptions. This trailing fragment was cut"
    raw["capacity_driver"] = "Productive stores, including detailed explanation that does not belong in the label"
    result = calculate_model(baseline_from_sources([official_source()]), raw, {"F1"})
    assert result["assumptions"]["rationale"] == "Complete supported conditional assumptions."
    assert result["assumptions"]["capacity_driver"] == "Productive stores"
