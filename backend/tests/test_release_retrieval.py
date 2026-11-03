"""Regression coverage for fresh release retrieval and cache handoff."""
from unittest.mock import Mock
import pytest
from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument, SECFetcher

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
