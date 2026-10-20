import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import company_financials as financials


def fact(val, start, end, filed, *, form="10-K", fp="FY", unit="USD", fy=None):
    result = {"val": val, "end": end, "filed": filed, "form": form, "fp": fp, "fy": fy or int(end[:4])}
    if start:
        result["start"] = start
    return unit, result


def payload(entries, *, name="Example Corp"):
    concepts = {}
    for tag, facts in entries.items():
        for unit, item in facts:
            concepts.setdefault(tag, {}).setdefault("units", {}).setdefault(unit, []).append(item)
    return {"entityName": name, "facts": {"us-gaap": concepts}}


@pytest.fixture(autouse=True)
def clear_ticker_cache():
    financials._ticker_index.cache_clear()
    yield
    financials._ticker_index.cache_clear()


def install_sec(monkeypatch, company_facts, *, index=None):
    responses = {
        financials._TICKERS_URL: index or {"0": {"ticker": "EXM", "cik_str": 123}},
        financials._FACTS_URL.format(cik=123): company_facts,
    }
    calls = []

    class Response:
        status_code = 200

        def __init__(self, data):
            self.data = data

        def json(self):
            return self.data

    def get(url, **kwargs):
        calls.append((url, kwargs))
        if url not in responses:
            raise AssertionError(f"Unexpected URL {url}")
        return Response(responses[url])

    monkeypatch.setattr(financials.requests, "get", get)
    return calls


def test_uses_annual_periods_restatements_as_of_cutoff_and_eps_proof(monkeypatch):
    entries = {
        "Revenues": [
            fact(100, "2022-01-01", "2022-12-31", "2023-02-01"),
            fact(110, "2022-01-01", "2022-12-31", "2024-02-01", fy=2023),
            fact(120, "2023-01-01", "2023-12-31", "2024-02-01"),
            fact(999, "2024-01-01", "2024-12-31", "2025-02-01"),  # after as_of
            fact(55, "2023-01-01", "2023-06-30", "2023-08-01", form="10-Q", fp="Q2"),
        ],
        "NetIncomeLoss": [fact(10, "2022-01-01", "2022-12-31", "2023-02-01"), fact(12, "2023-01-01", "2023-12-31", "2024-02-01")],
        "NetCashProvidedByUsedInOperatingActivities": [fact(20, "2022-01-01", "2022-12-31", "2023-02-01"), fact(24, "2023-01-01", "2023-12-31", "2024-02-01")],
        "PaymentsToAcquirePropertyPlantAndEquipment": [fact(5, "2022-01-01", "2022-12-31", "2023-02-01"), fact(6, "2023-01-01", "2023-12-31", "2024-02-01")],
        "EarningsPerShareDiluted": [
            fact(1.25, "2022-01-01", "2022-12-31", "2023-02-01", unit="USD-per-shares"),
            fact(1.5, "2023-01-01", "2023-12-31", "2024-02-01", unit="USD/shares"),
            fact(0.7, "2023-10-01", "2023-12-31", "2024-02-01", form="10-K", fp="FY", unit="USD-per-shares"),
        ],
    }
    calls = install_sec(monkeypatch, payload(entries))
    source = financials.get_sec_company_source("EXM", "2024-12-31")

    assert source and source["id"] == "F1" and source["basis"] == "primary"
    assert source["url"] == financials._FACTS_URL.format(cik=123)
    assert "For the full year ended 2023-12-31, filed 2024-02-01: Revenue USD 120" in source["text"]
    assert source["annual_financials"][0]["values"]["Revenue"] == 120
    assert source["annual_financials"][0]["currency"] == "USD"
    assert "For the full year ended 2023-12-31, diluted earnings per share USD/shares 1.5." in source["text"]
    assert "Free cash flow (calculated) USD 18" in source["text"]
    assert "USD 999" not in source["text"] and "USD 55" not in source["text"] and "USD 0.7" not in source["text"]
    assert "2022-12-31" in source["text"]
    assert all(call[1]["timeout"] == 8 and call[1]["allow_redirects"] is False for call in calls)


