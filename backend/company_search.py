"""Company suggestions from exchange catalogues; never treat index membership as proof of a filing."""
import base64
import json
import os
import re
import time
import unicodedata
import requests

from agents.sec_fetcher import SECFetcher
from agents.brapi_client import search_b3

_cache = {"sec": (0, []), "b3": (0, [])}
_twelve_cache = {}
_known = [
    {"name": "Micron Technology", "ticker": "MU", "market": "Nasdaq"},
    {"name": "Track & Field", "ticker": "TFCO4", "market": "B3"},
    {"name": "Panvel / Dimed", "ticker": "PNVL3", "market": "B3"},
    {"name": "SK hynix", "ticker": "000660.KS", "market": "Coreia"},
    {"name": "Google / Alphabet", "ticker": "GOOGL", "market": "Nasdaq"},
]

def _normalized(value):
    text = re.sub(r"[^A-Z0-9]+", " ", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().upper()).strip()
    return re.sub(r"\bAND\b", "", text).replace("  ", " ").strip()

def _load(kind):
    expires, rows = _cache[kind]
    if time.monotonic() < expires:
        return rows
    try:
        if kind == "sec":
            response = requests.get("https://www.sec.gov/files/company_tickers_exchange.json", headers=SECFetcher.headers, timeout=8)
            response.raise_for_status()
            payload = response.json()
            fields = payload["fields"]
            items = [dict(zip(fields, entry)) for entry in payload["data"]]
            fresh = [{"name": str(x["name"]), "ticker": str(x["ticker"]), "market": str(x["exchange"])}
                     for x in items if x.get("name") and x.get("ticker") and x.get("exchange")]
        else:
            fresh = []
            for index in ("IBOV", "SMLL"):
                query = base64.b64encode(json.dumps({"language": "pt-br", "pageNumber": 1, "pageSize": 200, "index": index, "segment": "1"}, separators=(",", ":")).encode()).decode()
                response = requests.get("https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/" + query, timeout=5)
                response.raise_for_status()
                payload = response.json()
                if payload.get("page", {}).get("totalPages") != 1:
                    raise ValueError("Incomplete B3 portfolio")
                fresh.extend({"name": str(x["asset"]), "ticker": str(x["cod"]), "market": "B3"}
                             for x in payload["results"] if x.get("asset") and re.fullmatch(r"[A-Z]{4}\d{1,2}", str(x.get("cod", ""))))
        if fresh:
            _cache[kind] = (time.monotonic() + 86400, fresh)
            return fresh
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    return rows

def _twelve_search(query, sec_rows):
    token = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not token or len(query.strip()) < 3:
        return []
    key = _normalized(query)
    cached = _twelve_cache.get(key)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    try:
        response = requests.get("https://api.twelvedata.com/symbol_search", params={"symbol": query, "outputsize": 30},
                                headers={"Authorization": f"apikey {token}"}, timeout=4)
        response.raise_for_status()
        payload = response.json()
        entries = payload.get("data", [])
        if not isinstance(entries, list):
            return []
        known = {(x["ticker"].upper(), x["market"].upper()) for x in sec_rows}
        results = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            ticker, name, market = entry.get("symbol"), entry.get("instrument_name"), entry.get("exchange")
            if (isinstance(ticker, str) and isinstance(name, str) and isinstance(market, str)
                    and re.fullmatch(r"[A-Z]{1,5}(?:[-.][A-Z])?", ticker)
                    and (ticker, market.upper()) in known
                    and entry.get("instrument_type") in ("Common Stock", "Depositary Receipt")):
                results.append({"name": name, "ticker": ticker, "market": market})
        if len(_twelve_cache) >= 256:
            _twelve_cache.clear()
        _twelve_cache[key] = (time.monotonic() + 300, results)
        return results
    except (requests.RequestException, ValueError, TypeError):
        return []

def search_companies(query):
    target = _normalized(query)
    if len(target) < 2:
        return []
    sec_rows = _load("sec")
    rows = _known + search_b3(query) + sec_rows + _load("b3")
    if not any(target in _normalized(item["ticker"]) or target in _normalized(item["name"]) for item in rows):
        rows += _twelve_search(query, sec_rows)
    matches = []
    seen = set()
    for item in rows:
        ticker, name = _normalized(item["ticker"]), _normalized(item["name"])
        if target not in ticker and target not in name:
            continue
        key = (item["ticker"].upper(), item["market"].upper())
        if key in seen:
            continue
        seen.add(key)
        rank = 0 if target == ticker or target == name else 1 if ticker.startswith(target) or name.startswith(target) else 2
        matches.append((rank, item["name"].upper(), item))
    return [item for _, _, item in sorted(matches, key=lambda x: (x[0], x[1]))[:10]]
