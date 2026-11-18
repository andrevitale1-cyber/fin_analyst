from unittest.mock import Mock
import pytest
import market_data
real_completed_price_day = market_data.completed_price_day


@pytest.fixture(autouse=True)
def settled_market_day(monkeypatch):
    monkeypatch.setattr(market_data, 'completed_price_day', lambda symbol: '2026-11-13')
    monkeypatch.delenv('ALPACA_MARKET_DATA_ENABLED', raising=False)

@pytest.mark.parametrize('period', ['1d', '5d'])
def test_b3_retries_restricted_intraday_with_daily_closes(monkeypatch, period):
    monkeypatch.setattr(market_data, 'yahoo_market_snapshot', lambda *args: {})
    monkeypatch.setenv('BRAPI_API_KEY', 'test')
    market_data._cache.clear()
    responses = []
    for body in [
        {'results': [{'symbol': 'PNVL3', 'data': {'regularMarketPrice': 10.08}}]},
        {'code': 'INVALID_INTERVAL', 'details': {'limit': {'current': ['1d']}}},
        {'results': [{'symbol': 'PNVL3', 'data': {'usedInterval': '1d', 'historicalDataPrice': [
            {'date': 1793329200, 'close': 10.08}, {'date': 1793242800, 'close': 10.29}
        ]}}]},
    ]:
        response = Mock(); response.json.return_value = body; responses.append(response)
    get = Mock(side_effect=responses)
    monkeypatch.setattr(market_data.requests, 'get', get)
    result = market_data.market_snapshot('PNVL3', period)
    assert len(result['points']) == 2 and result['price'] == 10.08
    assert result['points'][0]['close'] == 10.29
    assert result['interval'] == '1d'
    assert get.call_args.kwargs['params']['range'] == period
    assert get.call_args.kwargs['params']['interval'] == '1d'

def test_b3_range_denial_preserves_quote_without_substituting_another_period(monkeypatch):
    monkeypatch.setattr(market_data, 'yahoo_market_snapshot', lambda *args: {})
    monkeypatch.setenv('BRAPI_API_KEY', 'test')
    market_data._cache.clear()
    quote = Mock(); quote.json.return_value = {'results': [{'symbol': 'TFCO4', 'data': {'regularMarketPrice': 9.8}}]}
    denied = Mock(); denied.json.return_value = {'code': 'INVALID_RANGE', 'details': {'limit': {'current': ['1mo']}}}
    get = Mock(side_effect=[quote, denied]); monkeypatch.setattr(market_data.requests, 'get', get)
    result = market_data.market_snapshot('TFCO4', 'max')
    assert result['price'] == 9.8 and result['points'] == []
    assert result['unavailableReason'] == 'plan_range'
    assert get.call_count == 2

def test_invalid_symbols_and_ranges_are_rejected():
    with pytest.raises(ValueError): market_data.market_snapshot('../bad')
    with pytest.raises(ValueError): market_data.market_snapshot('AAPL','bogus')

def test_twelve_prices_are_sorted_and_provider_errors_are_optional(monkeypatch):
    monkeypatch.setenv('TWELVE_DATA_API_KEY','test')
    market_data._cache.clear()
    response = Mock()
    response.json.side_effect = [{'close':'100','percent_change':'2','currency':'USD','datetime':'2026-10-30'}, {'meta':{'symbol':'AAPL','currency':'USD'},'values':[{'datetime':'2026-10-30','close':'100'},{'datetime':'2026-10-29','close':'98'},{'datetime':'2026-10-28','close':'NaN'}]}]
    monkeypatch.setattr(market_data.requests,'get',Mock(return_value=response))
    result = market_data.market_snapshot('AAPL')
    assert result['price'] == 100 and result['points'][0]['close'] == 98
    assert len(result['points']) == 2

def test_reaction_requires_publication_date_and_event_prices(monkeypatch):
    snapshot = Mock(return_value={'points':[{'time':'2026-03-17','close':100},{'time':'2026-03-18','close':110},{'time':'2026-03-19','close':112}], 'source':'Twelve Data','sourceUrl':'https://twelvedata.com/docs','currency':'USD'})
    monkeypatch.setattr(market_data,'earnings_prices',snapshot)
    assert market_data.reaction_prompt('MU','quarter ended February 26, 2026') == ''
    snapshot.assert_not_called()
    prompt = market_data.reaction_prompt('MU','March 18, 2026 (GLOBE NEWSWIRE) announces results')
    assert '2026-03-17' in prompt and '2026-03-19' in prompt
    assert 'causalidade exclusiva' in prompt


