import json
from unittest.mock import Mock

import pytest
import requests

from agents.equibles_client import EquiblesClient
from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument


@pytest.fixture(autouse=True)
def isolated_key(monkeypatch):
    monkeypatch.delenv("EQUIBLES_API_KEY", raising=False)


def response(monkeypatch, payload, status=200):
    result = Mock(status_code=status)
    result.__enter__ = Mock(return_value=result); result.__exit__ = Mock(return_value=False)
    result.iter_content.return_value = [json.dumps(payload).encode()]
    get = Mock(return_value=result)
    monkeypatch.setattr(requests, "get", get)
    return get


def test_missing_key_performs_no_request(monkeypatch):
    get = Mock(side_effect=AssertionError("No network")); monkeypatch.setattr(requests, "get", get)
    assert EquiblesClient().release_candidates("VIVA3") == []
    get.assert_not_called()


def test_ir_news_authentication_is_bounded_and_not_forwarded(monkeypatch):
    monkeypatch.setenv("EQUIBLES_API_KEY", "unit-test-secret")
    get = response(monkeypatch, {"data": [{"title": "Vivara 2T26 Resultados", "url": "https://ri.vivara.com.br/resultados/2t26.pdf", "summary": "Do not analyze this summary"}]})
    client = EquiblesClient(); rows = client.release_candidates("VIVA3")
    assert rows == [{"title": "Vivara 2T26 Resultados", "url": "https://ri.vivara.com.br/resultados/2t26.pdf"}]
    args = get.call_args
    assert args.args[0] == "https://api.equibles.com/v1/stocks/VIVA3/ir-news"
    assert args.kwargs["headers"] == {"Authorization": "Bearer unit-test-secret"}
    assert args.kwargs["allow_redirects"] is False and args.kwargs["timeout"] == (2, 6)
    assert client.last_status == "ok"


@pytest.mark.parametrize("status", [302, 401, 403, 404, 429, 500])
def test_api_errors_return_to_existing_lookup_without_exposing_key(monkeypatch, caplog, status):
    monkeypatch.setenv("EQUIBLES_API_KEY", "unit-test-secret")
    response(monkeypatch, {"error": "unit-test-secret"}, status)
    assert EquiblesClient().release_candidates("VIVA3") == []
    assert "unit-test-secret" not in caplog.text


@pytest.mark.parametrize("payload", [[], {"data": None}, {"data": [], "ticker": "AAPL"}])
def test_invalid_or_wrong_issuer_response_is_rejected(monkeypatch, payload):
    monkeypatch.setenv("EQUIBLES_API_KEY", "unit-test-secret"); response(monkeypatch, payload)
    assert EquiblesClient().release_candidates("VIVA3") == []


def test_success_skips_web_lookup_and_reuses_existing_release_cache(monkeypatch, tmp_path):
    fetcher = AutoFetcher(tmp_path)
    lookup = Mock(return_value=[{"title": "Vivara resultados 2T26", "url": "https://ri.vivara.com.br/release.pdf"}])
    fetcher.equibles_client.release_candidates = lookup
    download = Mock(return_value=FetchedDocument("https://ri.vivara.com.br/release.pdf", "RI", text="Vivara resultados 2T26 Receita líquida e lucro líquido."))
    monkeypatch.setattr(fetcher, "_download_release", download)
    fallback = Mock(side_effect=AssertionError("No paid web search")); monkeypatch.setattr(fetcher, "_fetch_b3", fallback)
    first = fetcher.fetch_result_pdf("Vivara", "2026", "2T")
    assert first.source == "Equibles / RI"
    assert fetcher.fetch_result_pdf("VIVA3", "2026", "Q2") == first
    lookup.assert_called_once_with("VIVA3"); fallback.assert_not_called()
    assert download.call_args.kwargs == {"depth": 1, "timeout": 8}


def test_wrong_period_and_company_keep_original_fallback(monkeypatch, tmp_path):
    fetcher = AutoFetcher(tmp_path)
    rows = [{"title": "Vivara resultados 1T26", "url": "https://ri.vivara.com.br/1t26.pdf"},
            {"title": "Resultados 2T26", "url": "https://ri.other.example/release.pdf"}]
    fetcher.equibles_client.release_candidates = Mock(return_value=rows)
    download = Mock(return_value=FetchedDocument(rows[1]["url"], "RI", text="WEG resultados 2T26 Receita líquida."))
    monkeypatch.setattr(fetcher, "_download_release", download)
    correct = FetchedDocument("https://ri.vivara.com.br/correct.pdf", "RI", text="Vivara 2T26")
    fallback = Mock(return_value=correct); monkeypatch.setattr(fetcher, "_fetch_b3", fallback)
    assert fetcher.fetch_result_pdf("VIVA3", "2026", "2T") == correct
    assert download.call_count == 1
    fallback.assert_called_once_with("VIVA3", 2026, 2)
