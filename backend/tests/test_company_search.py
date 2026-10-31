from company_search import search_companies


def test_search_deduplicates_and_prioritizes_exact_ticker(monkeypatch):
    import company_search
    monkeypatch.setattr(company_search, "search_b3", lambda query: [])
    monkeypatch.setattr(company_search, "_load", lambda kind: ([
        {"name": "MICRON TECHNOLOGY INC", "ticker": "MU", "market": "Nasdaq"},
        {"name": "MURPHY OIL", "ticker": "MUR", "market": "NYSE"},
    ] if kind == "sec" else []))
    results = search_companies("mu")
    assert results[0] == {"name": "Micron Technology", "ticker": "MU", "market": "Nasdaq"}
    assert sum(item["ticker"] == "MU" for item in results) == 1


def test_search_supports_brazil_and_korean_company_names(monkeypatch):
    import company_search
    monkeypatch.setattr(company_search, "search_b3", lambda query: [])
    monkeypatch.setattr(company_search, "_load", lambda kind: [])
    assert search_companies("track and field")[0]["ticker"] == "TFCO4"
    assert search_companies("track")[0]["ticker"] == "TFCO4"
    assert search_companies("000660")[0]["ticker"] == "000660.KS"
    assert search_companies("panvel")[0]["ticker"] == "PNVL3"
    assert search_companies("s")[0:] == []


def test_twelve_suggestions_require_verified_us_exchange(monkeypatch):
    import company_search
    from unittest.mock import Mock
    monkeypatch.setenv("TWELVE_DATA_API_KEY", "test-key")
    company_search._twelve_cache.clear()
    response = Mock()
    response.json.return_value = {"data": [
        {"symbol": "ABC", "instrument_name": "Example Company", "exchange": "NASDAQ", "instrument_type": "Common Stock"},
        {"symbol": "ABC", "instrument_name": "Another Company", "exchange": "LSE", "instrument_type": "Common Stock"},
        {"symbol": "FAKE", "instrument_name": "Fake", "exchange": "NASDAQ", "instrument_type": "Common Stock"},
    ]}
    monkeypatch.setattr(company_search.requests, "get", Mock(return_value=response))
    sec = [{"name": "EXAMPLE INC", "ticker": "ABC", "market": "Nasdaq"}]
    results = company_search._twelve_search("example", sec)
    assert results == [{"name": "Example Company", "ticker": "ABC", "market": "NASDAQ"}]
    assert company_search._twelve_search("example", sec) == results
    assert company_search.requests.get.call_count == 1
