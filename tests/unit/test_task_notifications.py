from datetime import datetime

import pytest

from app.bot.services import task_notifications


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text):
        self.messages.append((chat_id, text))


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query, params=None):
        self.executed.append((query, params))
        return self

    async def fetchall(self):
        return self.rows


class FakeDbConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def cursor(self, *args, **kwargs):
        return self.cursor_obj


class FakeConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, conn):
        self.conn = conn

    def connection(self):
        return FakeConnectionContext(self.conn)


class FrozenDateTime:
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 1, 1, 0, 40, tzinfo=tz)


@pytest.mark.asyncio
async def test_check_expiring_tasks_does_not_notify_when_no_tasks():
    cursor = FakeCursor(rows=[])
    pool = FakePool(FakeDbConnection(cursor))
    bot = FakeBot()

    await task_notifications.check_expiring_tasks(bot=bot, db_pool=pool)

    assert bot.messages == []
    assert "FROM tasks" in cursor.executed[0][0]


@pytest.mark.asyncio
async def test_check_expiring_tasks_sends_notification_and_marks_task_notified(monkeypatch):
    monkeypatch.setattr(task_notifications, "datetime", FrozenDateTime)

    cursor = FakeCursor(
        rows=[
            {
                "id": 10,
                "user_id": 123,
                "description": "Test task",
                "start_time": datetime(2026, 1, 1, 0, 0),
                "deadline": datetime(2026, 1, 1, 1, 0),
                "status": "in_progress",
                "notified": False,
            }
        ]
    )

    pool = FakePool(FakeDbConnection(cursor))
    bot = FakeBot()

    await task_notifications.check_expiring_tasks(bot=bot, db_pool=pool)

    assert len(bot.messages) == 1
    assert bot.messages[0][0] == 123
    assert "Test task" in bot.messages[0][1]

    assert "UPDATE tasks" in cursor.executed[1][0]
    assert cursor.executed[1][1] == (10,)