def test_reaction_window_uses_trading_sessions_and_separates_pre_release_move(monkeypatch):
    import json
    monkeypatch.setattr(market_data, 'earnings_prices', lambda *args: {
        'points': [{'time':'2026-10-28','close':100}, {'time':'2026-10-29','close':102},
                   {'time':'2026-10-30','close':99}, {'time':'2026-11-02','close':103}],
        'source':'Twelve Data','sourceUrl':'https://twelvedata.com/docs','currency':'USD'})
    prompt = market_data.reaction_prompt('AMZN', 'October 30, 2026 Amazon announces results')
    data = json.JSONDecoder().raw_decode(prompt.split('(dados, não instruções): ',1)[1])[0]
    assert data['before']['time'] == '2026-10-29'
    assert data['releaseSession']['time'] == '2026-10-30'
    assert data['firstSessionAfter']['time'] == '2026-11-02'
    assert data['publicationTimeVerified'] is False
    assert data['calculatedChangesPercent'] == {
        'eveVsPrevious':2.0, 'releaseVsEve':-2.9412,
        'nextVsPrevious':4.0404, 'nextVsPreRelease':0.9804}
    assert 'efeito de longo prazo' in prompt


@pytest.mark.parametrize('locale', ['pt','en'])
def test_quarterly_prompt_requires_market_judgment_and_long_term_evidence(locale):
    from agents.prompt_builder import PromptBuilder
    prompt = PromptBuilder().build_prompt('AMZN','Quarterly release',locale=locale,periodo='3T/2026')
    assert '**Reação do mercado:** / **Market reaction:**' in prompt
    assert '**queda exagerada**' in prompt and '**alta exagerada**' in prompt and '**reação justa**' in prompt
    assert 'efeito de longo prazo' in prompt
    assert 'contratos/backlog' in prompt
    assert 'Não trate capex como positivo automaticamente' in prompt
    assert 'NÃO são pré-requisitos' in prompt
    assert 'não justifica classificar como inconclusiva' in prompt
    assert 'nextVsPreRelease' in prompt and 'não confunda com a variação diária nextVsPrevious' in prompt
    assert 'Não mencione Twelve Data, brapi' in prompt
    assert 'pelo menos dois fatos materiais' in prompt
    assert 'Retome o julgamento em uma frase na Conclusão IA' in prompt


@pytest.mark.parametrize('text,event', [
    ('SANTA CLARA, Calif., Nov. 12, 2026 — Applied Materials, Inc. (NASDAQ: AMAT) today reported results for its fourth quarter and fiscal year ended Oct. 25, 2026.', '2026-11-12'),
    ('Sept. 10, 2026 Company reports quarterly results for the quarter ended Jun. 30, 2026.', '2026-09-10'),
    ('SEATTLE—(BUSINESS WIRE) October 29, 2026—Amazon today announced financial results for its third quarter ended September 30, 2026.', '2026-10-29'),
    ('São Paulo, 29 de outubro de 2026 — divulga os resultados do trimestre encerrado em 30 de setembro de 2026.', '2026-10-29'),
])
def test_publication_date_is_not_confused_with_quarter_end(monkeypatch, text, event):
    prices = Mock(return_value={'points':[{'time':'2026-09-09','close':100}, {'time':'2026-09-11','close':101}, {'time':'2026-10-28','close':100},
        {'time':'2026-10-29','close':98},{'time':'2026-10-30','close':99}],
        'source':'Twelve Data','sourceUrl':'https://twelvedata.com/docs'})
    monkeypatch.setattr(market_data,'earnings_prices',prices)
    assert 'CONTEXTO DE MERCADO VERIFICADO' in market_data.reaction_prompt('AMZN',text)
    prices.assert_called_once_with('AMZN',event)


