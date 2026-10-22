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
    quote = "At June 30 2026 financial debt current BRL 50 and noncurrent BRL 100, leases current BRL 10 and noncurrent BRL 40, cash BRL 100, noncontrolling interests BRL 10 and outstanding ON and PN shares 50."
    rights = "Each outstanding common and preferred share has equal participation in distributed earnings, subject to the preferred minimum rights."
    source["text"] += " " + quote + " " + rights
    source["text"] += """ Consolidated Interim Accounting Information / Statement of Financial Position - Assets
        (R$ Units) Account Code Account Description 06.30.2026 12.31.2025
        1.01.01 Cash and Cash Equivalents 100 90 1.01.02 Marketable Securities 20 15
        Consolidated Interim Accounting Information / Statement of Financial Position - Liabilities
        (R$ Units) Account Code Account Description 06.30.2026 12.31.2025
        2.01.04.01 Current Debt 50 45 2.01.04.03 Lease Obligations 10 8
        2.02.01.01 Non-Current Debt 100 95 2.02.01.03 Lease Obligations 40 35
        2.03.09 Non-controlling interests 10 9 """
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
    raw = dict(bridge=dict(shares=amount(50, "shares"), share_rights_quote=rights, share_rights_source_id="F1",
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
    assert base["equity_bridge"]["net_debt"] == 80
    assert base["methods"][0]["present_value"] == round((pv + terminal - 80 - 10) / 50, 2)
    exit_ev = 270 * 5 / 1.12 ** base["projections"][-1]["discount_years"]
    assert base["methods"][1]["present_value"] == round((pv + exit_ev - 80 - 10) / 50, 2)
    assert len(base["sensitivity"]) == 9
    assert row["eps"] is None and row["net_income"] is None
    assert model["valuation_share_basis"]["shares"] == 50
    assert model["valuation_share_basis"]["historical_baseline_shares_used"] is False
    verify_model(model, sources)
    section = model_valuation_section(model, "pt")["section"]
    assert len(section["paragraphs"]) == 5 and "arrendamentos" in " ".join(section["paragraphs"])


@pytest.mark.parametrize("mutation", ["currency", "quote", "scale", "date", "stale", "shares", "source", "rights", "years", "capex", "spread", "scenario", "nan"])
def test_invalid_oil_inputs_are_rejected(mutation):
    sources, raw = fixture()
    baseline = baseline_from_sources(sources)
    if mutation == "currency": baseline["currency"] = "USD"
    if mutation == "quote": raw["bridge"]["shares"]["value"] = 999
    if mutation == "scale": raw["bridge"]["shares"]["multiplier"] = 1000000
    if mutation == "date": sources[0]["text"] = sources[0]["text"].replace("Assets\n        (R$ Units) Account Code Account Description 06.30.2026", "Assets\n        (R$ Units) Account Code Account Description 06.29.2026")
    if mutation == "stale":
        sources[0]["text"] = sources[0]["text"].replace("06.30.2026", "12.31.2025")
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


def test_populated_oil_scenarios_reject_a_contradictory_refusal():
    sources, raw = fixture()
    raw["rationale"] = "PUBLICAÇÃO DE VALUATION BLOQUEADA. Não foram preenchidos cenários numéricos."
    with pytest.raises(ValueError, match="cannot describe"):
        calculate(baseline_from_sources(sources), raw, sources)
    raw["rationale"] = "Explicit conditional assumptions explain the projected cash generation. An unfinished"
    model = calculate(baseline_from_sources(sources), raw, sources)
    assert model["oil_inputs"]["rationale"].endswith("generation.")


def test_rights_quote_accepts_capitalization_but_not_changed_economic_terms():
    sources, raw = fixture()
    raw["bridge"]["share_rights_quote"] = raw["bridge"]["share_rights_quote"].upper()
    assert calculate(baseline_from_sources(sources), raw, sources)["available"]
    raw["bridge"]["share_rights_quote"] = raw["bridge"]["share_rights_quote"].replace("EQUAL", "UNEQUAL")
    with pytest.raises(ReportValidationError, match="economic rights"):
        calculate(baseline_from_sources(sources), raw, sources)


def test_internal_editorial_copy_and_paragraph_signals_require_repair():
    from agents.report_verifier import reader_copy_issues
    report = {"coverage": "Publicação editorial definitiva bloqueada: faltam documentos.",
              "sections": [{"id": "verdict", "summary": "Conclusão de investimento.", "paragraphs": [], "bullets": []}],
              "signals": [{"value": "Este texto é uma explicação longa que não funciona como rótulo."}]}
    assert {i["target"] for i in reader_copy_issues(report)} == {"coverage", "signals"}
    report["coverage"] = "Análise corporativa com histórico de cinco anos e atualização até o 2T26."
    report["signals"][0]["value"] = "Disciplina sob acompanhamento"
    assert reader_copy_issues(report) == []
    report["breakdowns"] = [{"label": "Eliminações intersegmentos"}]
    market = {"id": "MKT1", "document_type": "market_data", "text": "PETR4 stock has a consensus rating of Buy."}
    issues = reader_copy_issues(report, [market])
    assert len(issues) == 2 and any(i["target"] == "breakdowns" for i in issues)


def test_original_model_context_includes_surrounding_table_and_rights():
    from agents.petrobras_model import original_model_contexts
    sources, raw = fixture()
    model = calculate(baseline_from_sources(sources), raw, sources)
    context = original_model_contexts(model, sources)
    text = " ".join(context[0]["excerpts"])
    assert "Consolidated Interim Accounting Information" in text
    assert "2.02.01.03 Lease Obligations 40 35" in text
    assert raw["bridge"]["share_rights_quote"] in text


def test_model_narrative_repair_cannot_change_any_numerical_input(monkeypatch):
    from agents.petrobras_model import repair_narratives
    from unittest.mock import Mock
    monkeypatch.setattr("report_runtime.checkpoint", lambda stage, identity, compute: compute())
    sources, raw = fixture()
    model = calculate(baseline_from_sources(sources), raw, sources)
    narrative = {"rationale": "Conditional cash generation explains the discounted operating value.",
                 "counterthesis": raw["counterthesis"], "scenarios": [{key: c[key] for key in
                    ("case", "rationale", "terminal_reinvestment_rationale")} for c in raw["scenarios"]]}
    client = Mock(model="test")
    client.analyze_full_report.return_value = narrative
    repaired = repair_narratives(client, model, [], sources, "en")
    assert repaired["fair_value"] == model["fair_value"]
    for old, new in zip(model["cases"], repaired["cases"]):
        assert old["equity_bridge"] == new["equity_bridge"]
        assert old["projections"] == new["projections"]
        assert old["methods"] == new["methods"]
    assert repaired["assumptions"]["rationale"] == narrative["rationale"]
    narrative["counterthesis"] = "Supported operating efficiency remains an explicitly conditional counterargument."
    issues = [{"target": "investment_model.oil_inputs.counterthesis", "reason": "Unsupported historical claim", "source_ids": ["F1"]}]
    selective = repair_narratives(client, model, issues, sources, "en")
    assert selective["oil_inputs"]["rationale"] == model["oil_inputs"]["rationale"]
    assert selective["oil_inputs"]["scenarios"] == model["oil_inputs"]["scenarios"]
    assert selective["oil_inputs"]["counterthesis"] == narrative["counterthesis"]


def test_bear_residual_floor_is_explicit_and_base_distress_still_requires_review():
    sources, raw = fixture()
    # A deeper commodity downside can leave enterprise value below debt.
    for row in raw["scenarios"][0]["years"]:
        row["upstream_ebitda_brl"] = 110
        row["downstream_ebitda_brl"] = 10
    model = calculate(baseline_from_sources(sources), raw, sources)
    bear = model["cases"][0]["equity_bridge"]
    assert bear["residual_negative"] and bear["equity_value"] < 0 and bear["present_value"] == 0
    for row in raw["scenarios"][1]["years"]:
        row["upstream_ebitda_brl"] = 110
        row["downstream_ebitda_brl"] = 10
    with pytest.raises(ReportValidationError): calculate(baseline_from_sources(sources), raw, sources)


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
