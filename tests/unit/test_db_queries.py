from datetime import timedelta
from typing import Any

import pytest

from app.bot.entities.group import Group
from app.bot.entities.user import User
from app.bot.enums.roles import TaskStatus, UserRole
from app.infastructure.database import db


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.executed_queries = []

    async def execute(self, query, params=None):
        self.executed_queries.append((query, params))
        return self

    @property
    def executed_query(self):
        return self.executed_queries[-1][0]

    @property
    def executed_params(self):
        return self.executed_queries[-1][1]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def fetchone(self):
        return self.fetchone_result

    async def fetchall(self):
        return self.fetchall_result


class FakeConnection:
    def __init__(self, cursor: FakeCursor):
        self.cursor_instance = cursor

    def cursor(self, *args, **kwargs):
        return self.cursor_instance


@pytest.mark.asyncio
async def test_add_user_executes_insert_with_expected_params():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    user = User(
        user_id=123,
        user_name="username",
        lang="ru",
        role=UserRole.USER.value,
        free_time_at_week=timedelta(hours=5),
        raiting=10,
    )

    await db.add_user(conn, user=user)

    assert "INSERT INTO users" in cursor.executed_query
    assert cursor.executed_params["user_id"] == 123
    assert cursor.executed_params["username"] == "username"
    assert cursor.executed_params["language"] == "ru"
    assert cursor.executed_params["role"] == "user"
    assert cursor.executed_params["is_alive"] is True
    assert cursor.executed_params["banned"] is False
    assert cursor.executed_params["free_time"] == timedelta(hours=5)
    assert cursor.executed_params["raiting"] == 10


@pytest.mark.asyncio
async def test_get_user_lang_returns_language_when_user_exists():
    cursor = FakeCursor(fetchone_result=("ru",))
    conn = FakeConnection(cursor)

    result = await db.get_user_lang(conn, user_id=123)

    assert result == "ru"
    assert "SELECT language FROM users" in cursor.executed_query
    assert cursor.executed_params == (123,)


@pytest.mark.asyncio
async def test_get_user_lang_returns_none_when_user_not_found():
    cursor = FakeCursor(fetchone_result=None)
    conn = FakeConnection(cursor)

    result = await db.get_user_lang(conn, user_id=999)

    assert result is None


@pytest.mark.asyncio
async def test_get_user_role_returns_user_role_enum():
    cursor = FakeCursor(fetchone_result=("admin",))
    conn = FakeConnection(cursor)

    result = await db.get_user_role(conn, user_id=123)

    assert result == UserRole.ADMIN


@pytest.mark.asyncio
async def test_change_user_banned_status_by_id_executes_update():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    await db.change_user_banned_status_by_id(conn, user_id=123, banned=True)

    assert "UPDATE users" in cursor.executed_query
    assert "SET banned = %s" in cursor.executed_query
    assert cursor.executed_params == (True, 123)


@pytest.mark.asyncio
async def test_update_user_time_executes_update():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    await db.update_user_time(conn, user_id=123, time=timedelta(hours=3))

    assert "UPDATE users" in cursor.executed_query
    assert "SET free_time = %s" in cursor.executed_query
    assert cursor.executed_params == (timedelta(hours=3), 123)


@pytest.mark.asyncio
async def test_add_group_executes_insert_with_expected_params():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    group = Group(
        group_id=777,
        title="Test Group",
        name="test_group",
        is_alive=True,
        banned=False,
    )

    await db.add_group(conn, group=group)

    assert "INSERT INTO groups" in cursor.executed_query
    assert cursor.executed_params == {
        "group_id": 777,
        "title": "Test Group",
        "name": "test_group",
        "is_alive": True,
        "banned": False,
    }


@pytest.mark.asyncio
async def test_get_group_free_tasks_returns_rows():
    rows = [
        {
            "id": 1,
            "description": "Task 1",
            "status": TaskStatus.PENDING.value,
            "group_id": 777,
        }
    ]
    cursor = FakeCursor(fetchall_result=rows)
    conn = FakeConnection(cursor)

    result = await db.get_group_free_tasks(conn, group_id=777)

    assert result == rows
    assert "FROM tasks" in cursor.executed_query
    assert "WHERE group_id = %s AND status = %s" in cursor.executed_query

@pytest.mark.asyncio
async def test_get_user_alive_status_returns_bool():
    cursor = FakeCursor(fetchone_result=(True,))
    conn = FakeConnection(cursor)

    result = await db.get_user_alive_status(conn, user_id=123)

    assert result is True
    assert "SELECT is_alive FROM users" in cursor.executed_query
    assert cursor.executed_params == (123,)   

@pytest.mark.asyncio
async def test_get_user_banned_status_by_username_returns_bool():
    cursor = FakeCursor(fetchone_result=(False,))
    conn = FakeConnection(cursor)

    result = await db.get_user_banned_status_by_username(
        conn,
        username="username",
    )

    assert result is False
    assert "SELECT banned FROM users" in cursor.executed_query
    assert cursor.executed_params == ("username",)

@pytest.mark.asyncio
async def test_add_to_user_group_table_executes_insert():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    await db.add_to_user_group_table(
        conn,
        user_id=123,
        group_id=777,
    )

    assert "INSERT INTO user_group" in cursor.executed_query
    assert cursor.executed_params == {
        "user_id": 123,
        "group_id": 777,
    }

@pytest.mark.asyncio
async def test_user_accept_task_updates_status_and_user():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    result = await db.user_accept_task(
        conn,
        task_id=10,
        status="in_progress",
        user_id=123,
    )

    assert result is True
    assert "UPDATE tasks" in cursor.executed_query
    assert "SET status = %s, user_id = %s" in cursor.executed_query
    assert cursor.executed_params == ("in_progress", 123, 10)

    