import copy
import json
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from test_account_limits import database, finish
import company_comparison as comparison
from agents import results_duel as agent
from report_auth import SessionUser, require_report_user
from account_limits import reserve_usage

DOC_A = ('Apple Inc. (AAPL). First quarter 2026. Quarter ended March 31, 2026. '
         'Revenue was USD 100 million versus USD 80 million. Operating margin was 30%. '
         'Cash generation supports investment. Guidance remains subject to demand. ')*8
DOC_B = ('Microsoft Corporation (MSFT). First quarter 2026. Quarter ended March 31, 2026. '
         'Revenue was USD 50 million versus USD 40 million. Operating margin was 20%. '
         'Cash generation supports investment. Guidance remains subject to demand. ')*8


def analysis(symbol='AAPL', score=5, call=False):
    return {'metadata': {'empresa':symbol,'periodo':'1T/2026', **({'tipo':'Earnings Call'} if call else {})},
            'data': dict(zip(comparison.SCORES,[score]*5)), 'analise_completa':'Existing analysis - never modified.'}


@pytest.fixture
def setup(database, monkeypatch):
    db, factory = database
    db.executescript('''ALTER TABLE historico ADD COLUMN empresa TEXT;
        ALTER TABLE historico ADD COLUMN ano TEXT;
        ALTER TABLE historico ADD COLUMN trimestre TEXT;
        ALTER TABLE historico ADD COLUMN resultado_json TEXT;
        CREATE TABLE analysis_documents(analysis_id INTEGER,source_title TEXT,source_url TEXT,source_text TEXT);
        CREATE TABLE results_duels(id TEXT PRIMARY KEY,user_id TEXT,cache_key TEXT UNIQUE,left_id INTEGER,right_id INTEGER,
          locale TEXT,state TEXT,stage TEXT DEFAULT 'queued',ticket TEXT,input_data TEXT,content TEXT,error_code TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);''')
    def insert(id, symbol, owner='user_owner', source=DOC_A, call=False, score=5):
        db.execute('INSERT INTO historico(id,user_id,data_criacao,empresa,ano,trimestre,resultado_json) VALUES(?,?,CURRENT_TIMESTAMP,?,?,?,?)',
                   (id,owner,symbol,'2026','1T',json.dumps(analysis(symbol,score,call))))
        db.execute('INSERT INTO analysis_documents VALUES(?,?,?,?)',(id,'Official release','https://example.com/release',source))
        db.commit()
    insert(1,'AAPL'); insert(2,'MSFT',source=DOC_B); insert(3,'MU',owner='user_other',source='Micron MU first quarter 2026. '*40)
    monkeypatch.setattr(comparison,'connection',factory)
    app=FastAPI(); app.include_router(comparison.router)
    owner=SessionUser('user_owner',plan='premium')
    app.dependency_overrides[require_report_user]=lambda:owner
    with TestClient(app) as http:
        yield db,factory,app,http,insert,owner


def body(a=1,b=2):
    return {'left_id':a,'right_id':b,'locale':'en'}


def run_job(db, monkeypatch, report=None, fail=False):
    row=db.execute('SELECT id,user_id,locale,input_data,ticket,cache_key FROM results_duels').fetchone()
    db.execute("UPDATE results_duels SET state='running' WHERE id=?",(row[0],)); db.commit()
    mock=Mock()
    mock.run.side_effect=ValueError('invalid citation') if fail else None
    mock.run.return_value=report or {'verdict':'A','summary':'Verified comparison','dimensions':[], 'charged':True}
    monkeypatch.setattr(comparison,'ResultsDuelAgent',lambda:mock)
    comparison.process(row)
    return row[0],mock


def test_history_is_private_and_calls_are_excluded(setup):
    db,_,_,http,insert,_=setup
    insert(4,'AAPL',call=True)
    insert(5,'AAPL',source='',score=4.5)
    rows=http.get('/api/company-comparison/analyses').json()['analyses']
    assert {row['id'] for row in rows}=={1,2,5}
    assert next(row for row in rows if row['id']==5)['scores']['nota_geral']==4.5
    assert not next(row for row in rows if row['id']==5)['duel_eligible']
    assert all('_source_text' not in row and '_analysis' not in row for row in rows)
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==0


