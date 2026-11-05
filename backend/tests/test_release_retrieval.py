"""Regression coverage for fresh release retrieval and cache handoff."""
from unittest.mock import Mock
import pytest
from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument, SECFetcher
from release_pipeline import validate_document, ReleaseError


def test_rd_saude_current_ir_and_rebranded_release_do_not_require_web(tmp_path, monkeypatch):
    fetcher = AutoFetcher(tmp_path)
    url = 'https://ri.rdsaude.com.br/central-de-resultados'
    assert fetcher.ir_urls['RADL3'] == url
    assert fetcher.resolve_ticker('RD Saúde') == 'RADL3'
    assert fetcher.resolve_ticker('Raia Drogasil S.A.') == 'RADL3'
    document = FetchedDocument('https://ri.rdsaude.com.br/Download.aspx?Arquivo=verified', 'RI',
        text='RDsaúde — RESULTADOS 3T26\nReceita bruta de 10.000 milhões. Lucro líquido de 500 milhões.\n' * 8)
    response = Mock(url=url, text='<a href="/Download.aspx?Arquivo=verified">Resultados 3T26</a>')
    monkeypatch.setattr('agents.auto_fetcher.requests.get', lambda *args, **kwargs: response)
    download = Mock(return_value=document)
    monkeypatch.setattr(fetcher, '_download_release', download)
    fetcher.equibles_client = Mock()
    fetcher.search_client = Mock()
    result = fetcher._fetch_b3('RADL3', 2026, 3)
    assert result == document
    download.assert_called_once_with(document.url, 2026, 3)
    fetcher.search_client.search_financial_reports.assert_not_called()
    identity = {'symbol': 'RADL3', 'name': 'RAIA DROGASIL S.A.', 'cnpj': '61585865000151'}
    assert validate_document(result, fetcher, identity, 2026, 3) == document.text
    with pytest.raises(ReleaseError):
        validate_document(result, fetcher, identity, 2026, 2)
    wrong = FetchedDocument(document.url, 'RI', text='Suzano RESULTADOS 3T26. Receita e lucro de 500 milhões. ' * 20)
    with pytest.raises(ReleaseError):
        validate_document(wrong, fetcher, identity, 2026, 3)

@pytest.mark.parametrize("ticker", ["GOOGL", "MSFT", "WEGE3"])
def test_new_release_is_returned_and_cached_without_breaking_lookup(tmp_path, monkeypatch, ticker):
    fetcher = AutoFetcher(tmp_path)
    monkeypatch.setattr(SECFetcher, "resolve_name", lambda self, name: name)
    doc = FetchedDocument("https://example.com/earnings-q2-2026.pdf", "Official release",
                          pdf_bytes=b"%PDF-test", text=f"{ticker} Q2 2026 earnings release")
    sec = Mock(return_value=doc)
    monkeypatch.setattr(SECFetcher, "fetch", sec)
    b3 = Mock(return_value=doc)
    monkeypatch.setattr(fetcher, "_fetch_b3", b3)
    assert fetcher.fetch_result_pdf(ticker, 2026, "2Q") == doc
    assert sec.call_count == (0 if ticker == "WEGE3" else 1)
    assert b3.call_count == (1 if ticker == "WEGE3" else 0)
    assert fetcher.fetch_result_pdf(ticker, 2026, "2Q") == doc
    assert sec.call_count + b3.call_count == 1
