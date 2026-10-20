import sys
from pathlib import Path
from time import perf_counter
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.prompt_builder import PromptBuilder, QUALITY_RULES, QUARTERLY_FIELDS
from agents.report_facts import extract_facts
from agents.report_pipeline import generate_report
from test_report_agents import AgentClient, SOURCES
from full_reports import company_cache_key


@pytest.mark.parametrize("locale", ["pt", "en"])
def test_full_report_uses_active_quarterly_field_instructions_without_quarter_output_structure(locale):
    builder = PromptBuilder()
    quarterly = builder.build_prompt("WEGE3", "release", locale, "1T/2026")
    company = builder.company_field_rules("WEGE3", locale)
    for instruction in QUARTERLY_FIELDS.values():
        assert instruction in quarterly and instruction in company
    for rule in ("Separe crescimento orgânico de crescimento adquirido", "Não transforme ausência de dado em nota máxima"):
        assert rule in quarterly and rule in company
    assert "Backlog" in company and "industrial_logistica" in company
    assert "company-wide, multi-year" in company and "do not import" in company
    assert "Seção 6:" not in company and "Section 6:" not in company and "Seção 7:" not in company
    assert QUALITY_RULES in quarterly


@pytest.mark.parametrize("ticker,sector_metric", [("ITUB4", "Basileia"), ("TOTS3", "Rule of 40"), ("EGIE3", "Dívida Líquida/EBITDA")])
def test_shared_sector_guidance_matches_quarterly_prompt(ticker, sector_metric):
    builder = PromptBuilder()
    assert builder.sector_rules(ticker) in builder.company_field_rules(ticker)
    assert sector_metric in builder.build_prompt(ticker, "release")


def test_extraction_writing_and_audit_share_methodology_while_valuation_stays_specialized():
    client = AgentClient()
    api = Mock(side_effect=client.analyze_full_report)
    client.analyze_full_report = api
    dossier = extract_facts(client, "WEGE3", "2026-10-20", SOURCES)
    generate_report(client, "WEGE3", "2026-10-20", "pt", SOURCES, dossier, deadline=perf_counter() + 300)
    assert api.call_count == 4
    for call in api.call_args_list:
        prompt = call.args[0]
        if prompt.startswith("AGENT 3"):
            assert "SHARED QUARTERLY ANALYSIS METHODOLOGY" not in prompt
            assert "bear/base/bull" in prompt
        else:
            assert "SHARED QUARTERLY ANALYSIS METHODOLOGY" in prompt
            assert "Backlog" in prompt and "não reduza a nota apenas pela existência de M&A" in prompt


def test_methodology_upgrade_invalidates_reports_but_reuses_unchanged_public_research():
    args = ("WEGE3", "model", "2026-10-20")
    assert company_cache_key(*args, "pt") != company_cache_key(*args, "pt", version="company-v5")
    assert company_cache_key(*args, version="company-v5") == company_cache_key(*args, None, version="company-v5")
