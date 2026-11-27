"""Refresh public releases in the background, without generating or charging analyses."""
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from threading import Event, Thread

from psycopg2 import Error as DatabaseError
from database import get_db_connection
from agents.cvm_ipe import OFF_CALENDAR, latest_released
from company_search import _load
from release_pipeline import BRAZIL_ABROAD, fetch_release, ReleaseError, issuer_identity, VERSION

stop = Event()
logger = logging.getLogger('uvicorn.error')
def sp500_batteries():
    return json.loads((Path(__file__).parent / 'data' / 'sp500.json').read_text(encoding='utf-8'))['batteries']


def b3_universe():
    return _load('b3')


INITIAL = ('MSFT','NVDA','AAPL','GOOGL','AMZN','META','PETR4','WEGE3','VIVA3')


def seed_period(symbol, now):
    if symbol in OFF_CALENDAR:
        return latest_released(symbol, now.date())
    end = issuer_identity(symbol).get('fiscal_year_end') or '1231'
    month = int(end[:2]) if len(end) == 4 and end.isdigit() and 1 <= int(end[:2]) <= 12 else 12
    if month == 1 and int(end[2:]) <= 7:
        month = 12  # 52/53-week years ending in the first days of January (Domino's) belong to the prior year.
    fiscal_year = now.year + (now.month > month)
    current_quarter = ((now.month - month - 1) % 12) // 3 + 1
    return (fiscal_year, current_quarter - 1) if current_quarter > 1 else (fiscal_year - 1, 4)


def refresh_once(connection=get_db_connection):
    conn = connection()
    try:
        with conn.cursor() as cur:
            # A session lock prevents every web instance from starting its own refresh batch.
            cur.execute('SELECT pg_try_advisory_lock(20261104, 7201)')
            if not cur.fetchone()[0]:
                return False
            cur.execute('''SELECT symbol,fiscal_year,fiscal_quarter FROM official_release_cache
                WHERE version<>%s OR checked_at<NOW()-INTERVAL '1 hour' ORDER BY status='found', checked_at LIMIT 30''', (VERSION,))
            tasks = cur.fetchall()
            if not tasks:
                cur.execute('SELECT COUNT(*) FROM official_release_cache')
                if cur.fetchone()[0] == 0:
                    now = datetime.now(timezone.utc)
                    tasks = [(symbol, *seed_period(symbol, now)) for symbol in INITIAL]
            # Failures are rechecked first; each batch also adds IBOV/SMLL companies never checked, so official-source coverage is tested across B3.
            cur.execute('SELECT DISTINCT symbol,fiscal_year,fiscal_quarter FROM official_release_cache')
            pairs = {tuple(row) for row in cur.fetchall()}
            known = {row[0] for row in pairs}
            today = datetime.now(timezone.utc)
            # Off-calendar issuers also need their latest labelled quarter, which the calendar seed never asks for.
            missing = [symbol for symbol in dict.fromkeys([*(item['ticker'] for item in b3_universe()), *BRAZIL_ABROAD])
                       if symbol not in known or (symbol in OFF_CALENDAR and (symbol, *latest_released(symbol, today.date())) not in pairs)][:8]
            # S&P 500 coverage runs in ten batteries; each run adds the first battery that still has unchecked companies.
            battery = next(([symbol for symbol in group if symbol.replace('.', '-') not in known and symbol not in known]
                            for group in sp500_batteries() if any(s not in known and s.replace('.', '-') not in known for s in group)), [])
            missing += battery
            if missing:
                now = datetime.now(timezone.utc)
                tasks = [(symbol, *seed_period(symbol, now)) for symbol in missing] + list(tasks)[:30 - min(len(missing), 30)]
        for symbol, year, quarter in tasks:
            if stop.is_set():
                break
            try:
                fetch_release(symbol, year, quarter, connection=connection, refresh=True, allow_web=False)
            except (ReleaseError, ValueError, TimeoutError):
                logger.info('release_prefetch issuer=%s year=%s quarter=%s outcome=not_ready',symbol,year,quarter)
            # Keep SEC and RI queries paced; this worker never calls an analysis model.
            if stop.wait(2):
                break
    finally:
        conn.close()  # Releases the session advisory lock even on failure.
    return bool(missing)


def _run():
    if stop.wait(45):
        return
    while not stop.is_set():
        pending = False
        try:
            pending = refresh_once()
        except (DatabaseError, ValueError, RuntimeError):
            logger.warning('release_prefetch outcome=unavailable')
        # While IBOV/SMLL companies remain unchecked, run every 5 minutes so the first full pass ends within hours.
        if stop.wait(300 if pending else 3600):
            break


def start():
    if os.getenv('RELEASE_PREFETCH_ENABLED', os.getenv('RENDER','')).lower() not in ('1','true'):
        return
    stop.clear()
    Thread(target=_run, name='official-release-prefetch', daemon=True).start()
