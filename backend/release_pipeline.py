"""Verified public releases, bounded supplements and durable caching before analysis starts."""
import base64
from dataclasses import asdict, replace
from functools import lru_cache
import hashlib
import json
import logging
import re
from threading import Lock
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from psycopg2 import Error as DatabaseError
import requests

from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument, SECFetcher
from agents.search_client import SearchError
from openai_client import OpenAIClient, OpenAIError

logger = logging.getLogger('uvicorn.error')
VERSION = 'verified-release-v2'


class ReleaseError(RuntimeError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def create_tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS official_release_cache (
        symbol TEXT NOT NULL, fiscal_year INTEGER NOT NULL, fiscal_quarter INTEGER NOT NULL,
        version TEXT NOT NULL, issuer JSONB, document JSONB, fingerprint TEXT,
        status TEXT NOT NULL, elapsed_ms INTEGER, checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY(symbol,fiscal_year,fiscal_quarter))''')


@lru_cache(maxsize=2048)
def _lock(symbol, year, quarter):
    return Lock()


_issuers = {}


def issuer_identity(symbol):
    cached = _issuers.get(symbol)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    result = {'symbol': symbol}
    try:
        if re.fullmatch(r'[A-Z]{4}\d{1,2}', symbol):
            query = base64.b64encode(json.dumps({'language':'pt-br','pageNumber':1,'pageSize':50,
                                                 'company':symbol[:4]}, separators=(',', ':')).encode()).decode()
            response = requests.get('https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/' + query, timeout=5)
            response.raise_for_status()
            payload = response.json()
            rows = [r for r in payload.get('results', []) if isinstance(r,dict) and r.get('issuingCompany') == symbol[:4]
                    and r.get('status') == 'A' and r.get('type') == '1']
            if len(rows) == 1 and payload.get('page', {}).get('totalPages') == 1:
                row = rows[0]
                result.update(market='B3', name=row['companyName'], cvm=row.get('codeCVM'), cnpj=row.get('cnpj'))
        else:
            rows = [r for r in SECFetcher()._catalog() if isinstance(r,dict) and r.get('ticker') == symbol.replace('.', '-')]
            if len(rows) == 1:
                result.update(market='US', name=rows[0]['title'], cik=str(int(rows[0]['cik_str'])).zfill(10))
                info = SECFetcher()._get(f'https://data.sec.gov/submissions/CIK{result["cik"]}.json').json()
                result['domains'] = [urlparse(info.get(field) or '').hostname for field in ('website','investorWebsite') if info.get(field)]
                result['fiscal_year_end'] = info.get('fiscalYearEnd')
    except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError):
        logger.info('release_identity issuer=%s outcome=catalog_unavailable', symbol)
    if len(_issuers) > 4096:
        _issuers.clear()
    _issuers[symbol] = (time.monotonic() + (86400 if result.get('name') else 60), result)
    return result


def validate_document(document, fetcher, identity, year, quarter):
    if not document or not fetcher._valid_url(document.url):
        raise ReleaseError('document_invalid')
    try:
        text = document.text or OpenAIClient.extract_text(document.pdf_bytes)
    except OpenAIError:
        raise ReleaseError('document_empty') from None
    if len(text.strip()) < 300:
        raise ReleaseError('document_empty')
    name = identity.get('name')
    parsed = urlparse(document.url)
    domains = {host for host in (urlparse(fetcher.ir_urls.get(identity['symbol'], '')).hostname, *identity.get('domains', [])) if host}
    official = (parsed.hostname in {'www.sec.gov','www.rad.cvm.gov.br','rad.cvm.gov.br','dados.cvm.gov.br'}
                or parsed.hostname in domains
                or (identity['symbol'] == 'SK HYNIX' and parsed.hostname == 'news.skhynix.com'))
    catalog = fetcher.mziq_catalogs.get(identity['symbol'])
    if catalog and parsed.hostname in ('api.mziq.com','filemanager-cdn.mziq.com'):
        official = catalog[0] in parsed.path.split('/')
    if not official:
        cdn = any(parsed.hostname == suffix or parsed.hostname.endswith('.'+suffix)
                  for suffix in ('mziq.com','q4cdn.com','cloudfront.net'))
        official = cdn and any(urlparse(source.get('url','')).hostname in domains for source in document.sources
                               if isinstance(source, dict) and source.get('name') == 'RI catalogue')
    if not official:
        raise ReleaseError('source_unverified')
    sec_path = re.match(r'/Archives/edgar/data/(\d+)/', parsed.path)
    if parsed.hostname == 'www.sec.gov' and sec_path and identity.get('cik') and int(sec_path[1]) != int(identity['cik']):
        raise ReleaseError('issuer_mismatch')
    verified = fetcher._release_company_matches(document, identity['symbol'])
    if not verified and name:
        normalized = SECFetcher._company_name(name)
        verified = bool(normalized and normalized in SECFetcher._company_name(text[:12000]))
    if not verified and identity.get('cnpj'):
        verified = identity['cnpj'] in re.sub(r'\D', '', text[:12000])
    if not verified:
        raise ReleaseError('issuer_mismatch')
    # Use the primary document's heading, never a supplemental comparison year.
    period_text = re.sub(r'(?<![A-Z0-9])([1-4])\s+([TQ])', r'\1\2', text[:4000].upper())
    period_text = re.sub(r'(?<![A-Z0-9])([1-4][TQ])\s*((?:\d\s+){1,3}\d)(?!\d)',
                         lambda m: m[1] + re.sub(r'\s+', '', m[2]), period_text)
    fiscal_proof = (parsed.hostname == 'www.sec.gov' and sec_path
                    and document.fiscal_year == year and document.fiscal_quarter == quarter
                    and document.issuer_cik == identity.get('cik')
                    and document.issuer_cik is not None and int(sec_path[1]) == int(document.issuer_cik))
    if not fiscal_proof and not fetcher._period_matches(period_text, year, quarter):
        raise ReleaseError('period_mismatch')
    primary_period = fetcher._transcript_period(period_text)
    if not fiscal_proof and primary_period and primary_period not in ((quarter, year), (quarter, year % 100)):
        raise ReleaseError('period_mismatch')
    metrics = re.findall(r'net income|operating income|revenues?|net sales|lucro|receita|margem|ebitda', text, re.I)
    if len(metrics) < 2 or not re.search(r'\d', text):
        raise ReleaseError('financial_content_missing')
    return text


def supplements(document, year, quarter):
    """Only follow financial exhibits inside this exact SEC filing, at most two."""
    parsed = urlparse(document.url)
    if parsed.hostname != 'www.sec.gov' or not parsed.path.startswith('/Archives/edgar/data/'):
        return document
    try:
        sec = SECFetcher()
        response = sec._get(document.url)
        if response.content.startswith(b'%PDF-'):
            return document
        soup = BeautifulSoup(response.text, 'html.parser')
        primary_text = document.text or soup.get_text('\n', strip=True)
        def period_end(text):
            match = re.search(r'\b(?:quarter|months)\s+ended\s+([A-Z]+)\s+(\d{1,2}),?\s+(20\d{2})', ' '.join(text[:6000].split()), re.I)
            return (match[1].lower(), int(match[2]), int(match[3])) if match else None
        end = period_end(primary_text)
        sources = [{'name':document.source,'url':document.url}]
        parts = [primary_text]
        directory = parsed.path.rsplit('/', 1)[0] + '/'
        seen = {document.url}
        for link in soup.find_all('a', href=True):
            if not re.search(r'99[-_.]?2|supplement|financial statements', link['href'] + link.get_text(), re.I):
                continue
            target = urlparse(urljoin(document.url, link['href']))._replace(fragment='').geturl()
            destination = urlparse(target)
            if (destination.scheme != 'https' or destination.hostname != parsed.hostname
                    or not destination.path.startswith(directory) or target in seen):
                continue
            if len(seen) >= 3:
                break
            seen.add(target)
            response = sec._get(target)
            if response.content.startswith(b'%PDF-'):
                text = OpenAIClient.extract_text(response.content)
            else:
                extra = BeautifulSoup(response.text, 'html.parser')
                for tag in extra(['script','style','nav','footer']): tag.decompose()
                text = extra.get_text('\n', strip=True)
            same_period = AutoFetcher._period_matches(text[:6000], year, quarter) or (end and period_end(text) == end)
            if not same_period or not SECFetcher.has_financial_results(text):
                continue
            parts.append('\n\nOFFICIAL SUPPLEMENT: ' + target + '\n' + text[:80000])
            sources.append({'name':'SEC financial supplement','url':target})
            if len(sources) == 3:
                break
        if len(parts) > 1:
            document = replace(document, pdf_bytes=b'', text='\n'.join(parts)[:180000], sources=sources)
        logger.info('release_supplements issuer_path=%s count=%d', directory, len(sources)-1)
    except (requests.RequestException, OpenAIError, ValueError, TypeError):
        logger.info('release_supplements outcome=unavailable')
    return document


def stored(connection, symbol, year, quarter, *, payload=None):
    if connection is None:
        return None
    conn = None
    try:
        conn = connection()
        with conn.cursor() as cur:
            if payload is None:
                cur.execute('''SELECT document,issuer FROM official_release_cache WHERE symbol=%s AND fiscal_year=%s
                    AND fiscal_quarter=%s AND version=%s AND status='found' AND checked_at>NOW()-INTERVAL '1 hour' ''',
                            (symbol, year, quarter, VERSION))
                row = cur.fetchone()
                return {**row[0], '_issuer':row[1] if len(row)>1 and isinstance(row[1],dict) else {}} if row and isinstance(row[0], dict) else None
            cur.execute('''INSERT INTO official_release_cache(symbol,fiscal_year,fiscal_quarter,version,issuer,document,fingerprint,status,elapsed_ms)
                VALUES(%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)
                ON CONFLICT(symbol,fiscal_year,fiscal_quarter) DO UPDATE SET version=EXCLUDED.version,issuer=EXCLUDED.issuer,
                document=COALESCE(EXCLUDED.document,official_release_cache.document),
                fingerprint=COALESCE(EXCLUDED.fingerprint,official_release_cache.fingerprint),status=EXCLUDED.status,
                elapsed_ms=EXCLUDED.elapsed_ms,checked_at=NOW()''',
                        (symbol, year, quarter, VERSION, json.dumps(payload.get('issuer', {})),
                         json.dumps(payload.get('document')), payload.get('fingerprint'),payload['status'],payload['elapsed_ms']))
        conn.commit()
    except (DatabaseError, ValueError, TypeError, KeyError):
        logger.warning('release_cache issuer=%s outcome=unavailable', symbol)
    finally:
        if conn: conn.close()
    return None


def fetch_release(symbol, year, quarter, *, connection=None, refresh=False, allow_web=True, market=''):
    fetcher = AutoFetcher()
    symbol = fetcher.resolve_ticker(symbol)
    match = re.fullmatch(r'(?:([1-4])[TQ]?|[TQ]([1-4]))', str(quarter).upper())
    if not match or not re.fullmatch(r'20\d{2}', str(year)) or not re.fullmatch(r"[\w .,&'()-]{1,100}", symbol):
        raise ValueError('Invalid company or fiscal period')
    year, quarter = int(year), int(match[1] or match[2])
    with _lock(symbol, year, quarter):
        started = time.monotonic()
        cached = stored(connection, symbol, year, quarter) if not refresh else None
        previous_identity = cached.get('_issuer', {}) if cached else {}
        identity = previous_identity if previous_identity.get('symbol') == symbol and previous_identity.get('name') else issuer_identity(symbol)
        if market and ((market.upper() == 'B3') != bool(re.fullmatch(r'[A-Z]{4}\d{1,2}', symbol))) and market.upper() in ('B3','NASDAQ','NYSE','AMEX'):
            raise ReleaseError('issuer_mismatch')
        if identity.get('name'):
            fetcher.transcript_issuers = {**fetcher.transcript_issuers,
                symbol: (*fetcher.transcript_issuers.get(symbol, ()), identity['name'], SECFetcher._company_name(identity['name']))}
        if cached:
            try:
                cached = dict(cached)
                cached.pop('_issuer', None)
                document = FetchedDocument(**cached)
                validate_document(document, fetcher, identity, year, quarter)
                logger.info('release_pipeline issuer=%s year=%s quarter=%s stage=cache outcome=found', symbol, year, quarter)
                return document
            except (ReleaseError, ValueError, TypeError) as exc:
                logger.warning('release_pipeline issuer=%s stage=cache outcome=invalid reason=%s', symbol, getattr(exc,'code',type(exc).__name__))
        fetcher.allow_web = allow_web
        status, document, fingerprint = 'not_found', None, None
        try:
            document = fetcher.fetch_result_pdf(symbol, year, str(quarter))
            if not document:
                raise ReleaseError('not_found')
            text = validate_document(document, fetcher, identity, year, quarter)
            document = supplements(document, year, quarter)
            text = document.text or text
            document = replace(document, pdf_bytes=b'', text=text)
            fingerprint = hashlib.sha256(text.encode()).hexdigest()
            # Only verified public documents enter the shared cache; no uploaded/private files.
            cached_document = asdict(document)
            cached_document.pop('pdf_bytes')
            status = 'found'
            return document
        except SearchError:
            status = 'search_unavailable'
            raise ReleaseError(status) from None
        except ReleaseError as exc:
            status = exc.code
            raise
        finally:
            elapsed = int((time.monotonic() - started) * 1000)
            stored(connection, symbol, year, quarter, payload={'issuer':identity,
                'document':cached_document if status == 'found' else None,'fingerprint':fingerprint,
                'status':status,'elapsed_ms':elapsed})
            logger.info('release_pipeline issuer=%s year=%s quarter=%s stage=document outcome=%s elapsed_ms=%d',
                        symbol, year, quarter, status, elapsed)