def test_free_and_anonymous_cannot_access_comparison(setup):
    _,_,app,http,_,_=setup
    app.dependency_overrides.clear()
    assert http.get('/api/company-comparison/analyses').status_code==401
    app.dependency_overrides[require_report_user]=lambda:SessionUser('user_free',plan='free')
    assert http.get('/api/company-comparison/analyses').status_code==403
    assert http.get('/api/company-comparison/duels').status_code==403
    assert http.post('/api/company-comparison/duels',json=body()).status_code==403


def test_reversed_order_reuses_pending_and_completed_job_without_charge(setup, monkeypatch):
    db,_,_,http,_,_=setup
    first=http.post('/api/company-comparison/duels',json=body()).json()
    reverse=http.post('/api/company-comparison/duels',json=body(2,1)).json()
    assert first['id']==reverse['id'] and reverse['reused'] and not reverse['charged']
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==1
    before=db.execute('SELECT resultado_json FROM historico ORDER BY id').fetchall()
    job_id,_=run_job(db,monkeypatch)
    assert http.get('/api/company-comparison/duels/'+job_id).json()['state']=='completed'
    assert db.execute('SELECT state FROM account_usage').fetchone()[0]=='completed'
    assert http.post('/api/company-comparison/duels',json=body()).json()['reused']
    assert before==db.execute('SELECT resultado_json FROM historico ORDER BY id').fetchall()


def test_access_period_identity_and_distinct_issuer_validation(setup):
    db,_,_,http,insert,_=setup
    assert http.post('/api/company-comparison/duels',json=body(1,3)).status_code==404
    assert http.post('/api/company-comparison/duels',json=body(1,1)).status_code==422
    insert(4,'AAPL')
    assert http.post('/api/company-comparison/duels',json=body(1,4)).status_code==422
    insert(5,'TFCO4',source='Suzano results first quarter 2026. '*40)
    assert http.post('/api/company-comparison/duels',json=body(1,5)).status_code==422
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==0


def test_failed_or_inconclusive_duel_refunds_the_reservation(setup, monkeypatch):
    db,_,_,http,_,_=setup
    http.post('/api/company-comparison/duels',json=body())
    job_id,_=run_job(db,monkeypatch,fail=True)
    assert http.get('/api/company-comparison/duels/'+job_id).json()['state']=='failed'
    assert db.execute('SELECT state FROM account_usage').fetchone()[0]=='failed'
    assert http.post('/api/company-comparison/duels',json=body()).json()['id']==job_id
    run_job(db,monkeypatch,report={'verdict':'insufficient'})
    result=http.get('/api/company-comparison/duels/'+job_id).json()
    assert result['state']=='completed' and not result['content']['charged']
    assert db.execute("SELECT COUNT(*) FROM account_usage WHERE state='completed'").fetchone()[0]==0


def test_changed_analysis_or_methodology_invalidates_result(setup,monkeypatch):
    db,_,_,http,_,_=setup
    job_id=http.post('/api/company-comparison/duels',json=body()).json()['id']
    run_job(db,monkeypatch)
    db.execute("UPDATE historico SET resultado_json=? WHERE id=1",(json.dumps(analysis(score=4)),));db.commit()
    result=http.get('/api/company-comparison/duels/'+job_id).json()
    assert result['state']=='stale' and 'content' not in result
    assert http.post('/api/company-comparison/duels',json=body()).json()['id']!=job_id
    monkeypatch.setattr(comparison,'methodology',lambda:'new-rubric')
    assert all(job['state']=='stale' for job in http.get('/api/company-comparison/duels').json()['duels'])


