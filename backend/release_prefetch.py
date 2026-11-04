"""Refresh public releases in the background, without generating or charging analyses."""
from datetime import datetime, timezone
import logging
import os
from threading import Event, Thread

from psycopg2 import Error as DatabaseError
from database import get_db_connection
from release_pipeline import fetch_release, ReleaseError, issuer_identity, VERSION

stop = Event()
logger = logging.getLogger('uvicorn.error')
INITIAL = ('MSFT','NVDA','AAPL','GOOGL','AMZN','META','PETR4','WEGE3','VIVA3')


def seed_period(symbol, now):
    end = issuer_identity(symbol).get('fiscal_year_end') or '1231'
    month = int(end[:2]) if len(end) == 4 and end.isdigit() and 1 <= int(end[:2]) <= 12 else 12
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
                return
            cur.execute('''SELECT symbol,fiscal_year,fiscal_quarter FROM official_release_cache
                WHERE version<>%s OR checked_at<NOW()-INTERVAL '1 hour' ORDER BY checked_at LIMIT 12''', (VERSION,))
            tasks = cur.fetchall()
            if not tasks:
                cur.execute('SELECT COUNT(*) FROM official_release_cache')
                if cur.fetchone()[0] == 0:
                    now = datetime.now(timezone.utc)
                    tasks = [(symbol, *seed_period(symbol, now)) for symbol in INITIAL]
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


def _run():
    if stop.wait(45):
        return
    while not stop.is_set():
        try:
            refresh_once()
        except (DatabaseError, ValueError, RuntimeError):
            logger.warning('release_prefetch outcome=unavailable')
        if stop.wait(3600):
            break


def start():
    if os.getenv('RELEASE_PREFETCH_ENABLED', os.getenv('RENDER','')).lower() not in ('1','true'):
        return
    stop.clear()
    Thread(target=_run, name='official-release-prefetch', daemon=True).start()
