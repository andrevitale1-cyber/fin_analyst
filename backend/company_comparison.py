"""Private Premium score history and durable, quota-safe results duels."""
from datetime import datetime
import hashlib
import json
import logging
import os
import re
from threading import Event, Thread
from types import SimpleNamespace
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from account_limits import plan_for, reserve_usage, complete_usage, cancel_usage
from report_auth import require_report_user
from agents.auto_fetcher import AutoFetcher
from agents.prompt_builder import PromptBuilder
from agents.results_duel import ResultsDuelAgent, methodology, duel_model

def private_response(response: Response):
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(prefix='/api/company-comparison', tags=['Company comparison'], dependencies=[Depends(private_response)])
stop = Event()
logger = logging.getLogger('uvicorn.error')
SCORES = ('nota_geral', 'receita_nota', 'lucro_nota', 'divida_nota', 'rentabilidade_nota')


def connection():
    from main import get_db_connection
    return get_db_connection()


def premium_user(user=Depends(require_report_user)):
    if plan_for(user) != 'premium':
        raise HTTPException(403, 'Comparar empresas é exclusivo do Premium. Company comparison requires Premium.')
    return user


def create_tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS results_duels (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL, cache_key TEXT UNIQUE NOT NULL,
        left_id INTEGER NOT NULL REFERENCES historico(id) ON DELETE CASCADE,
        right_id INTEGER NOT NULL REFERENCES historico(id) ON DELETE CASCADE,
        locale TEXT NOT NULL CHECK(locale IN ('pt','en')),
        state TEXT NOT NULL CHECK(state IN ('queued','running','completed','failed')),
        stage TEXT NOT NULL DEFAULT 'queued', ticket TEXT, input_data JSONB NOT NULL, content JSONB,
        error_code TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )''')
    cur.execute('CREATE INDEX IF NOT EXISTS results_duels_user ON results_duels(user_id,created_at DESC)')
    cur.execute('CREATE INDEX IF NOT EXISTS results_duels_pending ON results_duels(state,created_at)')


def parse_period(year, quarter, meta):
    try:
        year = int(year)
        quarter = int(re.search('[1-4]', str(quarter)).group())
        if 1990 <= year <= 2100:
            return year, quarter
    except (ValueError, TypeError, AttributeError):
        pass
    match = re.search(r'([1-4])[TQ]/(\d{4})', str(meta.get('periodo', '')), re.I)
    return (int(match[2]), int(match[1])) if match and 1990 <= int(match[2]) <= 2100 else (None, None)


def period_end(meta, source):
    value = meta.get('period_end') or meta.get('fiscal_period_end')
    if isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            pass
    match = re.search(r'(?:quarterly period|quarter|three months)\s+(?:ended|ending)\s+([A-Za-z]+\s+\d{1,2},?\s+20\d{2})', normalized(source[:60000]), re.I)
    if match:
        try:
            return datetime.strptime(match[1].replace(',', ''), '%B %d %Y').date().isoformat()
        except ValueError:
            pass
    return None


def normalized(text):
    return re.sub(r'\s+', ' ', str(text)).strip()


def evidence_excerpt(text):
    # Keep cover/period and distributed financial sections, never just the beginning of a filing.
    header = re.search(r'UNITED\s+STATES\s+SECURITIES', text[:60000], re.I)
    if header:
        text = text[header.start():]  # Exclude invisible inline-XBRL contexts preceding the actual filing cover.
    if len(text) <= 30000:
        return text
    intervals = [(0, min(5000, len(text)))]
    groups = (r'cash flows?|fluxos? de caixa', r'balance sheet|balan[cç]o',
              r'statements of operations|income statement|demonstra[cç][oõ]es',
              r'net revenue|receita l[ií]quida|net income', r'guidance|outlook|perspectivas', r'credit loss|capital ratio')
    for pattern in groups:
        candidates = [(max(0,m.start()-350),min(len(text),m.start()+2300)) for m in re.finditer(pattern,text,re.I)]
        candidates = [(a,b) for a,b in candidates if not any(x<=a and b<=y for x,y in intervals)]
        if candidates:
            # Numeric density distinguishes actual statements from their table-of-contents links.
            intervals.append(max(candidates,key=lambda span:len(re.findall(r'\d+',text[span[0]:span[1]]))))
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return '\n\n'.join(text[start:end] for start, end in merged)


def load_records(cur, user, ids=None):
    condition = ' AND h.id IN (%s,%s)' if ids is not None else ''
    cur.execute('''SELECT h.id,h.empresa,h.ano,h.trimestre,h.data_criacao,h.resultado_json,
        d.source_title,d.source_url,d.source_text FROM historico h
        LEFT JOIN analysis_documents d ON d.analysis_id=h.id
        WHERE CAST(h.user_id AS TEXT)=%s''' + condition + ' ORDER BY h.id DESC', (str(user), *(ids or [])))
    output = []
    fetcher, prompts = AutoFetcher(), PromptBuilder()
    for row in cur.fetchall():
        try:
            result = json.loads(row[5]) if isinstance(row[5], str) else row[5]
            meta, data = result.get('metadata') or {}, result.get('data') or {}
            if meta.get('tipo') == 'Earnings Call':
                continue
            symbol = fetcher.resolve_ticker(str(meta.get('ticker') or meta.get('symbol') or row[1] or meta.get('empresa') or ''))
            year, quarter = parse_period(row[2], row[3], meta)
            if not symbol or not year:
                continue
            scores = {}
            for field in SCORES:
                try:
                    value = float(data.get(field))
                    scores[field] = value if 1 <= value <= 5 else None
                except (TypeError, ValueError):
                    scores[field] = None
            source = str(row[8] or '')
            verified = len(source.strip()) >= 500 and fetcher._release_company_matches(SimpleNamespace(text=source, pdf_bytes=b''), symbol)
            fiscal_focus = bool(re.search(rf'--\d{{2}}-\d{{2}}\s+{year}\s+Q{quarter}\b', source[:5000]))
            matches_period = bool(source and (fetcher._period_matches(source[:20000], year, quarter) or fiscal_focus))
            fingerprint = hashlib.sha256(json.dumps([result, source, row[6], row[7]], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            output.append({'id': row[0], 'symbol': symbol, 'company': str(meta.get('company_name') or meta.get('company') or symbol),
                           'year': year, 'quarter': quarter, 'period': f'{quarter}T/{year}', 'created_at': str(row[4] or ''),
                           'period_end': period_end(meta, source), 'scores': scores,
                           'scoring_version': meta.get('scoring_version') or 'legacy-unknown',
                           'sector': prompts.get_sector(symbol), 'duel_eligible': verified and matches_period,
                           'source': {'name': row[6] or 'Source document', 'url': row[7] if row[7] and fetcher._valid_url(row[7]) else None},
                           '_source_text': source,
                           '_fingerprint': fingerprint})
        except (ValueError, TypeError, AttributeError):
            continue
    return output


def public_record(record):
    return {key: value for key, value in record.items() if not key.startswith('_')}


def key_for(user, records, locale):
    # Canonical order removes the UI's left/right order as a source of verdict changes or duplicate charges.
    records = sorted(records, key=lambda item: (item['symbol'], item['id']))
    payload = [str(user), locale, methodology(), duel_model(), [(r['id'], r['_fingerprint']) for r in records]]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), records


@router.get('/analyses')
def analyses(user=Depends(premium_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            records = load_records(cur, user)
        return {'analyses': [public_record(record) for record in records]}
    finally:
        conn.close()


class StartDuel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    left_id: int = Field(gt=0)
    right_id: int = Field(gt=0)
    locale: Literal['pt', 'en'] = 'pt'


@router.post('/duels')
def start_duel(body: StartDuel, user=Depends(premium_user)):
    if body.left_id == body.right_id:
        raise HTTPException(422, 'Selecione duas empresas diferentes. Select two different companies.')
    ticket = None
    conn = connection()
    try:
        with conn.cursor() as cur:
            records = load_records(cur, user, [body.left_id, body.right_id])
            if len(records) != 2:
                raise HTTPException(404, 'Analysis not found. Análise não encontrada.')
            if records[0]['symbol'] == records[1]['symbol']:
                raise HTTPException(422, 'Selecione duas empresas diferentes. Select two different companies.')
            if not all(record['duel_eligible'] for record in records):
                raise HTTPException(422, 'Refaça a análise para obter um documento da empresa e do trimestre verificados. Reanalyze to attach verified company and fiscal-period evidence.')
            key, records = key_for(user, records, body.locale)
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (int(hashlib.sha256(f'duel:{user}'.encode()).hexdigest()[:15], 16),))
            cur.execute('SELECT id,state FROM results_duels WHERE cache_key=%s', (key,))
            existing = cur.fetchone()
            if existing and existing[1] != 'failed':
                conn.commit()
                return {'id': existing[0], 'state': existing[1], 'reused': True, 'charged': False}
            cur.execute("SELECT id FROM results_duels WHERE user_id=%s AND state IN ('queued','running') LIMIT 1", (str(user),))
            if cur.fetchone():
                raise HTTPException(409, 'Aguarde o duelo em andamento. Wait for your current duel to finish.')
            ticket = reserve_usage(user, 'analysis', body.locale)
            participants = [{**public_record(record), 'side': side, 'evidence': evidence_excerpt(record['_source_text']),
                              'fingerprint': record['_fingerprint']}
                             for side, record in zip(('A', 'B'), records)]
            job_id = existing[0] if existing else str(uuid.uuid4())
            payload = json.dumps({'participants': participants, 'methodology': methodology(), 'model': duel_model()}, ensure_ascii=False)
            cur.execute('''INSERT INTO results_duels(id,user_id,cache_key,left_id,right_id,locale,state,ticket,input_data)
                VALUES(%s,%s,%s,%s,%s,%s,'queued',%s,%s::jsonb)
                ON CONFLICT(cache_key) DO UPDATE SET state='queued',stage='queued',ticket=EXCLUDED.ticket,
                input_data=EXCLUDED.input_data,content=NULL,error_code=NULL,updated_at=NOW()''',
                (job_id, str(user), key, records[0]['id'], records[1]['id'], body.locale, ticket, payload))
        conn.commit()
        return {'id': job_id, 'state': 'queued', 'reused': False, 'charged': True}
    except Exception:
        conn.rollback()
        cancel_usage(ticket)
        raise
    finally:
        conn.close()


def decoded(value):
    return json.loads(value) if isinstance(value, str) else value


def job_result(row, records, user, *, detail=False):
    job_id, state, stage, payload, content, error, created, cache_key, locale = row
    payload = decoded(payload)
    participants = payload['participants']
    current = [record for record in records if record['id'] in [p['id'] for p in participants]]
    stale = len(current) != 2 or key_for(user, current, locale)[0] != cache_key
    response = {'id': job_id, 'state': 'stale' if stale else state, 'stage': stage, 'error_code': error,
                'created_at': str(created), 'locale': locale,
                'participants': [{k: v for k, v in p.items() if k not in ('evidence', 'previous_analysis', 'fingerprint')} for p in participants]}
    if detail and state == 'completed' and not stale:
        response['content'] = decoded(content)
    return response


@router.get('/duels')
def duel_history(user=Depends(premium_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            records = load_records(cur, user)
            cur.execute('''SELECT id,state,stage,input_data,content,error_code,created_at,cache_key,locale
                FROM results_duels WHERE user_id=%s ORDER BY created_at DESC LIMIT 100''', (str(user),))
            return {'duels': [job_result(row, records, user) for row in cur.fetchall()]}
    finally:
        conn.close()


@router.get('/duels/{duel_id}')
def get_duel(duel_id: str, user=Depends(premium_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT id,state,stage,input_data,content,error_code,created_at,cache_key,locale
                FROM results_duels WHERE id=%s AND user_id=%s''', (duel_id, str(user)))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, 'Duel not found. Duelo não encontrado.')
            records = load_records(cur, user, [p['id'] for p in decoded(row[3])['participants']])
            return job_result(row, records, user, detail=True)
    finally:
        conn.close()