def test_private_duel_cannot_be_opened_by_another_premium_user(setup):
    _,_,app,http,_,_=setup
    job_id=http.post('/api/company-comparison/duels',json=body()).json()['id']
    app.dependency_overrides[require_report_user]=lambda:SessionUser('user_other',plan='premium')
    assert http.get('/api/company-comparison/duels/'+job_id).status_code==404
    assert http.get('/api/company-comparison/duels').json()['duels']==[]


def test_cached_duel_reopens_after_monthly_allowance_is_used(setup,monkeypatch):
    db,factory,_,http,_,owner=setup
    job_id=http.post('/api/company-comparison/duels',json=body()).json()['id']
    run_job(db,monkeypatch)
    for _ in range(49): finish(factory,reserve_usage(owner,'analysis'))
    assert http.post('/api/company-comparison/duels',json=body(2,1)).json()['id']==job_id
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==50


def test_parallel_repeats_reserve_only_one_analysis(setup):
    db,_,_,_,_,owner=setup
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=list(pool.map(lambda _:comparison.start_duel(comparison.StartDuel(**body()),owner),range(2)))
    assert jobs[0]['id']==jobs[1]['id']
    assert db.execute('SELECT COUNT(*) FROM account_usage').fetchone()[0]==1


def participants():
    return [{'side':'A','period_end':'2026-03-31','evidence':DOC_A},
            {'side':'B','period_end':'2026-03-31','evidence':DOC_B}]


def verdict():
    return {'verdict':'A','confidence':'moderate','summary':'Company A delivered the stronger supported result.',
            'dimensions':[{'id':key,'winner':'A','left_assessment':'Operating margin was 30%.',
                           'right_assessment':'Operating margin was 20%.','left_quote':'Operating margin was 30%.',
                           'right_quote':'Operating margin was 20%.','reason':'The supported margin is stronger on the left.'} for key in agent.DIMENSIONS],
            'watchpoints':[], 'conclusion':'The supported dimension tally favors company A. This is a result comparison.'}


def test_verifier_rejects_invented_numbers_quotes_and_contradictory_winner():
    assert agent.validate_verdict(verdict(),participants(),[])['verdict']=='A'
    for field,value in [('left_quote','Revenue invented in a different company document.'),('left_assessment','Operating margin was 95%.')]:
        invalid=verdict();invalid['dimensions'][0][field]=value
        with pytest.raises(ValueError):agent.validate_verdict(invalid,participants(),[])
    invalid=verdict();invalid['verdict']='B'
    with pytest.raises(ValueError):agent.validate_verdict(invalid,participants(),[])
    invalid=verdict();invalid['confidence']='high';unknown=participants();unknown[0]['period_end']=None
    with pytest.raises(ValueError):agent.validate_verdict(invalid,unknown,[])


def test_missing_evidence_is_not_a_negative_score():
    dims=[{'winner':winner} for winner in ['A','B','tie','insufficient','insufficient']]
    assert agent.expected_verdict(dims)=='tie'
    assert agent.expected_verdict([{'winner':'A'}]*2+[{'winner':'insufficient'}]*3)=='insufficient'


def test_fact_quotes_values_units_and_safe_growth_calculation():
    fact={'side':'A','metric':'revenue','basis':'current','accounting_basis':'reported','value':100,'unit':'currency_millions','currency':'USD',
          'quote':'Revenue was USD 100 million versus USD 80 million.','unit_quote':'USD 100 million'}
    prior={**fact,'basis':'prior_year','value':80}
    valid=agent.checked_facts({'facts':[fact,prior]},participants())
    assert len(valid)==2 and agent.comparisons(valid)[0]['growth_pct']==25
    assert not agent.checked_facts({'facts':[{**fact,'value':900}]},participants())
    assert not agent.checked_facts({'facts':[{**fact,'unit':'currency_billions'}]},participants())
    assert agent.comparisons([fact,{**prior,'currency':'BRL'}])==[]
    assert agent.comparisons([fact,{**prior,'accounting_basis':'adjusted'}])==[]
    assert agent.comparisons([fact,{**prior,'value':-80}])[0]['growth_pct'] is None
    assert not agent.checked_facts({'facts':[fact,fact]},participants())