def test_foreign_currency_fallback_stays_aligned_and_goog_alias(monkeypatch):
    end, start, filed = "2024-06-30", "2023-07-01", "2024-08-01"
    entries = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": [fact(50, start, end, filed, unit="CAD")],
        "NetIncomeLoss": [fact(7, start, end, filed, unit="CAD")],
        "NetCashProvidedByUsedInOperatingActivities": [fact(9, start, end, filed, unit="CAD")],
        "PaymentsToAcquirePropertyPlantAndEquipment": [fact(2, start, end, filed, unit="CAD")],
        "EarningsPerShareDiluted": [fact(1.1, start, end, filed, unit="CAD-per-shares")],
    }
    calls = install_sec(monkeypatch, payload(entries), index={"0": {"ticker": "GOOGL", "cik_str": 123}})
    source = financials.get_sec_company_source("GOOG", "2024-12-31")
    assert source and "CAD 50" in source["text"] and "CAD 7" in source["text"]
    assert "Free cash flow (calculated) CAD 7" in source["text"]
    assert "diluted earnings per share USD" not in source["text"]
    assert calls[-1][0].endswith("CIK0000000123.json")


def test_bad_symbols_and_transient_sec_failures_return_none_and_retry(monkeypatch):
    assert financials.get_sec_company_source("AAPL/evil", "2024-01-01") is None
    calls = []

    def fail(url, **kwargs):
        calls.append(url)
        raise requests.Timeout("blocked")

    monkeypatch.setattr(financials.requests, "get", fail)
    assert financials.get_sec_company_source("EXM", "2024-01-01") is None
    assert financials.get_sec_company_source("EXM", "2024-01-01") is None
    assert calls == [financials._TICKERS_URL, financials._TICKERS_URL]


def test_small_reported_eps_is_not_rounded_to_a_different_value():
    assert financials._format(0.000051) == "0.000051"
    assert financials._format(2500000000) == "2500000000"


def test_alternative_revenue_tag_and_balance_only_dates_preserve_annual_history(monkeypatch):
    entries = {
        "RevenueFromContractWithCustomerIncludingAssessedTax": [
            fact(100, "2023-01-01", "2023-12-31", "2024-02-01")],
        "CashAndCashEquivalentsAtCarryingValue": [
            fact(10, None, f"2024-{month:02d}-01", "2024-12-31") for month in range(1, 7)],
    }
    install_sec(monkeypatch, payload(entries))
    source = financials.get_sec_company_source("EXM", "2024-12-31")
    assert "full year ended 2023-12-31" in source["text"] and "Revenue USD 100" in source["text"]
    assert "full year ended 2024-" not in source["text"]


def test_redirect_and_non_annual_or_invalid_values_never_become_evidence(monkeypatch):
    entries = {
        "Revenues": [fact(1, "2023-01-01", "2023-12-31", "2024-02-01", form="8-K"), fact(float("nan"), "2023-01-01", "2023-12-31", "2024-02-01")],
        "EarningsPerShareDiluted": [fact(True, "2023-01-01", "2023-12-31", "2024-02-01", unit="USD-per-shares")],
    }
    install_sec(monkeypatch, payload(entries))
    assert financials.get_sec_company_source("EXM", "2024-12-31") is None

    financials._ticker_index.cache_clear()

    class Redirect:
        status_code = 302

    monkeypatch.setattr(financials.requests, "get", lambda *args, **kwargs: Redirect())
    assert financials.get_sec_company_source("EXM", "2024-12-31") is None


@pytest.mark.parametrize("revenue, expected", [(100, (-20, 60, -10)), (0, None), (-100, None)])
def test_calculated_margins_preserve_losses_and_skip_nonpositive_revenue(monkeypatch, revenue, expected):
    start, end, filed = "2023-01-01", "2023-12-31", "2024-02-01"
    entries = {"Revenues": [fact(revenue, start, end, filed)],
               "OperatingIncomeLoss": [fact(-20, start, end, filed)],
               "GrossProfit": [fact(60, start, end, filed)],
               "NetCashProvidedByUsedInOperatingActivities": [fact(5, start, end, filed)],
               "PaymentsToAcquirePropertyPlantAndEquipment": [fact(15, start, end, filed)]}
    install_sec(monkeypatch, payload(entries))
    source = financials.get_sec_company_source("EXM", "2024-12-31")
    row = source["annual_financials"][0]
    names = ("Operating margin (calculated)", "Gross margin (calculated)", "Free cash flow margin (calculated)")
    if expected is None:
        assert not any(name in row["values"] for name in names)
    else:
        assert tuple(row["values"][name] for name in names) == expected
        assert all(row["value_units"][name] == "percent" for name in names)
        assert "Operating margin (calculated) percent -20" in source["text"]
        assert "Free cash flow margin (calculated) percent -10" in source["text"]
    assert "ROIC" not in row["values"]