def test_earnings_query_targets_event_dates_and_caches_success_only(monkeypatch):
    monkeypatch.setenv('TWELVE_DATA_API_KEY','test')
    market_data._cache.clear()
    monkeypatch.setattr(market_data,'yahoo_earnings_prices',lambda *a:{})
    get = Mock(side_effect=[{}, {'meta':{'symbol':'AMZN','currency':'USD'},'values':[
        {'datetime':'2024-10-30','close':'99'}, {'datetime':'2024-10-31','close':'100'}, {'datetime':'2024-11-01','close':'105'}]}])
    monkeypatch.setattr(market_data,'_json',get)
    assert market_data.earnings_prices('AMZN','2024-10-31') == {}
    result = market_data.earnings_prices('AMZN','2024-10-31')
    assert len(result['points']) == 3
    assert market_data.earnings_prices('AMZN','2024-10-31') == result
    assert get.call_count == 2
    url, params, _ = get.call_args.args
    assert url.endswith('/time_series') and params['symbol'] == 'AMZN'
    assert params['start_date']=='2023-10-17' and params['end_date']=='2026-11-13'
    assert params['interval']=='1day' and params['outputsize']==5000 and params['adjust']=='splits'


def test_earnings_query_rejects_wrong_company(monkeypatch):
    monkeypatch.setenv('TWELVE_DATA_API_KEY','test')
    market_data._cache.clear()
    monkeypatch.setattr(market_data,'_json',lambda *a: {'meta':{'symbol':'MSFT'},'values':[{'datetime':'2026-10-29','close':'100'}]})
    assert market_data.earnings_prices('AMZN','2026-10-29') == {}


def test_primary_failure_uses_one_complete_alternate_series(monkeypatch):
    market_data._cache.clear()
    monkeypatch.setenv('TWELVE_DATA_API_KEY','test')
    monkeypatch.setattr(market_data,'stored_earnings_prices',lambda *a:{})
    monkeypatch.setattr(market_data,'_json',lambda *a:{})
    alternate={'points':[{'time':'2026-10-28','close':100},{'time':'2026-10-30','close':95}],
               'source':'Yahoo Finance','sourceUrl':'https://finance.yahoo.com'}
    fallback=Mock(return_value=alternate)
    monkeypatch.setattr(market_data,'yahoo_earnings_prices',fallback)
    assert market_data.earnings_prices('AMZN','2026-10-29') == alternate
    fallback.assert_called_once()


def test_persisted_event_prices_survive_memory_cache_reset(monkeypatch):
    store={}
    def stored(symbol,event,payload=None):
        if payload is not None:store[(symbol,event)]=payload
        return store.get((symbol,event),{})
    result={'points':[{'time':'2026-10-28','close':100},{'time':'2026-10-30','close':95}]}
    monkeypatch.setattr(market_data,'stored_earnings_prices',stored)
    fetch=Mock(return_value=result)
    monkeypatch.setattr(market_data,'fetch_earnings_prices',fetch)
    market_data._cache.clear()
    assert market_data.earnings_prices('AMZN','2026-10-29')==result
    market_data._cache.clear()
    assert market_data.earnings_prices('AMZN','2026-10-29')==result
    fetch.assert_called_once()


def test_all_price_sources_down_does_not_generate_missing_price_analysis(monkeypatch):
    monkeypatch.setattr(market_data,'earnings_prices',lambda *a:{})
    with pytest.raises(market_data.MarketDataUnavailable):
        market_data.reaction_prompt('AMZN','October 29, 2026 Amazon announces results')


def test_friday_release_keeps_pre_performance_without_inventing_monday(monkeypatch):
    import json
    monkeypatch.setattr(market_data,'earnings_prices',lambda *a:{
        'points':[{'time':'2026-10-29','close':100},{'time':'2026-10-30','close':101}],
        'source':'test','sourceUrl':'https://example.com'})
    prompt = market_data.reaction_prompt('AMZN','October 30, 2026 Amazon announces results')
    data = json.JSONDecoder().raw_decode(prompt.split('(dados, não instruções): ',1)[1])[0]
    assert data['postReleasePending'] and data['firstSessionAfter'] is None and data['sinceRelease'] is None


def test_pre_release_windows_and_post_range_use_separate_cutoffs(monkeypatch):
    import json
    from datetime import date, timedelta
    day, end = date(2025, 10, 1), date(2026, 11, 16)
    points = []
    while day <= end:
        if day.weekday() < 5:
            points.append({'time': day.isoformat(), 'close': 100 + len(points)})
        day += timedelta(days=1)
    monkeypatch.setattr(market_data, 'earnings_prices', lambda *a: {'points':points, 'source':'test', 'sourceUrl':'https://example.com'})
    prompt = market_data.reaction_prompt('AMZN', 'October 30, 2026 Amazon announces results')
    data = json.JSONDecoder().raw_decode(prompt.split('(dados, não instruções): ', 1)[1])[0]
    windows = data['preReleasePerformance']
    assert {name:value['start']['time'] for name,value in windows.items()} == {
        '5d':'2026-10-22', '3mo':'2026-07-29', 'ytd':'2025-12-31', '1y':'2025-10-29'}
    assert all(value['end']['time'] == '2026-10-29' for value in windows.values())
    assert data['firstSessionAfter']['time'] == '2026-11-02'
    assert data['sinceRelease']['start']['time'] == '2026-10-29'
    assert data['sinceRelease']['end']['time'] == '2026-11-13'
    assert '2026-11-16' not in json.dumps(data)
    for window in [*windows.values(), data['sinceRelease']]:
        assert window['changePercent'] == pytest.approx((window['end']['close']/window['start']['close']-1)*100, abs=.0001)


