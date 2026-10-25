from contextlib import contextmanager
import sqlite3

from fastapi import FastAPI, HTTPException
import pytest
from pydantic import ValidationError

import report_feedback as feedback
from report_auth import require_report_user


@pytest.fixture
def clients(monkeypatch):
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript("""CREATE TABLE report_feedback(user_id TEXT,report_kind TEXT,report_id TEXT,vote INTEGER,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(user_id,report_kind,report_id));
      CREATE TABLE historico(id INTEGER,user_id TEXT);
      INSERT INTO historico VALUES(1,'user_owner');
      CREATE TABLE full_reports(id TEXT,is_public BOOLEAN,content TEXT);
      INSERT INTO full_reports VALUES('private',0,'{}'),('public',1,'{}'),('retired',1,'{"public_library_state":"retired"}');
      CREATE TABLE full_report_access(user_id TEXT,report_id TEXT);
      INSERT INTO full_report_access VALUES('user_owner','private');""")

    class Connection:
        @contextmanager
        def cursor(self):
            class Cursor:
                def execute(self, sql, args=()):
                    self.result=db.execute(sql.replace('%s','?').replace('NOW()','CURRENT_TIMESTAMP'), args)
                def fetchone(self): return self.result.fetchone()
            yield Cursor()
        def commit(self): db.commit()
        def close(self): pass
    monkeypatch.setattr(feedback, 'connection', Connection)
    app=FastAPI();app.include_router(feedback.router)
    yield app, db
    db.close()


def test_requires_login(clients):
    with pytest.raises(HTTPException) as error:
        require_report_user("")
    assert error.value.status_code==401
    # Route schema also enforces valid kinds and a bounded report id.
    schema=clients[0].openapi()
    assert len(schema['paths'])==1


def test_rating_is_persistent_editable_and_per_reader(clients):
    _, db=clients
    rid='editorial-aapl-20261022'
    assert feedback.get_feedback('full',rid,'user_owner')=={'vote':None}
    assert feedback.save_feedback('full',feedback.Rating(vote=1),rid,'user_owner')=={'vote':1}
    assert feedback.get_feedback('full',rid,'user_owner')=={'vote':1}
    assert feedback.save_feedback('full',feedback.Rating(vote=-1),rid,'user_owner')=={'vote':-1}
    assert db.execute('SELECT COUNT(*) FROM report_feedback').fetchone()[0]==1
    assert feedback.get_feedback('full',rid,'user_other')=={'vote':None}
    with pytest.raises(ValidationError):feedback.Rating(vote=0)


@pytest.mark.parametrize('kind,report_id,owner,expected',[
    ('full','private','user_owner',200),('full','private','user_other',404),
    ('full','public','user_other',200),('full','retired','user_owner',404),
    ('full','nonexistent','user_owner',404),('analysis','1','user_owner',200),
    ('analysis','1','user_other',404),('analysis','bad-id','user_owner',404),
])
def test_feedback_respects_report_visibility(clients,kind,report_id,owner,expected):
    for operation in [lambda:feedback.get_feedback(kind,report_id,owner),lambda:feedback.save_feedback(kind,feedback.Rating(vote=1),report_id,owner)]:
        if expected==200:operation()
        else:
            with pytest.raises(HTTPException) as error:operation()
            assert error.value.status_code==expected