def test_primary_quote_cannot_cross_spliced_excerpt_boundaries():
    docs=participants();docs[0]['_original_evidence']='Primary text. Another primary paragraph.'
    with pytest.raises(ValueError):agent.validate_verdict(verdict(),docs,[])


def test_evidence_excerpt_keeps_later_cash_flow_sections():
    text='Company cover. '+('long business description '*1000)+' Cash flows operating cash USD 500 million.'
    excerpt=comparison.evidence_excerpt(text)
    assert 'Company cover' in excerpt and 'Cash flows operating cash' in excerpt


def test_agent_uses_passage_identifiers_and_server_inserts_original_quotes(monkeypatch):
    client=Mock()
    def respond(prompt,schema,**kwargs):
        if 'FactSet' == schema.get('title'):
            fields=schema['$defs']['NumericFact']['properties']
            assert 'quote' not in fields and 'quote_id' in fields
            return {'facts':[{'side':'A','metric':'revenue','basis':'current','accounting_basis':'reported',
                             'value':100,'unit':'currency_millions','currency':'USD','quote_id':'A001','unit_quote_id':'A001'}]}
        raw=verdict()
        for dimension in raw['dimensions']:
            dimension.pop('left_quote');dimension.pop('right_quote')
            dimension['left_evidence_ids']=['A001'];dimension['right_evidence_ids']=['B001']
            if dimension['id']=='cash':dimension['winner']='insufficient'
        return raw
    client.analyze_full_report.side_effect=respond
    monkeypatch.setattr(agent,'OpenAIClient',lambda **_:client)
    result=agent.ResultsDuelAgent().run(participants(),'pt')
    assert client.analyze_full_report.call_count==2
    assert agent.normalized(result['dimensions'][0]['left_quote']) in agent.normalized(DOC_A)
    assert result['facts'][0]['value']==100


def test_decimal_localization_does_not_allow_rounding_or_remove_thousands():
    assert agent.numbers('14.61')==agent.numbers('14,61')
    assert agent.numbers('58.99')!=agent.numbers('59')
    assert agent.numbers('1,000')!=agent.numbers('1')
    assert agent.numbers('1,000')!=agent.numbers('1000')
    assert -116403 in agent.values('(116,403)') and 116403 not in agent.values('(116,403)')


def test_sec_fiscal_focus_is_not_a_calendar_quarter(setup):
    db,_,_,http,insert,_=setup
    source='iren-20251231\n--06-30\n2026\nQ2\nIREN\n'+('For the quarterly period ended December 31, 2025. '*20)
    insert(6,'IREN',source=source)
    db.execute("UPDATE historico SET trimestre='2T' WHERE id=6");db.commit()
    row=next(row for row in http.get('/api/company-comparison/analyses').json()['analyses'] if row['id']==6)
    assert row['duel_eligible'] and row['quarter']==2 and row['year']==2026
    assert row['period_end']=='2025-12-31'
    assert comparison.parse_period('invalid','invalid',{'periodo':'1T/1000'})==(None,None)


def test_new_duel_is_blocked_when_monthly_allowance_is_exhausted(setup):
    db,factory,_,http,_,owner=setup
    for _ in range(50):finish(factory,reserve_usage(owner,'analysis'))
    response=http.post('/api/company-comparison/duels',json=body())
    assert response.status_code==429
    assert db.execute('SELECT COUNT(*) FROM results_duels').fetchone()[0]==0


def test_verifier_accepts_multiple_primary_passages_without_fabricating_quotes():
    data=verdict()
    data['dimensions'][0]['left_assessment']='Operating margin was 30% and revenue was USD 100 million.'
    data['dimensions'][0]['left_supporting_quotes']=['Revenue was USD 100 million versus USD 80 million.']
    assert agent.validate_verdict(data,participants(),[])['verdict']=='A'
    data['dimensions'][0]['left_supporting_quotes']=['A fabricated document excerpt.']
    with pytest.raises(ValueError):agent.validate_verdict(data,participants(),[])


