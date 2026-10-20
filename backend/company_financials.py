"""Annual financial evidence from the SEC's public companyfacts API."""

from datetime import date
from decimal import Decimal
from functools import lru_cache
import math
import re

import requests


_HEADERS = {"User-Agent": "FinAnalyzer contact@finanalyser.com.br", "Accept": "application/json"}
_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
_SYMBOL = re.compile(r"[A-Z]{1,5}(?:\.[A-Z])?\Z")
_ALIASES = {"NIKE": "NKE", "PETR4": "PBR", "PETR3": "PBR"}
_KNOWN_CIKS = {"NKE": 320187, "PBR": 1119639}
_TAGS = {
    "Revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"),
    "Net income": ("NetIncomeLoss", "ProfitLoss"),
    "Operating cash flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "Capital expenditures": ("PaymentsToAcquirePropertyPlantAndEquipment",),
    "Diluted EPS": ("EarningsPerShareDiluted",),
    "Operating income": ("OperatingIncomeLoss",),
    "Gross profit": ("GrossProfit",),
    "Cash and cash equivalents": ("CashAndCashEquivalentsAtCarryingValue",),
    "Current long-term debt": ("LongTermDebtCurrent",),
    "Noncurrent long-term debt": ("LongTermDebtNoncurrent",),
}
_IFRS_TAGS = {
    "Revenue": ("Revenue",),
    "Net income": ("ProfitLossAttributableToOwnersOfParent", "ProfitLoss"),
    "Operating cash flow": ("CashFlowsFromUsedInOperatingActivities",),
    "Capital expenditures": ("PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
        "PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwillInvestmentPropertyAndOtherNoncurrentAssets"),
    "Diluted EPS": ("DilutedEarningsLossPerShare",),
    "Operating income": ("ProfitLossFromOperatingActivities",),
    "Gross profit": ("GrossProfit",),
    "Cash and cash equivalents": ("CashAndCashEquivalents",),
}
_INSTANT = {"Cash and cash equivalents", "Current long-term debt", "Noncurrent long-term debt"}
_MARGINS = {"Operating margin (calculated)": "Operating income", "Gross margin (calculated)": "Gross profit",
            "Free cash flow margin (calculated)": "Free cash flow (calculated)"}


def _get_json(url):
    response = requests.get(url, headers=_HEADERS, timeout=8, allow_redirects=False)
    if response.status_code != 200:
        raise requests.RequestException(f"SEC returned HTTP {response.status_code}")
    return response.json()


@lru_cache(maxsize=1)
def _ticker_index():
    payload = _get_json(_TICKERS_URL)
    rows = payload.values() if isinstance(payload, dict) else ()
    index = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker, cik = row.get("ticker"), row.get("cik_str")
        if isinstance(ticker, str) and isinstance(cik, int) and not isinstance(cik, bool):
            index[ticker.upper()] = cik
    if not index:
        raise ValueError("SEC ticker index is empty")
    return index


def _number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _annual_facts(payload, as_of):
    taxonomies = payload.get("facts", {})
    facts = dict(taxonomies.get("us-gaap", {}))
    for label, tags in _IFRS_TAGS.items():
        for tag in tags:
            if tag in taxonomies.get("ifrs-full", {}):
                facts["ifrs:" + tag] = taxonomies["ifrs-full"][tag]
    periods = {}
    for label, tags in _TAGS.items():
        for tag in (*tags, *("ifrs:" + tag for tag in _IFRS_TAGS.get(label, ()))):
            concept = facts.get(tag, {})
            units = concept.get("units", {}) if isinstance(concept, dict) else {}
            for unit, entries in units.items():
                for entry in entries if isinstance(entries, list) else ():
                    if not isinstance(entry, dict) or entry.get("form") not in ("10-K", "20-F") or entry.get("fp") != "FY":
                        continue
                    filed, end, start = entry.get("filed"), entry.get("end"), entry.get("start")
                    try:
                        filed_date, end_date = date.fromisoformat(filed), date.fromisoformat(end)
                        duration = (end_date - date.fromisoformat(start)).days if start else None
                    except (TypeError, ValueError):
                        continue
                    if filed_date > as_of or end_date > as_of or (label not in _INSTANT and not 300 <= (duration or 0) <= 380):
                        continue
                    if label in _INSTANT and start:
                        continue
                    value = entry.get("val")
                    if not _number(value):
                        continue
                    period = periods.setdefault(end, {"filed": {}, "values": {}, "starts": {}})
                    # Restatements replace earlier reports for that period, regardless of fiscal year label.
                    key = (label, unit)
                    if filed > period["filed"].get(key, ""):
                        period["filed"][key] = filed
                        period["values"][key] = value
                        period["starts"][key] = start
    return periods


def _currency(period):
    currencies = [unit for _, unit in period["values"] if re.fullmatch(r"[A-Z]{3}", unit)]
    if "USD" in currencies:
        return "USD"
    counts = {unit: currencies.count(unit) for unit in set(currencies)}
    return max(counts, key=counts.get) if counts else None


def _metric(period, label, currency):
    values = period["values"]
    units = (currency, f"{currency}/shares", f"{currency}-per-shares", f"{currency} / shares")
    candidates = [values[(label, unit)] for unit in units if (label, unit) in values]
    return candidates[0] if candidates else None


