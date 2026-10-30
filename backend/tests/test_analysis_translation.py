import asyncio
import json
import importlib
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from agents.prompt_builder import PromptBuilder


@pytest.fixture
def main(monkeypatch):
    monkeypatch.setattr("psycopg2.connect", Mock())
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("REPORT_JOB_WORKER", "0")
    return importlib.import_module("main")


def test_quarterly_prompt_requires_portuguese_for_english_source():
    prompt = PromptBuilder().build_prompt("AAPL", "Revenue rose", locale="pt")
    assert "português brasileiro" in prompt
    assert "mesmo que o documento esteja em inglês" in prompt


def test_translation_uses_owned_analysis_and_rejects_changed_numbers(monkeypatch, main):
    cursor = Mock()
    cursor.fetchone.return_value = (json.dumps({"metadata": {}, "data": {"tese_investimento": "Revenue was $100 in 2026."}}),)
    conn = Mock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(main, "get_db_connection", lambda: conn)
    monkeypatch.setattr(main, "OpenAIClient", lambda **kwargs: Mock(translate_analysis=lambda text, locale: "Receita de $101 em 2026."))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.translate_saved_analysis(7, main.AnalysisTranslationRequest(locale="pt"), "owner"))
    assert exc.value.status_code == 502
    assert cursor.execute.call_args.args[1] == (7, "owner")


def test_translation_returns_translated_text(monkeypatch, main):
    cursor = Mock()
    cursor.fetchone.return_value = (json.dumps({"metadata": {}, "data": {"tese_investimento": "Revenue was $100 in 2026."}}),)
    conn = Mock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(main, "get_db_connection", lambda: conn)
    monkeypatch.setattr(main, "OpenAIClient", lambda **kwargs: Mock(translate_analysis=lambda text, locale: "Receita de $100 em 2026."))
    assert asyncio.run(main.translate_saved_analysis(7, main.AnalysisTranslationRequest(locale="pt"), "owner")) == {"text": "Receita de $100 em 2026."}
