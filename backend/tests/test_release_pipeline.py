from unittest.mock import Mock, MagicMock
import pytest
from fastapi import HTTPException
import requests

import release_pipeline as pipeline
from agents.auto_fetcher import AutoFetcher
from agents.sec_fetcher import FetchedDocument, SECFetcher
from agents.search_client import SearchError
from quarterly_results import parse_results, validate_quarterly_result


def document(company='McDonalds', period='third quarter 2026'):
    return FetchedDocument('https://official.example/release.htm','RI',text=
        f'{company} reports {period} results. Revenue rose to 7 billion. Net income increased to 2 billion. '+
        'Official financial results, currency USD, quarterly period. '*8)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(pipeline,'issuer_identity',lambda symbol:{'symbol':symbol,'name':'McDonalds','domains':['official.example']})
    monkeypatch.setattr(requests,'get',Mock(side_effect=AssertionError('Unexpected network request')))


def test_complete_pipeline_validates_and_reuses_shared_document_cache(monkeypatch):
    store={}
    def cached(connection,symbol,year,quarter,payload=None):
        if payload is not None:
            store['record']=payload
        return store.get('record',{}).get('document')
    monkeypatch.setattr(pipeline,'stored',cached)
    fetch=Mock(return_value=document())
    monkeypatch.setattr(AutoFetcher,'fetch_result_pdf',fetch)
    first=pipeline.fetch_release('MCD',2026,3)
    second=pipeline.fetch_release('MCD',2026,'3T')
    assert first.text==second.text and store['record']['status']=='found'
    assert len(store['record']['fingerprint'])==64 and 'pdf_bytes' not in store['record']['document']
    fetch.assert_called_once()


@pytest.mark.parametrize('company,period,code',[
    ('Suzano','third quarter 2026','issuer_mismatch'),
    ('McDonalds','second quarter 2026','period_mismatch'),
    ('McDonalds','third quarter 2025','period_mismatch')])
def test_wrong_company_and_fiscal_period_never_reach_analysis(monkeypatch,company,period,code):
    monkeypatch.setattr(AutoFetcher,'fetch_result_pdf',lambda *a:document(company,period))
    with pytest.raises(pipeline.ReleaseError) as error:
        pipeline.fetch_release('MCD',2026,3)
    assert error.value.code==code


def test_empty_search_and_search_outage_are_different(monkeypatch):
    monkeypatch.setattr(AutoFetcher,'fetch_result_pdf',lambda *a:None)
    with pytest.raises(pipeline.ReleaseError) as error:
        pipeline.fetch_release('MCD',2026,3)
    assert error.value.code=='not_found'
    monkeypatch.setattr(AutoFetcher,'fetch_result_pdf',Mock(side_effect=SearchError('Search unavailable')))
    with pytest.raises(pipeline.ReleaseError) as error:
        pipeline.fetch_release('MCD',2026,3)
    assert error.value.code=='search_unavailable'


def test_republication_replaces_fingerprint_and_document(monkeypatch):
    records=[]
    monkeypatch.setattr(pipeline,'stored',lambda *a, payload=None:records.append(payload) if payload else None)
    fetch=Mock(side_effect=[document(),document('McDonalds','third quarter 2026 revised')])
    monkeypatch.setattr(AutoFetcher,'fetch_result_pdf',fetch)
    pipeline.fetch_release('MCD',2026,3,refresh=True)
    pipeline.fetch_release('MCD',2026,3,refresh=True)
    assert records[0]['fingerprint']!=records[1]['fingerprint']


def test_sec_supplement_stays_inside_same_filing_and_same_period(monkeypatch):
    base='https://www.sec.gov/Archives/edgar/data/63908/0001/'
    doc=document();doc.url=base+'ex991.htm'
    html='<a href="https://evil.example/ex992.htm">99.2</a><a href="../other/ex992.htm">99.2</a><a href="ex992.htm">Supplement</a>'
    extra='McDonalds third quarter 2026 supplemental financial information. Revenue 7 billion, net income 2 billion.'
    get=Mock(side_effect=[Mock(content=html.encode(),text=html),Mock(content=extra.encode(),text=extra)])
    monkeypatch.setattr(SECFetcher,'_get',get)
    result=pipeline.supplements(doc,2026,3)
    assert extra in result.text and len(result.sources)==2
    assert get.call_args.args[0]==base+'ex992.htm' and get.call_count==2


