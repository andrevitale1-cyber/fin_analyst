from unittest.mock import MagicMock, Mock
import json

import pytest
import curated_reports_job as job
import full_reports as reports


def test_authorized_job_removes_only_the_named_weg_report_and_publishes_a_separate_petrobras_copy(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.side_effect = [(True,), None, None]; cur.rowcount = 1
    monkeypatch.setattr(reports, "connection", lambda: conn)
    private = {"id": "private-cache", "company": "PETR4", "period": "Company overview", "is_public": False}
    generation = Mock(return_value={"report": private})
    monkeypatch.setattr(reports, "open_company_report", generation)
    job.curate()
    delete = next(call for call in cur.execute.call_args_list if "DELETE FROM full_reports" in call.args[0])
    assert delete.args[1] == (job.WEG_REPORT_ID,)
    assert "company='WEGE3'" in delete.args[0] and "2026-10-19" in delete.args[0]
    insert = next(call for call in cur.execute.call_args_list if "INSERT INTO full_reports" in call.args[0])
    public = json.loads(insert.args[1][-1])
    assert public["is_public"] and public["id"] != private["id"] and private["is_public"] is False
    assert not any("UPDATE full_reports SET is_public" in call.args[0] for call in cur.execute.call_args_list)
    body, curator = generation.call_args.args
    assert body.company == "PETR4" and body.locale == "pt" and curator.plan == "premium"
    assert any("state='completed'" in call.args[0] for call in cur.execute.call_args_list)


def test_completed_curation_does_not_repeat_deletion_or_paid_generation(monkeypatch):
    conn = MagicMock(); cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.side_effect = [(True,), ("completed",)]
    monkeypatch.setattr(reports, "connection", lambda: conn)
    generate = Mock(side_effect=AssertionError("Do not generate again")); monkeypatch.setattr(reports, "open_company_report", generate)
    job.curate()
    assert not any("DELETE" in call.args[0] for call in cur.execute.call_args_list)
    generate.assert_not_called()


def test_curation_requires_explicit_server_enablement(monkeypatch):
    monkeypatch.delenv("CURATE_PUBLIC_REPORTS_20261019", raising=False)
    thread = Mock(); monkeypatch.setattr(job, "Thread", thread)
    job.start_if_enabled()
    thread.assert_not_called()


def test_repairs_keep_public_ids_and_only_replace_after_successful_generation(monkeypatch):
    conn=MagicMock();cur=conn.cursor.return_value.__enter__.return_value
    cur.fetchone.side_effect=[(True,),None,(True,),None];cur.rowcount=1
    monkeypatch.setattr(reports,"connection",lambda:conn)
    generate=Mock(side_effect=[{"report":{"id":"new-private","is_public":False}},RuntimeError("unavailable")])
    monkeypatch.setattr(reports,"open_company_report",generate)
    job.repair_reports()
    updates=[c for c in cur.execute.call_args_list if "UPDATE full_reports SET content" in c.args[0]]
    assert len(updates)==1
    saved=json.loads(updates[0].args[1][0])
    assert saved["id"]=="4d25c3c1-3e7d-4685-b9c1-13a2a2495192" and saved["is_public"]
    assert "AND is_public" in updates[0].args[0]
