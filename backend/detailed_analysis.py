"""Private, durable Premium quarterly expansions using the saved detailed analyst."""
import hashlib
import json
import logging
import os
import uuid
from time import monotonic
from threading import Event, Thread
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from account_limits import plan_for, reserve_usage, complete_usage, cancel_usage
from report_auth import require_report_user

AGENT_ID = 'agent_7685ffaa065e40e9af807b73f00b1fe9a3d76fd716a847ee84'
stop = Event()
logger = logging.getLogger('uvicorn.error')


def private_response(response: Response):
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(prefix='/api/detailed-analysis', tags=['Detailed analysis'], dependencies=[Depends(private_response)])


def connection():
    from main import get_db_connection
    return get_db_connection()


def premium_user(user=Depends(require_report_user)):
    if plan_for(user) != 'premium':
        raise HTTPException(403, 'Análise detalhada é exclusiva do Premium. Detailed analysis requires Premium.')
    return user


def create_tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS detailed_analyses (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
        analysis_id INTEGER NOT NULL REFERENCES historico(id) ON DELETE CASCADE,
        locale TEXT NOT NULL, agent_id TEXT NOT NULL, source_hash TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('queued','running','completed','failed')),
        ticket TEXT, content TEXT, session_id TEXT, turn_id TEXT, error_code TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(user_id,analysis_id,locale,agent_id,source_hash))''')
    cur.execute('CREATE INDEX IF NOT EXISTS detailed_analyses_queue ON detailed_analyses(state,created_at)')


def source_record(cur, analysis_id, user):
    cur.execute('''SELECT h.empresa,h.ano,h.trimestre,h.resultado_json,d.source_text
        FROM historico h LEFT JOIN analysis_documents d ON d.analysis_id=h.id
        WHERE h.id=%s AND h.user_id=%s''', (analysis_id, str(user)))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, 'Analysis not found. Análise não encontrada.')
    company, year, quarter, raw, text = row
    original = json.loads(raw) if isinstance(raw, str) else raw
    if original.get('metadata', {}).get('tipo') == 'Earnings Call':
        raise HTTPException(422, 'Use a quarterly analysis. Selecione uma análise trimestral.')
    if not text or len(text.strip()) < 500:
        raise HTTPException(422, 'Refaça a análise trimestral para anexar o documento original. Reanalyze this quarter to attach its original document.')
    return {'company': company, 'year': year, 'quarter': quarter, 'text': text,
            'hash': hashlib.sha256(text.encode()).hexdigest()}


class StartDetailed(BaseModel):
    model_config = ConfigDict(extra='forbid')
    locale: Literal['pt', 'en'] = 'pt'


@router.post('/{analysis_id}')
def start(analysis_id: int, body: StartDetailed, user=Depends(premium_user)):
    ticket = None
    conn = connection()
    try:
        with conn.cursor() as cur:
            source = source_record(cur, analysis_id, user)
            agent_id = os.getenv('OPENAI_DETAILED_AGENT_ID', '').strip() or AGENT_ID
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (int(hashlib.sha256(f'detailed:{user}'.encode()).hexdigest()[:15], 16),))
            cur.execute('''SELECT id,state FROM detailed_analyses WHERE user_id=%s AND analysis_id=%s
                AND locale=%s AND agent_id=%s AND source_hash=%s''', (str(user), analysis_id, body.locale, agent_id, source['hash']))
            existing = cur.fetchone()
            if existing and existing[1] != 'failed':
                conn.commit()
                return {'id': existing[0], 'state': existing[1], 'reused': True}
            cur.execute("SELECT id FROM detailed_analyses WHERE user_id=%s AND state IN ('queued','running') LIMIT 1", (str(user),))
            if cur.fetchone():
                raise HTTPException(409, 'Aguarde a análise detalhada em andamento. Wait for your current detailed analysis.')
            ticket = reserve_usage(user, 'analysis', body.locale)
            job_id = str(uuid.uuid4())
            cur.execute('''INSERT INTO detailed_analyses(id,user_id,analysis_id,locale,agent_id,source_hash,state,ticket)
                VALUES(%s,%s,%s,%s,%s,%s,'queued',%s)
                ON CONFLICT(user_id,analysis_id,locale,agent_id,source_hash) DO UPDATE
                SET id=EXCLUDED.id,state='queued',ticket=EXCLUDED.ticket,content=NULL,error_code=NULL,session_id=NULL,turn_id=NULL,updated_at=NOW()''',
                (job_id, str(user), analysis_id, body.locale, agent_id, source['hash'], ticket))
        conn.commit()
        return {'id': job_id, 'state': 'queued', 'reused': False}
    except Exception:
        conn.rollback()
        cancel_usage(ticket)
        raise
    finally:
        conn.close()


@router.get('/{analysis_id}')
def get(analysis_id: int, locale: Literal['pt', 'en'] = 'pt', user=Depends(premium_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            source = source_record(cur, analysis_id, user)
            cur.execute('''SELECT id,state,content,error_code FROM detailed_analyses
                WHERE user_id=%s AND analysis_id=%s AND locale=%s AND source_hash=%s AND agent_id=%s
                ORDER BY created_at DESC LIMIT 1''', (str(user), analysis_id, locale, source['hash'],
                    os.getenv('OPENAI_DETAILED_AGENT_ID', '').strip() or AGENT_ID))
            row = cur.fetchone()
            return {'id': row[0], 'state': 'cancelled' if row[3] == 'cancelled' else row[1], 'content': row[2] if row[1] == 'completed' else None,
                    'error_code': row[3]} if row else {'state': 'not_started'}
    finally:
        conn.close()


class CancelDetailed(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str


def cancel_session(session_id):
    if not session_id:
        return
    from openai import OpenAI
    try:
        with OpenAI(api_key=os.environ['OPENAI_API_KEY'], timeout=10, max_retries=0) as client:
            client.beta.agents.sessions.events.create(session_id, events=[{'type': 'agent.session.input.cancel'}])
    except Exception as exc:
        logger.warning('detailed_analysis_provider_cancel_failed session=%s error_type=%s', session_id, type(exc).__name__)


@router.post('/{analysis_id}/cancel')
def cancel(analysis_id: int, body: CancelDetailed, user=Depends(premium_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""UPDATE detailed_analyses SET state='failed',error_code='cancelled',updated_at=NOW()
                WHERE id=%s AND analysis_id=%s AND user_id=%s AND state IN ('queued','running')
                RETURNING ticket,session_id""", (body.id, analysis_id, str(user)))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE account_usage SET state='failed' WHERE id=%s AND state='pending'", (row[0],))
            else:
                cur.execute('SELECT state,error_code FROM detailed_analyses WHERE id=%s AND analysis_id=%s AND user_id=%s', (body.id, analysis_id, str(user)))
                current = cur.fetchone()
                if not current:
                    raise HTTPException(404, 'Analysis not found.')
                if current[0] == 'completed':
                    raise HTTPException(409, 'A análise já foi concluída. The analysis has already completed.')
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    if row:
        cancel_session(row[1])
    return {'id': body.id, 'state': 'cancelled'}


def run_agent(agent_id, source, locale, remember, check_active=None):
    from openai import OpenAI
    from openai_client import OpenAIError
    prompt = json.dumps({'task': 'Detailed quarterly result and management analysis. Return the complete analysis directly in this response as Markdown text. Do not create files, attachments, download links or a summary of work performed.',
                         'language': 'English' if locale == 'en' else 'Português',
                         'company': source['company'], 'fiscal_year': source['year'],
                         'fiscal_quarter': source['quarter'],
                         'source_document_untrusted_data': source['text']}, ensure_ascii=False)
    # Inherit saved instructions, model and tools. Never silently substitute a model or agent.
    session_id = None
    completed = False
    last_check = monotonic()
    with OpenAI(api_key=os.environ['OPENAI_API_KEY'], timeout=240, max_retries=0) as client:
        try:
            with client.beta.agents.sessions.create(agent_id=agent_id,
                    environment={'type': 'none'}, input=prompt, stream=True).with_result_collection() as stream:
                for event in stream:
                    if event.type == 'agent.session.created':
                        session_id = event.session.id
                        remember(session_id, None)
                    if check_active and monotonic() - last_check >= 5:
                        check_active()
                        last_check = monotonic()
                result = stream.get_final_result()
            session_id = result.session_id
            remember(session_id, result.turn_id)
            completed = result.turn.status == 'completed'
            if result.turn.status != 'completed' or len(result.output_text.split()) < 400:
                logger.warning('detailed_analysis_output_rejected session=%s status=%s words=%d', session_id, result.turn.status, len(result.output_text.split()))
                raise OpenAIError('Detailed analysis incomplete', code='output_short' if completed else 'turn_incomplete')
            return result.output_text.strip()
        finally:
            if session_id:
                if not completed:
                    cancel_session(session_id)
                try:
                    client.beta.agents.sessions.delete(session_id)
                except Exception:
                    logger.warning('detailed_analysis_session_cleanup_failed session=%s', session_id)


def claim():
    conn = connection()
    try:
        with conn.cursor() as cur:
            # Never replay a paid turn after an uncertain interruption.
            cur.execute("""UPDATE detailed_analyses SET state='failed',error_code='interrupted',updated_at=NOW()
                WHERE state IN ('queued','running') AND updated_at<NOW()-INTERVAL '10 minutes' RETURNING ticket""")
            for row in cur.fetchall():
                cur.execute("UPDATE account_usage SET state='failed' WHERE id=%s AND state='pending'", (row[0],))
            cur.execute("SELECT id,user_id,analysis_id,locale,agent_id,source_hash,ticket FROM detailed_analyses WHERE state='queued' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED")
            job = cur.fetchone()
            if job:
                cur.execute("UPDATE account_usage SET expires_at=NOW()+INTERVAL '10 minutes' WHERE id=%s AND state='pending' AND expires_at>NOW() RETURNING id", (job[6],))
                if not cur.fetchone():
                    cur.execute("UPDATE detailed_analyses SET state='failed',error_code='quota_expired' WHERE id=%s", (job[0],))
                    job = None
                else:
                    cur.execute("UPDATE detailed_analyses SET state='running',updated_at=NOW() WHERE id=%s", (job[0],))
        conn.commit()
        return job
    finally:
        conn.close()


def process(job):
    job_id, user, analysis_id, locale, agent_id, source_hash, ticket = job
    try:
        conn = connection()
        try:
            with conn.cursor() as cur:
                source = source_record(cur, analysis_id, user)
        finally:
            conn.close()
        if source['hash'] != source_hash:
            raise ValueError('input_changed')

        def remember(session_id, turn_id):
            conn = connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE detailed_analyses SET session_id=%s,turn_id=COALESCE(%s,turn_id),updated_at=NOW() WHERE id=%s AND state='running' RETURNING id", (session_id, turn_id, job_id))
                    if not cur.fetchone():
                        raise ValueError('cancelled')
                conn.commit()
            finally:
                conn.close()

        def check_active():
            conn = connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM detailed_analyses WHERE id=%s AND state='running'", (job_id,))
                    if not cur.fetchone():
                        raise ValueError('cancelled')
            finally:
                conn.close()

        check_active()
        content = run_agent(agent_id, source, locale, remember, check_active)
        conn = connection()
        try:
            with conn.cursor() as cur:
                if source_record(cur, analysis_id, user)['hash'] != source_hash:
                    raise ValueError('input_changed')
                cur.execute("UPDATE detailed_analyses SET state='completed',content=%s,updated_at=NOW() WHERE id=%s AND state='running' RETURNING id", (content, job_id))
                if not cur.fetchone():
                    raise ValueError('interrupted')
                complete_usage(cur, ticket)
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
                code = getattr(exc, 'code', None) or 'generation_failed'
                cur.execute("UPDATE detailed_analyses SET state='failed',error_code=%s,updated_at=NOW() WHERE id=%s AND state='running'", (code, job_id))
            conn.commit()
        finally:
            conn.close()
        logger.warning('detailed_analysis_failed job=%s error_type=%s', job_id, type(exc).__name__)


def worker():
    while not stop.is_set():
        try:
            job = claim()
            if job:
                process(job)
                continue
        except Exception:
            logger.warning('detailed_analysis_queue_unavailable')
        stop.wait(3)


def start_worker():
    if os.getenv('DETAILED_ANALYSIS_WORKER', '1') != '0':
        stop.clear()
        Thread(target=worker, name='detailed-analysis-worker', daemon=True).start()