def test_margins_require_same_currency_and_exact_annual_period(monkeypatch):
    end, filed = "2023-12-31", "2024-02-01"
    entries = {"Revenues": [fact(100, "2023-01-01", end, filed)],
               "OperatingIncomeLoss": [fact(20, "2023-01-01", end, filed, unit="CAD")],
               "GrossProfit": [fact(60, "2023-02-01", end, filed)],
               "NetCashProvidedByUsedInOperatingActivities": [fact(25, "2023-01-01", end, filed)],
               "PaymentsToAcquirePropertyPlantAndEquipment": [fact(15, "2023-02-01", end, filed)]}
    install_sec(monkeypatch, payload(entries))
    source = financials.get_sec_company_source("EXM", "2024-12-31")
    assert not source["annual_financials"][0]["value_units"]
    assert "margin (calculated)" not in source["text"]
    assert "Free cash flow (calculated)" not in source["text"]


def test_revenue_cagr_uses_elapsed_years_not_observation_count(monkeypatch):
    entries = {"Revenues": [fact(100 * 1.1 ** index, f"{year}-01-01", f"{year}-12-31", f"{year+1}-02-01")
                             for index, year in enumerate(range(2020, 2025))]}
    install_sec(monkeypatch, payload(entries))
    source = financials.get_sec_company_source("EXM", "2025-12-31")
    cagr = source["annual_financials"][0]["revenue_cagr"]
    assert cagr == {"start_period": "2020-12-31", "end_period": "2024-12-31", "years": 4,
                    "numeric_value": 10, "unit": "percent"}
    assert "over 4 elapsed years: percent 10" in source["text"]
    assert "5-year" not in source["text"]


@pytest.mark.parametrize("first,last,currency", [(0, 100, "USD"), (-100, 100, "USD"), (100, -10, "USD"), (100, 200, "CAD")])
def test_revenue_cagr_omits_invalid_baselines_losses_and_currency_changes(monkeypatch, first, last, currency):
    entries = {"Revenues": [fact(first, "2022-01-01", "2022-12-31", "2023-02-01"),
                             fact(last, "2023-01-01", "2023-12-31", "2024-02-01", unit=currency)]}
    install_sec(monkeypatch, payload(entries))
    source = financials.get_sec_company_source("EXM", "2024-12-31")
    assert not any("revenue_cagr" in row for row in source["annual_financials"])
    assert "Revenue CAGR" not in source["text"]


@pytest.mark.parametrize("symbol,cik", [("NIKE",320187),("NKE",320187),("PETR4",1119639)])
def test_known_issuer_resolution_does_not_depend_on_ticker_index(monkeypatch,symbol,cik):
    data = payload({"Revenue": [fact(100,"2023-01-01","2023-12-31","2024-03-01",form="20-F")]})
    data["facts"]["ifrs-full"] = data["facts"].pop("us-gaap")
    seen=[]
    def fetch(url):
        seen.append(url)
        return data
    monkeypatch.setattr(financials,"_get_json",fetch)
    source=financials.get_sec_company_source(symbol,"2024-12-31")
    assert seen == [financials._FACTS_URL.format(cik=cik)]
    assert source["annual_financials"][0]["values"]["Revenue"] == 100


def test_ifrs_cash_flow_and_eps_keep_reported_currency_and_full_year(monkeypatch):
    data=payload({tag:[fact(value,"2023-01-01","2023-12-31","2024-03-01",form="20-F",unit=unit)] for tag,value,unit in [
        ("Revenue",100,"USD"),("ProfitLossAttributableToOwnersOfParent",12,"USD"),
        ("CashFlowsFromUsedInOperatingActivities",30,"USD"),
        ("PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",10,"USD"),
        ("DilutedEarningsLossPerShare",0.5,"USD/shares")]})
    data["facts"]["ifrs-full"]=data["facts"].pop("us-gaap")
    monkeypatch.setattr(financials,"_get_json",lambda url:data)
    source=financials.get_sec_company_source("PETR4","2024-12-31")
    row=source["annual_financials"][0]
    assert row["currency"]=="USD" and row["values"]["Free cash flow (calculated)"]==20
    assert row["values"]["Diluted EPS"]==0.5
