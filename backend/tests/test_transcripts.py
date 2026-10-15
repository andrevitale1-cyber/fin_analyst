"""Offline regressions for earnings-call transcript discovery and analysis."""
import importlib
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.auto_fetcher import AutoFetcher
from agents.prompt_builder import PromptBuilder
from agents.search_client import SearchError
from agents.sec_fetcher import FetchedDocument
from openai_client import OpenAIClient, OpenAIError


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr("psycopg2.connect", Mock())
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    main = importlib.import_module("main")
    from fastapi.testclient import TestClient
    return main, TestClient(main.app)


def html_response(url, text):
    return Mock(url=url, content=text.encode(), text=text,
                headers={"Content-Type": "text/html"}, raise_for_status=lambda: None)


@pytest.mark.parametrize("heading", [
    "Q1 FY2026", "FY26 first quarter", "1Q26",
    "2026 First Quarter", "FY-2026-Q1", "Q1 FY'26",
])
def test_period_matches_common_fiscal_quarter_headings(heading):
    assert AutoFetcher._period_matches(heading, 2026, 1)


def test_transcript_download_accepts_html_and_validates_identity_period_and_primary_heading(monkeypatch):
    fetcher = AutoFetcher()
    monkeypatch.setattr("requests.get", lambda *a, **k: Mock(
        url="https://ir.apple.com/call", content=b"<html>",
        text="<h1>Apple Inc. Q1 FY2026 Earnings Call Transcript</h1><p>Operator: " + "Revenue grew. " * 60 + "</p>",
        headers={"Content-Type": "text/html"}, raise_for_status=lambda: None,
    ))
    doc = fetcher._download_transcript("https://ir.apple.com/call", 2026, 1, company="Apple")
    assert doc and "Revenue grew" in doc.text and not doc.pdf_bytes


@pytest.mark.parametrize("text", [
    "Microsoft Q1 FY2026 earnings call transcript",
    "Apple Q4 FY2025 earnings call transcript; comparative Q1 FY2026 results",
])
def test_transcript_download_rejects_wrong_company_or_comparison_period(monkeypatch, text):
    fetcher = AutoFetcher()
    monkeypatch.setattr("requests.get", lambda *a, **k: Mock(
        url="https://ir.example.com/call", content=b"<html>", text=f"<h1>{text}</h1><p>Operator: " + "discussion. " * 60 + "</p>",
        headers={"Content-Type": "text/html"}, raise_for_status=lambda: None,
    ))
    assert fetcher._download_transcript("https://ir.example.com/call", 2026, 1, company="Apple") is None


def test_competitor_mention_does_not_change_transcript_issuer():
    text = "Microsoft Q1 FY2026 earnings call transcript\nOperator: We also discussed Apple. " + "Prepared remarks. " * 50
    assert not AutoFetcher()._valid_transcript(text, "Apple", 2026, 1)


def test_transcript_search_keeps_company_name_and_ticker(tmp_path):
    fetcher = AutoFetcher(tmp_path)
    fetcher._fetch_transcript_ir = Mock(return_value=None)
    fetcher.search_client.search_transcripts = Mock(return_value=[])
    fetcher.fetch_transcript("Apple", 2026, "1T")
    query = fetcher.search_client.search_transcripts.call_args.args[0]
    assert "Apple" in query


def test_bad_tavily_candidates_still_allow_one_openai_fallback(tmp_path):
    fetcher = AutoFetcher(tmp_path)
    fetcher._fetch_transcript_ir = Mock(return_value=None)
    valid = {"title": "Apple 1Q26 earnings call transcript", "url": "https://apple.com/call"}
    search = Mock(side_effect=[[{"title": "wrong company", "url": "https://example.com/1Q26-transcript"}], [valid]])
    fetcher.search_client.search_transcripts = search
    document = FetchedDocument(valid["url"], "Earnings Call Transcript", text="Apple 1Q26 transcript")
    fetcher._download_transcript = Mock(side_effect=[None, document])
    assert fetcher.fetch_transcript("Apple", 2026, "1T") == document
    assert search.call_count == 2
    assert search.call_args_list[-1].kwargs["allow_openai"] is True


