import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_account_limits import database
from report_auth import SessionUser, require_report_user
import detailed_analysis as detailed


@pytest.fixture
def setup(database, monkeypatch):
    db, factory = database
    db.executescript('''ALTER TABLE historico ADD COLUMN empresa TEXT;
        ALTER TABLE historico ADD COLUMN ano TEXT;
        ALTER TABLE historico ADD COLUMN trimestre TEXT;
        ALTER TABLE historico ADD COLUMN resultado_json TEXT;
        CREATE TABLE analysis_documents(analysis_id INTEGER,source_text TEXT);
        CREATE TABLE detailed_analyses(id TEXT PRIMARY KEY,user_id TEXT,analysis_id INTEGER,locale TEXT,
          agent_id TEXT,source_hash TEXT,state TEXT,ticket TEXT,content TEXT,session_id TEXT,turn_id TEXT,error_code TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(user_id,analysis_id,locale,agent_id,source_hash));''')
    for id, owner, call, text in [(1,'owner',False,'Official quarterly financial source. '*60),
                                  (2,'other',False,'Private document. '*60),
                                  (3,'owner',True,'Earnings call. '*60),(4,'owner',False,'')]:
        db.execute('INSERT INTO historico VALUES(?,?,CURRENT_TIMESTAMP,?,?,?,?)',
                   (id,owner,'MU','2026','2T',json.dumps({'metadata':{'tipo':'Earnings Call' if call else 'Quarterly'},'data':{'nota_geral':5}})))
        db.execute('INSERT INTO analysis_documents VALUES(?,?)',(id,text))
    db.commit()
    monkeypatch.setattr(detailed,'connection',factory)
    app=FastAPI(); app.include_router(detailed.router)
    app.dependency_overrides[require_report_user]=lambda:SessionUser('owner',plan='premium')
    with TestClient(app) as http:
        yield db,app,http


def test_auth_ownership_and_source_before_quota(setup):
    db,app,http=setup
    for id, status in [(2,404),(3,422),(4,422)]:
        assert http.post(f'/api/detailed-analysis/{id}',json={'locale':'en'}).status_code==status
    assert http.post('/api/detailed-analysis/1',json={'locale':'en','user_id':'other'}).status_code==422
    app.dependency_overrides[require_report_user]=lambda:SessionUser('owner',plan='free')
    assert http.post('/api/detailed-analysis/1',json={}).status_code==403
    assert http.get('/api/detailed-analysis/1').status_code==403
    app.dependency_overrides.clear()
    assert http.get('/api/detailed-analysis/1').status_code==401
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==0


def test_opening_status_does_not_queue_or_charge_an_analysis(setup):
    db,_,http=setup
    for _ in range(3):
        assert http.get('/api/detailed-analysis/1?locale=en').json()['state']=='not_started'
    assert db.execute('SELECT COUNT(*) FROM detailed_analyses').fetchone()[0]==0
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==0


def process_job(db, monkeypatch, failure=False):
    row=db.execute('SELECT id,user_id,analysis_id,locale,agent_id,source_hash,ticket FROM detailed_analyses').fetchone()
    db.execute("UPDATE detailed_analyses SET state='running'"); db.commit()
    run=Mock(return_value='Detailed result')
    if failure: run.side_effect=ValueError('private source must not leak')
    monkeypatch.setattr(detailed,'run_agent',run)
    detailed.process(row)
    return run


def test_duplicate_pending_and_saved_are_free_original_unchanged(setup,monkeypatch):
    db,_,http=setup
    before=db.execute('SELECT resultado_json FROM historico').fetchall()
    first=http.post('/api/detailed-analysis/1',json={'locale':'en'}).json()
    again=http.post('/api/detailed-analysis/1',json={'locale':'en'}).json()
    assert first['id']==again['id'] and again['reused']
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==1
    run=process_job(db,monkeypatch)
    assert run.call_args.args[0]==detailed.AGENT_ID
    assert run.call_args.args[2]=='en'
    saved=http.get('/api/detailed-analysis/1?locale=en')
    assert saved.json()['content']=='Detailed result' and saved.headers['cache-control']=='no-store'
    assert http.post('/api/detailed-analysis/1',json={'locale':'en'}).json()['reused']
    assert db.execute('SELECT state FROM account_usage').fetchone()[0]=='completed'
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==1
    assert before==db.execute('SELECT resultado_json FROM historico').fetchall()
    assert http.get('/api/detailed-analysis/1?locale=pt').json()['state']=='not_started'


def test_failure_refunds_allowance_without_partial_result(setup,monkeypatch):
    db,_,http=setup
    http.post('/api/detailed-analysis/1',json={})
    process_job(db,monkeypatch,failure=True)
    assert db.execute('SELECT state FROM account_usage').fetchone()[0]=='failed'
    result=http.get('/api/detailed-analysis/1').json()
    assert result['state']=='failed' and not result['content']
    assert 'private source' not in str(result)
    assert http.post('/api/detailed-analysis/1',json={}).json()['state']=='queued'


