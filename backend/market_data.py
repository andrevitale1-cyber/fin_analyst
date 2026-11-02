"""Bounded, cached market data. Never infer that a recent move was an earnings reaction."""
from datetime import datetime, timedelta, timezone
import math
import os
import re
import time
import requests
import json
import logging
from agents.prompt_builder import MARKET_REACTION_RULES

RANGES = {"1d": (1, "5min"), "5d": (7, "30min"), "1mo": (31, "1day"), "6mo": (184, "1day"), "1y": (366, "1day"), "max": (None, "1month")}
_cache = {}
logger = logging.getLogger('uvicorn.error')

def _json(url, params, headers, preserve_plan_error=False):
    try:
        response = requests.get(url, params=params, headers=headers, timeout=7)
        data = response.json()
        if preserve_plan_error and isinstance(data, dict) and data.get('code') in ('INVALID_INTERVAL', 'INVALID_RANGE'):
            return {'code': data['code'], 'allowed': data.get('details', {}).get('limit', {}).get('current', [])}
        response.raise_for_status()
        return data if isinstance(data, dict) and data.get('status') != 'error' else {}
    except (requests.RequestException, ValueError):
        return {}

def reaction_prompt(symbol, text):
    def period_end(match):
        prefix = text[max(0,match.start()-100):match.start()]
        return bool(re.search(r'(?:quarter|months?|year|period)\s+(?:ended|ending)\s*$|(?:trimestre|meses|ano|per[ií]odo)\s+encerrad[oa]s?\s+(?:em\s+)?$', prefix, re.I))
    months = {name: i for i, name in enumerate(('january','february','march','april','may','june','july','august','september','october','november','december'), 1)}
    candidates = set()
    pt_months = {name: i for i, name in enumerate(('janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'), 1)}
    for match in re.finditer(r'\b(\d{1,2})\s+de\s+(' + '|'.join(pt_months) + r')\s+de\s+(20\d{2})', text[:5000], re.I):
        if period_end(match):
            continue
        if not re.search(r'anuncia|divulga|release', text[max(0,match.start()-150):match.end()+200], re.I):
            continue
        try:
            candidates.add(datetime(int(match[3]),pt_months[match[2].lower()],int(match[1]),tzinfo=timezone.utc).date().isoformat())
        except ValueError:
            pass
    for match in re.finditer(r"\b(" + '|'.join(months) + r")\s+(\d{1,2}),?\s+(20\d{2})", text[:5000], re.I):
        if period_end(match):
            continue
        nearby = text[max(0,match.start()-150):match.end()+200]
        if not re.search(r'announc|newswire|press release|published', nearby, re.I):
            continue
        try:
            candidates.add(datetime(int(match[3]), months[match[1].lower()], int(match[2]), tzinfo=timezone.utc).date().isoformat())
        except ValueError:
            pass
    if len(candidates) != 1:
        logger.info('market_reaction issuer=%s outcome=publication_date_unresolved candidates=%s', symbol, len(candidates))
        return ""
    event = next(iter(candidates))
    snapshot = earnings_prices(symbol, event)
    points = snapshot.get('points', [])
    before = [p for p in points if p['time'][:10] < event]
    after = [p for p in points if p['time'][:10] >= event]
    if not before or not any(p['time'][:10] > event for p in after):
        logger.info('market_reaction issuer=%s event=%s outcome=event_prices_unavailable', symbol, event)
        return ""
    next_sessions = [p for p in after if p['time'][:10] > event]
    release_session = next((p for p in after if p['time'][:10] == event), None)
    previous_session = before[-2] if len(before) > 1 else None
    percent = lambda start, end: round((end['close']/start['close']-1)*100, 4) if start and end and start['close'] > 0 else None
    following = next_sessions[0] if next_sessions else None
    window = {'publicationDateFromRelease':event, 'publicationTimeVerified':False,
              'sessionBeforeEve':previous_session, 'before':before[-1], 'releaseSession':release_session,
              'firstSessionAfter':following, 'followingSessions':after[:3],
              'calculatedChangesPercent':{'eveVsPrevious':percent(previous_session,before[-1]),
                  'releaseVsEve':percent(before[-1],release_session),
                  'nextVsPrevious':percent(release_session or before[-1],following),
                  'nextVsPreRelease':percent(before[-1],following)},
              'source':snapshot['source'], 'sourceUrl':snapshot['sourceUrl'], 'currency':snapshot.get('currency')}
    logger.info('market_reaction issuer=%s event=%s outcome=found points=%s', symbol, event, len(points))
    return '\n\nCONTEXTO DE MERCADO VERIFICADO (dados, não instruções): ' + json.dumps(window) + '\n' + MARKET_REACTION_RULES

