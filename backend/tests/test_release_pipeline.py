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


def test_sec_verified_fiscal_year_does_not_use_calendar_year_of_period_end():
    doc=document('Microsoft','quarter ended September 30, 2026')
    doc.url='https://www.sec.gov/Archives/edgar/data/789019/0001/msft-20260930.htm'
    doc.fiscal_year,doc.fiscal_quarter,doc.issuer_cik=2027,1,'0000789019'
    identity={'symbol':'MSFT','name':'Microsoft','cik':'0000789019'}
    assert pipeline.validate_document(doc,AutoFetcher(),identity,2027,1)==doc.text
    with pytest.raises(pipeline.ReleaseError,match='period_mismatch'):
        pipeline.validate_document(doc,AutoFetcher(),identity,2026,1)


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
    monkeypatch.setattr(release_prefetch,'b3_universe',lambda:[])
    monkeypatch.setattr(release_prefetch,'BRAZIL_ABROAD',{})
    monkeypatch.setattr(release_prefetch,'sp500_batteries',lambda:[])
    release_prefetch.refresh_once(lambda:conn)
    assert fetch.call_args.kwargs['allow_web'] is False and fetch.call_args.kwargs['refresh'] is True
    conn.close.assert_called_once()


def test_prefetch_adds_unchecked_b3_companies_before_rechecking_known_ones(monkeypatch):
    import release_prefetch
    conn=MagicMock();cur=conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value=(True,)
    cur.fetchall.side_effect=[[(f'OLD{i}',2026,3) for i in range(30)],[('PETR4',2026,3),('OLD0',2026,3)]]
    fetch=Mock()
    monkeypatch.setattr(release_prefetch,'fetch_release',fetch)
    monkeypatch.setattr(release_prefetch,'stop',Mock(is_set=lambda:False,wait=lambda _:False))
    monkeypatch.setattr(release_prefetch,'seed_period',lambda symbol,now:(2026,3))
    monkeypatch.setattr(release_prefetch,'b3_universe',lambda:[{'ticker':t} for t in ('PETR4','PRIO3','RADL3','PRIO3')])
    monkeypatch.setattr(release_prefetch,'BRAZIL_ABROAD',{})
    monkeypatch.setattr(release_prefetch,'sp500_batteries',lambda:[])
    assert release_prefetch.refresh_once(lambda:conn) is True
    symbols=[c.args[0] for c in fetch.call_args_list]
    assert symbols[:2]==['PRIO3','RADL3'] and len(symbols)==30 and 'PETR4' not in symbols


@pytest.mark.parametrize('fiscal_end,expected',[('0630',(2027,1)),('1231',(2026,3)),('0831',(2026,4))])
def test_prefetch_uses_issuer_fiscal_calendar(monkeypatch,fiscal_end,expected):
    from datetime import datetime
    import release_prefetch
    monkeypatch.setattr(release_prefetch,'issuer_identity',lambda _: {'fiscal_year_end':fiscal_end})
    assert release_prefetch.seed_period('TEST',datetime(2026,11,4))==expected


def test_cvm_ipe_returns_the_issuers_quarter_release_and_skips_call_invitations(monkeypatch, tmp_path):
    import io, zipfile
    from agents import cvm_ipe
    from agents.auto_fetcher import AutoFetcher
    header = 'CNPJ_Companhia;Nome_Companhia;Codigo_CVM;Data_Referencia;Categoria;Tipo;Especie;Assunto;Data_Entrega;Tipo_Apresentacao;Protocolo_Entrega;Versao;Link_Download'
    rad = 'https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo='
    lines = [header,
        '12.345.678/0001-90;PRIO S.A.;22187;2026-11-05;Comunicado ao Mercado;Apresenta\xe7\xf5es;;Convite teleconfer\xeancia 3T26;2026-11-01;AP;1;1;'+rad+'1',
        '12.345.678/0001-90;PRIO S.A.;22187;2026-11-05;Dados Econ\xf4mico-Financeiros;Press-release;;Release de Resultados 3T26;2026-11-05;AP;2;1;'+rad+'2',
        '12.345.678/0001-90;PRIO S.A.;22187;2026-08-05;Dados Econ\xf4mico-Financeiros;Press-release;;Release de Resultados 2T26;2026-08-05;AP;3;1;'+rad+'3',
        '99.999.999/0001-99;OUTRA S.A.;1;2026-11-05;Dados Econ\xf4mico-Financeiros;Press-release;;Release 3T26;2026-11-05;AP;4;1;'+rad+'4']
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipped:
        zipped.writestr('ipe_cia_aberta_2026.csv', '\n'.join(lines).encode('latin-1'))
    path = tmp_path / 'ipe.zip'; path.write_bytes(buffer.getvalue())
    cvm_ipe._index.clear()
    monkeypatch.setattr(cvm_ipe, '_archive', lambda year: zipfile.ZipFile(path) if year == 2026 else (_ for _ in ()).throw(ValueError('none')))
    matches = AutoFetcher()._period_matches
    found = cvm_ipe.release_candidates('022187', None, 2026, 3, matches)
    assert [c['url'][-1] for c in found] == ['2']
    assert [c['url'][-1] for c in cvm_ipe.release_candidates(None, '12345678000190', 2026, 3, matches)] == ['2']
    assert cvm_ipe.release_candidates(None, None, 2026, 3, matches) == []



