from unittest.mock import Mock
import pytest
import market_data

@pytest.mark.parametrize('period', ['1d', '5d'])
def test_b3_retries_restricted_intraday_with_daily_closes(monkeypatch, period):
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
    ('SEATTLE—(BUSINESS WIRE) October 29, 2026—Amazon today announced financial results for its third quarter ended September 30, 2026.', '2026-10-29'),
    ('São Paulo, 29 de outubro de 2026 — divulga os resultados do trimestre encerrado em 30 de setembro de 2026.', '2026-10-29'),
])
def test_publication_date_is_not_confused_with_quarter_end(monkeypatch, text, event):
    prices = Mock(return_value={'points':[{'time':'2026-10-28','close':100},
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
    assert params['start_date']=='2024-10-21' and params['end_date']=='2024-11-07'
    assert params['interval']=='1day' and params['outputsize']==30


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


def test_friday_release_waits_for_monday_not_weekend(monkeypatch):
    monkeypatch.setattr(market_data,'earnings_prices',lambda *a:{
        'points':[{'time':'2026-10-29','close':100},{'time':'2026-10-30','close':101}],
        'source':'test','sourceUrl':'https://example.com'})
    assert market_data.reaction_prompt('AMZN','October 30, 2026 Amazon announces results')==''


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
