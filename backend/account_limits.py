"""Trial and monthly entitlements with transaction-safe usage reservations."""
from datetime import datetime, timedelta, timezone
import math
from hashlib import sha256
import logging
import os
from time import monotonic
import uuid
from zoneinfo import ZoneInfo

from fastapi import Depends, Form, HTTPException
import requests

from report_auth import require_report_user

TRIAL_DAYS = 7
TRIAL_ANALYSES = 10
PREMIUM_ANALYSES = 50
TIMEZONE = ZoneInfo("America/Sao_Paulo")
_plans = {}
logger = logging.getLogger("uvicorn.error")


def connection():
    from main import get_db_connection
    return get_db_connection()


def create_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS account_usage (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('analysis','full_report')),
        usage_day DATE NOT NULL, state TEXT NOT NULL CHECK(state IN ('pending','completed','failed')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW()+INTERVAL '15 minutes'
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS account_usage_user_day ON account_usage(user_id,usage_day,kind)")
    cur.execute("CREATE INDEX IF NOT EXISTS account_usage_user_period ON account_usage(user_id,kind,created_at)")
    reset_existing_trials(cur)


def reset_existing_trials(cur):
    # One-time customer reset, committed with database initialization; never renew on restart.
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (64209120261101,))
    cur.execute("CREATE TABLE IF NOT EXISTS account_migrations (id TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    cur.execute("INSERT INTO account_migrations(id) VALUES (%s) ON CONFLICT(id) DO NOTHING RETURNING id", ('existing-trials-reset-2026-11-01',))
    if not cur.fetchone(): return
    cur.execute("""INSERT INTO trial_users(user_id,trial_start)
        SELECT user_id,NOW() FROM (
            SELECT user_id FROM trial_users UNION SELECT user_id FROM account_usage
            UNION SELECT CAST(user_id AS TEXT) FROM historico
        ) existing_accounts WHERE user_id IS NOT NULL AND user_id<>''
        ON CONFLICT(user_id) DO UPDATE SET trial_start=EXCLUDED.trial_start""")
    logger.info('existing_trial_reset accounts=%s',cur.rowcount)


def plan_for(user):
    if getattr(user, "plan", None) in ("free", "premium"):
        return user.plan
    cached = _plans.get(str(user))
    if cached and cached[1] > monotonic():
        return cached[0]
    token = getattr(user, "token", "")
    if not token:
        raise HTTPException(401, "Entre novamente para verificar seu plano.")
    try:
        base = os.getenv("PLATFORM_URL", "https://finanalyser.com.br").rstrip("/")
        if not base.startswith("https://"):
            raise ValueError("Plan verification requires HTTPS")
        response = requests.get(base + "/api/account-plan", headers={"Authorization": "Bearer " + token}, timeout=12)
        response.raise_for_status()
        payload = response.json()
        if payload.get("user_id") != str(user) or payload.get("plan") not in ("free", "premium"):
            raise ValueError("Invalid plan response")
        if len(_plans) > 10000:
            _plans.clear()
        _plans[str(user)] = payload["plan"], monotonic() + 60
        return payload["plan"]
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        raise HTTPException(503, "Não foi possível verificar seu plano. Tente novamente em instantes.") from None


def usage_count(cur, user, kind, start, end):
    cur.execute("""SELECT COUNT(*) FROM account_usage WHERE user_id=%s AND kind=%s AND created_at>=%s AND created_at<%s
        AND (state='completed' OR (state='pending' AND expires_at>NOW()))""", (str(user), kind, start, end))
    return cur.fetchone()[0]


def trial_window(cur, user):
    # Preserve existing trial dates; older usage must not receive a renewed trial.
    cur.execute("SELECT trial_start FROM trial_users WHERE user_id=%s", (str(user),))
    row = cur.fetchone()
    if not row:
        starts = [datetime.now(timezone.utc)]
        cur.execute("SELECT MIN(created_at) FROM account_usage WHERE user_id=%s", (str(user),))
        usage = cur.fetchone()
        cur.execute("SELECT data_criacao FROM historico WHERE CAST(user_id AS TEXT)=%s ORDER BY id ASC LIMIT 1", (str(user),))
        history = cur.fetchone()
        for record in (usage, history):
            if not record or not record[0]: continue
            try:
                value = datetime.fromisoformat(record[0]) if isinstance(record[0], str) else record[0]
                starts.append(value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value)
            except (ValueError, AttributeError): pass
        cur.execute("INSERT INTO trial_users(user_id,trial_start) VALUES (%s,%s) ON CONFLICT(user_id) DO NOTHING", (str(user),min(starts)))
        cur.execute("SELECT trial_start FROM trial_users WHERE user_id=%s", (str(user),))
        row = cur.fetchone()
    start = row[0]
    if isinstance(start, str): start = datetime.fromisoformat(start)
    if start.tzinfo is None: start = start.replace(tzinfo=timezone.utc)
    return start, start + timedelta(days=TRIAL_DAYS)


def entitlement_window(cur, user, plan, now):
    if plan == 'premium':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, end, PREMIUM_ANALYSES
    start, end = trial_window(cur, user)
    return start, end, TRIAL_ANALYSES


def require_active_user(user: str = Depends(require_report_user)):
    if plan_for(user) == 'premium': return user
    conn = connection()
    try:
        with conn.cursor() as cur: _, end = trial_window(cur, user)
        conn.commit()
    finally: conn.close()
    if datetime.now(TIMEZONE) >= end:
        raise HTTPException(403, 'Seu teste de 7 dias terminou. Assine o Premium para continuar. / Your 7-day trial has ended. Upgrade to continue.')
    return user


def require_premium_user(user: str = Depends(require_active_user)):
    if plan_for(user) != 'premium':
        raise HTTPException(403, 'Gerar relatórios completos é exclusivo do Premium. / Creating full reports requires Premium.')
    return user


def reserve_usage(user, kind, locale="pt"):
    plan = plan_for(user)
    if kind == 'full_report':
        require_premium_user(require_active_user(user))
        return None
    now = datetime.now(TIMEZONE)
    key = int.from_bytes(sha256(f"usage:{user}:{kind}".encode()).digest()[:8], "big", signed=True)
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (key,))
            start, end, limit = entitlement_window(cur, user, plan, now)
            if now >= end:
                raise HTTPException(403, 'Your 7-day trial has ended. Upgrade to continue.' if locale == 'en' else 'Seu teste de 7 dias terminou. Assine o Premium para continuar.')
            if usage_count(cur, user, kind, start, end) >= limit:
                detail = (('Your 50 monthly analyses have been used. The allowance renews next month.' if locale == 'en' else 'Você utilizou as 50 análises mensais. O limite renova no próximo mês.') if plan == 'premium' else
                          ('You have used the 10 analyses included in your trial. Upgrade to continue analyzing.' if locale == 'en' else 'Você utilizou as 10 análises incluídas no teste. Assine o Premium para continuar analisando.'))
                raise HTTPException(429, detail)
            ticket = str(uuid.uuid4())
            cur.execute("INSERT INTO account_usage (id,user_id,kind,usage_day,state) VALUES (%s,%s,%s,%s,'pending')", (ticket, str(user), kind, now.date()))
        conn.commit()
        return ticket
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def complete_usage(cur, ticket):
    if ticket:
        cur.execute("UPDATE account_usage SET state='completed' WHERE id=%s AND state='pending'", (ticket,))


