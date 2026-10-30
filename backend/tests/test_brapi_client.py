from agents import brapi_client


def test_company_search_filters_inactive_and_non_stock(monkeypatch):
    monkeypatch.setattr(brapi_client, "_get", lambda *args, **kwargs: {"results": [
        {"name": "WEG S.A.", "symbol": "WEGE3", "isActive": True, "subType": "stock"},
        {"name": "Inactive", "symbol": "TEST3", "isActive": False, "subType": "stock"},
        {"name": "Fund", "symbol": "TEST11", "isActive": True, "subType": "fii"},
    ]})
    assert brapi_client.search_b3("WEG") == [{"name": "WEG S.A.", "ticker": "WEGE3", "market": "B3"}]


def test_financial_context_requires_unambiguous_period_and_exact_ticker(monkeypatch):
    monkeypatch.setenv("BRAPI_API_KEY", "test-token")
    def get(path, params, **kwargs):
        return {"results": [{"symbol": "PETR4", "data": [
            {"type": "quarterly", "endDate": "2025-12-31", "consolidationType": "consolidated", "totalRevenue": 100, "operatingCashFlow": 50, "freeCashFlow": 35},
            {"type": "quarterly", "endDate": "2024-12-31", "totalRevenue": 90},
        ]}]}
    monkeypatch.setattr(brapi_client, "_get", get)
    result = brapi_client.quarterly_context("PETR4", "Resultados 4T25 encerrados em 31 de dezembro de 2025", 2025, 4)
    assert result["endDate"] == "2025-12-31"
    assert result["statements"]["income-statement"]["values"]["totalRevenue"] == 100
    assert "freeCashFlow" not in result["statements"]["cash-flow"]["values"]
    assert brapi_client.quarterly_context("PETR4", "Sem data de encerramento", 2025, 4) is None
    assert brapi_client.quarterly_context("PETR4", "4T25 em 31/12/2025 comparado com 31/12/2024", 2025, 4) is None
    assert brapi_client.quarterly_context("PETR4", "3T25 em 31/12/2025", 2025, 4) is None
    assert brapi_client.quarterly_context("VALE3", "4T25 em 31/12/2025", 2025, 4) is None


def test_no_key_skips_requests(monkeypatch):
    monkeypatch.delenv("BRAPI_API_KEY", raising=False)
    monkeypatch.setattr(brapi_client.requests, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("unexpected network call")))
    assert brapi_client.quarterly_context("WEGE3", "31/12/2025", 2025, 4) is None