def test_insufficient_pre_history_and_new_year_are_not_invented():
    before = [{'time':'2025-12-30', 'close':100}, {'time':'2025-12-31', 'close':110}]
    assert market_data._pre_release_performance(before, '2026-01-02') == dict.fromkeys(('5d','3mo','ytd','1y'))


def test_fresh_price_cache_expires_when_analysis_cutoff_changes(monkeypatch):
    market_data._cache.clear()
    store = {}
    def stored(symbol, event, payload=None):
        if payload is not None: store['value'] = payload
        return store.get('value', {})
    monkeypatch.setattr(market_data, 'stored_earnings_prices', stored)
    fetch = Mock(side_effect=[
        {'points':[{'time':'2026-10-29','close':100}, {'time':'2026-11-02','close':105}]},
        {'points':[{'time':'2026-10-29','close':100}, {'time':'2026-11-03','close':108}]}])
    monkeypatch.setattr(market_data, 'fetch_earnings_prices', fetch)
    monkeypatch.setattr(market_data, 'completed_price_day', lambda _: '2026-11-02')
    assert market_data.earnings_prices('AMZN','2026-10-30')['points'][-1]['close'] == 105
    monkeypatch.setattr(market_data, 'completed_price_day', lambda _: '2026-11-03')
    assert market_data.earnings_prices('AMZN','2026-10-30')['points'][-1]['close'] == 108
    assert fetch.call_count == 2


def test_alpaca_requires_explicit_activation_and_credentials(monkeypatch):
    from datetime import datetime
    get = Mock()
    monkeypatch.setattr(market_data, '_json', get)
    assert market_data.alpaca_earnings_prices('AMZN',datetime(2026,10,30)) == {}
    monkeypatch.setenv('ALPACA_MARKET_DATA_ENABLED','1')
    monkeypatch.delenv('APCA_API_KEY_ID', raising=False)
    monkeypatch.delenv('APCA_API_SECRET_KEY', raising=False)
    assert market_data.alpaca_earnings_prices('AMZN',datetime(2026,10,30)) == {}
    get.assert_not_called()


def test_alpaca_consolidated_history_handles_pagination_and_bad_prices(monkeypatch):
    from datetime import datetime
    monkeypatch.setenv('ALPACA_MARKET_DATA_ENABLED','1')
    monkeypatch.setenv('APCA_API_KEY_ID','paper-test-key')
    monkeypatch.setenv('APCA_API_SECRET_KEY','test-secret')
    get = Mock(side_effect=[{'symbol':'AMZN', 'bars':[
        {'t':'2026-10-29T04:00:00Z','c':100}, {'t':'2026-10-30T04:00:00Z','c':'NaN'},
        {'t':'2026-10-28','c':98}], 'next_page_token':'page2'},
        {'symbol':'AMZN','bars':[{'t':'2026-11-02T05:00:00Z','c':105},
                                {'t':'2026-11-16T05:00:00Z','c':999}], 'next_page_token':None}])
    monkeypatch.setattr(market_data,'_json',get)
    result = market_data.alpaca_earnings_prices('AMZN',datetime(2026,10,30))
    assert result['points'] == [{'time':'2026-10-29','close':100}, {'time':'2026-11-02','close':105}]
    url, params, headers = get.call_args.args
    assert url == 'https://data.alpaca.markets/v2/stocks/AMZN/bars'
    assert params['feed'] == 'sip' and params['adjustment'] == 'split' and params['page_token'] == 'page2'
    assert headers == {'APCA-API-KEY-ID':'paper-test-key', 'APCA-API-SECRET-KEY':'test-secret'}
    assert result['source'] == 'Alpaca SIP'
    get.reset_mock()
    assert market_data.alpaca_earnings_prices('PETR4',datetime(2026,10,30)) == {}
    get.assert_not_called()