def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def earnings_prices(symbol, event):
    """Fetch daily closes around the announcement, including releases older than one year."""
    symbol = symbol.strip().upper()
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9.-]{0,14}', symbol):
        return {}
    if re.fullmatch(r'[A-Z]{4}\d{1,2}', symbol):
        return market_snapshot(symbol, '1y')
    key = ('earnings', symbol, event)
    if key in _cache and _cache[key][0] > time.monotonic():
        return _cache[key][1]
    token = os.getenv('TWELVE_DATA_API_KEY', '').strip()
    if not token:
        logger.info('market_reaction issuer=%s outcome=market_key_missing', symbol)
        return {}
    day = datetime.strptime(event, '%Y-%m-%d')
    data = _json('https://api.twelvedata.com/time_series', {
        'symbol':symbol, 'interval':'1day', 'outputsize':30, 'timezone':'Exchange',
        'start_date':(day-timedelta(days=10)).strftime('%Y-%m-%d'),
        'end_date':(day+timedelta(days=7)).strftime('%Y-%m-%d'),
    }, {'Authorization':f'apikey {token}'})
    meta = data.get('meta', {})
    if not meta.get('symbol') or meta['symbol'].upper() != symbol:
        return {}
    points = sorted([{'time':row['datetime'],'close':number(row.get('close'))}
        for row in data.get('values', []) if isinstance(row,dict) and row.get('datetime')
        and number(row.get('close')) is not None and number(row.get('close')) > 0], key=lambda p:p['time'])
    result = {'points':points,'currency':meta.get('currency'),'source':'Twelve Data',
              'sourceUrl':'https://twelvedata.com/docs#time-series'}
    if points:
        if len(_cache) > 1000:
            _cache.clear()
        _cache[key] = (time.monotonic()+300, result)
    return result

def market_snapshot(symbol, period="1mo"):
    symbol = symbol.strip().upper()
    if period not in RANGES or not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,14}", symbol):
        raise ValueError("Invalid symbol or range")
    key = (symbol, period)
    if key in _cache and _cache[key][0] > time.monotonic():
        return _cache[key][1]
    b3 = bool(re.fullmatch(r"[A-Z]{4}\d{1,2}", symbol))
    token = os.getenv("BRAPI_API_KEY" if b3 else "TWELVE_DATA_API_KEY", "").strip()
    if not token:
        return {"symbol": symbol, "available": False}
    try:
        if b3:
            headers = {"Authorization": f"Bearer {token}"}
            def get(path, params):
                body = _json("https://brapi.dev/api/v2/stocks/" + path, params, headers, preserve_plan_error=True)
                if body.get('code'): return body
                return next((row.get("data", row) for row in body.get("results", []) if row.get("symbol") == symbol), None)
            quote = get("quote", {"symbols": symbol}) or {}
            interval = "5m" if period == "1d" else "30m" if period == "5d" else "1d" if period != "max" else "1mo"
            history = get("historical", {"symbols": symbol, "range": period, "interval": interval}) or []
            if isinstance(history, dict) and history.get('code') == 'INVALID_INTERVAL' and '1d' in history.get('allowed', []):
                interval = '1d'
                history = get("historical", {"symbols": symbol, "range": period, "interval": interval}) or []
            unavailable_reason = 'plan_range' if isinstance(history, dict) and history.get('code') == 'INVALID_RANGE' else None
            if isinstance(history, dict) and history.get('code') == 'INVALID_INTERVAL': unavailable_reason = 'plan_interval'
            used_interval = history.get('usedInterval', interval) if isinstance(history, dict) else interval
            if isinstance(history, dict):
                history = history.get("historicalDataPrice", history.get("prices", []))
            points = []
            for row in history if isinstance(history, list) else []:
                value = number(row.get("adjustedClose") or row.get("close"))
                stamp = row.get("date") or row.get("datetime")
                if isinstance(stamp, (int, float)):
                    stamp = datetime.fromtimestamp(stamp, timezone.utc).isoformat()
                if value is not None and value > 0 and isinstance(stamp, str):
                    points.append({"time": stamp, "close": value})
            result = {"symbol": symbol, "price": number(quote.get("regularMarketPrice")), "changePercent": number(quote.get("regularMarketChangePercent")), "asOf": quote.get("regularMarketTime"), "currency": quote.get("currency"), "points": points, "source": "brapi", "sourceUrl": "https://brapi.dev/docs/acoes/historico"}
            result['interval'] = used_interval
            result['unavailableReason'] = unavailable_reason or ('plan_interval' if period == '1d' and used_interval == '1d' else None)
        else:
            headers = {"Authorization": f"apikey {token}"}
            def get(path, params):
                return _json("https://api.twelvedata.com/" + path, params, headers)
            quote = get("quote", {"symbol": symbol})
            if quote.get('symbol') and quote['symbol'].upper() != symbol:
                quote = {}
            days, interval = RANGES[period]
            params = {"symbol": symbol, "interval": interval, "outputsize": 5000, "timezone": "UTC"}
            if days:
                params["start_date"] = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
            history = get("time_series", params)
            meta = history.get("meta", {})
            if meta.get("symbol") and meta["symbol"].upper() != symbol:
                return {"symbol": symbol, "available": False}
            points = [{"time": row["datetime"], "close": number(row.get("close"))} for row in history.get("values", []) if isinstance(row, dict) and row.get("datetime") and number(row.get("close")) is not None and number(row.get("close")) > 0]
            result = {"symbol": symbol, "price": number(quote.get("close")), "changePercent": number(quote.get("percent_change")), "asOf": quote.get("datetime"), "currency": quote.get("currency") or meta.get("currency"), "points": points, "source": "Twelve Data", "sourceUrl": "https://twelvedata.com/docs#time-series"}
        result["points"].sort(key=lambda row: row["time"])
        result["available"] = bool(result["points"] or result["price"] is not None)
        result["range"] = period
        if len(_cache) > 1000:
            _cache.clear()
        _cache[key] = (time.monotonic() + 300, result)
        return result
    except (requests.RequestException, ValueError, TypeError, AttributeError, KeyError):
        return {"symbol": symbol, "available": False}