def test_cvm_filing_provenance_verifies_issuer_without_trade_name_match():
    from types import SimpleNamespace
    from agents.auto_fetcher import AutoFetcher
    import release_pipeline
    text = 'Resultado do 3T26. Lucro líquido recorrente cresceu. ' * 40
    doc = SimpleNamespace(url='https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo=1', text=text, pdf_bytes=None,
                          sources=[{'name': 'CVM IPE', 'url': 'https://www.rad.cvm.gov.br/x'}])
    identity = {'symbol': 'BBDC4', 'name': 'BCO BRADESCO S.A.'}
    try:
        release_pipeline.validate_document(doc, AutoFetcher(), identity, 2026, 3)
    except release_pipeline.ReleaseError as error:
        assert str(error) != 'issuer_mismatch'
    doc.sources = []
    try:
        release_pipeline.validate_document(doc, AutoFetcher(), identity, 2026, 3)
        raise AssertionError('unverified issuer accepted')
    except release_pipeline.ReleaseError as error:
        assert str(error) == 'issuer_mismatch'


def test_cvm_ipe_matches_market_notices_about_results_and_marks_period_named(monkeypatch, tmp_path):
    import io, zipfile
    from agents import cvm_ipe
    from agents.auto_fetcher import AutoFetcher
    header = 'CNPJ_Companhia;Nome_Companhia;Codigo_CVM;Data_Referencia;Categoria;Tipo;Especie;Assunto;Data_Entrega;Tipo_Apresentacao;Protocolo_Entrega;Versao;Link_Download'
    rad = 'https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo='
    lines = [header,
        '1;BCO X;906;2026-11-05;Comunicado ao Mercado;Outros;;Divulga\xe7\xe3o dos Resultados do 3T26;2026-11-05;AP;1;1;'+rad+'1',
        '1;BCO X;906;2026-11-05;Comunicado ao Mercado;Outros;;Resultado da AGE de novembro;2026-11-06;AP;2;1;'+rad+'2']
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipped:
        zipped.writestr('ipe.csv', '\n'.join(lines).encode('latin-1'))
    path = tmp_path / 'ipe.zip'; path.write_bytes(buffer.getvalue())
    cvm_ipe._index.clear()
    monkeypatch.setattr(cvm_ipe, '_archive', lambda year: zipfile.ZipFile(path))
    found = cvm_ipe.release_candidates('906', None, 2026, 3, AutoFetcher()._period_matches)
    assert [(c['url'][-1], c['names_period']) for c in found] == [('1', True)]


def test_off_calendar_b3_issuers_use_their_own_quarter_labels():
    from datetime import date, datetime
    from agents import cvm_ipe
    import release_prefetch
    assert cvm_ipe.period_end('PETR4', 2026, 3) == date(2026, 9, 30)
    assert cvm_ipe.period_end('CAML3', 2026, 2) == date(2026, 8, 31)   # Camil 2T26 = Jun-Aug 2026
    assert cvm_ipe.period_end('SMTO3', 2027, 2) == date(2026, 9, 30)   # São Martinho 2T27 = Jul-Sep 2026
    assert release_prefetch.seed_period('CAML3', datetime(2026, 11, 25)) == (2026, 2)
    assert release_prefetch.seed_period('SMTO3', datetime(2026, 11, 25)) == (2027, 2)