def test_official_microsoft_transcript_skips_search(tmp_path, monkeypatch):
    fetcher = AutoFetcher(tmp_path)
    event_url = "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q1"
    body = "Microsoft Q1 FY2026 earnings call transcript\nOperator: " + "Prepared remarks and answers. " * 25
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return html_response(event_url, f"<main><h1>Microsoft Q1 FY2026 earnings call transcript</h1><p>{body}</p></main>")
    monkeypatch.setattr("requests.get", get)
    search = Mock(side_effect=AssertionError("official transcript should be enough"))
    fetcher.search_client.search_transcripts = search
    doc = fetcher.fetch_transcript("Microsoft", 2026, "1T")
    assert doc and doc.source == "Earnings Call Transcript" and len(doc.text) > 500
    assert calls == [event_url]
    search.assert_not_called()


def test_audio_only_ir_falls_back_to_matching_public_archive_link(tmp_path, monkeypatch):
    fetcher = AutoFetcher(tmp_path)
    archive = "https://stockanalysis.com/stocks/aapl/transcripts/"
    old = "https://stockanalysis.com/stocks/aapl/transcripts/2025-q4/"
    target = "https://stockanalysis.com/stocks/aapl/transcripts/2026-q1/"
    transcript = "Apple Q1 FY2026 Earnings Call Transcript\nOperator: " + "Prepared remarks and question answers. " * 25
    pages = {
        "https://investor.apple.com/investor-relations/default.aspx": html_response(
            "https://investor.apple.com/investor-relations/default.aspx", "<main><p>Listen to the audio webcast.</p></main>"),
        archive: html_response(archive, f'<main><h1>Apple earnings calls</h1><a href="{old}">Apple Q4 FY2025 Transcript</a><a href="{target}">Apple Q1 FY2026 Earnings Call Transcript</a></main>'),
        target: html_response(target, f"<article><h1>{transcript.splitlines()[0]}</h1><p>{transcript.splitlines()[1]}</p></article>"),
    }
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return pages[url]
    monkeypatch.setattr("requests.get", get)
    search = Mock(side_effect=AssertionError("public archive should resolve the transcript"))
    fetcher.search_client.search_transcripts = search
    doc = fetcher.fetch_transcript("Apple", 2026, "1T")
    assert doc and doc.url == target and doc.text.startswith("Apple Q1 FY2026")
    assert calls == ["https://investor.apple.com/investor-relations/default.aspx", archive, target]
    search.assert_not_called()


def test_search_provider_errors_still_reach_openai_fallback(tmp_path, monkeypatch):
    fetcher = AutoFetcher(tmp_path)
    fetcher._fetch_transcript_ir = Mock(return_value=None)
    fetcher.search_client.api_key = "test-placeholder"
    monkeypatch.setattr("requests.post", Mock(side_effect=requests.RequestException("offline")))
    result = [{"title": "Apple 1Q26 earnings call transcript", "url": "https://apple.com/call"}]
    fallback = Mock(return_value=result)
    monkeypatch.setattr(OpenAIClient, "search_pdf_links", fallback)
    document = FetchedDocument(result[0]["url"], "Earnings Call Transcript", text="verified transcript")
    fetcher._download_transcript = Mock(return_value=document)
    assert fetcher.fetch_transcript("Apple", 2026, "1T") == document
    fallback.assert_called_once()
    assert fallback.call_args.kwargs["document_type"] == "transcript"


def test_openai_transcript_search_prompt_does_not_request_releases(monkeypatch):
    client = OpenAIClient()
    calls = []
    def request(_, path, **kwargs):
        calls.append(kwargs["json"]["input"])
        return {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "[]"}]}]}
    monkeypatch.setattr(client, "_client", lambda: _Context(client))
    monkeypatch.setattr(client, "_request", request)
    client.search_pdf_links('"Apple" Q1 2026 transcript', document_type="transcript")
    prompt = calls[0].lower()
    assert "transcript" in prompt
    assert "earnings-release pdf" not in prompt and "release pages" not in prompt


