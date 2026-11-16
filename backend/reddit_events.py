"""Verified SignUp and explicit Get started clicks for Reddit CAPI v3."""
from hashlib import sha256
from time import time
from uuid import UUID
from threading import Lock
from typing import Literal
import logging
import os
import requests
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, ConfigDict
from account_limits import connection
from report_auth import require_report_user
from tiktok_events import milestone, ORIGINS

router = APIRouter()
logger = logging.getLogger('uvicorn.error')
_clicks = {}
_lock = Lock()


def create_tables(cur):
    cur.execute("CREATE TABLE IF NOT EXISTS reddit_events (conversion_id TEXT PRIMARY KEY, sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    cur.execute("CREATE TABLE IF NOT EXISTS reddit_rollout (id INTEGER PRIMARY KEY CHECK(id=1), started_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    cur.execute("INSERT INTO reddit_rollout(id) VALUES(1) ON CONFLICT DO NOTHING")


class RedditEvent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    event: Literal['SignUp', 'AddToCart']
    event_id: UUID


def deliver(event, conversion_id, identity, stamp):
    token = os.getenv('REDDIT_CONVERSIONS_API_TOKEN', '').strip()
    if not token:
        raise HTTPException(503, 'Advertising delivery unavailable')
    conn = connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (int.from_bytes(sha256(conversion_id.encode()).digest()[:8], 'big', signed=True),))
            cur.execute('SELECT 1 FROM reddit_events WHERE conversion_id=%s', (conversion_id,))
            if cur.fetchone(): return
            payload = {'events': [{'event_at': int(stamp * 1000), 'action_source': 'WEBSITE',
                'event_source_url': 'https://finanalyser.com.br/',
                'type': {'tracking_type': 'SIGN_UP' if event == 'SignUp' else 'ADD_TO_CART'},
                'metadata': {'conversion_id': conversion_id}, 'user': identity}]}
            try:
                response = requests.post('https://ads-api.reddit.com/api/v3/pixels/a2_jzugsawslzp2/conversion_events',
                    headers={'Authorization': 'Bearer ' + token}, json=payload, timeout=8)
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict) or 'Successfully processed' not in str(result.get('data', {}).get('message', '')):
                    raise ValueError('Event not accepted')
            except (requests.RequestException, ValueError):
                logger.warning('reddit_delivery event=%s outcome=failed', event)
                raise HTTPException(503, 'Advertising delivery unavailable') from None
            cur.execute('INSERT INTO reddit_events(conversion_id) VALUES(%s)', (conversion_id,))
        logger.info('reddit_delivery event=%s outcome=accepted', event)
    finally:
        conn.close()


@router.post('/api/conversions/reddit')
def conversion(body: RedditEvent, request: Request):
    if request.headers.get('origin') not in ORIGINS:
        raise HTTPException(400, 'Invalid origin')
    stamp = time()
    conversion_id = sha256(('reddit-click:' + str(body.event_id)).encode()).hexdigest()
    identity = {'ip_address': request.client.host if request.client else '', 'user_agent': request.headers.get('user-agent', '')[:1000]}
    if body.event == 'SignUp':
        user = require_report_user(request.headers.get('authorization', ''))
        stamp = milestone('CompleteRegistration', user)
        conn = connection()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT started_at FROM reddit_rollout WHERE id=1')
                started = cur.fetchone()[0].timestamp()
        finally:
            conn.close()
        if stamp is None or stamp < started: return {'event': None}
        conversion_id = sha256(('reddit-signup:' + str(user)).encode()).hexdigest()
        identity['external_id'] = sha256(str(user).encode()).hexdigest()
    else:
        with _lock:
            minute = int(time() // 60)
            for key, value in list(_clicks.items()):
                if value[0] != minute: del _clicks[key]
            ip = identity['ip_address']
            count = _clicks.get(ip, (minute, 0))[1] + 1
            if count > 30 or len(_clicks) > 10000: raise HTTPException(429, 'Too many events')
            _clicks[ip] = (minute, count)
    deliver(body.event, conversion_id, identity, stamp)
    return {'event': body.event, 'conversionId': conversion_id}
