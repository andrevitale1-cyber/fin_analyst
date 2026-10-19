from pathlib import Path
import sys
from unittest.mock import Mock

from bs4 import BeautifulSoup
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.auto_fetcher import AutoFetcher
from openai_client import OpenAIClient

COMPANY = "50c1bd3e-8ac6-42d9-884f-b9d69f690602"
CATEGORY = "central_de_resultados_release_resultados"
PDF = f"https://api.mziq.com/mzfilemanager/v2/d/{COMPANY}/release?origin=2"
HTML = f"<script>var fmId='{COMPANY}'; categories.push({{internal_name:'{CATEGORY}'}});</script>"
ROW = {"company_id": COMPANY, "internal_name": CATEGORY, "file_year": 2026, "file_quarter": 1,
       "is_published": True, "file_url": PDF, "file_title": "Release de Resultados 1T26"}


def test_weg_dynamic_catalog_finds_exact_period_without_paid_search_and_caches(tmp_path, monkeypatch):
    page = Mock(url="https://ri.weg.net/informacoes-financeiras/central-de-resultados/", text=HTML)
    pdf = Mock(url=PDF, content=b"%PDF-official-weg")
    get = Mock(side_effect=[page, pdf]); monkeypatch.setattr(requests, "get", get)
    post = Mock(return_value=Mock(json=lambda: {"success": True, "data": {"document_metas": [
        {**ROW, "file_quarter": 2, "file_url": PDF + "wrong"}, ROW]}}))
    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setattr(OpenAIClient, "extract_text", staticmethod(lambda _: "WEG Resultados 1T26. Receita líquida."))
    fetcher = AutoFetcher(tmp_path)
    fetcher.search_client.search_financial_reports = Mock(side_effect=AssertionError("No paid search"))
    document = fetcher.fetch_result_pdf("Weg", "2026", "1T")
    assert document and document.url == PDF
    assert post.call_args.kwargs["json"] == {"year": 2026, "categories": [CATEGORY], "language": "pt_BR", "published": True}
    for alias in ("WEGE3", "WEGE3.SA", "WEG S.A."):
        assert AutoFetcher(tmp_path).fetch_result_pdf(alias, "2026", "Q1") == document
    assert get.call_count == 2 and post.call_count == 1
    fetcher.search_client.search_financial_reports.assert_not_called()


@pytest.mark.parametrize("patch", [
    {"file_year": 2025}, {"file_quarter": 2}, {"company_id": "another-company"},
    {"is_published": False}, {"internal_name": "transcripts"},
    {"file_url": "http://127.0.0.1/release.pdf"}, {"file_url": "https://other.example/release.pdf"},
    {"file_url": "https://api.mziq.com/mzfilemanager/v2/d/another-company/release"},
])
def test_catalog_rejects_wrong_period_issuer_unpublished_and_untrusted_links(monkeypatch, patch):
    monkeypatch.setattr(requests, "post", Mock(return_value=Mock(json=lambda: {
        "success": True, "data": {"document_metas": [{**ROW, **patch}]}})))
    assert AutoFetcher()._mziq_release_candidates(BeautifulSoup(HTML, "html.parser"), 2026, 1) == []


def test_catalog_failure_preserves_the_existing_search_fallback(monkeypatch):
    page = Mock(url="https://ri.weg.net/informacoes-financeiras/central-de-resultados/", text=HTML)
    monkeypatch.setattr(requests, "get", Mock(return_value=page))
    monkeypatch.setattr(requests, "post", Mock(side_effect=requests.Timeout()))
    fetcher = AutoFetcher()
    fetcher.search_client.search_financial_reports = Mock(return_value=[])
    assert fetcher._fetch_b3("WEGE3", 2026, 1) is None
    fetcher.search_client.search_financial_reports.assert_called_once_with("WEGE3", 2026, "1T")


def test_catalog_metadata_does_not_override_downloaded_document_period(monkeypatch):
    monkeypatch.setattr(requests, "get", Mock(return_value=Mock(url=PDF, content=b"%PDF-wrong-quarter")))
    monkeypatch.setattr(OpenAIClient, "extract_text", staticmethod(lambda _: "WEG Resultados 2T26 comparativo 1T26"))
    assert AutoFetcher()._download_release(PDF, 2026, 1) is None


def test_dynamic_center_found_by_search_also_uses_verified_catalog_links(monkeypatch):
    page = Mock(url="https://ri.weg.net/results/", text=HTML, content=HTML.encode(), headers={"Content-Type": "text/html"})
    pdf = Mock(url=PDF, content=b"%PDF-official-weg")
    monkeypatch.setattr(requests, "get", Mock(side_effect=[page, pdf]))
    monkeypatch.setattr(requests, "post", Mock(return_value=Mock(json=lambda: {"success": True, "data": {"document_metas": [ROW]}})))
    monkeypatch.setattr(OpenAIClient, "extract_text", staticmethod(lambda _: "WEG Resultados 1T26. Receita líquida."))
    assert AutoFetcher()._download_release(page.url, 2026, 1).url == PDF


def test_search_service_failure_is_distinct_from_an_empty_result(monkeypatch):
    from agents.search_client import SearchClient, SearchError
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    search = Mock(side_effect=TimeoutError())
    monkeypatch.setattr(OpenAIClient, "search_pdf_links", search)
    with pytest.raises(SearchError): SearchClient().search_financial_reports("WEGE3", 2026, "1T")
    assert "WEG" in search.call_args.args[0]
    search.side_effect = None; search.return_value = []
    assert SearchClient().search_financial_reports("WEGE3", 2026, "1T") == []
