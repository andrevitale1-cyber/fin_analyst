from unittest.mock import Mock
import pytest
from agents.sec_fetcher import FetchedDocument, SECFetcher
from openai_client import OpenAIClient


def test_fresh_earnings_exhibit_is_found_before_xbrl_and_quarterly_filing(monkeypatch):
    fetcher=SECFetcher()
    monkeypatch.setattr(fetcher,'_catalog',lambda:[{'ticker':'MCD','cik_str':63908}])
    batch={'form':['8-K'],'filingDate':['2026-11-04'],'reportDate':['2026-11-04'],
           'accessionNumber':['new-release'],'primaryDocument':['cover.htm'],'items':['2.02,9.01']}
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