def test_concurrent_double_click_reserves_only_once(setup):
    db,_,http=setup
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _: http.post('/api/detailed-analysis/1',json={}).json(), range(2)))
    assert results[0]['id']==results[1]['id']
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==1


def test_detailed_uses_shared_fifty_monthly_allowance(setup):
    from account_limits import reserve_usage
    db,_,http=setup
    for _ in range(50): reserve_usage(SessionUser('owner',plan='premium'),'analysis')
    assert http.post('/api/detailed-analysis/1',json={}).status_code==429
    assert db.execute('SELECT COUNT(*) FROM detailed_analyses').fetchone()[0]==0


def test_source_change_during_generation_discards_result_and_refunds(setup,monkeypatch):
    db,_,http=setup
    http.post('/api/detailed-analysis/1',json={})
    row=db.execute('SELECT id,user_id,analysis_id,locale,agent_id,source_hash,ticket FROM detailed_analyses').fetchone()
    db.execute("UPDATE detailed_analyses SET state='running'"); db.commit()
    def changed(*args):
        db.execute("UPDATE analysis_documents SET source_text='changed document' WHERE analysis_id=1"); db.commit()
        return 'Obsolete detailed analysis'
    monkeypatch.setattr(detailed,'run_agent',changed)
    detailed.process(row)
    assert db.execute('SELECT state,content FROM detailed_analyses').fetchone()==('failed',None)
    assert db.execute('SELECT state FROM account_usage').fetchone()[0]=='failed'


@pytest.mark.parametrize('running',[False,True])
def test_cancel_pending_or_running_refunds_and_stale_worker_cannot_publish(setup,monkeypatch,running):
    db,_,http=setup
    first=http.post('/api/detailed-analysis/1',json={}).json()
    row=db.execute('SELECT id,user_id,analysis_id,locale,agent_id,source_hash,ticket FROM detailed_analyses').fetchone()
    if running:
        db.execute("UPDATE detailed_analyses SET state='running',session_id='session-live'");db.commit()
    remote=Mock();monkeypatch.setattr(detailed,'cancel_session',remote)
    assert http.post('/api/detailed-analysis/1/cancel',json={'id':first['id']}).json()['state']=='cancelled'
    assert db.execute('SELECT state FROM account_usage').fetchone()[0]=='failed'
    assert http.get('/api/detailed-analysis/1').json()['state']=='cancelled'
    retry=http.post('/api/detailed-analysis/1',json={}).json()
    assert retry['id']!=first['id']
    run=Mock();monkeypatch.setattr(detailed,'run_agent',run)
    detailed.process(row)
    run.assert_not_called()
    assert db.execute('SELECT state,content FROM detailed_analyses').fetchone()==('queued',None)


def test_cancel_requires_owner_and_does_not_refund_completed_work(setup,monkeypatch):
    db,app,http=setup
    first=http.post('/api/detailed-analysis/1',json={}).json()
    app.dependency_overrides[require_report_user]=lambda:SessionUser('other',plan='premium')
    assert http.post('/api/detailed-analysis/1/cancel',json={'id':first['id']}).status_code==404
    app.dependency_overrides[require_report_user]=lambda:SessionUser('owner',plan='premium')
    process_job(db,monkeypatch)
    assert http.post('/api/detailed-analysis/1/cancel',json={'id':first['id']}).status_code==409
    assert db.execute('SELECT state FROM account_usage').fetchone()[0]=='completed'


@pytest.mark.parametrize('status,text',[('completed','word '*500),('failed','word '*500),('completed','partial')])
def test_exact_saved_agent_locale_no_overrides_and_session_cleanup(monkeypatch,status,text):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    client=MagicMock()
    sdk=client.__enter__.return_value
    stream=sdk.beta.agents.sessions.create.return_value.with_result_collection.return_value.__enter__.return_value
    stream.__iter__.return_value=iter([SimpleNamespace(type='agent.session.created',session=SimpleNamespace(id='session-test'))])
    stream.get_final_result.return_value=SimpleNamespace(session_id='session-test',turn_id='turn-test',turn=SimpleNamespace(status=status),output_text=text)
    monkeypatch.setattr('openai.OpenAI',lambda **kwargs:client)
    remember=Mock()
    source={'company':'MU','year':2026,'quarter':'2T','text':'Original private document'}
    if status=='completed' and len(text.split())>=400:
        assert detailed.run_agent(detailed.AGENT_ID,source,'en',remember)==text.strip()
    else:
        with pytest.raises(Exception): detailed.run_agent(detailed.AGENT_ID,source,'en',remember)
    args=sdk.beta.agents.sessions.create.call_args.kwargs
    assert args['agent_id']==detailed.AGENT_ID and 'agent' not in args
    assert args['environment']=={'type':'none'}
    assert 'Do not create files' in json.loads(args['input'])['task']
    payload=json.loads(args['input'])
    assert payload['language']=='English' and payload['source_document_untrusted_data']==source['text']
    sdk.beta.agents.sessions.delete.assert_called_once_with('session-test')
    remember.assert_any_call('session-test','turn-test')
