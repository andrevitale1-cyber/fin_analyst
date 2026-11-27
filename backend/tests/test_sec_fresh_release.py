from unittest.mock import Mock
import pytest
from agents.sec_fetcher import FetchedDocument, SECFetcher
from openai_client import OpenAIClient


@pytest.mark.parametrize('form,items', [('8-K','2.02,9.01'),('6-K','')])
def test_fresh_earnings_exhibit_is_found_before_xbrl_and_quarterly_filing(monkeypatch,form,items):
    fetcher=SECFetcher()
    monkeypatch.setattr(fetcher,'_catalog',lambda:[{'ticker':'MCD','cik_str':63908}])
    batch={'form':[form],'filingDate':['2026-11-04'],'reportDate':['2026-11-04'],
           'accessionNumber':['new-release'],'primaryDocument':['cover.htm'],'items':[items]}
    monkeypatch.setattr(fetcher,'_get',lambda url:Mock(json=lambda:
        {'facts':{}} if 'companyfacts' in url else {'filings':{'recent':batch}}))
    doc=FetchedDocument('https://www.sec.gov/earnings.pdf','SEC',pdf_bytes=b'%PDF-test')
    filing=Mock(return_value=doc)
    monkeypatch.setattr(fetcher,'_filing_document',filing)
    monkeypatch.setattr(OpenAIClient,'extract_text',lambda _:"McDonald's reports third quarter 2026 results. Third quarter 2025 comparisons.")
    assert fetcher.fetch('MCD',2026,3)==doc
    filing.assert_called_once_with(batch,0,63908,exhibit=True)
    assert fetcher.fetch('MCD',2025,3) is None


@pytest.mark.parametrize('text,year,quarter,expected', [
    ('Third quarter 2026 results. Third quarter 2025 comparisons.',2025,3,False),
    ('Third quarter 2026 results. Third quarter 2025 comparisons.',2026,3,True),
    ('Q3 2026 results compared with Q3 2025.',2025,3,False),
    ('Second fiscal quarter ended February 26, 2026',2026,2,True),
    ('Fourth quarter and full year 2026 results',2026,4,True),
])
def test_release_period_uses_own_heading_not_prior_year_comparison(text,year,quarter,expected):
    assert SECFetcher._mentions_quarter(text,year,quarter) is expected


def test_foreign_filer_release_is_found_beyond_the_eight_latest_6ks(monkeypatch):
    fetcher=SECFetcher()
    monkeypatch.setattr(fetcher,'_catalog',lambda:[{'ticker':'NU','cik_str':1691493}])
    dates=[f'2026-11-{d:02d}' for d in range(25,5,-1)] + ['2026-08-13']  # twenty newer 6-Ks, then the 2Q26 release
    batch={'form':['6-K']*len(dates),'filingDate':dates,'reportDate':dates,
           'accessionNumber':[f'a{i}' for i in range(len(dates))],'primaryDocument':['x.htm']*len(dates),'items':['']*len(dates)}
    monkeypatch.setattr(fetcher,'_get',lambda url:Mock(json=lambda:
        {'facts':{}} if 'companyfacts' in url else {'filings':{'recent':batch}}))
    release=FetchedDocument('https://www.sec.gov/nu2q26.htm','SEC',text='Nu Holdings reports second quarter 2026 results')
    other=FetchedDocument('https://www.sec.gov/other.htm','SEC',text='Notice of annual general meeting')
    monkeypatch.setattr(fetcher,'_filing_document',lambda b,i,cik,exhibit=False: release if b['filingDate'][i]=='2026-08-13' else other)
    assert fetcher.fetch('NU',2026,2)==release


def test_release_window_follows_the_issuers_fiscal_calendar():
    from datetime import date
    ends = {(2027, 2): '2026-07-31', (2027, 1): '2026-04-30', (2026, 4): '2026-01-31'}
    assert SECFetcher._quarter_ends(ends, 2027, 2) == [date(2026, 7, 31)]
    walmart_q3 = SECFetcher._quarter_ends(ends, 2027, 3)[0]
    assert date(2026, 10, 25) <= walmart_q3 <= date(2026, 11, 5)
    assert SECFetcher._quarter_ends({}, 2026, 3) == [date(2026, 9, 30)]