def claim():
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''UPDATE results_duels SET state='failed',error_code='interrupted',updated_at=NOW()
                WHERE state='running' AND updated_at<NOW()-INTERVAL '5 minutes' RETURNING ticket''')
            for row in cur.fetchall():
                cur.execute("UPDATE account_usage SET state='failed' WHERE id=%s AND state='pending'", (row[0],))
            cur.execute("SELECT id,user_id,locale,input_data,ticket,cache_key FROM results_duels WHERE state='queued' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED")
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE account_usage SET expires_at=NOW()+INTERVAL '10 minutes' WHERE id=%s AND state='pending' AND expires_at>NOW() RETURNING id", (row[4],))
                if cur.fetchone():
                    cur.execute("UPDATE results_duels SET state='running',stage='facts',updated_at=NOW() WHERE id=%s", (row[0],))
                else:
                    cur.execute("UPDATE results_duels SET state='failed',error_code='quota_expired',updated_at=NOW() WHERE id=%s", (row[0],))
                    row = None
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def process(job):
    job_id, user, locale, raw, ticket, expected_key = job
    payload = decoded(raw)
    try:
        conn = connection()
        try:
            with conn.cursor() as cur:
                records = load_records(cur, user, [p['id'] for p in payload['participants']])
            if len(records) != 2 or key_for(user, records, locale)[0] != expected_key:
                raise ValueError('Stale duel inputs')
        finally:
            conn.close()

        def progress(stage):
            conn = connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE results_duels SET stage=%s,updated_at=NOW() WHERE id=%s AND state='running'", (stage, job_id))
                conn.commit()
            finally:
                conn.close()

        originals = {r['id']: r['_source_text'] for r in records}
        participants = [{**p, '_original_evidence': originals[p['id']]} for p in payload['participants']]
        result = ResultsDuelAgent().run(participants, locale, progress)
        charged = result['verdict'] != 'insufficient'
        result['charged'] = charged
        conn = connection()
        try:
            with conn.cursor() as cur:
                # Recheck inputs after generation; edits/deletions must not publish an obsolete verdict.
                latest = load_records(cur, user, [p['id'] for p in payload['participants']])
                if len(latest) != 2 or key_for(user, latest, locale)[0] != expected_key:
                    raise ValueError('Duel inputs changed')
                cur.execute("UPDATE results_duels SET state='completed',stage='completed',content=%s::jsonb,updated_at=NOW() WHERE id=%s AND state='running' RETURNING id", (json.dumps(result, ensure_ascii=False), job_id))
                if not cur.fetchone():
                    raise ValueError('Duel no longer active')
                if charged:
                    complete_usage(cur, ticket)
                else:
                    cur.execute("UPDATE account_usage SET state='failed' WHERE id=%s AND state='pending'", (ticket,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception as exc:
        cancel_usage(ticket)
        conn = connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE results_duels SET state='failed',error_code='verification_failed',updated_at=NOW() WHERE id=%s AND state='running'", (job_id,))
            conn.commit()
        finally:
            conn.close()
        logger.warning('results_duel_failed job=%s error_type=%s', job_id, type(exc).__name__)


def worker():
    while not stop.is_set():
        try:
            job = claim()
            if job:
                process(job)
                continue
        except Exception:
            logger.warning('results_duel_queue_unavailable')
        stop.wait(3)


def start_worker():
    if os.getenv('COMPARISON_WORKER', '1') != '0':
        stop.clear()
        Thread(target=worker, name='results-duel-worker', daemon=True).start()