def test_alpaca_rejects_wrong_symbol_and_never_combines_provider_series(monkeypatch):
    from datetime import datetime
    monkeypatch.setenv('ALPACA_MARKET_DATA_ENABLED','1')
    monkeypatch.setenv('APCA_API_KEY_ID','test')
    monkeypatch.setenv('APCA_API_SECRET_KEY','test')
    monkeypatch.setattr(market_data,'_json',lambda *a: {'symbol':'MSFT','bars':[{'t':'2026-10-29T04:00:00Z','c':100}]})
    assert market_data.alpaca_earnings_prices('AMZN',datetime(2026,10,30)) == {}
    monkeypatch.setenv('TWELVE_DATA_API_KEY','test')
    monkeypatch.setattr(market_data,'_json',lambda *a: {'meta':{'symbol':'AMZN'}, 'values':[{'datetime':'2026-10-29','close':100}]})
    monkeypatch.setattr(market_data,'alpaca_earnings_prices',lambda *a: {'points':[{'time':'2026-11-02','close':105}]})
    fallback={'points':[{'time':'2026-10-29','close':101},{'time':'2026-11-02','close':106}], 'source':'alternate'}
    monkeypatch.setattr(market_data,'yahoo_earnings_prices',lambda *a: fallback)
    assert market_data.fetch_earnings_prices('AMZN','2026-10-30') == fallback


def test_prompt_requires_all_windows_and_honest_reaction_judgment():
    from agents.prompt_builder import MARKET_REACTION_RULES
    for label in ('5 pregões','3 meses','ytd','1 ano','preReleasePerformance','sinceRelease','postReleasePending'):
        assert label in MARKET_REACTION_RULES
    assert 'não chame desempenho anterior de reação à notícia' in MARKET_REACTION_RULES
    assert 'não o atribua integralmente ao resultado' in MARKET_REACTION_RULES
    assert 'classifique os dois movimentos separadamente' in MARKET_REACTION_RULES


@pytest.mark.parametrize('symbol,stamp,expected', [
    ('AMZN','2026-11-13T16:14:00-05:00','2026-11-12'),
    ('AMZN','2026-11-13T16:15:00-05:00','2026-11-13'),
    ('AMZN','2026-11-14T18:00:00-05:00','2026-11-13'),
    ('AMZN','2026-11-16T15:00:00-05:00','2026-11-13'),
    ('PETR4','2026-11-13T18:14:00-03:00','2026-11-12'),
    ('PETR4','2026-11-13T18:15:00-03:00','2026-11-13'),
])
def test_daily_cutoff_excludes_unfinished_sessions_and_weekends(monkeypatch, symbol, stamp, expected):
    from datetime import datetime
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(stamp).astimezone(tz)
    monkeypatch.setattr(market_data, 'datetime', Clock)
    assert real_completed_price_day(symbol) == expected


def test_calendar_windows_handle_leap_year():
    from datetime import date
    assert market_data._months_before(date(2024,2,29),12) == date(2023,2,28)


def test_yahoo_prices_use_exchange_dates_and_reject_invalid_values(monkeypatch):
    from datetime import datetime,timezone
    stamps=[int(datetime(2026,10,day,20,tzinfo=timezone.utc).timestamp()) for day in (28,29,30)]
    monkeypatch.setattr(market_data,'_json',lambda *a:{'chart':{'result':[{
        'meta':{'symbol':'AMZN','exchangeTimezoneName':'America/New_York','currency':'USD'},
        'timestamp':stamps,'indicators':{'quote':[{'close':[100,None,95]}]}}]}})
    result=market_data.yahoo_earnings_prices('AMZN',datetime(2026,10,29))
    assert result['points']==[{'time':'2026-10-28','close':100},{'time':'2026-10-30','close':95}]
    assert result['source']=='Yahoo Finance'


def test_event_cache_uses_bound_symbol_date_keys_and_json(monkeypatch):
    from unittest.mock import MagicMock
    monkeypatch.setenv('DATABASE_URL','test')
    conn=MagicMock()
    cursor=conn.cursor.return_value.__enter__.return_value
    payload={'points':[{'time':'2026-10-28','close':100},{'time':'2026-10-30','close':95}]}
    cursor.fetchone.return_value=(payload,)
    monkeypatch.setattr(market_data,'get_db_connection',lambda:conn)
    assert market_data.stored_earnings_prices('AMZN','2026-10-29')==payload
    assert cursor.execute.call_args.args[1]==('AMZN','2026-10-29')
    market_data.stored_earnings_prices('AMZN','2026-10-29',payload)
    assert cursor.execute.call_args.args[1][:2]==('AMZN','2026-10-29')
    conn.commit.assert_called_once()
    assert conn.close.call_count==2