def cancel_usage(ticket):
    if not ticket:
        return
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE account_usage SET state='failed' WHERE id=%s AND state='pending'", (ticket,))
        conn.commit()
    except Exception:
        conn.rollback()
        logger.warning("usage_reservation_cleanup_failed; pending lease will expire")
    finally:
        conn.close()


def analysis_access(user_id: str = Form(...), locale: str = Form(default="pt"), user: str = Depends(require_report_user)):
    if user_id != user:
        raise HTTPException(403, "A conta informada não corresponde à sessão.")
    ticket = reserve_usage(user, "analysis", locale)
    try:
        yield ticket
    finally:
        # Successful endpoints complete the reservation in the same transaction as the saved analysis.
        cancel_usage(ticket)


def access_snapshot(user):
    plan = plan_for(user)
    now = datetime.now(TIMEZONE)
    conn = connection()
    try:
        with conn.cursor() as cur:
            start, end, limit = entitlement_window(cur, user, plan, now)
            remaining = max(0, limit - usage_count(cur, user, 'analysis', start, end))
        conn.commit()
    finally:
        conn.close()
    active = plan == 'premium' or now < end
    return {"plan": plan, "status": plan if active else 'expired', "has_access": active,
            "can_analyze": active and remaining > 0, "can_generate_full_report": plan == 'premium',
            "days_left": None if plan == 'premium' else max(0, math.ceil((end - now).total_seconds()/86400)),
            "trial_end": end.isoformat() if plan == 'free' else None,
            "analysis_remaining": remaining if active else 0, "analysis_limit": limit,
            "full_report_remaining": None if plan == 'premium' else 0, "full_report_limit": None if plan == 'premium' else 0,
            "resets_at": end.isoformat() if plan == 'premium' else None}
