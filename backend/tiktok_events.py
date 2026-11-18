"""Minimal TikTok Events API delivery; money and account milestones are verified here."""
from datetime import timezone
from hashlib import sha256
import logging
import os
from time import time
from typing import Literal
from uuid import UUID
from threading import Lock
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict
import requests
import stripe

from account_limits import connection
from report_auth import require_report_user

router = APIRouter()
logger = logging.getLogger('uvicorn.error')
ORIGINS = {'https://finanalyser.com.br', 'https://www.finanalyser.com.br'}
PREMIUM_PAYMENT_LINK_IDS = {'plink_1SwWowJClb7vlD0oRzqoStWT', 'plink_1SwWpkJClb7vlD0o8f84AOs8'}
_views = {}
_view_lock = Lock()


def create_tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS tiktok_events (
        event_id TEXT PRIMARY KEY, sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
    cur.execute('''CREATE TABLE IF NOT EXISTS tiktok_rollout (
        id INTEGER PRIMARY KEY CHECK(id=1), started_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
    cur.execute('INSERT INTO tiktok_rollout(id) VALUES(1) ON CONFLICT DO NOTHING')


def deliver(event, event_id, properties, user, page, event_time=None):
    token = os.getenv('TIKTOK_EVENTS_API_TOKEN', '').strip()
    pixel = os.getenv('TIKTOK_PIXEL_ID', '').strip()
    if not token or not pixel:
        raise HTTPException(503, 'Advertising delivery unavailable')
    conn = connection()
    try:
        with conn, conn.cursor() as cur:
            # Serialize retries across processes; only persist after TikTok accepts the event.
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (int.from_bytes(sha256(event_id.encode()).digest()[:8], 'big', signed=True),))
            cur.execute('SELECT 1 FROM tiktok_events WHERE event_id=%s', (event_id,))
            if cur.fetchone():
                return
            payload = {'event_source': 'web', 'event_source_id': pixel, 'data': [{
                'event': event, 'event_id': event_id, 'event_time': event_time or int(time()),
                'user': user, 'page': {'url': page}, 'properties': properties}]}
            try:
                result = requests.post('https://business-api.tiktok.com/open_api/v1.3/event/track/',
                    headers={'Access-Token': token}, json=payload, timeout=8)
                result.raise_for_status()
                if result.json().get('code') != 0:
                    raise ValueError('Provider rejected event')
            except (requests.RequestException, ValueError):
                logger.warning('tiktok_delivery event=%s outcome=failed', event)
                raise HTTPException(503, 'Advertising delivery unavailable') from None
            cur.execute('INSERT INTO tiktok_events(event_id) VALUES(%s)', (event_id,))
        logger.info('tiktok_delivery event=%s outcome=accepted', event)
    finally:
        conn.close()


class EventInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    event: Literal['CompleteRegistration', 'FirstAnalysisCompleted', 'InitiateCheckout', 'ViewContent']
    event_id: UUID
    content: Literal['premium_pricing', 'public_report', 'monthly', 'yearly'] | None = None


@router.post('/api/conversions/tiktok/content')
def public_content(body: EventInput, request: Request):
    if request.headers.get('origin') not in ORIGINS or body.event != 'ViewContent' or body.content not in ('premium_pricing', 'public_report'):
        raise HTTPException(400, 'Invalid content event')
    ip = request.client.host if request.client else ''
    with _view_lock:
        now = int(time() // 60)
        if len(_views) > 10000:
            for key, value in list(_views.items()):
                if value[0] != now:
                    del _views[key]
        bucket, count = _views.get(ip, (now, 0))
        count = count + 1 if bucket == now else 1
        if count > 30 or len(_views) > 10000:
            raise HTTPException(429, 'Too many events')
        _views[ip] = (now, count)
    properties = {'contents': [{'content_id': body.content}]}
    deliver('ViewContent', str(body.event_id), properties,
        {'ip': ip, 'user_agent': request.headers.get('user-agent', '')[:1000]},
        'https://finanalyser.com.br/')
    return {'event': 'ViewContent', 'event_id': str(body.event_id), 'properties': properties}



def milestone(event, user):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT started_at FROM tiktok_rollout WHERE id=1')
            started = cur.fetchone()[0].timestamp()
            if event == 'FirstAnalysisCompleted':
                # historico.data_criacao is a TEXT column; cast so psycopg2 returns a datetime.
                cur.execute('SELECT MIN(CAST(data_criacao AS TIMESTAMPTZ)) FROM historico WHERE CAST(user_id AS TEXT)=%s', (str(user),))
                created = cur.fetchone()[0]
                if not created:
                    return None
                stamp = created.replace(tzinfo=timezone.utc).timestamp() if created.tzinfo is None else created.timestamp()
            else:
                try:
                    result = requests.get(os.getenv('PLATFORM_URL', 'https://finanalyser.com.br').rstrip('/') + '/api/account-plan',
                        headers={'Authorization': 'Bearer ' + user.token}, timeout=12)
                    result.raise_for_status()
                    account = result.json()
                    if account.get('user_id') != str(user):
                        raise ValueError('Wrong account')
                    stamp = account['created_at'] / 1000
                except (requests.RequestException, ValueError, KeyError, TypeError):
                    raise HTTPException(503, 'Registration verification unavailable') from None
            return int(stamp) if started <= stamp <= time() and time() - stamp < 86400 else None
    finally:
        conn.close()


@router.post('/api/conversions/tiktok')
def account_event(body: EventInput, request: Request, response: Response, user=Depends(require_report_user)):
    response.headers['Cache-Control'] = 'private, no-store'
    event_id = str(body.event_id)
    properties = {}
    stamp = None
    if body.event in ('CompleteRegistration', 'FirstAnalysisCompleted'):
        stamp = milestone(body.event, user)
        if stamp is None:
            return {'event': None}
        event_id = sha256(f'{body.event}:{user}'.encode()).hexdigest()
    elif body.event == 'InitiateCheckout':
        if body.content not in ('monthly', 'yearly'):
            raise HTTPException(400, 'Invalid plan')
        properties = {'currency': 'BRL', 'value': 290 if body.content == 'yearly' else 29,
                      'contents': [{'content_id': 'premium_' + body.content, 'quantity': 1}]}
    elif body.content not in ('premium_pricing', 'public_report'):
        raise HTTPException(400, 'Invalid content')
    else:
        properties = {'contents': [{'content_id': body.content}]}
    # No email, phone, ticker, query string or research content is forwarded.
    identity = {'external_id': sha256(str(user).encode()).hexdigest(),
                'user_agent': request.headers.get('user-agent', '')[:1000]}
    deliver(body.event, event_id, properties, identity, 'https://finanalyser.com.br/', stamp)
    return {'event': body.event, 'event_id': event_id, 'properties': properties}


@router.post('/api/conversions/tiktok/stripe')
async def stripe_purchase(request: Request):
    secret = os.getenv('STRIPE_TIKTOK_WEBHOOK_SECRET', '')
    if not secret:
        raise HTTPException(503, 'Payment verification unavailable')
    try:
        event = stripe.Webhook.construct_event(await request.body(), request.headers.get('stripe-signature', ''), secret)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, 'Invalid signature') from None
    return await asyncio.to_thread(verified_purchase, event)


def verified_purchase(event):
    if event['type'] not in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        return {'received': True}
    session = event['data']['object']
    if (event.get('livemode') is not True or session.get('status') != 'complete' or session.get('payment_status') != 'paid'
            or session.get('mode') != 'subscription' or session.get('currency') != 'brl'
            or type(session.get('amount_total')) is not int or session['amount_total'] <= 0
            or session.get('payment_link') not in PREMIUM_PAYMENT_LINK_IDS
            or not str(session.get('client_reference_id', '')).startswith('user_')):
        return {'received': True}
    deliver('Purchase', sha256(('tiktok-purchase:' + session['id']).encode()).hexdigest(),
        {'currency': 'BRL', 'value': session['amount_total'] / 100},
        {'external_id': sha256(session['client_reference_id'].encode()).hexdigest()},
        'https://finanalyser.com.br/', event['created'])
    return {'received': True}
