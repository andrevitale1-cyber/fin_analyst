"""Optional signed OpenBot discovery; returned URLs remain untrusted candidates."""
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import socket
import time
from urllib.parse import urljoin, urlparse
from uuid import uuid4, UUID

import requests
from fastapi import APIRouter, Header, HTTPException, Request
from psycopg2 import Error as DatabaseError

from database import get_db_connection

router = APIRouter()
logger = logging.getLogger('uvicorn.error')
EVENT = 'finanalyser.document.search'


def create_tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS openbot_document_requests (
        id TEXT PRIMARY KEY, request_key TEXT NOT NULL, token_hash TEXT NOT NULL,
        query TEXT NOT NULL, expires_at DOUBLE PRECISION NOT NULL,
        result TEXT, created_at DOUBLE PRECISION NOT NULL)''')
    cur.execute('CREATE INDEX IF NOT EXISTS openbot_document_request_key ON openbot_document_requests(request_key)')


def signed_headers(body, delivery_id, secret, timestamp=None):
    timestamp = str(int(time.time()) if timestamp is None else timestamp)
    signature = hmac.new(secret.encode(), timestamp.encode() + b'.' + delivery_id.encode() + b'.' + body,
                         hashlib.sha256).hexdigest()
    return {'Content-Type': 'application/json', 'X-OpenBot-Timestamp': timestamp,
            'X-OpenBot-Delivery-Id': delivery_id, 'X-OpenBot-Signature': 'sha256=' + signature}


def _read(request_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT result FROM openbot_document_requests WHERE id=%s', (request_id,))
            row = cur.fetchone()
            return json.loads(row[0]) if row and row[0] else None
    finally:
        conn.close()


def discover(symbol, year, quarter, document_type):
    url, secret = os.getenv('OPENBOT_WEBHOOK_URL', ''), os.getenv('OPENBOT_WEBHOOK_SECRET', '')
    callback = os.getenv('OPENBOT_CALLBACK_ORIGIN', '').rstrip('/')
    if not url or not secret or not callback:
        return None
    if urlparse(url).scheme != 'https' or urlparse(callback).scheme != 'https':
        return None
    query = {'symbol': symbol, 'fiscal_year': year, 'fiscal_quarter': quarter, 'document_type': document_type}
    key = json.dumps(query, sort_keys=True)
    request_id, token = str(uuid4()), secrets.token_urlsafe(32)
    now = time.time()
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Share one pending discovery across workers, without holding a connection while the bot runs.
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big', signed=True),))
            cur.execute('DELETE FROM openbot_document_requests WHERE expires_at < %s', (now - 86400,))
            cur.execute('SELECT id FROM openbot_document_requests WHERE request_key=%s AND expires_at>%s ORDER BY created_at DESC LIMIT 1', (key, now))
            row = cur.fetchone()
            owner = not row
            if row:
                request_id = row[0]
            else:
                cur.execute('INSERT INTO openbot_document_requests(id,request_key,token_hash,query,expires_at,created_at) VALUES(%s,%s,%s,%s,%s,%s)',
                            (request_id, key, hashlib.sha256(token.encode()).hexdigest(), key, now + 600, now))
        conn.commit()
    finally:
        conn.close()
    if owner:
        data = {**query, 'request_id': request_id,
                'callback_url': callback + '/api/document-search/openbot/result/' + request_id,
                'callback_token': token}
        body = json.dumps({'type': EVENT, 'data': data}, separators=(',', ':')).encode()
        try:
            response = requests.post(url, data=body, headers=signed_headers(body, request_id, secret), timeout=5, allow_redirects=False)
            accepted = response.status_code in (200, 202)
        except requests.RequestException:
            accepted = False
        if not accepted:
            logger.info('openbot_discovery issuer=%s outcome=relay_unavailable', symbol)
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute('UPDATE openbot_document_requests SET result=%s,expires_at=%s WHERE id=%s',
                                (json.dumps({'status': 'temporarily_unavailable'}), time.time() + 30, request_id))
                conn.commit()
            finally:
                conn.close()
            return None
    deadline = time.monotonic() + 70
    while time.monotonic() < deadline:
        result = _read(request_id)
        if result is not None:
            return result if result.get('status') == 'found' else None
        time.sleep(1)
    logger.info('openbot_discovery issuer=%s outcome=timeout', symbol)
    return None


@router.post('/api/document-search/openbot/result/{request_id}')
async def receive_result(request_id: str, request: Request, authorization: str = Header(default='')):
    try:
        UUID(request_id)
    except ValueError:
        raise HTTPException(404, 'Unknown request') from None
    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not 32 <= len(token) <= 128:
        raise HTTPException(401, 'Invalid callback token')
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 16384:
            raise HTTPException(413, 'Result too large')
    try:
        result = json.loads(body)
        if not isinstance(result, dict) or result.get('status') not in ('found', 'not_found', 'temporarily_unavailable'):
            raise ValueError()
        if result['status'] == 'found':
            parsed = urlparse(result.get('source_url', ''))
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or len(result['source_url']) > 2048:
                raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(422, 'Invalid result') from None
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT token_hash,query,expires_at,result FROM openbot_document_requests WHERE id=%s FOR UPDATE', (request_id,))
            row = cur.fetchone()
            if not row or not hmac.compare_digest(row[0], hashlib.sha256(token.encode()).hexdigest()):
                raise HTTPException(401, 'Invalid callback token')
            if row[2] < time.time():
                raise HTTPException(410, 'Request expired')
            query = json.loads(row[1])
            if any(result.get(field) != value for field, value in query.items()):
                raise HTTPException(422, 'Company, period or document type mismatch')
            # Store only the bounded public candidate, never arbitrary text or callback credentials.
            clean = {**query, 'status': result['status'], 'source_url': result.get('source_url', '')}
            if row[3] and json.loads(row[3]) != clean:
                raise HTTPException(409, 'Result already submitted')
            cur.execute('UPDATE openbot_document_requests SET result=%s WHERE id=%s', (json.dumps(clean), request_id))
        conn.commit()
    finally:
        conn.close()
    return {'accepted': True}


def fetch_document(fetcher, symbol, year, quarter, document_type):
    """Only download direct documents from known issuer/regulator hosts; never follow arbitrary links."""
    if os.getenv('OPENBOT_DISCOVERY_ENABLED') != '1':
        return None
    try:
        result = discover(symbol, year, quarter, document_type)
        if not result:
            return None
        from release_pipeline import issuer_identity, validate_document
        from agents.sec_fetcher import FetchedDocument, SECFetcher
        from openai_client import OpenAIClient
        from bs4 import BeautifulSoup
        identity = issuer_identity(symbol)
        allowed = {urlparse(fetcher.ir_urls.get(symbol, '')).hostname, *identity.get('domains', []),
                   'www.sec.gov', 'www.rad.cvm.gov.br', 'rad.cvm.gov.br', 'dados.cvm.gov.br'} - {None}
        url = result['source_url']
        for _ in range(4):
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.username or parsed.port not in (None, 443) or parsed.hostname not in allowed:
                return None
            addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
                return None
            with requests.get(url, headers=SECFetcher.headers, timeout=10, stream=True, allow_redirects=False) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers.get('Location', ''))
                    continue
                response.raise_for_status()
                content = bytearray()
                for chunk in response.iter_content(65536):
                    content.extend(chunk)
                    if len(content) > 20 * 1024 * 1024:
                        return None
                if content.startswith(b'%PDF-'):
                    text = OpenAIClient.extract_text(bytes(content))
                elif 'html' in response.headers.get('Content-Type', '').lower():
                    soup = BeautifulSoup(bytes(content), 'html.parser')
                    for tag in soup(['script', 'style', 'nav', 'footer']):
                        tag.decompose()
                    text = soup.get_text('\n', strip=True)[:180000]
                else:
                    return None
            document = FetchedDocument(url, 'RI / OpenBot', text=text)
            if document_type == 'release':
                validate_document(document, fetcher, identity, year, quarter)
            elif not fetcher._valid_transcript(text, symbol, year, quarter):
                return None
            return document
    except (requests.RequestException, DatabaseError, ValueError, OSError, RuntimeError):
        logger.info('openbot_discovery issuer=%s outcome=candidate_unusable', symbol)
    return None