def test_different_sec_cik_is_rejected_even_if_ticker_appears_in_text():
    doc=document();doc.url='https://www.sec.gov/Archives/edgar/data/999/0001/release.htm'
    with pytest.raises(pipeline.ReleaseError,match='issuer_mismatch'):
        pipeline.validate_document(doc,AutoFetcher(),{'symbol':'MCD','cik':'63908'},2026,3)


def test_supplement_inherits_fiscal_period_only_when_reporting_end_matches_parent(monkeypatch):
    base='https://www.sec.gov/Archives/edgar/data/63908/0001/'
    doc=document();doc.url=base+'ex991.htm'
    doc.text+=' Quarter ended September 30, 2026.'
    html='<a href="ex992.htm">Supplement</a>'
    extra='Supplemental information Quarter and Nine Months Ended September 30, 2026. Net income 20 million.'
    monkeypatch.setattr(SECFetcher,'_get',Mock(side_effect=[Mock(content=html.encode(),text=html),Mock(content=extra.encode(),text=extra)]))
    assert len(pipeline.supplements(doc,2026,3).sources)==2


def test_source_index_without_financial_numbers_is_rejected():
    doc=document();doc.text='McDonalds third quarter 2026 investor relations navigation links. '*12
    with pytest.raises(pipeline.ReleaseError,match='financial_content_missing'):
        pipeline.validate_document(doc,AutoFetcher(),{'symbol':'MCD','domains':['official.example']},2026,3)


def analysis(missing='N/A'):
    return '\n'.join(f'**Section Score {i}:** {missing if i==3 else "4/5"}' for i in range(1,5))+\
        '\nSection 5: Investment Thesis\nEvidence-based operating conclusion.\n**Overall Score:** 4/5'


def test_missing_category_does_not_become_zero_or_block_other_fundamentals():
    parsed=parse_results(analysis())
    validate_quarterly_result(parsed,'en')
    assert parsed['divida_nota'] is None and parsed['rated_fundamentals']==3
    assert parsed['nota_geral']==4


def test_unrecognized_score_format_is_not_silently_accepted():
    parsed=parse_results(analysis('unparseable'))
    with pytest.raises(HTTPException):validate_quarterly_result(parsed,'en')


def test_insufficient_overall_evidence_still_cannot_be_saved_or_charged():
    parsed=parse_results(analysis().replace('**Section Score 2:** 4/5','Section Score 2: N/A'))
    with pytest.raises(HTTPException):validate_quarterly_result(parsed,'en')


def test_cache_queries_are_bounded_and_only_accept_document_objects():
    conn=MagicMock();cur=conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value=({'url':'https://example.com/release'},)
    assert pipeline.stored(lambda:conn,'MCD',2026,3)['url'].startswith('https://')
    assert cur.execute.call_args.args[1]==('MCD',2026,3,pipeline.VERSION)
    conn.close.assert_called_once()


def test_prefetch_disables_web_model_and_respects_worker_lock(monkeypatch):
    import release_prefetch
    conn=MagicMock();cur=conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value=(True,)
    cur.fetchall.return_value=[('MCD',2026,3)]
    fetch=Mock()
    monkeypatch.setattr(release_prefetch,'fetch_release',fetch)
    monkeypatch.setattr(release_prefetch,'stop',Mock(is_set=lambda:False,wait=lambda _:False))
    release_prefetch.refresh_once(lambda:conn)
    assert fetch.call_args.kwargs['allow_web'] is False and fetch.call_args.kwargs['refresh'] is True
    conn.close.assert_called_once()


@pytest.mark.parametrize('fiscal_end,expected',[('0630',(2027,1)),('1231',(2026,3)),('0831',(2026,4))])
def test_prefetch_uses_issuer_fiscal_calendar(monkeypatch,fiscal_end,expected):
    from datetime import datetime
    import release_prefetch
    monkeypatch.setattr(release_prefetch,'issuer_identity',lambda _: {'fiscal_year_end':fiscal_end})
    assert release_prefetch.seed_period('TEST',datetime(2026,11,4))==expected
