import copy

import pytest

from agents.petrobras_model import calculate
from agents.report_model import baseline_from_sources, verify_model, model_valuation_section
from full_report_content import ReportValidationError
from test_operating_model import official_source


def fixture():
    source = official_source()
    for row in source["annual_financials"]:
        row["currency"] = "BRL"
    quote = "At June 30 2026 financial debt was BRL 150, lease debt BRL 50, cash BRL 100, noncontrolling interests BRL 10 and outstanding ON and PN shares 50."
    rights = "Each outstanding common and preferred share has equal participation in distributed earnings, subject to the preferred minimum rights."
    source["text"] += " " + quote + " " + rights
    def amount(n, unit="BRL"):
        return dict(value=n, multiplier=1, quote=quote, unit_quote=quote, source_id="F1", period="2026-06-30", unit=unit)
    scenarios = []
    for case, factor in [("bear", .8), ("base", 1), ("bull", 1.2)]:
        years = [dict(year=year, brent_usd=70 * factor, usd_brl=5, production_kboed=2000 * factor,
                      external_revenue_brl=1000 * factor, upstream_ebitda_brl=220 * factor,
                      downstream_ebitda_brl=70 * factor, other_and_eliminations_ebitda_brl=-20,
                      depreciation_brl=30, capex_including_lease_reinvestment_brl=60,
                      working_capital_investment_brl=10, tax_percent=30,
                      rationale="Synthetic scenario assumptions for arithmetic tests, not issuer forecasts.") for year in range(2027, 2032)]
        scenarios.append(dict(case=case, wacc_percent=12, perpetual_growth_percent=2, terminal_ev_ebitda=5,
                              rationale="Synthetic operational scenario with a constant nominal discount rate.",
                              terminal_reinvestment_rationale="Maintenance and reserve replacement are included in projected reinvestment.",
                              source_ids=["F1", "S1"], years=years))
    raw = dict(bridge=dict(shares=amount(50, "shares"), financial_debt=amount(150), lease_debt=amount(50), cash=amount(100),
                          noncontrolling_interests=amount(10), share_rights_quote=rights, share_rights_source_id="F1",
                          lease_treatment="Debt includes lease obligations and capex includes economic replacement of leased assets."),
               conviction="medium", rationale="Scenario assumptions illustrate commodity and volume exposure with reinvestment.",
               counterthesis="Commodity prices and capital allocation could erode the projected operating cash generation.", scenarios=scenarios)
    return [source, {"id": "S1", "basis": "primary", "text": "Source for synthetic assumptions."}], raw


def test_oil_dcf_and_exit_multiple_include_intermediate_flows_and_equity_bridge():
    sources, raw = fixture()
    baseline = baseline_from_sources(sources)
    model = calculate(baseline, raw, sources)
    base = model["cases"][1]
    row = base["projections"][0]
    assert row["ebitda"] == 270
    assert row["fcff"] == 128
    pv = sum(r["fcff"] / 1.12 ** r["discount_years"] for r in base["projections"])
    terminal = 128 * 1.02 / .10 / 1.12 ** base["projections"][-1]["discount_years"]
    assert base["equity_bridge"]["enterprise_value"] == pytest.approx(pv + terminal)
    assert base["methods"][0]["present_value"] == round((pv + terminal - 100 - 10) / 50, 2)
    exit_ev = 270 * 5 / 1.12 ** base["projections"][-1]["discount_years"]
    assert base["methods"][1]["present_value"] == round((pv + exit_ev - 100 - 10) / 50, 2)
    assert len(base["sensitivity"]) == 9
    assert row["eps"] is None and row["net_income"] is None
    verify_model(model, sources)
    section = model_valuation_section(model, "pt")["section"]
    assert len(section["paragraphs"]) == 5 and "arrendamentos" in " ".join(section["paragraphs"])


@pytest.mark.parametrize("mutation", ["currency", "quote", "scale", "date", "stale", "shares", "source", "rights", "years", "capex", "spread", "scenario", "nan"])
def test_invalid_oil_inputs_are_rejected(mutation):
    sources, raw = fixture()
    baseline = baseline_from_sources(sources)
    if mutation == "currency": baseline["currency"] = "USD"
    if mutation == "quote": raw["bridge"]["cash"]["value"] = 999
    if mutation == "scale": raw["bridge"]["cash"]["multiplier"] = 1000000
    if mutation == "date": raw["bridge"]["cash"]["period"] = "2025-12-31"
    if mutation == "stale":
        for key in ("financial_debt", "lease_debt", "cash", "noncontrolling_interests"):
            raw["bridge"][key]["period"] = "2025-12-31"
    if mutation == "shares": raw["bridge"]["shares"]["unit"] = "BRL"
    if mutation == "source": sources[0]["basis"] = "web_research"
    if mutation == "rights": raw["bridge"]["share_rights_quote"] = "This is an invented economic rights statement."
    if mutation == "years": raw["scenarios"][0]["years"][0]["year"] = 2026
    if mutation == "capex": raw["scenarios"][0]["years"][-1]["capex_including_lease_reinvestment_brl"] = 20
    if mutation == "spread": raw["scenarios"][0]["wacc_percent"] = 4; raw["scenarios"][0]["perpetual_growth_percent"] = 4
    if mutation == "scenario": raw["scenarios"][0]["case"] = "base"
    if mutation == "nan": raw["scenarios"][0]["years"][0]["brent_usd"] = float("nan")
    with pytest.raises((ReportValidationError, ValueError)):
        calculate(baseline, raw, sources)


def test_independent_review_recomputes_oil_model():
    sources, raw = fixture()
    model = calculate(baseline_from_sources(sources), raw, sources)
    corrupted = copy.deepcopy(model)
    corrupted["cases"][1]["equity_bridge"]["shares"] *= 2
    with pytest.raises(ReportValidationError):
        verify_model(corrupted, sources)


@pytest.mark.parametrize("missing", [None, "signal", "year", "model", "currency", "review", "paragraphs", "metrics"])
def test_publication_requires_complete_sector_edition(missing):
    from thesis_library import validate_publication
    sources, raw = fixture()
    report = dict(scope="company", company="PETR4", locale="pt", is_public=False, as_of="2026-10-21",
                  research_profile="editorial-v1", pipeline={"verification": {"passed": True, "checks": ["petrobras_sector"]}},
                  sections=[{"paragraphs": ["A complete paragraph."] * 2, "id": str(i)} for i in range(10)],
                  financial_history=[{"period": f"{year}-12-31"} for year in range(2021, 2026)],
                  signals=[{"id": id} for id in ("moat", "profitability", "management", "growth", "valuation", "sentiment")],
                  metrics=[{}] * 8, investment_model=calculate(baseline_from_sources(sources), raw, sources))
    if missing == "signal": report["signals"].pop()
    if missing == "year": report["financial_history"][-1]["period"] = "2020-12-31"
    if missing == "model": report["investment_model"]["version"] = "operating-model-v2"
    if missing == "currency": report["investment_model"]["baseline"]["currency"] = "USD"
    if missing == "review": report["pipeline"]["verification"]["checks"] = []
    if missing == "paragraphs": report["sections"][0]["paragraphs"] = []
    if missing == "metrics": report["metrics"] = []
    if missing:
        with pytest.raises(ValueError): validate_publication(report, "PETR4", "pt")
    else:
        validate_publication(report, "PETR4", "pt")
