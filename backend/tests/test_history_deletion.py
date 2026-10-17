import importlib
import sqlite3
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


@pytest.fixture
def history_database(monkeypatch):
    monkeypatch.setattr("psycopg2.connect", Mock())
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
    main = importlib.import_module("main")
    db = sqlite3.connect(":memory:")
    db.executescript("CREATE TABLE historico (id INTEGER, user_id TEXT); INSERT INTO historico VALUES (1,'user_one'),(2,'user_two');")
    class Cursor:
        def execute(self, sql, params): self.cursor = db.execute(sql.replace("%s", "?"), params)
        def fetchone(self): return self.cursor.fetchone()
        def close(self): pass
    class Connection:
        def cursor(self): return Cursor()
        def commit(self): db.commit()
        def rollback(self): db.rollback()
        def close(self): pass
    monkeypatch.setattr(main, "get_db_connection", Connection)
    yield main, db
    db.close()


def test_history_deletion_requires_authentication(history_database):
    main, db = history_database
    assert TestClient(main.app).delete("/api/history/1").status_code == 401
    assert db.execute("SELECT COUNT(*) FROM historico").fetchone()[0] == 2


def test_history_deletion_only_removes_the_authenticated_users_analysis(history_database):
    main, db = history_database
    main.delete_history_item(1, "user_one")
    assert db.execute("SELECT * FROM historico").fetchall() == [(2, "user_two")]


@pytest.mark.parametrize("item_id", [2, 999])
def test_history_deletion_rejects_another_users_analysis_and_unknown_id(history_database, item_id):
    main, db = history_database
    with pytest.raises(HTTPException) as error: main.delete_history_item(item_id, "user_one")
    assert error.value.status_code == 404
    assert db.execute("SELECT COUNT(*) FROM historico").fetchone()[0] == 2
