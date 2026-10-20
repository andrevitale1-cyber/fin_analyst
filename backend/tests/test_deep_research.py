from collections import Counter
from unittest.mock import Mock

import company_research as research
from openai_client import OpenAIError
from test_company_reports import cited_response


def test_thematic_research_is_bounded_and_failed_topic_resumes_without_repeating_other_calls(monkeypatch):
    from test_operating_model import official_source
    cache, calls = {}, Counter()
    source = official_source()
    source["url"] = "https://www.sec.gov/official"
    monkeypatch.setattr(research, "get_sec_company_source", lambda *a: source)
    monkeypatch.setattr(research, "collect_issuer_annual_sources", lambda *a: [])
    monkeypatch.setattr(research, "collect_transcript_sources", lambda *a: [])
    monkeypatch.setattr(research, "hydrate_company_documents", lambda company, sources: sources)
    def checkpoint(stage, identity, compute):
        key = stage, repr(identity)
        if key not in cache: cache[key] = compute()
        return cache[key]
    monkeypatch.setattr(research, "checkpoint", checkpoint)
    def fetch(prompt, **kwargs):
        name = prompt.split()[2]
        calls[name] += 1
        assert kwargs == {"max_tool_calls": 2, "max_output_tokens": 2200, "timeout": 85}
        if name == "market" and calls[name] == 1: raise OpenAIError("temporary")
        result = cited_response()
        for citation in result["output"][0]["content"][0]["annotations"]:
            citation["url"] += "/" + name
        return result
    client = Mock(model="luna", research_company=fetch)
    first = research.collect_deep_company_sources(client, "MU", "2026-10-20")
    second = research.collect_deep_company_sources(client, "MU", "2026-10-20")
    assert len({s["id"] for s in second}) == len(second)
    assert all(calls[name] == 1 for name in research.RESEARCH_TOPICS if name != "market")
    assert calls["market"] == 2 and len(second) > len(first)
    manifest = research.evidence_manifest(second)
    assert len(manifest["annual_periods"]) == 5 and manifest["has_annual_eps"]