class _Context:
    def __init__(self, value): self.value = value
    def __enter__(self): return self.value
    def __exit__(self, *args): pass


def test_transcript_cache_avoids_second_search(tmp_path):
    fetcher = AutoFetcher(tmp_path)
    fetcher._fetch_transcript_ir = Mock(return_value=None)
    text = "Apple Q1 FY2026 Earnings Call Transcript\nOperator: " + "Prepared remarks and question answers. " * 20
    doc = FetchedDocument("https://apple.com/call", "Earnings Call Transcript", text=text)
    fetcher.search_client.search_transcripts = Mock(return_value=[{"title": "Apple Q1 FY2026 transcript", "url": doc.url}])
    fetcher._download_transcript = Mock(return_value=doc)
    assert fetcher.fetch_transcript("Apple", "2026", "1T") == doc
    again = AutoFetcher(tmp_path)
    again._fetch_transcript_ir = Mock(return_value=None)
    again.search_client.search_transcripts = Mock(side_effect=AssertionError("cache should be used"))
    assert again.fetch_transcript("Apple", "2026", "1T") == doc


def test_call_prompt_is_localized_and_places_verified_timestamps_inline():
    builder = PromptBuilder()
    pt = builder.build_call_prompt("Apple", "1T/2026")
    en = builder.build_call_prompt("Apple", "1T/2026", locale="en")
    assert "Apple" in pt and "1T/2026" in pt and "Tom predominante:" in pt
    assert "Apple" in en and "1T/2026" in en and "Predominant tone:" in en
    assert "imediatamente após essa informação" in pt
    assert "immediately after that information" in en
    assert "Quando não houver minutagem, omita" in pt
    assert "When timing is unavailable, omit" in en
    for prompt in (pt, en):
        assert "**5." not in prompt
        assert "[mm:ss]" in prompt and "[hh:mm:ss]" in prompt
        assert "Never estimate from text position" in prompt or "Nunca estime pela posição do texto" in prompt
        assert "voice, emotion, or body language" in prompt or "voz, emoção ou linguagem corporal" in prompt
        assert "300–450" in prompt
        assert "Markdown **bold**" in prompt or "Markdown **negrito**" in prompt
        assert "up to three concise bullets" in prompt or "até três bullets concisos" in prompt
        assert "up to two material questions" in prompt or "até duas perguntas" in prompt


def test_auto_transcript_route_keeps_body_out_of_prompt_and_sends_text_once(api, monkeypatch):
    main, client = api
    conn = Mock()
    conn.cursor.return_value.fetchone.return_value = (17,)
    monkeypatch.setattr(main, "get_db_connection", lambda: conn)
    transcript = "Apple Q1 FY2026 transcript body " * 30
    monkeypatch.setattr(AutoFetcher, "fetch_transcript", Mock(return_value=FetchedDocument(
        "https://apple.com/call", "Earnings Call Transcript", text=transcript,
    )))
    analyze = Mock(return_value="Analysis [12:34]\n**5. Key moments**\nOld list")
    monkeypatch.setattr(OpenAIClient, "analyze_transcript", analyze)
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    response = client.post("/api/analyze-call-auto", data={
        "company": "Apple", "ano": "2026", "trimestre": "1T", "user_id": "test", "locale": "en",
    })
    assert response.status_code == 200
    assert response.json()["analise_completa"] == "Analysis [12:34]"
    analyze.assert_called_once()
    prompt, text = analyze.call_args.args
    assert "Apple" in prompt and transcript not in prompt
    assert prompt == PromptBuilder().build_call_prompt("Apple", "1T/2026", locale="en")
    assert text == transcript


