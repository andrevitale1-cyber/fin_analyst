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
    monkeypatch.setattr(market_data,'market_snapshot',snapshot)
    assert market_data.reaction_prompt('MU','quarter ended February 26, 2026') == ''
    snapshot.assert_not_called()
    prompt = market_data.reaction_prompt('MU','March 18, 2026 (GLOBE NEWSWIRE) announces results')
    assert '2026-03-17' in prompt and '2026-03-19' in prompt
    assert 'não atribua causalidade' in prompt
