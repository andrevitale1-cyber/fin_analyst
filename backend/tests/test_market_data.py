from unittest.mock import Mock
import pytest
import market_data

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