def test_agent_makes_at_most_one_evidence_repair(monkeypatch):
    calls=[]
    def respond(prompt,schema,**kwargs):
        calls.append(schema.get('title'))
        if schema.get('title')=='FactSet':return {'facts':[]}
        raw=verdict()
        for dimension in raw['dimensions']:
            dimension.pop('left_quote');dimension.pop('right_quote')
            dimension['left_evidence_ids']=['A001'];dimension['right_evidence_ids']=['B001']
            if dimension['id']=='cash':dimension['winner']='insufficient'
        if len(calls)==2:raw['dimensions'][0]['left_assessment']='Operating margin was 95%.'
        return raw
    client=Mock();client.analyze_full_report.side_effect=respond
    monkeypatch.setattr(agent,'OpenAIClient',lambda **_:client)
    stages=[]
    result=agent.ResultsDuelAgent().run(participants(),'en',stages.append)
    assert client.analyze_full_report.call_count==3 and stages==['facts','judging','verifying']
    assert result['verdict']=='A'


def test_validation_reports_all_numeric_and_verdict_issues_in_one_repair():
    raw=verdict()
    raw['dimensions'][0]['left_assessment']='Revenue increased 95%.'
    raw['dimensions'][1]['right_assessment']='Cash increased 89%.'
    raw['verdict']='B'
    with pytest.raises(agent.DuelValidationError) as error:
        agent.validate_verdict(raw,participants(),[])
    fields={issue['field'] for issue in error.value.issues}
    assert {'growth/A','profitability/B','verdict'}.issubset(fields)
    assert comparison.period_end({},'Micron announced its second quarter of fiscal 2026 ended February 26, 2026.')=='2026-02-26'


def test_missing_quarter_cash_never_awards_the_other_company_a_win():
    docs=participants();docs[0]['quarter_cash_verified']=False;docs[1]['quarter_cash_verified']=True
    with pytest.raises(agent.DuelValidationError) as error:
        agent.validate_verdict(verdict(),docs,[])
    assert any(issue['issue']=='missing_comparable_quarter_cash' for issue in error.value.issues)
    raw=verdict();raw['dimensions'][2]['winner']='insufficient'
    assert agent.validate_verdict(raw,docs,[])['verdict']=='A'


def test_currencies_cannot_be_declared_different_without_verification():
    raw=verdict();raw['summary']='As empresas possuem moedas diferentes.'
    docs=participants();docs[0]['verified_currencies']=['USD'];docs[1]['verified_currencies']=[]
    with pytest.raises(agent.DuelValidationError) as error:agent.validate_verdict(raw,docs,[])
    assert any(issue['issue']=='currency_difference_not_established' for issue in error.value.issues)


def test_cumulative_cash_flows_are_not_standalone_quarter_facts():
    source='Cash flows for six months ended March 31, 2026. USD 100 million net cash from operations.'
    docs=[{'side':'A','evidence':source}]
    fact={'side':'A','metric':'operating_cash_flow','basis':'current','accounting_basis':'reported',
          'value':100,'unit':'currency_millions','currency':'USD','quote':source,'unit_quote':source}
    assert agent.checked_facts({'facts':[fact]},docs)==[]


def test_only_the_rollout_qa_duel_can_be_withdrawn_and_refunded():
    cur=Mock();cur.fetchall.return_value=[('invalid-duel-ticket',)]
    comparison.create_tables(cur)
    calls=[call.args for call in cur.execute.call_args_list]
    assert any('cash_basis_invalidated' in sql and 'COUNT(DISTINCT' in sql for sql,*_ in calls)
    assert "WHERE r.id='183f97b6-feec-4dab-aecb-d20871f3e331'" in calls[-1][0]
    assert 'UPDATE account_usage' in calls[-1][0]
    assert 'SELECT ticket FROM invalidated' in calls[-1][0]
    assert "state='completed'" in calls[-1][0]
