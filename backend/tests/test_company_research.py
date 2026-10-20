from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import company_research as research
from openai_client import OpenAIError
from test_company_reports import cited_response


@pytest.fixture(autouse=True)
def isolate_document_collection(monkeypatch):
    monkeypatch.setattr(research,"collect_transcript_sources",lambda *a:[])
    monkeypatch.setattr(research,"hydrate_company_documents",lambda company,sources:sources)


def market_response(url="https://stockanalysis.com/stocks/msft/forecast/"):
    text = "As of 2026-10-15, analyst consensus rating Buy; mean price target USD 500 from 30 analysts [1]."
    return {"status": "completed", "output": [{"content": [{"type": "output_text", "text": text,
        "annotations": [{"type": "url_citation", "url": url, "title": "MSFT analyst consensus",
                         "start_index": text.index("[1]"), "end_index": len(text)}]}]}]}


def test_market_gap_triggers_one_bounded_targeted_lookup_and_unique_citations(monkeypatch):
    monkeypatch.setattr(research, "get_sec_company_source", lambda *args: None)
    client = Mock(research_company=Mock(side_effect=[cited_response(), market_response()]))
    sources = research.collect_company_sources(client, "MSFT", "2026-10-15")
    assert [source["id"] for source in sources] == ["S1", "S2", "S3", "S4"]
    assert "target USD 500" in sources[-1]["text"]
    assert client.research_company.call_count == 2
    assert client.research_company.call_args_list[0].kwargs == {"timeout": 120}
    request = client.research_company.call_args
    assert request.kwargs == {"max_tool_calls": 2, "max_output_tokens": 2000, "timeout": 35}
    for phrase in ("independent market-data", "not only issuer", "exact observation dates", "Do not infer a consensus"):
        assert phrase in request.args[0]


def test_dated_independent_market_data_skips_supplementary_lookup(monkeypatch):
    monkeypatch.setattr(research, "get_sec_company_source", lambda *args: None)
    response = cited_response()
    response["output"] += market_response()["output"]
    client = Mock(research_company=Mock(return_value=response))
    sources = research.collect_company_sources(client, "MSFT", "2026-10-15")
    assert research.has_market_evidence(sources)
    client.research_company.assert_called_once()


@pytest.mark.parametrize("failure", [OpenAIError("incomplete", code="research_incomplete"), TimeoutError("timed out"),
                                    {"status": "completed", "output": []}])
def test_supplementary_lookup_without_evidence_preserves_facts_and_never_retries(monkeypatch, failure):
    monkeypatch.setattr(research, "get_sec_company_source", lambda *args: None)
    client = Mock(research_company=Mock(side_effect=[cited_response(), failure]))
    sources = research.collect_company_sources(client, "MSFT", "2026-10-15")
    assert len(sources) == 3 and client.research_company.call_count == 2


def test_supplementary_lookup_merges_same_url_without_duplicate_source_ids(monkeypatch):
    monkeypatch.setattr(research, "get_sec_company_source", lambda *args: None)
    client = Mock(research_company=Mock(side_effect=[cited_response(), market_response("https://source3.example/report")]))
    sources = research.collect_company_sources(client, "MSFT", "2026-10-15")
    assert len(sources) == 3 and sources[-1]["id"] == "S3"
    assert "target USD 500" in sources[-1]["text"] and "Dated market consensus" in sources[-1]["text"]


def test_official_filings_and_missing_or_undated_consensus_do_not_replace_market_lookup():
    source = research.cited_sources(market_response(), minimum=0)[0]
    for patch in ({"url": "https://www.microsoft.com/investor/results"},
                  {"text": "No analyst consensus available as of 2026-10-15; USD 500 revenue."},
                  {"text": "Consensus rating Buy, analyst target USD 500, observation date unavailable."}):
        assert not research.has_market_evidence([{**source, **patch}])


@pytest.mark.parametrize("prefix", ["Sources:", "Evidence:", "Market source:"])
def test_citation_attribution_retains_its_preceding_table_without_unrelated_prose(prefix):
    unrelated = "UNSUPPORTED assertion without citation."
    table = "| Segment | Revenue |\n|---|---|\n| Services | USD 100 billion |"
    text = unrelated + "\n\n## Segment mix\n\n" + table + "\n\n" + prefix + " Annual results [1]."
    response = {"status": "completed", "output": [{"content": [{"type": "output_text", "text": text,
        "annotations": [{"type": "url_citation", "url": "https://issuer.example/results", "title": "Annual results",
                         "start_index": text.index("[1]"), "end_index": len(text)}]}]}]}
    source = research.cited_sources(response, minimum=1)[0]
    assert table in source["text"] and unrelated not in source["text"]
