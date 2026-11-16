from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from uuid import uuid4
import pytest
from fastapi import HTTPException
from starlette.requests import Request
import reddit_events as events


@pytest.fixture
def cur(monkeypatch):
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    monkeypatch.setattr(events, 'connection', lambda: conn)
    return cursor


def test_payload_and_dedup(cur, monkeypatch):
    monkeypatch.setenv('REDDIT_CONVERSIONS_API_TOKEN','test-only')
    cur.fetchone.return_value = None
    post = Mock(return_value=Mock(json=lambda:{'data':{'message':'Successfully processed 1 conversion events.'}}))
    monkeypatch.setattr(events.requests,'post',post)
    events.deliver('AddToCart','same-id',{'ip_address':'127.0.0.1'},1794800000)
    event = post.call_args.kwargs['json']['events'][0]
    assert event['event_at']==1794800000000
    assert event['type']['tracking_type']=='ADD_TO_CART'
    assert event['metadata']=={'conversion_id':'same-id'}
    cur.fetchone.return_value=(1,)
    post.reset_mock()
    events.deliver('AddToCart','same-id',{},1794800000)
    post.assert_not_called()
    cur.fetchone.return_value=None
    post.return_value.json=lambda:{'error':'bad token'}
    cur.reset_mock()
    with pytest.raises(HTTPException): events.deliver('SignUp','new',{},1794800000)
    assert not any('INSERT INTO reddit_events' in c.args[0] for c in cur.execute.call_args_list)


def test_signup_is_verified_and_old_accounts_are_not_counted(cur,monkeypatch):
    monkeypatch.setattr(events,'require_report_user',lambda _: 'user_owner')
    monkeypatch.setattr(events,'milestone',lambda *_:None)
    cur.fetchone.return_value=(datetime.now(timezone.utc),)
    send=Mock()
    monkeypatch.setattr(events,'deliver',send)
    request=Request({'type':'http','headers':[(b'origin',b'https://finanalyser.com.br')],'client':('127.0.0.1',10)})
    body=events.RedditEvent(event='SignUp',event_id=uuid4())
    assert events.conversion(body,request)=={'event':None}
    send.assert_not_called()
    monkeypatch.setattr(events,'milestone',lambda *_:datetime.now(timezone.utc).timestamp()+1)
    result=events.conversion(body,request)
    assert result['event']=='SignUp' and len(result['conversionId'])==64
    bad=Request({'type':'http','headers':[(b'origin',b'https://other.example')],'client':('127.0.0.1',10)})
    with pytest.raises(HTTPException): events.conversion(body,bad)
