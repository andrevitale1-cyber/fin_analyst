import hashlib
from contextlib import contextmanager
import hmac
import json
from pathlib import Path
import sys
import time
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import openbot_documents as bot
from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument
from test_account_limits import database


@pytest.fixture
def callback(database, monkeypatch):
    db, factory = database
    db.execute('CREATE TABLE openbot_document_requests(id TEXT PRIMARY KEY,request_key TEXT,token_hash TEXT,query TEXT,expires_at REAL,result TEXT,created_at REAL)')
    class Connection:
        def __init__(self): self.conn = factory()
        @contextmanager
        def cursor(self):
            with self.conn.cursor() as cur:
                original = cur.execute
                cur.execute = lambda sql, params=(): original(sql.replace(' FOR UPDATE', ''), params)
                yield cur
        def commit(self): self.conn.commit()
        def close(self): self.conn.close()
    monkeypatch.setattr(bot, 'get_db_connection', Connection)
    query = dict(symbol='AMAT', fiscal_year=2026, fiscal_quarter=3, document_type='release')
    request_id, token = str(uuid4()), 'a' * 43
    db.execute('INSERT INTO openbot_document_requests VALUES(?,?,?,?,?,NULL,?)',
               (request_id, json.dumps(query, sort_keys=True), hashlib.sha256(token.encode()).hexdigest(), json.dumps(query), time.time() + 90, time.time()))
    db.commit()
    app = FastAPI(); app.include_router(bot.router)
    with TestClient(app) as client:
        yield client, '/api/document-search/openbot/result/' + request_id, {'Authorization': 'Bearer ' + token}, query, db


def test_signature_matches_exact_wire_bytes():
    body = b'{"type":"finanalyser.document.search","data":{"symbol":"AMAT"}}'
    headers = bot.signed_headers(body, 'job-1', 'whsec_test', timestamp=123)
    expected = hmac.new(b'whsec_test', b'123.job-1.' + body, hashlib.sha256).hexdigest()
    assert headers['X-OpenBot-Signature'] == 'sha256=' + expected
    assert bot.signed_headers(body + b' ', 'job-1', 'whsec_test', timestamp=123) != headers


def test_callback_auth_period_and_idempotency(callback):
    client, url, headers, query, db = callback
    payload = {**query, 'status': 'found', 'source_url': 'https://ir.appliedmaterials.com/static-files/release'}
    assert client.post(url, json=payload).status_code == 401
    assert client.post(url, json={**payload, 'symbol': 'NVDA'}, headers=headers).status_code == 422
    assert client.post(url, json={**payload, 'fiscal_quarter': 2}, headers=headers).status_code == 422
    assert client.post(url, json=payload, headers=headers).status_code == 200
    assert client.post(url, json=payload, headers=headers).status_code == 200
    assert client.post(url, json={**payload, 'source_url': 'https://example.com/a'}, headers=headers).status_code == 409
    assert client.post(url, content=b'x' * 16385, headers=headers).status_code == 413
    db.execute('UPDATE openbot_document_requests SET expires_at=0'); db.commit()
    assert client.post(url, json=payload, headers=headers).status_code == 410


def test_disabled_does_not_contact_bot_or_database(monkeypatch):
    monkeypatch.delenv('OPENBOT_WEBHOOK_URL', raising=False)
    monkeypatch.setattr(bot, 'get_db_connection', lambda: pytest.fail('Unexpected database access'))
    assert bot.discover('AMAT', 2026, 3, 'release') is None


def test_unknown_or_private_host_is_never_downloaded(monkeypatch):
    monkeypatch.setenv('OPENBOT_DISCOVERY_ENABLED', '1')
    import release_pipeline
    monkeypatch.setattr(release_pipeline, 'issuer_identity', lambda _: {'symbol': 'AMAT'})
    fetcher = AutoFetcher()
    fetcher.ir_urls['AMAT'] = 'https://ir.appliedmaterials.com/'
    monkeypatch.setattr(bot.requests, 'get', lambda *a, **kw: pytest.fail('Unsafe URL downloaded'))
    for url in ('https://127.0.0.1/a', 'https://attacker.example/a', 'https://ir.appliedmaterials.com:444/a'):
        monkeypatch.setattr(bot, 'discover', lambda *a: {'source_url': url})
        assert bot.fetch_document(fetcher, 'AMAT', 2026, 3, 'release') is None
    monkeypatch.setattr(bot, 'discover', lambda *a: {'source_url': fetcher.ir_urls['AMAT']})
    monkeypatch.setattr(bot.socket, 'getaddrinfo', lambda *a, **kw: [(2, 1, 6, '', ('127.0.0.1', 443))])
    assert bot.fetch_document(fetcher, 'AMAT', 2026, 3, 'release') is None


