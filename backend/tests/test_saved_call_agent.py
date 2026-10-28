from unittest.mock import MagicMock

import pytest

from openai_client import OpenAIClient, OpenAIError


def test_saved_agent_receives_transcript_and_current_prompt(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_CALL_AGENT_ID", "agent-test")
    client = MagicMock()
    stream = client.__enter__.return_value.beta.agents.sessions.create.return_value.with_result_collection.return_value.__enter__.return_value
    stream.get_final_result.return_value.output_text = "Análise da call"
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: client)

    result = OpenAIClient(task="analysis").analyze_transcript("Instruções em português", "Transcrição de teste")

    assert result == "Análise da call"
    args = client.__enter__.return_value.beta.agents.sessions.create.call_args.kwargs
    assert args["agent_id"] == "agent-test"
    assert "Instruções em português" in args["input"]
    assert "Transcrição de teste" in args["input"]
    assert args["environment"] == {"type": "openai_hosted"}


def test_saved_agent_failure_does_not_fall_back_or_leak_transcript(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_CALL_AGENT_ID", "agent-test")
    client = MagicMock()
    client.__enter__.return_value.beta.agents.sessions.create.side_effect = ValueError("conteúdo privado")
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: client)

    with pytest.raises(OpenAIError) as error:
        OpenAIClient(task="analysis").analyze_transcript("prompt", "conteúdo privado")
    assert "conteúdo privado" not in str(error.value)