def test_parallel_snapshot_requests_share_provider_work(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import time
    monkeypatch.setenv('TWELVE_DATA_API_KEY', 'test')
    market_data._cache.clear()
    calls = []
    def get(url, *args, **kwargs):
        calls.append(url)
        time.sleep(.025)
        if url.endswith('/quote'):
            return {'symbol':'MSFT','close':'400','currency':'USD'}
        return {'meta':{'symbol':'MSFT','currency':'USD'},'values':[{'datetime':'2026-11-02','close':'399'},{'datetime':'2026-11-03','close':'400'}]}
    monkeypatch.setattr(market_data, '_json', get)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: market_data.market_snapshot('MSFT'), range(4)))
    assert all(r['price'] == 400 and len(r['points']) == 2 for r in results)
    assert len(calls) == 2
    market_data.market_snapshot('MSFT','1d')
    assert sum(url.endswith('/quote') for url in calls) == 1


def test_rate_limited_primary_uses_matching_public_fallback_and_caches(monkeypatch):
    monkeypatch.setenv('TWELVE_DATA_API_KEY', 'test')
    market_data._cache.clear()
    requests = []
    def get(url, *args, **kwargs):
        requests.append(url)
        if 'twelvedata' in url:
            return {}
        return {'chart':{'result':[{'meta':{'symbol':'MSFT','regularMarketPrice':401,'previousClose':400,'currency':'USD','regularMarketTime':1793700000,'exchangeTimezoneName':'America/New_York'},'timestamp':[1793613600,1793700000],'indicators':{'quote':[{'close':[400,401]}]}}]}}
    monkeypatch.setattr(market_data, '_json', get)
    result = market_data.market_snapshot('MSFT')
    assert result['price'] == 401 and result['changePercent'] == pytest.approx(.25)
    assert result['source'] == 'Yahoo Finance' and len(result['points']) == 2
    assert market_data.market_snapshot('MSFT') == result and len(requests) == 3


def test_fallback_does_not_accept_another_issuer(monkeypatch):
    monkeypatch.setattr(market_data, '_json', lambda *a, **k: {'chart':{'result':[{'meta':{'symbol':'AAPL','regularMarketPrice':100}}]}})
    assert market_data.yahoo_market_snapshot('MSFT','1mo') == {}



def test_sidebar_quote_skips_history_and_reuses_quote_for_full_chart(monkeypatch):
    monkeypatch.setenv('TWELVE_DATA_API_KEY','test')
    market_data._cache.clear()
    calls=[]
    def get(url, *args, **kwargs):
        calls.append(url)
        return {'symbol':'MSFT','close':'400','currency':'USD'} if url.endswith('/quote') else {'meta':{'symbol':'MSFT','currency':'USD'},'values':[{'datetime':'2026-11-02','close':'399'},{'datetime':'2026-11-03','close':'400'}]}
    monkeypatch.setattr(market_data,'_json',get)
    result=market_data.market_snapshot('MSFT','1d',quote_only=True)
    assert result['price']==400 and result['points']==[]
    assert len(calls)==1 and calls[0].endswith('/quote')
    assert market_data.market_snapshot('MSFT','1d',quote_only=True)==result
    full=market_data.market_snapshot('MSFT','1mo')
    assert len(full['points'])==2 and len(calls)==2 and calls[-1].endswith('/time_series')


@pytest.mark.parametrize('period,interval', [('1d','5m'),('5d','30m'),('1mo','1d'),
    ('6mo','1d'),('1y','1d'),('5y','1d'),('max','1mo')])
