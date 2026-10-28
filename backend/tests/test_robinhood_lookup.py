from unittest.mock import Mock

from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument


def test_robinhood_company_name_uses_sec_ticker(monkeypatch, tmp_path):
    document = FetchedDocument("https://www.sec.gov/filing", "SEC", text="Robinhood 3Q 2026")
    fetch = Mock(return_value=document)
    monkeypatch.setattr("agents.auto_fetcher.SECFetcher.fetch", fetch)

    assert AutoFetcher(tmp_path).fetch_result_pdf("Robinhood", "2026", "3T") == document
    fetch.assert_called_once_with("HOOD", 2026, 3)
