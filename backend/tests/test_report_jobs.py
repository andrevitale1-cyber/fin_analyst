from unittest.mock import MagicMock, Mock

from fastapi import HTTPException
import pytest

import report_jobs as jobs
import full_reports as reports
from report_auth import SessionUser


def database(monkeypatch, rows):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.side_effect = rows
    monkeypatch.setattr(jobs, "connection", lambda: conn)
    return conn, cur


def test_enqueuing_an_active_job_reuses_it_without_new_quota_or_model_calls(monkeypatch):
    conn, cur = database(monkeypatch, [("same-job",)])
    reserve = Mock(side_effect=AssertionError("No second reservation"))
    monkeypatch.setattr(jobs, "reserve_usage", reserve)
    assert jobs.enqueue(jobs.StartReport(company="MU"), SessionUser("user_one", plan="free"))["job_id"] == "same-job"
    reserve.assert_not_called()


def test_new_job_reserves_once_and_never_persists_the_session_token(monkeypatch):
    conn, cur = database(monkeypatch, [None, None, (0,)])
    reserve = Mock(return_value="ticket"); monkeypatch.setattr(jobs, "reserve_usage", reserve)
    result = jobs.enqueue(jobs.StartReport(company="Vivara", locale="pt"), SessionUser("user_one", token="secret-session", plan="free"))
    assert result["state"] == "queued" and result["company"] == "VIVA3"
    reserve.assert_called_once()
    assert "secret-session" not in str(cur.execute.call_args_list)
    insert = next(c for c in cur.execute.call_args_list if "INSERT INTO report_jobs" in c.args[0])
    assert insert.args[1][-1] == "ticket"
    conn.commit.assert_called_once()


def test_ready_public_report_does_not_reserve_a_free_daily_allowance(monkeypatch):
    _, cur = database(monkeypatch, [None, ({"id": "public", "scope": "company", "company": "MU"}, True)])
    reserve = Mock(side_effect=AssertionError("No quota for public reads")); monkeypatch.setattr(jobs, "reserve_usage", reserve)
    result = jobs.enqueue(jobs.StartReport(company="MU"), SessionUser("user_one", plan="free"))
    assert result["report"]["is_public"] and result["reused"]
    assert "full_report_access" in cur.execute.call_args.args[0]


def test_another_users_job_is_not_readable_and_analysis_history_is_authorized(monkeypatch):
    _, cur = database(monkeypatch, [None, None])
    with pytest.raises(HTTPException) as error: jobs.status("private-job", "user_other")
    assert error.value.status_code == 404
    assert cur.execute.call_args.args[1] == ("private-job", "user_other")
    with pytest.raises(HTTPException): jobs.enqueue(jobs.StartReport(analysis_id=9), "user_other")
    assert cur.execute.call_args.args[1] == (9, "user_other")


@pytest.mark.parametrize("fails", [False, True])
def test_worker_reuses_reserved_quota_and_publishes_only_completed_private_reports(monkeypatch, fails):
    conn, cur = database(monkeypatch, [(1,), ("owner",)])
    cur.rowcount = 1
    monkeypatch.setattr(jobs, "Thread", Mock())
    cleanup = Mock(); monkeypatch.setattr(jobs, "cancel_usage", cleanup)
    def generate(body, user):
        assert jobs.reserved_ticket.get() == {"ticket": "ticket"}
        assert user == "user_one" and not user.token
        assert reports.reserve_report_usage(user, "pt") == "ticket"
        if fails: raise RuntimeError("Private diagnostic must not be public")
        return {"report": {"id": "private", "is_public": False}, "reused": False}
    monkeypatch.setattr(jobs, "open_company_report", generate)
    jobs.process(("job", "user_one", "MU", "pt", "ticket", "owner"))
    statements = str(cur.execute.call_args_list)
    assert ("state='failed'" if fails else "state='completed'") in statements
    assert "Private diagnostic" not in statements
    assert jobs.reserved_ticket.get() is None
    cleanup.assert_called_once_with("ticket")


def test_claim_is_locked_and_reclaims_only_interrupted_jobs(monkeypatch):
    conn, cur = database(monkeypatch, [("job", "user_one", "MU", "pt", None)])
    cur.fetchall.return_value = []
    claim = jobs.claim()
    assert claim[:3] == ("job", "user_one", "MU")
    sql = " ".join(c.args[0] for c in cur.execute.call_args_list)
    assert "FOR UPDATE SKIP LOCKED" in sql and "90 seconds" in sql and "attempts<2" in sql
    conn.commit.assert_called_once()


def test_expired_allowance_cannot_start_paid_generation(monkeypatch):
    _, cur = database(monkeypatch, [None, None, ("owner",)])
    monkeypatch.setattr(jobs, "Thread", Mock())
    generate = Mock(side_effect=AssertionError("Expired reservation must stop before model calls"))
    monkeypatch.setattr(jobs, "open_company_report", generate)
    cancel = Mock(); monkeypatch.setattr(jobs, "cancel_usage", cancel)
    jobs.process(("job", "user_one", "MU", "en", "expired", "owner"))
    generate.assert_not_called()
    assert "reservation expired" in str(cur.execute.call_args_list)
    cancel.assert_called_once_with("expired")


def test_old_worker_does_not_cancel_a_reclaimed_jobs_reservation(monkeypatch):
    _, cur = database(monkeypatch, [(1,), ("new-owner",)])
    monkeypatch.setattr(jobs, "Thread", Mock())
    monkeypatch.setattr(jobs, "open_company_report", Mock(side_effect=RuntimeError("old lease")))
    cancel = Mock(); monkeypatch.setattr(jobs, "cancel_usage", cancel)
    jobs.process(("job", "user_one", "MU", "en", "ticket", "old-owner"))
    cancel.assert_not_called()