def test_b3_blocked_history_uses_matching_complete_yahoo_snapshot_and_cache(monkeypatch, period, interval):
    monkeypatch.setenv('BRAPI_API_KEY','test')
    market_data._cache.clear()
    calls=[]
    def get(url, params, headers, **kwargs):
        calls.append((url,params,headers))
        if url.endswith('/quote'):
            return {'results':[{'symbol':'ITUB4','data':{'regularMarketPrice':40,'currency':'BRL'}}]}
        if 'brapi' in url:
            return {'code':'INVALID_RANGE'}
        return {'chart':{'result':[{'meta':{'symbol':'ITUB4.SA','currency':'BRL',
            'regularMarketPrice':42,'regularMarketTime':1793797200,'previousClose':41,
            'exchangeTimezoneName':'America/Sao_Paulo'},'timestamp':[1793710800,1793797200],
            'indicators':{'quote':[{'close':[40,42]}]}}]}}
    monkeypatch.setattr(market_data,'_json',get)
    result=market_data.market_snapshot('ITUB4',period)
    assert result['symbol']=='ITUB4' and result['source']=='Yahoo Finance'
    assert result['price']==42 and len(result['points'])==2 and result['range']==period
    assert result['interval']==interval and result['changePercent']==pytest.approx(100/41)
    assert calls[-1][0].endswith('/ITUB4.SA')
    assert calls[-1][1]=={'range':period,'interval':interval}
    assert 'Authorization' not in calls[-1][2]
    assert market_data.market_snapshot('ITUB4',period)==result and len(calls)==3


def test_usable_b3_history_does_not_call_fallback(monkeypatch):
    monkeypatch.setenv('BRAPI_API_KEY','test')
    market_data._cache.clear()
    def get(url,*args,**kwargs):
        return {'results':[{'symbol':'ITUB4','data':{'regularMarketPrice':42,
            'historicalDataPrice':[{'date':1793710800,'close':40},{'date':1793797200,'close':42}]}}]}
    monkeypatch.setattr(market_data,'_json',get)
    fallback=Mock(side_effect=AssertionError('Primary history is sufficient'))
    monkeypatch.setattr(market_data,'yahoo_market_snapshot',fallback)
    assert market_data.market_snapshot('ITUB4','5y')['source']=='brapi'
    fallback.assert_not_called()


def test_b3_daily_substitute_tries_intraday_fallback_without_losing_primary_on_failure(monkeypatch):
    monkeypatch.setenv('BRAPI_API_KEY','test')
    market_data._cache.clear()
    monkeypatch.setattr(market_data,'_json',lambda *a,**kw:{'results':[{'symbol':'ITUB4','data':{
        'regularMarketPrice':42,'usedInterval':'1d','historicalDataPrice':[
            {'date':1793710800,'close':40},{'date':1793797200,'close':42}]}}]})
    fallback=Mock(return_value={})
    monkeypatch.setattr(market_data,'yahoo_market_snapshot',fallback)
    result=market_data.market_snapshot('ITUB4','1d')
    fallback.assert_called_once_with('ITUB4.SA','1d')
    assert result['source']=='brapi' and result['price']==42 and len(result['points'])==2


def test_public_fallback_works_without_primary_key(monkeypatch):
    monkeypatch.delenv('BRAPI_API_KEY',raising=False)
    market_data._cache.clear()
    fallback=Mock(return_value={'symbol':'ITUB4.SA','price':42,'points':[{'time':'2021-11-04','close':20},
        {'time':'2026-11-04','close':42}],'source':'Yahoo Finance'})
    monkeypatch.setattr(market_data,'yahoo_market_snapshot',fallback)
    assert market_data.market_snapshot('ITUB4','5y')['symbol']=='ITUB4'
    fallback.assert_called_once_with('ITUB4.SA','5y')


def test_international_five_years_uses_calendar_start_date(monkeypatch):
    from datetime import datetime,timezone
    monkeypatch.setenv('TWELVE_DATA_API_KEY','test')
    market_data._cache.clear()
    calls=[]
    def get(url,params,*args,**kwargs):
        calls.append((url,params))
        return {'symbol':'AAPL','close':'42'} if url.endswith('/quote') else {
            'meta':{'symbol':'AAPL'},'values':[{'datetime':'2021-11-04','close':'20'},
            {'datetime':'2026-11-04','close':'42'}]}
    monkeypatch.setattr(market_data,'_json',get)
    assert len(market_data.market_snapshot('AAPL','5y')['points'])==2
    now=datetime.now(timezone.utc)
    assert calls[-1][1]['start_date']==now.replace(year=now.year-5,day=min(now.day,28) if now.month==2 else now.day).strftime('%Y-%m-%d')
    assert calls[-1][1]['interval']=='1day'


