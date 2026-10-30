"""Optional B3 company discovery and period-verified financial context from brapi."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import os
import re
import math
import unicodedata
import requests

BASE = "https://brapi.dev/api/v2"
FREE_TICKERS = frozenset(("PETR4", "MGLU3", "VALE3", "ITUB4"))
FIELDS = {
    "income-statement": ("totalRevenue", "grossProfit", "operatingIncome", "netIncome"),
    "balance-sheet": ("totalAssets", "totalLiab", "cash", "shortLongTermDebt", "longTermDebt"),
    "cash-flow": ("operatingCashFlow", "investmentCashFlow", "financingCashFlow"),
}

def _token():
    return os.getenv("BRAPI_API_KEY", "").strip()

def _get(path, params, *, public=False):
    token = _token()
    if not token and not public:
        return None
    try:
        response = requests.get(BASE + path, params=params, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=6)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else None
    except (requests.RequestException, ValueError):
        return None

def search_b3(query):
    data = _get("/tickers", {"search": query, "limit": 15, "type": "stock"}, public=True)
    if not data or not isinstance(data.get("results"), list):
        return []
    return [{"name": x["name"], "ticker": x["symbol"], "market": "B3"}
            for x in data["results"] if isinstance(x, dict) and x.get("isActive") is True
            and isinstance(x.get("name"), str) and re.fullmatch(r"[A-Z]{4}\d{1,2}", str(x.get("symbol", "")))
            and x.get("subType") in ("stock", "unit")]

def _date_position(text, end_date):
    try:
        dt = date.fromisoformat(end_date)
    except (ValueError, TypeError):
        return -1
    months = ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    expressions = (re.escape(dt.isoformat()), rf"\b0?{dt.day}[/.]0?{dt.month}[/.]{dt.year}\b",
                   rf"\b0?{dt.day}\s+de\s+{months[dt.month-1]}\s+de\s+{dt.year}\b")
    found = [match.start() for expression in expressions if (match := re.search(expression, normalized))]
    return min(found) if found else -1

def quarterly_context(ticker, document_text, year, quarter):
    if (not _token() and ticker not in FREE_TICKERS) or not re.fullmatch(r"[A-Z]{4}\d{1,2}", ticker) or not document_text:
        return None
    def fetch(kind):
        payload = _get(f"/stocks/{kind}", {"symbols": ticker, "period": "quarterly"}, public=ticker in FREE_TICKERS)
        results = payload.get("results", []) if payload else []
        if len(results) != 1 or results[0].get("symbol") != ticker or not isinstance(results[0].get("data"), list):
            return kind, []
        return kind, results[0]["data"]
    with ThreadPoolExecutor(max_workers=3) as pool:
        statements = dict(pool.map(fetch, FIELDS))
    # Only use a period explicitly dated near the beginning of the official release.
    dated = [(position, row.get("endDate")) for rows in statements.values() for row in rows if isinstance(row, dict)
             and row.get("type") == "quarterly" and (position := _date_position(document_text[:6000], row.get("endDate"))) >= 0]
    if not dated:
        return None
    dates = {end_date for _, end_date in dated}
    if len(dates) != 1:
        return None
    end_date = next(iter(dates))
    if not re.fullmatch(r"\d{4}", str(year)) or not re.fullmatch(r"[1-4]", str(quarter)):
        return None
    position = _date_position(document_text[:6000], end_date)
    nearby = unicodedata.normalize("NFKD", document_text[max(0, position - 250):position + 250]).encode("ascii", "ignore").decode().upper()
    yr = str(year)
    q = str(quarter)
    ordinal = ("FIRST|PRIMEIRO", "SECOND|SEGUNDO", "THIRD|TERCEIRO", "FOURTH|QUARTO")[int(q) - 1]
    if not re.search(rf"(?:{q}[TQ]|[TQ]{q})\s*(?:FY)?\s*(?:{yr}|{yr[-2:]})\b|(?:{ordinal}|{q})\s*(?:O\s*)?(?:TRIMESTRE|QUARTER).{{0,35}}{yr}", nearby):
        return None
    result = {}
    for kind, rows in statements.items():
        matches = [row for row in rows if isinstance(row, dict) and row.get("type") == "quarterly" and row.get("endDate") == end_date]
        if len(matches) != 1:
            continue
        row = matches[0]
        values = {key: row[key] for key in FIELDS[kind] if isinstance(row.get(key), (int, float)) and not isinstance(row[key], bool) and math.isfinite(row[key])}
        if values:
            result[kind] = {"consolidationType": row.get("consolidationType"), "values": values}
    return {"ticker": ticker, "endDate": end_date, "statements": result} if result else None
