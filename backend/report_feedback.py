"""One editable report rating per signed-in reader, with normal visibility checks."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from report_auth import require_report_user

router = APIRouter(prefix="/api/report-feedback", tags=["Report feedback"])
EDITORIAL_REPORTS = {"editorial-nvda-20261022", "editorial-aapl-20261022"}


def connection():
    from main import get_db_connection
    return get_db_connection()


def create_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS report_feedback (
        user_id TEXT NOT NULL, report_kind TEXT NOT NULL, report_id TEXT NOT NULL,
        vote SMALLINT NOT NULL CHECK (vote IN (-1,1)),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY(user_id, report_kind, report_id))""")


class Rating(BaseModel):
    vote: Literal[-1, 1]


def check_access(cur, kind, report_id, user_id):
    if kind == "full" and report_id in EDITORIAL_REPORTS:
        return
    if kind == "analysis":
        if not report_id.isdigit():
            raise HTTPException(404, "Report not found")
        cur.execute("SELECT id FROM historico WHERE id=%s AND CAST(user_id AS TEXT)=%s", (int(report_id), user_id))
    else:
        cur.execute("""SELECT r.id FROM full_reports r
            WHERE r.id=%s AND COALESCE(r.content->>'public_library_state','active') <> 'retired'
            AND (r.is_public OR EXISTS (SELECT 1 FROM full_report_access a
                WHERE a.report_id=r.id AND a.user_id=%s))""", (report_id, user_id))
    if not cur.fetchone():
        raise HTTPException(404, "Report not found")


@router.get("/{kind}/{report_id}")
def get_feedback(kind: Literal["full", "analysis"], report_id: str = Path(max_length=100), user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            check_access(cur, kind, report_id, user_id)
            cur.execute("SELECT vote FROM report_feedback WHERE user_id=%s AND report_kind=%s AND report_id=%s", (user_id, kind, report_id))
            row = cur.fetchone()
            return {"vote": row[0] if row else None}
    finally:
        conn.close()


@router.put("/{kind}/{report_id}")
def save_feedback(kind: Literal["full", "analysis"], body: Rating, report_id: str = Path(max_length=100), user_id: str = Depends(require_report_user)):
    conn = connection()
    try:
        with conn.cursor() as cur:
            check_access(cur, kind, report_id, user_id)
            cur.execute("""INSERT INTO report_feedback(user_id,report_kind,report_id,vote)
                VALUES (%s,%s,%s,%s) ON CONFLICT (user_id,report_kind,report_id)
                DO UPDATE SET vote=EXCLUDED.vote,updated_at=NOW()""", (user_id, kind, report_id, body.vote))
        conn.commit()
        return {"vote": body.vote}
    finally:
        conn.close()