def _reaction_prompt_for_table(monkeypatch, currency='BRL'):
    points = [{'time': day, 'close': close} for day, close in (
        ('2025-11-03', 9.45), ('2025-12-30', 9.31), ('2026-08-04', 12.45), ('2026-10-28', 10.78), ('2026-10-29', 10.70),
        ('2026-10-30', 10.66), ('2026-11-02', 10.60), ('2026-11-03', 10.55), ('2026-11-04', 10.48),
        ('2026-11-05', 10.90), ('2026-11-06', 11.37), ('2026-11-16', 11.00))]
    monkeypatch.setattr(market_data, 'earnings_prices', lambda *args: {'points': points, 'source': 'brapi', 'sourceUrl': 'https://brapi.dev', 'currency': currency})
    monkeypatch.setattr(market_data, 'completed_price_day', lambda symbol: '2026-11-16')
    return market_data.reaction_prompt('PNVL3', 'São Paulo, 5 de novembro de 2026 – A Panvel anuncia seus resultados')


def test_reaction_table_uses_verified_prices_in_portuguese(monkeypatch):
    prompt = _reaction_prompt_for_table(monkeypatch)
    analysis = '<!-- compact-quarterly -->\nTexto.\n\n**Reação do mercado:** A ação subiu.\n\n**Conclusão IA:** Bom.'
    result = market_data.with_reaction_table(analysis, prompt)
    lines = result.splitlines()
    start = lines.index('**Reação do mercado:**')
    assert lines[start + 2] == '| Janela | De | Até | Variação |'
    assert '| Reação (1º pregão) | 04/11/2026 · R$ 10,48 | 06/11/2026 · R$ 11,37 | +8,5% |' in lines
    assert '| Desde a divulgação | 04/11/2026 · R$ 10,48 | 16/11/2026 · R$ 11,00 | +5,0% |' in lines
    assert '| 5 pregões antes | 28/10/2026 · R$ 10,78 | 04/11/2026 · R$ 10,48 | −2,8% |' in lines
    assert 'A ação subiu.' in result and result.index('| Janela') < result.index('A ação subiu.')
    assert market_data.with_reaction_table(result, prompt) == result


def test_reaction_table_in_english_and_skips_without_data(monkeypatch):
    prompt = _reaction_prompt_for_table(monkeypatch, 'USD')
    result = market_data.with_reaction_table('**Market reaction:**\n\nShares rose.', prompt)
    assert '| Reaction (1st session) | Nov 4, 2026 · $10.48 | Nov 6, 2026 · $11.37 | +8.5% |' in result
    assert market_data.with_reaction_table('**Market reaction:** n/a', '') == '**Market reaction:** n/a\n\nEducational and informational content; not investment advice.'
    assert market_data.with_reaction_table('No heading', prompt) == 'No heading'


def test_reaction_section_ends_with_not_advice_notice_before_the_next_section():
    notice = 'Conteúdo educativo e informativo; não é recomendação de investimento.'
    text = '**Reação do mercado:**\n\nA ação caiu.\n\n**8. Conclusão da IA**\n\nTom: misto.'
    result = market_data.with_reaction_table(text, '')
    assert result.index('A ação caiu.') < result.index(notice) < result.index('**8. Conclusão da IA**')
    assert result.count(notice) == 1 and market_data.with_reaction_table(result, '') == result
    assert market_data.with_reaction_table('**Reação do mercado:** ok', '').endswith(notice)


def test_compact_thesis_keeps_reaction_table(monkeypatch):
    from quarterly_results import quarterly_thesis
    prompt = _reaction_prompt_for_table(monkeypatch)
    text = market_data.with_reaction_table('<!-- compact-quarterly -->\nSeção 5: Conclusão\n**Reação do mercado:**\nSubiu.\n\nSeção 6: Nota Final\nNota Geral: 4/5', prompt)
    assert '| Reação (1º pregão) |' in quarterly_thesis(text)


def test_call_transcript_date_anchors_the_reaction_window(monkeypatch):
    _reaction_prompt_for_table(monkeypatch)
    transcript = 'Fras-le S.A. (FRAS3) Q3 2026 Earnings Call Transcript\nNov 5, 2026\nOperator: Good morning.'
    assert market_data.reaction_prompt('FRAS3', transcript) == ''
    assert '"publicationDateFromRelease": "2026-11-05"' in market_data.reaction_prompt('FRAS3', transcript, True)
    pt = 'Transcrição da teleconferência de resultados do 3T26 – 5 de novembro de 2026'
    assert '"publicationDateFromRelease": "2026-11-05"' in market_data.reaction_prompt('FRAS3', pt, True)