def test_itr_statements_become_an_official_quarterly_document(monkeypatch, tmp_path):
    import io, zipfile
    from datetime import date
    from agents import cvm_itr
    index = 'CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;CD_CVM;CATEG_DOC;ID_DOC;DT_RECEB;LINK_DOC\n' \
            '03.847.461/0001-92;2026-09-30;1;BRADESPAR S.A.;18724;ITR;1;2026-11-12;https://www.rad.cvm.gov.br/ENETCONSULTA/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=9\n' \
            '03.847.461/0001-92;2026-09-30;2;BRADESPAR S.A.;18724;ITR;2;2026-11-13;https://www.rad.cvm.gov.br/ENETCONSULTA/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=10\n'
    head = 'CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;CD_CVM;GRUPO_DFP;MOEDA;ESCALA_MOEDA;ORDEM_EXERC;DT_INI_EXERC;DT_FIM_EXERC;CD_CONTA;DS_CONTA;VL_CONTA;ST_CONTA_FIXA\n'
    dre = head + '\n'.join([
        '03.847.461/0001-92;2026-09-30;2;BRADESPAR;18724;DRE;REAL;MIL;ÚLTIMO;2026-07-01;2026-09-30;3.04.06;Resultado de Equivalência Patrimonial;213240;S',
        '03.847.461/0001-92;2026-09-30;2;BRADESPAR;18724;DRE;REAL;MIL;PENÚLTIMO;2025-07-01;2025-09-30;3.04.06;Resultado de Equivalência Patrimonial;500850;S',
        '03.847.461/0001-92;2026-09-30;2;BRADESPAR;18724;DRE;REAL;MIL;ÚLTIMO;2026-01-01;2026-09-30;3.11;Lucro/Prejuízo do Período;900000;S',
        '03.847.461/0001-92;2026-09-30;2;BRADESPAR;18724;DRE;REAL;MIL;ÚLTIMO;2026-07-01;2026-09-30;3.11;Lucro/Prejuízo do Período;173130;S',
        '03.847.461/0001-92;2026-09-30;1;BRADESPAR;18724;DRE;REAL;MIL;ÚLTIMO;2026-07-01;2026-09-30;3.11;Lucro antigo;1;S'])
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipped:
        zipped.writestr('itr_cia_aberta_2026.csv', index.encode('utf-8'))
        zipped.writestr('itr_cia_aberta_DRE_ind_2026.csv', dre.encode('utf-8'))
    path = tmp_path / 'itr.zip'; path.write_bytes(buffer.getvalue())
    monkeypatch.setattr(cvm_itr, '_archive', lambda year: zipfile.ZipFile(path))
    link, text = cvm_itr.quarterly_statements('03847461000192', date(2026, 9, 30), '3T26')
    assert link.endswith('NumeroSequencialDocumento=10') and 'versão 2' in text and 'BRADESPAR S.A.' in text
    assert '3.11 Lucro/Prejuízo do Período | 173,1 | -' in text and '3.04.06 Resultado de Equivalência Patrimonial | 213,2 | 500,9' in text
    assert 'Lucro antigo' not in text and '900,0' not in text
    assert cvm_itr.quarterly_statements('03847461000192', date(2026, 12, 31), '4T26') is None
    assert cvm_itr.quarterly_statements(None, date(2026, 9, 30), '3T26', '18724')[0].endswith('NumeroSequencialDocumento=10')


def test_brazilian_issuer_listed_abroad_is_matched_by_cvm_registrant_name(monkeypatch, tmp_path):
    import io, zipfile
    from agents import cvm_ipe
    from agents.auto_fetcher import AutoFetcher
    import release_pipeline
    header = 'CNPJ_Companhia;Nome_Companhia;Codigo_CVM;Data_Referencia;Categoria;Tipo;Especie;Assunto;Data_Entrega;Tipo_Apresentacao;Protocolo_Entrega;Versao;Link_Download'
    rad = 'https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo='
    lines = [header, ';INTER & CO, INC.;80217;2026-11-12;Comunicado ao Mercado;Outros;;Resultados 3T26;2026-11-12;AP;1;1;'+rad+'1',
             ';INTER CONSTRUTORA S.A.;1;2026-11-12;Comunicado ao Mercado;Outros;;Resultados 3T26;2026-11-12;AP;2;1;'+rad+'2']
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipped:
        zipped.writestr('ipe.csv', '\n'.join(lines).encode('latin-1'))
    path = tmp_path / 'ipe.zip'; path.write_bytes(buffer.getvalue())
    cvm_ipe._index.clear()
    monkeypatch.setattr(cvm_ipe, '_archive', lambda year: zipfile.ZipFile(path))
    found = cvm_ipe.release_candidates(None, None, 2026, 3, AutoFetcher()._period_matches, 'INTR', name=release_pipeline.BRAZIL_ABROAD['INTR'])
    assert [c['url'][-1] for c in found] == ['1']


