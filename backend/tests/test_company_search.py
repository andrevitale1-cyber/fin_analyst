from company_search import search_companies


def test_search_deduplicates_and_prioritizes_exact_ticker(monkeypatch):
    import company_search
    monkeypatch.setattr(company_search, "_load", lambda kind: ([
        {"name": "MICRON TECHNOLOGY INC", "ticker": "MU", "market": "Nasdaq"},
        {"name": "MURPHY OIL", "ticker": "MUR", "market": "NYSE"},
    ] if kind == "sec" else []))
    results = search_companies("mu")
    assert results[0] == {"name": "Micron Technology", "ticker": "MU", "market": "Nasdaq"}
    assert sum(item["ticker"] == "MU" for item in results) == 1


def test_search_supports_brazil_and_korean_company_names(monkeypatch):
    import company_search
    monkeypatch.setattr(company_search, "_load", lambda kind: [])
    assert search_companies("track and field")[0]["ticker"] == "TFCO4"
    assert search_companies("track")[0]["ticker"] == "TFCO4"
    assert search_companies("000660")[0]["ticker"] == "000660.KS"
    assert search_companies("s")[0:] == []
