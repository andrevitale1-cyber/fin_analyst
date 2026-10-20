"""Daily entitlements: server-verified plans and transaction-safe usage reservations."""
from datetime import datetime, timedelta
from hashlib import sha256
import logging
import os
from time import monotonic
import uuid
from zoneinfo import ZoneInfo

from fastapi import Depends, Form, HTTPException
import requests

from report_auth import require_report_user

FREE_LIMITS = {"analysis": 3, "full_report": 1}
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


def usage_count(cur, user, kind, day):
    cur.execute("""SELECT COUNT(*) FROM account_usage WHERE user_id=%s AND kind=%s AND usage_day=%s
        AND (state='completed' OR (state='pending' AND expires_at>NOW()))""", (str(user), kind, day))
    return cur.fetchone()[0]


def reserve_usage(user, kind, locale="pt"):
    if plan_for(user) == "premium":
        return None
    day = datetime.now(TIMEZONE).date()
    key = int.from_bytes(sha256(f"usage:{user}:{kind}:{day}".encode()).digest()[:8], "big", signed=True)
    conn = connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (key,))
            if usage_count(cur, user, kind, day) >= FREE_LIMITS[kind]:
                detail = (f"Free daily limit reached: {FREE_LIMITS[kind]} {'quarterly/call analyses' if kind == 'analysis' else 'full report'}. Try again tomorrow or upgrade."
                          if locale == "en" else f"Limite diário do Free atingido: {FREE_LIMITS[kind]} {'análises trimestrais/calls' if kind == 'analysis' else 'relatório completo'}. Tente amanhã ou assine o Premium.")
                raise HTTPException(429, detail)
            ticket = str(uuid.uuid4())
            cur.execute("INSERT INTO account_usage (id,user_id,kind,usage_day,state) VALUES (%s,%s,%s,%s,'pending')", (ticket, str(user), kind, day))
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
    day = datetime.now(TIMEZONE).date()
    conn = connection()
    try:
        with conn.cursor() as cur:
            remaining = {kind: max(0, limit - usage_count(cur, user, kind, day)) for kind, limit in FREE_LIMITS.items()}
    finally:
        conn.close()
    return {"plan": plan, "status": plan, "has_access": plan == "premium" or remaining["analysis"] > 0,
            "days_left": None, "analysis_remaining": None if plan == "premium" else remaining["analysis"],
            "full_report_remaining": None if plan == "premium" else remaining["full_report"],
            "analysis_limit": None if plan == "premium" else 3, "full_report_limit": None if plan == "premium" else 1,
            "resets_at": datetime.combine(day + timedelta(days=1), datetime.min.time(), TIMEZONE).isoformat()}