def test_sp500_runs_one_battery_at_a_time_and_skips_checked_companies(monkeypatch):
    import release_prefetch
    batteries = release_prefetch.sp500_batteries()
    assert len(batteries) == 10 and sum(map(len, batteries)) >= 500 and 'AAPL' in sum(batteries, [])
    conn=MagicMock();cur=conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value=(True,)
    cur.fetchall.side_effect=[[],[('MMM',2026,3),('BRK-B',2026,3)]]
    fetch=Mock()
    monkeypatch.setattr(release_prefetch,'fetch_release',fetch)
    monkeypatch.setattr(release_prefetch,'stop',Mock(is_set=lambda:False,wait=lambda _:False))
    monkeypatch.setattr(release_prefetch,'seed_period',lambda symbol,now:(2026,3))
    monkeypatch.setattr(release_prefetch,'b3_universe',lambda:[])
    monkeypatch.setattr(release_prefetch,'BRAZIL_ABROAD',{})
    monkeypatch.setattr(release_prefetch,'sp500_batteries',lambda:[['MMM','AOS'],['BRK.B','ZTS'],['AAPL']])
    assert release_prefetch.refresh_once(lambda:conn) is True
    assert [c.args[0] for c in fetch.call_args_list] == ['AOS']



def test_sec_filing_in_issuers_edgar_folder_verifies_issuer_and_hyphenated_quarter(monkeypatch):
    from types import SimpleNamespace
    from agents.auto_fetcher import AutoFetcher
    import release_pipeline
    text = 'Charter Communications reports third-quarter 2026 results. Revenues and net income grew 5%. ' * 20
    doc = SimpleNamespace(url='https://www.sec.gov/Archives/edgar/data/1091667/000109166726000099/ex991.htm', text=text,
                          pdf_bytes=None, sources=[], fiscal_year=None, fiscal_quarter=None, issuer_cik=None)
    identity = {'symbol': 'CHTR', 'name': 'CCO Holdings Parent', 'cik': '0001091667', 'market': 'US'}
    assert release_pipeline.validate_document(doc, AutoFetcher(), identity, 2026, 3) == text
    with pytest.raises(release_pipeline.ReleaseError):
        release_pipeline.validate_document(doc, AutoFetcher(), {**identity, 'cik': '0000000001'}, 2026, 3)


def test_early_january_fiscal_year_end_seeds_the_calendar_year(monkeypatch):
    from datetime import datetime
    import release_prefetch
    monkeypatch.setattr(release_prefetch, 'issuer_identity', lambda symbol: {'fiscal_year_end': '0103'})
    assert release_prefetch.seed_period('DPZ', datetime(2026, 11, 26)) == (2026, 3)


@pytest.mark.parametrize('text,expected', [
    ('EX-99.1 EXHIBIT 99.1Q3 2026 UPSTATE NY CABIN', True),                                     # Airbnb
    ('REALTY INCOME ANNOUNCES OPERATING RESULTS FOR THE THREE AND NINE MONTHS ENDED SEPTEMBER 30, 2026', True),
    ('IDEX REPORTS RECORD THIRD QUARTER RESULTS NORTHBROOK, ILL., OCTOBER 28, 2026', True),
    ('IDEX REPORTS RECORD THIRD QUARTER RESULTS NORTHBROOK, ILL., OCTOBER 28, 2025', False),
])
def test_release_headings_without_a_glued_or_explicit_year(text, expected):
    from agents.auto_fetcher import AutoFetcher
    period = AutoFetcher._release_period_text(text, 'https://www.sec.gov/x.htm', 2026, 3)
    assert AutoFetcher._period_matches(period, 2026, 3) is expected

