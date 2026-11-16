from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock
from uuid import uuid4
import asyncio
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from report_auth import SessionUser
from pydantic import ValidationError
import tiktok_events as tracking


@pytest.fixture
def database(monkeypatch):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    monkeypatch.setattr(tracking, 'connection', lambda: conn)
    return cur


def test_delivery_uses_seconds_and_persists_only_after_acceptance(database, monkeypatch):
    monkeypatch.setenv('TIKTOK_EVENTS_API_TOKEN', 'test-only')
    monkeypatch.setenv('TIKTOK_PIXEL_ID', 'test-pixel')
    database.fetchone.return_value = None
    post = Mock(return_value=Mock(json=lambda: {'code': 0}))
    monkeypatch.setattr(tracking.requests, 'post', post)
    tracking.deliver('Purchase', 'stable-id', {'currency': 'BRL', 'value': 29}, {'external_id': 'hash'}, 'https://finanalyser.com.br/')
    payload = post.call_args.kwargs['json']['data'][0]
    assert payload['event_time'] < 10**11 and payload['event_id'] == 'stable-id'
    assert 'INSERT INTO tiktok_events' in database.execute.call_args.args[0]
    post.return_value.json = lambda: {'code': 40001}
    database.reset_mock()
    with pytest.raises(HTTPException) as error:
        tracking.deliver('Purchase', 'other', {}, {}, 'https://finanalyser.com.br/')
    assert error.value.status_code == 503
    assert not any('INSERT INTO tiktok_events' in call.args[0] for call in database.execute.call_args_list)


def test_delivered_events_are_not_resent(database, monkeypatch):
    monkeypatch.setenv('TIKTOK_EVENTS_API_TOKEN', 'test-only')
    monkeypatch.setenv('TIKTOK_PIXEL_ID', 'test-pixel')
    database.fetchone.return_value = (1,)
    post = Mock()
    monkeypatch.setattr(tracking.requests, 'post', post)
    tracking.deliver('ViewContent', 'existing', {}, {}, 'https://finanalyser.com.br/')
    post.assert_not_called()


def test_first_analysis_requires_a_recent_saved_result(database):
    now = datetime.now(timezone.utc)
    database.fetchone.side_effect = [(now - timedelta(hours=2),), (None,)]
    assert tracking.milestone('FirstAnalysisCompleted', 'user_a') is None
    database.fetchone.side_effect = [(now - timedelta(hours=2),), (now - timedelta(days=1),)]
    assert tracking.milestone('FirstAnalysisCompleted', 'user_a') is None
    database.fetchone.side_effect = [(now - timedelta(hours=2),), (now - timedelta(minutes=1),)]
    assert tracking.milestone('FirstAnalysisCompleted', 'user_a') == int((now - timedelta(minutes=1)).timestamp())


def test_schema_does_not_accept_purchase_price_email_or_private_content():
    for patch in ({'event': 'Purchase'}, {'content': 'AAPL'}, {'email': 'private@example.com'}, {'value': 1}):
        with pytest.raises(ValidationError):
            tracking.EventInput(**({'event': 'ViewContent', 'event_id': str(uuid4()), 'content': 'public_report'} | patch))


def test_registration_uses_verified_account_creation_not_login_time(database, monkeypatch):
    now = datetime.now(timezone.utc)
    user = SessionUser('user_a', token='verified-session')
    database.fetchone.return_value = (now - timedelta(hours=1),)
    get = Mock(return_value=Mock(json=lambda: {'user_id': 'user_a', 'created_at': (now - timedelta(minutes=1)).timestamp() * 1000}))
    monkeypatch.setattr(tracking.requests, 'get', get)
    assert tracking.milestone('CompleteRegistration', user) is not None
    get.return_value.json = lambda: {'user_id': 'user_a', 'created_at': (now - timedelta(days=3)).timestamp() * 1000}
    assert tracking.milestone('CompleteRegistration', user) is None
    get.return_value.json = lambda: {'user_id': 'user_other', 'created_at': now.timestamp() * 1000}
    with pytest.raises(HTTPException): tracking.milestone('CompleteRegistration', user)


def test_public_content_only_accepts_production_generic_views(monkeypatch):
    deliver = Mock()
    monkeypatch.setattr(tracking, 'deliver', deliver)
    tracking._views.clear()
    request = Request({'type': 'http', 'headers': [(b'origin', b'https://finanalyser.com.br')], 'client': ('127.0.0.1', 123)})
    body = tracking.EventInput(event='ViewContent', event_id=uuid4(), content='public_report')
    tracking.public_content(body, request)
    assert deliver.call_args.args[2] == {'contents': [{'content_id': 'public_report'}]}
    forged = Request({'type': 'http', 'headers': [(b'origin', b'https://other.example')], 'client': ('127.0.0.1', 123)})
    with pytest.raises(HTTPException): tracking.public_content(body, forged)
    for _ in range(29): tracking.public_content(body, request)
    with pytest.raises(HTTPException) as error: tracking.public_content(body, request)
    assert error.value.status_code == 429


def test_purchase_uses_signed_stripe_actual_amount_and_stable_session_id(monkeypatch):
    deliver = Mock()
    monkeypatch.setattr(tracking, 'deliver', deliver)
    session = {'id': 'cs_live_test', 'status': 'complete', 'payment_status': 'paid', 'mode': 'subscription', 'currency': 'brl',
        'amount_total': 2500, 'payment_link': sorted(tracking.PREMIUM_PAYMENT_LINK_IDS)[0], 'client_reference_id': 'user_owner'}
    event = {'type': 'checkout.session.completed', 'livemode': True, 'created': 1794800000, 'data': {'object': session}}
    tracking.verified_purchase(event)
    args = deliver.call_args.args
    assert args[0] == 'Purchase' and args[2] == {'currency': 'BRL', 'value': 25}
    event['type'] = 'checkout.session.async_payment_succeeded'
    tracking.verified_purchase(event)
    assert deliver.call_args.args[1] == args[1]
    for patch in ({'payment_status': 'unpaid'}, {'status': 'open'}, {'amount_total': 0}, {'amount_total': True}, {'payment_link': 'other'}, {'mode': 'payment'}, {'client_reference_id': ''}):
        deliver.reset_mock()
        changed = event | {'data': {'object': session | patch}}
        tracking.verified_purchase(changed)
        deliver.assert_not_called()


def test_stripe_rejects_unsigned_requests(monkeypatch):
    monkeypatch.setenv('STRIPE_TIKTOK_WEBHOOK_SECRET', 'test-only')
    request = Mock(headers={})
    async def body(): return b'{}'
    request.body = body
    with pytest.raises(HTTPException) as error:
        asyncio.run(tracking.stripe_purchase(request))
    assert error.value.status_code == 400
