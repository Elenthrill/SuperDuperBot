import sys
import types
from pathlib import Path
from app.bot.enums.roles import TaskStatus

import pytest

project_root = Path(__file__).resolve().parents[2]
bot_package = types.ModuleType("app.bot")
bot_package.__path__ = [str(project_root / "app" / "bot")]
sys.modules.setdefault("app.bot", bot_package)

from app.infastructure.database import db

class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.executed_queries = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query, params=None):
        self.executed_queries.append((query, params))
        return self

    async def fetchone(self):
        return self.fetchone_result

    async def fetchall(self):
        return self.fetchall_result

    @property
    def executed_query(self):
        return self.executed_queries[-1][0]

    @property
    def executed_params(self):
        return self.executed_queries[-1][1]


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def cursor(self, *args, **kwargs):
        return self.cursor_obj


@pytest.mark.asyncio
async def test_get_username_by_id_returns_username():
    cursor = FakeCursor(fetchone_result={"username": "tester"})
    conn = FakeConnection(cursor)

    result = await db.get_username_by_id(conn, user_id=123)

    assert result == "tester"
    assert "SELECT" in cursor.executed_query
    assert "username" in cursor.executed_query
    assert "FROM users" in cursor.executed_query
    assert cursor.executed_params == (123,)

@pytest.mark.asyncio
async def test_get_username_by_id_returns_none_when_not_found():
    cursor = FakeCursor(fetchone_result=None)
    conn = FakeConnection(cursor)

    result = await db.get_username_by_id(conn, user_id=123)

    assert result is None


@pytest.mark.asyncio
async def test_get_group_title_by_id_returns_title():
    cursor = FakeCursor(fetchone_result={"title": "Test Group"})
    conn = FakeConnection(cursor)

    result = await db.get_group_title_by_id(conn, group_id=-100)

    assert result == "Test Group"
    assert "SELECT" in cursor.executed_query
    assert "title" in cursor.executed_query
    assert "FROM groups" in cursor.executed_query
    assert cursor.executed_params == (-100,)

@pytest.mark.asyncio
async def test_get_group_title_by_id_returns_none_when_not_found():
    cursor = FakeCursor(fetchone_result=None)
    conn = FakeConnection(cursor)

    result = await db.get_group_title_by_id(conn, group_id=-100)

    assert result is None


@pytest.mark.asyncio
async def test_set_group_title_executes_update():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    await db.set_group_title(conn, group_id=-100, new_title="New Title")

    assert "UPDATE groups" in cursor.executed_query
    assert "SET title" in cursor.executed_query
    assert cursor.executed_params == ("New Title", -100)


@pytest.mark.asyncio
async def test_delete_group_executes_delete():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    await db.delete_group(conn, group_id=-100)

    assert "DELETE FROM groups" in cursor.executed_query
    assert cursor.executed_params == (-100,)


@pytest.mark.asyncio
async def test_get_user_groups_returns_rows():
    rows = [
        {"group_id": 1, "title": "Group 1"},
        {"group_id": 2, "title": "Group 2"},
    ]
    cursor = FakeCursor(fetchall_result=rows)
    conn = FakeConnection(cursor)

    result = await db.get_user_groups(conn, user_id=123)

    assert result == rows
    assert "SELECT" in cursor.executed_query
    assert cursor.executed_params == (123,)


@pytest.mark.asyncio
async def test_get_user_tasks_returns_rows():
    rows = [
        {"id": 1, "description": "Task 1"},
    ]
    cursor = FakeCursor(fetchall_result=rows)
    conn = FakeConnection(cursor)

    result = await db.get_user_tasks(conn, user_id=123)

    assert result == rows
    assert "SELECT" in cursor.executed_query
    assert "FROM tasks" in cursor.executed_query
    assert "WHERE user_id = %s AND status = %s" in cursor.executed_query
    assert cursor.executed_params == (123, TaskStatus.IN_PROGRESS)


@pytest.mark.asyncio
async def test_get_user_complete_tasks_returns_rows():
    rows = [
        {"id": 1, "description": "Task 1"},
    ]
    cursor = FakeCursor(fetchall_result=rows)
    conn = FakeConnection(cursor)

    result = await db.get_user_complete_tasks(conn, user_id=123)


    assert result == rows
    assert "SELECT" in cursor.executed_query
    assert "FROM tasks" in cursor.executed_query
    assert "WHERE user_id = %s AND status = %s" in cursor.executed_query
    assert cursor.executed_params == (123, TaskStatus.COMPLETED)


@pytest.mark.asyncio
async def test_get_group_completed_tasks_returns_rows():
    rows = [
        {"id": 1, "description": "Task 1"},
    ]
    cursor = FakeCursor(fetchall_result=rows)
    conn = FakeConnection(cursor)

    result = await db.get_group_completed_tasks(conn, group_id=-100)

    assert result == rows
    assert "SELECT" in cursor.executed_query
    assert "FROM tasks" in cursor.executed_query
    assert "WHERE group_id = %s AND status = %s" in cursor.executed_query
    assert cursor.executed_params == (-100, TaskStatus.COMPLETED)