def _format(value):
    text = format(Decimal(str(value)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def get_sec_company_source(symbol, as_of):
    """Return one concise primary-source block, or None when SEC data is unavailable."""
    try:
        if not isinstance(symbol, str):
            return None
        symbol = symbol.strip().upper()
        symbol = _ALIASES.get(symbol, symbol)
        if not _SYMBOL.fullmatch(symbol):
            return None
        as_of_date = date.fromisoformat(as_of)
        cik = _KNOWN_CIKS.get(symbol)
        if not cik:
            index = _ticker_index()
            cik = index.get(symbol) or (index.get("GOOGL") if symbol == "GOOG" else None)
        if not cik:
            return None
        payload = _get_json(_FACTS_URL.format(cik=cik))
        periods = _annual_facts(payload, as_of_date)
        first_year = as_of_date.year - 6
        period_ends = sorted((end for end, period in periods.items()
                              if first_year <= int(end[:4]) <= as_of_date.year
                              and any(label not in _INSTANT for label, _ in period["values"])), reverse=True)[:5]
        history = []
        for end in period_ends:
            period = periods[end]
            currency = _currency(period)
            if not currency:
                continue
            values = {}
            for label in _TAGS:
                metric = _metric(period, label, currency)
                if metric is not None:
                    values[label] = metric
            ocf, capex = values.get("Operating cash flow"), values.get("Capital expenditures")
            starts = {label: period["starts"].get((label, currency)) for label in _TAGS}
            if ocf is not None and capex is not None and starts["Operating cash flow"] == starts["Capital expenditures"]:
                values["Free cash flow (calculated)"] = ocf - capex
                starts["Free cash flow (calculated)"] = starts["Operating cash flow"]
            revenue = values.get("Revenue")
            if revenue is not None and revenue > 0:
                for label, numerator in _MARGINS.items():
                    if numerator in values and starts[numerator] == starts["Revenue"]:
                        margin = values[numerator] / revenue * 100
                        if math.isfinite(margin):
                            values[label] = round(margin, 6)
            if values:
                latest_filed = max(period["filed"].values())
                history.append((end, latest_filed, currency, values))
        if not history:
            return None
        lines = []
        legal_name = payload.get("entityName")
        if isinstance(legal_name, str) and legal_name.strip():
            lines.append(f"SEC companyfacts for {legal_name.strip()} ({symbol}); annual facts reported in {history[0][2]}.")
        else:
            lines.append(f"SEC companyfacts for {symbol}; annual facts reported in {history[0][2]}.")
        if payload.get("facts", {}).get("ifrs-full"):
            lines.append("IFRS capital expenditures may include the reported combined purchases of property, plant, equipment, intangible and other noncurrent assets. Calculated free cash flow is operating cash flow minus those purchases; do not describe it as issuer-defined FCF. EPS is per underlying ordinary share in the reported currency, not per ADR; never compare it to another listing currency or ADR price without verified conversion and depositary ratio.")
        for end, filed, currency, values in history:
            metrics = "; ".join(
                f"{label} {'percent' if label in _MARGINS else currency + '/shares' if label == 'Diluted EPS' else currency} {_format(value)}"
                for label, value in values.items()
            )
            lines.append(f"For the full year ended {end}, filed {filed}: {metrics}.")
            eps = values.get("Diluted EPS")
            if eps is not None:
                lines.append(f"For the full year ended {end}, diluted earnings per share {currency}/shares {_format(eps)}.")
        cagr = None
        revenue_history = [row for row in history if "Revenue" in row[3]]
        if len(revenue_history) >= 2 and len({row[2] for row in revenue_history}) == 1:
            latest, oldest = revenue_history[0], revenue_history[-1]
            start, end = date.fromisoformat(oldest[0]), date.fromisoformat(latest[0])
            years = (end.year - start.year if (start.month, start.day) == (end.month, end.day)
                     else (end - start).days / 365.25)
            first, last = oldest[3]["Revenue"], latest[3]["Revenue"]
            if years > 0 and first > 0 and last >= 0:
                try:
                    growth = ((last / first) ** (1 / years) - 1) * 100
                except OverflowError:
                    growth = float("inf")
                if math.isfinite(growth):
                    cagr = {"start_period": oldest[0], "end_period": latest[0], "years": round(years, 6),
                            "numeric_value": round(growth, 6), "unit": "percent"}
                    lines.append(f"Revenue CAGR (calculated) from {oldest[0]} to {latest[0]}, "
                                 f"over {_format(round(years, 6))} elapsed years: percent {_format(cagr['numeric_value'])}. "
                                 "The duration is the elapsed interval between annual endpoints, not the number of observations.")
        return {
            "id": "F1",
            "title": f"SEC companyfacts — {symbol} annual financials",
            "url": _FACTS_URL.format(cik=cik),
            "text": "\n".join(lines),
            "basis": "primary",
            "annual_financials": [{"period": end, "currency": currency, "values": values,
                                   "value_units": {label: "percent" for label in _MARGINS if label in values},
                                   **({"revenue_cagr": cagr} if cagr and end == cagr["end_period"] else {})}
                                  for end, _, currency, values in history],
        }
    except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError):
        return None