def test_discovery_deduplicates_and_sends_no_user_data(callback, monkeypatch):
    _, _, _, query, _ = callback
    monkeypatch.setenv('OPENBOT_WEBHOOK_URL', 'https://api.openbot.run/test')
    monkeypatch.setenv('OPENBOT_WEBHOOK_SECRET', 'whsec_test')
    monkeypatch.setenv('OPENBOT_CALLBACK_ORIGIN', 'https://api-finanalyzer.onrender.com')
    monkeypatch.setattr(bot, '_read', lambda _: {**query, 'status': 'found', 'source_url': 'https://ir.appliedmaterials.com/release'})
    post = MagicMock(return_value=MagicMock(status_code=202))
    monkeypatch.setattr(bot.requests, 'post', post)
    assert bot.discover('AMAT', 2026, 3, 'release')['status'] == 'found'
    assert post.call_count == 0  # Existing unexpired request is shared.
    assert bot.discover('AMAT', 2026, 2, 'release')['status'] == 'found'
    assert post.call_count == 1
    body = json.loads(post.call_args.kwargs['data'])
    assert set(body['data']) == {'symbol', 'fiscal_year', 'fiscal_quarter', 'document_type', 'request_id', 'callback_url', 'callback_token'}
    assert post.call_args.kwargs['allow_redirects'] is False


def test_release_prefetch_skips_bot_and_success_reuses_existing_document(monkeypatch):
    import agents.auto_fetcher as module
    fetcher = AutoFetcher()
    monkeypatch.setattr(fetcher, '_fetch_ir', lambda *a: None)
    monkeypatch.setattr(fetcher, '_fetch_equibles', lambda *a: None)
    lookup = MagicMock(return_value=FetchedDocument('https://example.com/release', 'RI', text='verified'))
    monkeypatch.setattr(module, 'fetch_openbot_document', lookup)
    fetcher.allow_web = False
    assert fetcher._fetch_b3('AMAT', 2026, 3) is None
    lookup.assert_not_called()
    fetcher.allow_web = True
    assert fetcher._fetch_b3('AMAT', 2026, 3).text == 'verified'
    lookup.assert_called_once_with(fetcher, 'AMAT', 2026, 3, 'release')


def test_offline_bot_does_not_leave_other_requests_waiting(callback, monkeypatch):
    monkeypatch.setenv('OPENBOT_WEBHOOK_URL', 'https://signal.openbot.run/test')
    monkeypatch.setenv('OPENBOT_WEBHOOK_SECRET', 'whsec_test')
    monkeypatch.setenv('OPENBOT_CALLBACK_ORIGIN', 'https://api-finanalyzer.onrender.com')
    post = MagicMock(return_value=MagicMock(status_code=503))
    monkeypatch.setattr(bot.requests, 'post', post)
    assert bot.discover('AMAT', 2026, 2, 'release') is None
    assert bot.discover('AMAT', 2026, 2, 'release') is None
    assert post.call_count == 1


def test_returned_document_still_passes_financial_validation(monkeypatch):
    import release_pipeline
    monkeypatch.setenv('OPENBOT_DISCOVERY_ENABLED', '1')
    monkeypatch.setattr(release_pipeline, 'issuer_identity', lambda _: {'symbol': 'AMAT', 'domains': ['ir.appliedmaterials.com']})
    monkeypatch.setattr(bot, 'discover', lambda *a: {'source_url': 'https://ir.appliedmaterials.com/release'})
    monkeypatch.setattr(bot.socket, 'getaddrinfo', lambda *a, **kw: [(2, 1, 6, '', ('8.8.8.8', 443))])
    response = MagicMock()
    response.__enter__.return_value = response
    response.is_redirect = False
    response.headers = {'Content-Type': 'text/html'}
    response.iter_content.return_value = [b'<html>AMAT Third quarter 2026 revenue net income 100</html>']
    monkeypatch.setattr(bot.requests, 'get', lambda *a, **kw: response)
    validate = MagicMock(side_effect=release_pipeline.ReleaseError('financial_content_missing'))
    monkeypatch.setattr(release_pipeline, 'validate_document', validate)
    assert bot.fetch_document(AutoFetcher(), 'AMAT', 2026, 3, 'release') is None
    validate.assert_called_once()
