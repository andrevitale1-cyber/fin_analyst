"""Model routing and request compatibility, without paid API calls."""
import json
from pathlib import Path
import sys
from unittest.mock import MagicMock, Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openai_client import OpenAIClient, model_for_task


@pytest.fixture(autouse=True)
def model_environment(monkeypatch):
    for variable in ("OPENAI_MODEL", "OPENAI_ANALYSIS_MODEL", "OPENAI_FULL_REPORT_MODEL"):
        monkeypatch.delenv(variable, raising=False)


def test_task_defaults_are_independent_of_the_legacy_general_model(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1")
    assert OpenAIClient().model == "gpt-4.1"
    assert OpenAIClient(task="analysis").model == "gpt-6-luna"
    assert OpenAIClient(task="full_report").model == "gpt-6.1-sol"


def test_each_task_can_be_configured_independently(monkeypatch):
    monkeypatch.setenv("OPENAI_ANALYSIS_MODEL", " gpt-4.1 ")
    monkeypatch.setenv("OPENAI_FULL_REPORT_MODEL", " gpt-6.1-sol ")
    assert OpenAIClient(task="analysis").model == "gpt-4.1"
    assert OpenAIClient(task="analysis")._model_options() == {}
    assert OpenAIClient(task="full_report").model == model_for_task("full_report") == "gpt-6.1-sol"
    monkeypatch.setenv("OPENAI_FULL_REPORT_MODEL", " ")
    assert model_for_task("full_report") == "gpt-6.1-sol"


@pytest.mark.parametrize("task,method,args,expected_model", [
    ("analysis", "analyze_document", ("Prompt",), "gpt-6-luna"),
    ("analysis", "analyze_transcript", ("Prompt", "Public call transcript"), "gpt-6-luna"),
    ("full_report", "analyze_full_report", ("Evidence", {"type": "object"}), "gpt-6.1-sol"),
    ("full_report", "research_company", ("Public company research",), "gpt-6.1-sol"),
    ("general", "search_pdf_links", ("Official earnings release",), "gpt-4.1"),
])
def test_response_requests_route_models_and_preserve_contracts(task, method, args, expected_model):
    client = OpenAIClient(task=task)
    client._client = MagicMock()
    result = [] if method == "search_pdf_links" else {"summary": "Evidence-based analysis"}
    client._request = Mock(return_value={"status": "completed", "output": [
        {"type": "message", "content": [{"type": "output_text", "text": json.dumps(result)}]}
    ]})
    kwargs = {"pdf_text": "Official quarterly results"} if method == "analyze_document" else {}
    getattr(client, method)(*args, **kwargs)
    request = client._request.call_args
    payload = request.kwargs["json"]
    assert request.args[1] == "responses"
    assert payload["model"] == expected_model and payload["store"] is False
    if task == "general":
        assert "reasoning" not in payload
    else:
        assert payload["reasoning"] == {"effort": "low"}
    if method == "analyze_full_report":
        assert payload["text"]["format"]["strict"] is True
        assert payload["max_output_tokens"] == 6500
    if method == "research_company":
        assert payload["max_tool_calls"] == 4 and request.kwargs["timeout"] == 70


def test_company_cache_is_separate_for_each_configured_full_report_model(monkeypatch):
    from full_reports import company_cache_key
    before = company_cache_key("MSFT", model_for_task("full_report"), "2026-10-17", "en")
    monkeypatch.setenv("OPENAI_FULL_REPORT_MODEL", "gpt-4.1")
    assert before != company_cache_key("MSFT", model_for_task("full_report"), "2026-10-17", "en")
    monkeypatch.setenv("OPENAI_ANALYSIS_MODEL", "gpt-4.1")
    assert model_for_task("full_report") == "gpt-4.1"
