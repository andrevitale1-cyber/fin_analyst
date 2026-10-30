import time
from unittest.mock import Mock

from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument, SECFetcher


def test_sec_catalog_resolves_exact_name_but_not_ambiguous(monkeypatch):
    monkeypatch.setattr(SECFetcher, "_company_catalog", [
        {"ticker": "COST", "title": "Costco Wholesale Corp /NEW"},
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


def test_small_cap_name_uses_b3_portfolio_and_rejects_ambiguous_names(monkeypatch, tmp_path):
    monkeypatch.setattr(AutoFetcher, "_small_caps", [
        {"cod": "TTEN3", "asset": "3TENTOS"},
        {"cod": "TEST3", "asset": "TESTE"}, {"cod": "TEST4", "asset": "TESTE"},
    ])
    monkeypatch.setattr(AutoFetcher, "_small_caps_expires", time.monotonic() + 60)
    response = Mock()
    response.json.return_value = {"results": []}
    monkeypatch.setattr("agents.auto_fetcher.requests.get", Mock(return_value=response))
    fetcher = AutoFetcher(tmp_path)
    assert fetcher._resolve_b3_name("3tentos") == "TTEN3"
    assert fetcher._resolve_b3_name("teste") is None


def test_micron_name_uses_sec_ticker_and_falls_back_to_web(monkeypatch, tmp_path):
    fetcher = AutoFetcher(tmp_path)
    assert fetcher.resolve_ticker("Micron") == "MU"
    assert fetcher.resolve_ticker("Micron Technology Inc.") == "MU"
    sec = Mock(return_value=None)
    monkeypatch.setattr(SECFetcher, "fetch", sec)
    monkeypatch.setattr(fetcher, "_fetch_equibles", lambda *args: None)
    release = FetchedDocument("https://example.com/micron", "RI", text="Micron Technology results 2Q 2026")
    monkeypatch.setattr(fetcher, "_fetch_b3", lambda *args: release)
    assert fetcher.fetch_result_pdf("Micron", 2026, "2T") == release
    sec.assert_called_once_with("MU", 2026, 2)


def test_track_field_name_and_catalog_category_with_trailing_space(monkeypatch, tmp_path):
    from bs4 import BeautifulSoup
    fetcher = AutoFetcher(tmp_path)
    assert fetcher.resolve_ticker("track and field") == "TFCO4"
    assert fetcher.resolve_ticker("Track&Field") == "TFCO4"
    catalog = Mock(return_value=[])
    monkeypatch.setattr(fetcher, "_mziq_catalog_candidates", catalog)
    html = "<script>var fmId = '8e49886e-dded-49c0-b8db-c35451e75eed'; internal_name: 'central_release_de_resultados ';</script>"
    fetcher._mziq_release_candidates(BeautifulSoup(html, "html.parser"), 2025, 4)
    catalog.assert_called_once_with("8e49886e-dded-49c0-b8db-c35451e75eed", ["central_release_de_resultados "], 2025, 4)


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
    monkeypatch.setattr(SECFetcher, "resolve_name", lambda *args: None)
    monkeypatch.setattr(AutoFetcher, "_resolve_b3_name", lambda *args: None)
    monkeypatch.setattr(AutoFetcher, "_fetch_equibles", lambda *args: None)
    other = FetchedDocument("https://example.com/release", "RI", text="Other company 3Q 2026")
    monkeypatch.setattr(AutoFetcher, "_fetch_b3", lambda *args: other)
    assert AutoFetcher(tmp_path).fetch_result_pdf("ZZZZ", 2026, "3T") is None
    own = FetchedDocument("https://example.com/release", "RI", text="ZZZZ earnings 3Q 2026")
    monkeypatch.setattr(AutoFetcher, "_fetch_b3", lambda *args: own)
    assert AutoFetcher(tmp_path).fetch_result_pdf("ZZZZ", 2026, "3T") == own


def test_brazilian_search_skips_release_of_another_issuer(monkeypatch, tmp_path):
    fetcher = AutoFetcher(tmp_path)
    wrong = FetchedDocument("https://example.com/suzano.pdf", "RI", text="Suzano resultados 4T25")
    right = FetchedDocument("https://example.com/track.pdf", "RI", text="Track & Field resultados 4T25")
    monkeypatch.setattr(fetcher.equibles_client, "release_candidates", lambda *args: [])
    monkeypatch.setattr(fetcher.search_client, "search_financial_reports", lambda *args: [
        {"title": "release resultados 4T25", "url": wrong.url},
        {"title": "release resultados 4T25", "url": right.url},
    ])
    monkeypatch.setattr(fetcher, "_download_release", lambda url, *args, **kwargs: wrong if url == wrong.url else right)
    assert fetcher._fetch_b3("TFCO4", 2025, 4) == right
    assert not fetcher._release_company_matches(wrong, "TFCO4")
