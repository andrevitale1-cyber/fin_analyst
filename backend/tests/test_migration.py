"""Regressões offline: sem banco, credenciais reais ou publicações no X."""
import importlib
import io
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import httpx
import pytest
from pypdf import PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openai_client import OpenAIClient, OpenAIError
from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument, SECFetcher
from report_generator import generate_report_html


ANALYSIS = "\n".join(f"Seção {i}: Teste\nResultados do trimestre.\nNota Seção {i}: 4/5" for i in range(1, 5)) + '\nSeção 5: Conclusão\nEmpresa com resultados consistentes.\nNota Geral: 4/5\n```json\n[{"name":"1T25","receita":100,"lucro":20,"margemBruta":40,"margemLiquida":20,"segmentos":[{"nome":"Serviços","valor":100}]}]\n```'


@pytest.fixture
def openai_client(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    return OpenAIClient()


def transport(monkeypatch, handler):
    original = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))


def answer(text="Resposta"):
    return httpx.Response(200, json={"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]})


def test_native_upload(monkeypatch, openai_client):
    calls = []
    def handler(request):
        calls.append(request)
        if request.url.path == "/v1/files":
            assert b"user_data" in request.content
            return httpx.Response(200, json={"id": "file-test"})
        payload = json.loads(request.content)
        assert payload["store"] is False
        assert payload["input"][0]["content"][1] == {"type": "input_file", "file_id": "file-test"}
        return answer()
    transport(monkeypatch, handler)
    assert openai_client.analyze_document("Prompt", pdf_bytes=b"%PDF-test") == "Resposta"
    assert len(calls) == 2


@pytest.mark.parametrize("upload_fails", [True, False])
def test_pdf_text_fallback(monkeypatch, openai_client, upload_fails):
    monkeypatch.setattr(OpenAIClient, "extract_text", staticmethod(lambda _: "Resultados 1T25"))
    def handler(request):
        if request.url.path.endswith("files"):
            return httpx.Response(400) if upload_fails else httpx.Response(200, json={"id": "file-test"})
        content = json.loads(request.content)["input"][0]["content"]
        if any(c.get("type") == "input_file" for c in content):
            return httpx.Response(400)
        assert "--- TEXTO DO PDF ---\nResultados 1T25" in content[0]["text"]
        return answer()
    transport(monkeypatch, handler)
    assert openai_client.analyze_document("Prompt", pdf_bytes=b"%PDF-test") == "Resposta"


def test_http_error_does_not_leak_body(monkeypatch, openai_client):
    transport(monkeypatch, lambda _: httpx.Response(401, text="test-placeholder private document"))
    with pytest.raises(OpenAIError, match=r"HTTP 401") as exc:
        openai_client.chat_text("Prompt")
    assert "test-placeholder" not in str(exc.value)
    assert "private document" not in str(exc.value)


def test_blank_pdf_rejected():
    out = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(640, 260)
    writer.write(out)
    with pytest.raises(OpenAIError, match="texto selecionável"):
        OpenAIClient.extract_text(out.getvalue())


def test_cache_persists_without_refetch(tmp_path, monkeypatch):
    document = FetchedDocument("https://www.sec.gov/report.htm", "SEC", text="Financial results")
    fetch = Mock(return_value=document)
    monkeypatch.setattr(SECFetcher, "fetch", fetch)
    assert AutoFetcher(tmp_path).fetch_result_pdf("aapl", "2025", "1T") == document
    assert AutoFetcher(tmp_path).fetch_result_pdf("AAPL", "2025", "Q1") == document
    fetch.assert_called_once_with("AAPL", 2025, 1)


def test_unmapped_petr4_wrong_quarter_rejected(tmp_path, monkeypatch):
    fetcher = AutoFetcher(tmp_path)
    fetcher.ir_urls = {}
    fetcher.search_client.search_financial_reports = Mock(return_value=[
        {"title": "Petrobras resultados 4T24", "url": "https://example.com/release-4T24.pdf"},
        {"title": "Petrobras resultados 2025", "url": "https://example.com/release-2025.pdf"},
    ])
    download = Mock(side_effect=AssertionError("Não deve baixar trimestre errado"))
    monkeypatch.setattr("requests.get", download)
    assert fetcher.fetch_result_pdf("PETR4", "2025", "1T") is None
    assert not list(tmp_path.iterdir())
    fetcher.search_client.search_financial_reports.assert_called_once_with("PETR4", 2025, "1T")


@pytest.mark.parametrize("selected", ["file:///secret.pdf", "https://other.test/1T25.pdf", None])
def test_picker_rejects_unlisted_urls(tmp_path, monkeypatch, selected):
    fetcher = AutoFetcher(tmp_path)
    fetcher.ir_urls = {}
    fetcher.search_client.search_financial_reports = Mock(return_value=[
        {"title": "Resultados 1T25", "url": "https://example.com/a.pdf"},
        {"title": "Resultados 1T25", "url": "https://example.com/b.pdf"},
    ])
    monkeypatch.setattr(OpenAIClient, "chat_text", Mock(return_value=json.dumps({"pdf_url": selected})))
    assert fetcher.fetch_result_pdf("PETR4", 2025, "1T") is None


def test_pdf_content_period_verified(tmp_path, monkeypatch):
    fetcher = AutoFetcher(tmp_path)
    response = Mock(content=b"%PDF-test", url="https://example.com/release-1T25.pdf")
    monkeypatch.setattr("requests.get", Mock(return_value=response))
    monkeypatch.setattr(OpenAIClient, "extract_text", Mock(return_value="Resultados 4T24 comparativo 1T25"))
    assert fetcher._download_release(response.url, 2025, 1) is None
    monkeypatch.setattr(OpenAIClient, "extract_text", Mock(return_value="Resultados 1T25 comparativo 1T24"))
    assert fetcher._download_release(response.url, 2025, 1).pdf_bytes == b"%PDF-test"


def test_sec_earnings_primary_and_exhibit(monkeypatch):
    urls = []
    def get(url, **kw):
        urls.append(url)
        assert kw["headers"]["User-Agent"] == "FinAnalyzer contact@finanalyser.com.br"
        if url.endswith("company_tickers.json"):
            return Mock(json=lambda: {"0": {"ticker": "AAPL", "cik_str": 320193}})
        if url.endswith("CIK0000320193.json"):
            return Mock(json=lambda: {"filings": {"recent": {
                "form": ["8-K", "8-K", "8-K"], "filingDate": ["2025-04-01", "2025-02-01", "2025-01-30"],
                "items": ["2.02", "5.02", "2.02"], "accessionNumber": ["1-1", "2-2", "3-3"],
                "primaryDocument": ["wrong.htm", "director.htm", "results.htm"],
            }}})
        html = ('<p>Results of operations 4T2024</p>' if url.endswith("wrong.htm")
                else '<p>Results of operations</p><a href="ex99.htm">99.1</a>' if url.endswith("results.htm")
                else "<p>Quarterly earnings 1T2025 revenue 100</p>")
        return Mock(content=html.encode(), text=html)
    monkeypatch.setattr("requests.get", get)
    doc = SECFetcher().fetch("AAPL", 2025, 1)
    assert doc.source == "SEC" and "revenue 100" in doc.text
    assert not any("director.htm" in u for u in urls)


def test_sec_balance_uses_report_date(monkeypatch):
    urls = []
    def get(url, **kw):
        urls.append(url)
        if url.endswith("company_tickers.json"):
            return Mock(json=lambda: {"0": {"ticker": "AAPL", "cik_str": 320193}})
        if url.endswith("CIK0000320193.json"):
            return Mock(json=lambda: {"filings": {"recent": {
                "form": ["10-Q", "10-Q"], "filingDate": ["2025-05-02", "2025-02-01"],
                "reportDate": ["2025-03-31", "2024-12-31"],
                "accessionNumber": ["1-1", "2-2"], "primaryDocument": ["balance.htm", "old.htm"],
            }}})
        return Mock(content=b"<p>Financial statements revenue 100</p>", text="<p>Financial statements revenue 100</p>")
    monkeypatch.setattr("requests.get", get)
    doc = SECFetcher().fetch("AAPL", 2025, 1)
    assert doc.source == "SEC" and "revenue 100" in doc.text
    assert not any("old.htm" in u for u in urls)


def test_openai_web_search_without_tavily(monkeypatch, openai_client):
    from agents.search_client import SearchClient
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return answer('[{"title":"Resultados 1T25","url":"https://ri.example.com/release-1T25.pdf"}]')
    transport(monkeypatch, handler)
    links = SearchClient().search_financial_reports("PETR4", 2025, "1T")
    assert links[0]["url"].endswith("1T25.pdf")
    assert calls[0]["tools"] == [{"type": "web_search", "search_context_size": "low"}]
    assert calls[0]["tool_choice"] == "required"


def test_search_rejects_local_urls():
    assert not AutoFetcher._valid_url("http://127.0.0.1/release.pdf")
    assert not AutoFetcher._valid_url("http://localhost/release.pdf")
    assert AutoFetcher._valid_url("https://ri.example.com/release.pdf")


def test_period_names_and_dates():
    assert AutoFetcher._period_matches("Resultados do primeiro trimestre de 2025", 2025, 1)
    assert AutoFetcher._period_matches("First quarter ended March 31, 2025", 2025, 1)
    assert not AutoFetcher._period_matches("Resultados do quarto trimestre de 2024", 2025, 1)


@pytest.fixture
def api(monkeypatch):
    # Evita efeitos colaterais do init_db() ao importar o backend legado.
    monkeypatch.setattr("psycopg2.connect", Mock())
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    main = importlib.import_module("main")
    from fastapi.testclient import TestClient
    return main, TestClient(main.app)


@pytest.mark.parametrize("route", ["analyze", "analyze-auto", "analyze-call"])
def test_missing_key(api, monkeypatch, route):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _, client = api
    result = client.post("/api/" + route, data={"empresa": "AAPL", "ticker": "AAPL", "ano": "2025", "trimestre": "1T", "user_id": "test"}, files={"file": ("report.pdf", b"%PDF-test")})
    assert result.status_code == 500
    assert result.json() == {"detail": "Chave OPENAI_API_KEY não encontrada"}


def test_manual_auto_same_parser_and_saved_format(api, monkeypatch, openai_client):
    main, client = api
    conn = Mock()
    conn.cursor.return_value.fetchone.return_value = (7,)
    monkeypatch.setattr(main, "get_db_connection", lambda: conn)
    analyze = Mock(return_value=ANALYSIS)
    monkeypatch.setattr(OpenAIClient, "analyze_document", analyze)
    monkeypatch.setattr(AutoFetcher, "fetch_result_pdf", lambda *a: FetchedDocument("https://www.sec.gov/report.htm", "SEC", text="SEC earnings"))
    data = {"empresa": "AAPL", "ticker": "AAPL", "ano": "2025", "trimestre": "1T", "user_id": "test"}
    manual = client.post("/api/analyze", data=data, files={"file": ("report.pdf", b"%PDF-test")})
    automatic = client.post("/api/analyze-auto", data=data)
    assert manual.status_code == automatic.status_code == 200
    assert manual.json()["data"] == automatic.json()["data"]
    assert automatic.json()["source"]["name"] == "SEC"
    assert manual.json()["data"]["nota_geral"] == 4
    saved = json.loads(conn.cursor.return_value.execute.call_args.args[1][3])
    assert set(saved) == {"metadata", "data", "analise_completa"}
    assert analyze.call_args.kwargs["pdf_text"] == "SEC earnings"


def test_auto_not_found_requests_manual_upload(api, monkeypatch, openai_client):
    _, client = api
    monkeypatch.setattr(AutoFetcher, "fetch_result_pdf", lambda *a: None)
    result = client.post("/api/analyze-auto", data={"ticker": "PETR4", "ano": "2025", "trimestre": "1T", "user_id": "test"})
    assert result.status_code == 404
    assert "upload manual" in result.json()["detail"]


def test_report_invalid_chart_data():
    html = generate_report_html({"metadata": {"empresa": "AAPL", "periodo": "1T/2025"}, "analise_completa": ANALYSIS.split('```')[0], "data": {"chart_data": {"invalid": 1}}})
    assert 'const CD = [];' in html
    assert "Sem série histórica neste relatório" in html
    assert 'width="640" height="260"' in html
    assert 'Rascunhos para o X' in html


def test_bot_generates_drafts_even_with_write_credentials(monkeypatch, tmp_path):
    from agents.x_replier_agent import XReplierAgent
    monkeypatch.chdir(tmp_path)
    for key in ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"):
        monkeypatch.setenv(key, "test-placeholder")
    agent = XReplierAgent()
    agent.client = Mock()
    agent.client.search_recent_tweets.return_value = Mock(data=[Mock(id="123", author_id="456", text="$AAPL earnings")])
    agent.is_already_replied = Mock(return_value=False)
    agent.get_company_analysis_from_db = Mock(return_value=None)
    agent.generate_reply_text = Mock(return_value="Rascunho")
    agent.record_reply_history = Mock()
    result = agent.run_auto_replier(limit=1)
    assert result["draft_only"] and result["replies_processed"] == 1
    agent.client.create_tweet.assert_not_called()
    agent.record_reply_history.assert_not_called()
