import time
from unittest.mock import Mock

from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument, SECFetcher


def test_sec_catalog_resolves_exact_name_but_not_ambiguous(monkeypatch):
    monkeypatch.setattr(SECFetcher, "_company_catalog", [
        {"ticker": "COST", "title": "Costco Wholesale Corporation"},
        {"ticker": "ONE", "title": "Example Inc"},
        {"ticker": "TWO", "title": "Example Corp"},
    ])
    monkeypatch.setattr(SECFetcher, "_catalog_expires", time.monotonic() + 60)
    sec = SECFetcher()
    assert sec.resolve_name("Costco Wholesale") == "COST"
    assert sec.resolve_name("Example") is None
    assert sec.resolve_name("Costco") is None


def test_unknown_name_still_uses_web_search(monkeypatch, tmp_path):
    monkeypatch.setattr(SECFetcher, "resolve_name", lambda *args: None)
    monkeypatch.setattr(AutoFetcher, "_resolve_b3_name", lambda *args: None)
    document = FetchedDocument("https://example.com/release", "RI", text="3Q 2026")
    web = Mock(return_value=document)
    monkeypatch.setattr(AutoFetcher, "_fetch_b3", web)
    assert AutoFetcher(tmp_path).fetch_result_pdf("Unknown Company", 2026, "3T") == document
    web.assert_called_once_with("UNKNOWN COMPANY", 2026, 3)


def test_b3_name_requires_a_unique_known_ticker(monkeypatch, tmp_path):
    response = Mock()
    response.json.return_value = {"results": [{"status": "A", "type": "1", "issuingCompany": "TOTS",
                                               "companyName": "TOTVS S.A.", "tradingName": "TOTVS"}]}
    monkeypatch.setattr("agents.auto_fetcher.requests.get", Mock(return_value=response))
    fetcher = AutoFetcher(tmp_path)
    assert fetcher._resolve_b3_name("TOTVS") == "TOTS3"
    fetcher.ir_urls["TOTS4"] = "https://example.com"
    assert fetcher._resolve_b3_name("TOTVS") is None


def test_us_ticker_falls_back_to_web_and_checks_issuer(monkeypatch, tmp_path):
    monkeypatch.setattr(SECFetcher, "fetch", lambda *args: None)
    monkeypatch.setattr(AutoFetcher, "_fetch_equibles", lambda *args: None)
    other = FetchedDocument("https://example.com/release", "RI", text="Other company 3Q 2026")
    monkeypatch.setattr(AutoFetcher, "_fetch_b3", lambda *args: other)
    assert AutoFetcher(tmp_path).fetch_result_pdf("ZZZZ", 2026, "3T") is None
    own = FetchedDocument("https://example.com/release", "RI", text="ZZZZ earnings 3Q 2026")
    monkeypatch.setattr(AutoFetcher, "_fetch_b3", lambda *args: own)
    assert AutoFetcher(tmp_path).fetch_result_pdf("ZZZZ", 2026, "3T") == own
