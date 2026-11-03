"""Bounded, cached market data. Never infer that a recent move was an earnings reaction."""
from datetime import datetime, timedelta, timezone
import math
from functools import lru_cache
from threading import Lock
import os
import re
import time
import requests
import json
import logging
from zoneinfo import ZoneInfo
from psycopg2 import Error as DatabaseError
from database import get_db_connection
from agents.prompt_builder import MARKET_REACTION_RULES

RANGES = {"1d": (1, "5min"), "5d": (7, "30min"), "1mo": (31, "1day"), "6mo": (184, "1day"), "1y": (366, "1day"), "max": (None, "1month")}
_cache = {}
logger = logging.getLogger('uvicorn.error')


class MarketDataUnavailable(RuntimeError):
    pass


def create_tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS earnings_price_cache (
        symbol TEXT NOT NULL, event_date DATE NOT NULL, payload JSONB NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(symbol,event_date))''')


def stored_earnings_prices(symbol, event, payload=None):
    if not os.getenv('DATABASE_URL'):
        return {}
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if payload is None:
                cur.execute("SELECT payload FROM earnings_price_cache WHERE symbol=%s AND event_date=%s AND updated_at>NOW()-INTERVAL '30 days'", (symbol,event))
                row = cur.fetchone()
                return row[0] if row and isinstance(row[0],dict) else {}
            cur.execute('''INSERT INTO earnings_price_cache(symbol,event_date,payload) VALUES(%s,%s,%s)
                ON CONFLICT(symbol,event_date) DO UPDATE SET payload=EXCLUDED.payload,updated_at=NOW()''', (symbol,event,json.dumps(payload)))
        conn.commit()
    except (DatabaseError, ValueError, TypeError):
        logger.warning('market_reaction issuer=%s event=%s outcome=price_cache_unavailable', symbol, event)
    finally:
        if conn:
            conn.close()
    return {}


def complete_event_prices(snapshot, event):
    points = snapshot.get('points', [])
    return any(p['time'][:10]<event for p in points) and any(p['time'][:10]>event for p in points)

def _json(url, params, headers, preserve_plan_error=False):
    try:
        response = requests.get(url, params=params, headers=headers, timeout=7)
        data = response.json()
        if preserve_plan_error and isinstance(data, dict) and data.get('code') in ('INVALID_INTERVAL', 'INVALID_RANGE'):
            return {'code': data['code'], 'allowed': data.get('details', {}).get('limit', {}).get('current', [])}
        response.raise_for_status()
        if isinstance(data,dict) and data.get('status') != 'error':
            return data
        code = data.get('code') if isinstance(data,dict) else None
        logger.info('market_provider endpoint=%s outcome=error code=%s', url.rsplit('/',1)[-1], code if isinstance(code,int) else 'invalid_response')
        return {}
    except requests.HTTPError as exc:
        logger.info('market_provider endpoint=%s outcome=http_error status=%s', url.rsplit('/',1)[-1], exc.response.status_code if exc.response is not None else 'unknown')
        return {}
    except (requests.RequestException, ValueError):
        logger.info('market_provider endpoint=%s outcome=request_failed', url.rsplit('/',1)[-1])
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
    if not points:
        raise MarketDataUnavailable('Event prices unavailable')
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
    logger.info('market_reaction issuer=%s event=%s outcome=found points=%s source=%s', symbol, event, len(points), snapshot.get('source'))
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
    key = ('earnings', symbol, event)
    if key in _cache and _cache[key][0] > time.monotonic():
        return _cache[key][1]
    stored = stored_earnings_prices(symbol,event)
    if complete_event_prices(stored,event):
        _cache[key] = (time.monotonic()+86400,stored)
        return stored
    result = fetch_earnings_prices(symbol,event)
    if complete_event_prices(result,event):
        if len(_cache) > 1000:
            _cache.clear()
        _cache[key] = (time.monotonic()+86400,result)
        stored_earnings_prices(symbol,event,result)
    return result


def fetch_earnings_prices(symbol,event):
    day = datetime.strptime(event, '%Y-%m-%d')
    if re.fullmatch(r'[A-Z]{4}\d{1,2}', symbol):
        snapshot = market_snapshot(symbol,'1y')
        return snapshot if complete_event_prices(snapshot,event) else yahoo_earnings_prices(symbol+'.SA',day)
    token = os.getenv('TWELVE_DATA_API_KEY', '').strip()
    if not token:
        logger.info('market_reaction issuer=%s outcome=market_key_missing', symbol)
        return yahoo_earnings_prices(symbol,day)
    data = _json('https://api.twelvedata.com/time_series', {
        'symbol':symbol, 'interval':'1day', 'outputsize':30, 'timezone':'Exchange',
        'start_date':(day-timedelta(days=10)).strftime('%Y-%m-%d'),
        'end_date':(day+timedelta(days=7)).strftime('%Y-%m-%d'),
    }, {'Authorization':f'apikey {token}'})
    meta = data.get('meta', {})
    if not meta.get('symbol') or meta['symbol'].upper() != symbol:
        return yahoo_earnings_prices(symbol,day)
    points = sorted([{'time':row['datetime'],'close':number(row.get('close'))}
        for row in data.get('values', []) if isinstance(row,dict) and row.get('datetime')
        and number(row.get('close')) is not None and number(row.get('close')) > 0], key=lambda p:p['time'])
    result = {'points':points,'currency':meta.get('currency'),'source':'Twelve Data',
              'sourceUrl':'https://twelvedata.com/docs#time-series'}
    return result if complete_event_prices(result,event) else yahoo_earnings_prices(symbol,day) or result


def yahoo_earnings_prices(symbol,day):
    data = _json('https://query1.finance.yahoo.com/v8/finance/chart/'+symbol, {
        'period1':int((day.replace(tzinfo=timezone.utc)-timedelta(days=10)).timestamp()),
        'period2':int((day.replace(tzinfo=timezone.utc)+timedelta(days=8)).timestamp()),'interval':'1d',
    }, {'User-Agent':'FinAnalyzer/1.0 contact@finanalyser.com.br'})
    rows = (data.get('chart') or {}).get('result') or []
    if not rows or rows[0].get('meta',{}).get('symbol','').upper()!=symbol:
        return {}
    row=rows[0]
    try:
        zone=ZoneInfo(row['meta']['exchangeTimezoneName'])
        closes=row['indicators']['quote'][0]['close']
        points=[{'time':datetime.fromtimestamp(stamp,zone).date().isoformat(),'close':number(close)}
                for stamp,close in zip(row.get('timestamp',[]),closes) if number(close) is not None and number(close)>0]
    except (KeyError,IndexError,TypeError,ValueError):
        return {}
    return {'points':sorted(points,key=lambda p:p['time']),'currency':row['meta'].get('currency'),
            'source':'Yahoo Finance','sourceUrl':'https://finance.yahoo.com/quote/'+symbol+'/history/'}

@lru_cache(maxsize=1024)
def _market_lock(symbol):
    return Lock()


def _cached_quote(provider, symbol, fetch):
    key = (provider, symbol, "quote")
    cached = _cache.get(key)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    quote = fetch() or {}
    price = number(quote.get("regularMarketPrice") if provider == "brapi" else quote.get("close"))
    _cache[key] = (time.monotonic() + (60 if price is not None and price > 0 else 15), quote)
    return quote


def yahoo_market_snapshot(symbol, period):
    interval = {"1d": "5m", "5d": "30m", "max": "1mo"}.get(period, "1d")
    payload = _json("https://query1.finance.yahoo.com/v8/finance/chart/" + symbol,
                    {"range": period, "interval": interval},
                    {"User-Agent": "FinAnalyzer/1.0 contact@finanalyser.com.br"})
    rows = (payload.get("chart") or {}).get("result") or []
    if not rows or rows[0].get("meta", {}).get("symbol", "").upper() != symbol:
        return {}
    row, meta = rows[0], rows[0].get("meta", {})
    try:
        zone = ZoneInfo(meta.get("exchangeTimezoneName") or "UTC")
        closes = row["indicators"]["quote"][0]["close"]
        points = [{"time": datetime.fromtimestamp(stamp, zone).isoformat(), "close": number(close)}
                  for stamp, close in zip(row.get("timestamp", []), closes)
                  if number(close) is not None and number(close) > 0]
    except (KeyError, IndexError, TypeError, ValueError):
        points = []
    price, previous = number(meta.get("regularMarketPrice")), number(meta.get("previousClose") or meta.get("chartPreviousClose"))
    return {"symbol": symbol, "price": price, "changePercent": (price / previous - 1) * 100 if price and previous else None,
            "asOf": meta.get("regularMarketTime"), "currency": meta.get("currency"), "points": points,
            "interval": interval, "source": "Yahoo Finance", "sourceUrl": "https://finance.yahoo.com/quote/" + symbol + "/history/"}


def market_snapshot(symbol, period="1mo", quote_only=False):
    symbol = symbol.strip().upper()
    if period not in RANGES or not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,14}", symbol):
        raise ValueError("Invalid symbol or range")
    # The sidebar and result can request the same issuer at the same time.
    with _market_lock(symbol):
        return _market_snapshot(symbol, period, quote_only)


def _market_snapshot(symbol, period, quote_only=False):
    key = (symbol, "quote" if quote_only else period)
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
            quote = _cached_quote("brapi", symbol, lambda: get("quote", {"symbols": symbol}))
            interval = "5m" if period == "1d" else "30m" if period == "5d" else "1d" if period != "max" else "1mo"
            history = [] if quote_only else get("historical", {"symbols": symbol, "range": period, "interval": interval}) or []
            if isinstance(history, dict) and history.get('code') == 'INVALID_INTERVAL' and '1d' in history.get('allowed', []):
                interval = '1d'
                history = [] if quote_only else get("historical", {"symbols": symbol, "range": period, "interval": interval}) or []
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
            quote = _cached_quote("twelve", symbol, lambda: get("quote", {"symbol": symbol}))
            if quote.get('symbol') and quote['symbol'].upper() != symbol:
                quote = {}
            days, interval = RANGES[period]
            params = {"symbol": symbol, "interval": interval, "outputsize": 5000, "timezone": "UTC"}
            if days:
                params["start_date"] = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
            history = {} if quote_only else get("time_series", params)
            meta = history.get("meta", {})
            if meta.get("symbol") and meta["symbol"].upper() != symbol:
                return {"symbol": symbol, "available": False}
            points = [{"time": row["datetime"], "close": number(row.get("close"))} for row in history.get("values", []) if isinstance(row, dict) and row.get("datetime") and number(row.get("close")) is not None and number(row.get("close")) > 0]
            result = {"symbol": symbol, "price": number(quote.get("close")), "changePercent": number(quote.get("percent_change")), "asOf": quote.get("datetime"), "currency": quote.get("currency") or meta.get("currency"), "points": points, "source": "Twelve Data", "sourceUrl": "https://twelvedata.com/docs#time-series"}
        if not b3 and (result["price"] is None or (not quote_only and len(result["points"]) < 2)):
            fallback = yahoo_market_snapshot(symbol, "1d" if quote_only else period)
            if fallback and (fallback.get("price") is not None or fallback.get("points")):
                # Keep each snapshot's quote, history and attribution from one source.
                if (fallback.get("price") is not None and len(fallback.get("points", [])) > 1) or (result["price"] is None and not result["points"]):
                    result = fallback
        result["points"].sort(key=lambda row: row["time"])
        if result["price"] is None and result["points"]:
            result["price"] = result["points"][-1]["close"]
            result["asOf"] = result["points"][-1]["time"]
        if quote_only:
            result["points"] = []
        result["available"] = bool(result["points"] or result["price"] is not None)
        result["range"] = period
        if len(_cache) > 1000:
            _cache.clear()
        _cache[key] = (time.monotonic() + ((60 if quote_only else 300) if result["available"] else 15), result)
        return result
    except (requests.RequestException, ValueError, TypeError, AttributeError, KeyError):
        return {"symbol": symbol, "available": False}
