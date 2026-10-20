import json
from unittest.mock import MagicMock, Mock

import full_reports
import report_runtime as runtime


def test_token_usage_and_configured_cost_are_based_on_provider_counts(monkeypatch):
    monkeypatch.setenv("REPORT_MODEL_PRICING_JSON", json.dumps({"test-model": {
        "input_per_million": 2, "cached_input_per_million": 1, "output_per_million": 4, "search_per_call": .01}}))
    result = {"model": "test-model", "usage": {"input_tokens": 1000, "output_tokens": 200,
              "input_tokens_details": {"cached_tokens": 400}, "output_tokens_details": {"reasoning_tokens": 50}},
              "output": [{"type": "web_search_call"}]}
    usage = runtime.usage_record(result, "fallback", 100, "research")
    assert usage["estimated_cost_usd"] == .0124
    assert usage["cached_input_tokens"] == 400 and usage["reasoning_tokens"] == 50
    monkeypatch.delenv("REPORT_MODEL_PRICING_JSON")
    assert runtime.usage_record(result, "fallback", 100, "research")["estimated_cost_usd"] is None


def test_checkpoint_reuses_paid_stage_and_does_not_cache_empty_evidence(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.side_effect = [(json.dumps({"facts": [1]}),), None]
    monkeypatch.setattr(full_reports, "connection", lambda: conn)
    compute = Mock(side_effect=AssertionError("Do not repeat paid calls"))
    assert runtime.checkpoint("facts", ["MU"], compute) == {"facts": [1]}
    assert runtime.checkpoint("missing", ["MU"], lambda: None) is None
    assert not any("INSERT" in c.args[0] for c in cur.execute.call_args_list)


def test_run_metrics_store_only_metadata_not_prompt_or_document_text(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    monkeypatch.setattr(full_reports, "connection", lambda: conn)
    client = Mock(usage_calls=[runtime.usage_record({"usage": {"input_tokens": 10}}, "model", 1, "AGENT 1")])
    runtime.record_run("MU", "model", "complete", 100, {"model_ms": 20}, [client])
    payload = json.loads(cur.execute.call_args.args[1][-1])
    assert payload["input_tokens"] == 10 and "prompt" not in payload and "source_text" not in payload
    conn.commit.assert_called_once()