def test_search_error_is_returned_as_502_not_not_found(api, monkeypatch):
    main, client = api
    monkeypatch.setattr(AutoFetcher, "fetch_transcript", Mock(side_effect=SearchError("search unavailable")))
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    response = client.post("/api/analyze-call-auto", data={
        "company": "Apple", "ano": "2026", "trimestre": "1T", "user_id": "test",
    })
    assert response.status_code == 502
    assert response.json()["detail"] == "search unavailable"


def test_saved_call_history_omits_retired_section_but_preserves_financial_reports(api, monkeypatch):
    main, _ = api
    conn = Mock()
    call = {"metadata": {"tipo": "Earnings Call"}, "analise_completa": "Conclusion [12:34]\n**5. Key moments**\nOld list"}
    report = {"metadata": {"tipo": "Financial Report"}, "analise_completa": "**5. Strategic outlook**\nKeep this"}
    conn.cursor.return_value.fetchall.return_value = [
        (1, "Example", "2026", "1Q", "2026-10-14", json.dumps(call)),
        (2, "Example", "2026", "1Q", "2026-10-14", json.dumps(report)),
    ]
    monkeypatch.setattr(main, "get_db_connection", lambda: conn)
    history = main.get_history("test-user")
    assert history[0]["conteudo"]["analise_completa"] == "Conclusion [12:34]"
    assert history[1]["conteudo"]["analise_completa"] == report["analise_completa"]


def test_manual_transcript_route_extracts_and_sends_text_once(api, monkeypatch):
    main, client = api
    conn = Mock()
    conn.cursor.return_value.fetchone.return_value = (18,)
    monkeypatch.setattr(main, "get_db_connection", lambda: conn)
    transcript = "Apple Q1 FY2026 transcript from uploaded PDF"
    monkeypatch.setattr(OpenAIClient, "extract_text", Mock(return_value=transcript))
    analyze = Mock(return_value="Analysis")
    monkeypatch.setattr(OpenAIClient, "analyze_transcript", analyze)
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    response = client.post("/api/analyze-call", data={
        "empresa": "Apple", "ano": "2026", "trimestre": "1T", "user_id": "test", "locale": "en",
    }, files={"file": ("transcript.pdf", b"placeholder pdf", "application/pdf")})
    assert response.status_code == 200
    analyze.assert_called_once()
    prompt, text = analyze.call_args.args
    assert "Apple" in prompt and transcript not in prompt
    assert prompt == PromptBuilder().build_call_prompt("Apple", "1T/2026", locale="en")
    assert text == transcript


def test_transcript_analysis_sends_text_once_without_file_upload(monkeypatch):
    client = OpenAIClient()
    sent = []
    monkeypatch.setattr(client, "_client", lambda: _Context(client))
    monkeypatch.setattr(client, "_chat", lambda _, content, *a, **k: sent.append(content) or "Analysis")
    transcript = "Apple Q1 FY2026 transcript body"
    assert client.analyze_transcript("Analyze this call", transcript) == "Analysis"
    assert len(sent) == 1 and len(sent[0]) == 1
    assert sent[0][0]["type"] == "input_text"
    assert sent[0][0]["text"].count(transcript) == 1


def test_scanned_manual_transcript_preserves_native_pdf_reading(api, monkeypatch):
    main, client = api
    conn = Mock()
    conn.cursor.return_value.fetchone.return_value = (19,)
    monkeypatch.setattr(main, "get_db_connection", lambda: conn)
    monkeypatch.setattr(OpenAIClient, "extract_text", Mock(side_effect=OpenAIError("No selectable text")))
    analyze = Mock(return_value="Analysis")
    monkeypatch.setattr(OpenAIClient, "analyze_document", analyze)
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    response = client.post("/api/analyze-call", data={
        "empresa": "Apple", "ano": "2026", "trimestre": "1T", "user_id": "test", "locale": "en",
    }, files={"file": ("transcript.pdf", b"scanned pdf", "application/pdf")})
    assert response.status_code == 200
    analyze.assert_called_once()
    assert analyze.call_args.kwargs["pdf_bytes"] == b"scanned pdf"
