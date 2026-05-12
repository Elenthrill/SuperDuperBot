from types import SimpleNamespace

import pytest

from app.bot.handlers import admin


class FakeMessage:
    def __init__(self, user_id: int = 123):
        self.from_user = SimpleNamespace(id=user_id)
        self.answers = []
        self.replies = []

    async def answer(self, text=None, **kwargs):
        self.answers.append({"text": text, "kwargs": kwargs})

    async def reply(self, text=None, **kwargs):
        self.replies.append({"text": text, "kwargs": kwargs})


def make_i18n():
    return {
        "/help_admin": "Admin help",
        "empty_ban_answer": "Empty ban",
        "empty_unban_answer": "Empty unban",
        "incorrect_ban_arg": "Incorrect ban arg",
        "incorrect_unban_arg": "Incorrect unban arg",
        "already_banned": "Already banned",
        "successfully_banned": "Successfully banned",
        "successfully_unbanned": "Successfully unbanned",
        "no_user": "No user",
        "not_banned": "Not banned",
    }


@pytest.mark.asyncio
async def test_admin_help_command_answers_i18n_text():
    message = FakeMessage()

    await admin.process_admin_help_command(message=message, i18n=make_i18n())

    assert message.answers == [{"text": "Admin help", "kwargs": {}}]


@pytest.mark.asyncio
async def test_ban_command_without_args_replies_empty_answer():
    message = FakeMessage()
    command = SimpleNamespace(args=None)

    await admin.process_ban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert message.replies[0]["text"] == "Empty ban"


@pytest.mark.asyncio
async def test_ban_command_rejects_incorrect_argument():
    message = FakeMessage()
    command = SimpleNamespace(args="not-a-user")

    await admin.process_ban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert message.replies[0]["text"] == "Incorrect ban arg"


@pytest.mark.asyncio
async def test_ban_command_replies_when_user_not_found(monkeypatch):
    async def fake_get_user_banned_status_by_id(conn, user_id):
        return None

    monkeypatch.setattr(
        admin,
        "get_user_banned_status_by_id",
        fake_get_user_banned_status_by_id,
    )

    message = FakeMessage()
    command = SimpleNamespace(args="123")

    await admin.process_ban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert message.replies[0]["text"] == "Incorrect ban arg"


@pytest.mark.asyncio
async def test_ban_command_replies_when_user_already_banned(monkeypatch):
    async def fake_get_user_banned_status_by_username(conn, username):
        assert username == "tester"
        return True

    monkeypatch.setattr(
        admin,
        "get_user_banned_status_by_username",
        fake_get_user_banned_status_by_username,
    )

    message = FakeMessage()
    command = SimpleNamespace(args="@tester")

    await admin.process_ban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert message.replies[0]["text"] == "Already banned"


@pytest.mark.asyncio
async def test_ban_command_bans_user_by_id(monkeypatch):
    calls = []

    async def fake_get_user_banned_status_by_id(conn, user_id):
        return False

    async def fake_change_user_banned_status_by_id(conn, user_id, banned):
        calls.append((user_id, banned))

    monkeypatch.setattr(
        admin,
        "get_user_banned_status_by_id",
        fake_get_user_banned_status_by_id,
    )
    monkeypatch.setattr(
        admin,
        "change_user_banned_status_by_id",
        fake_change_user_banned_status_by_id,
    )

    message = FakeMessage()
    command = SimpleNamespace(args="123")

    await admin.process_ban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert calls == [(123, True)]
    assert message.replies[0]["text"] == "Successfully banned"


@pytest.mark.asyncio
async def test_ban_command_bans_user_by_username(monkeypatch):
    calls = []

    async def fake_get_user_banned_status_by_username(conn, username):
        return False

    async def fake_change_user_banned_status_by_username(conn, username, banned):
        calls.append((username, banned))

    monkeypatch.setattr(
        admin,
        "get_user_banned_status_by_username",
        fake_get_user_banned_status_by_username,
    )
    monkeypatch.setattr(
        admin,
        "change_user_banned_status_by_username",
        fake_change_user_banned_status_by_username,
    )

    message = FakeMessage()
    command = SimpleNamespace(args="@tester")

    await admin.process_ban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert calls == [("tester", True)]
    assert message.replies[0]["text"] == "Successfully banned"


@pytest.mark.asyncio
async def test_unban_command_without_args_replies_empty_answer():
    message = FakeMessage()
    command = SimpleNamespace(args=None)

    await admin.process_unban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert message.replies[0]["text"] == "Empty unban"


@pytest.mark.asyncio
async def test_unban_command_rejects_incorrect_argument():
    message = FakeMessage()
    command = SimpleNamespace(args="tester")

    await admin.process_unban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert message.replies[0]["text"] == "Incorrect unban arg"


@pytest.mark.asyncio
async def test_unban_command_replies_when_user_not_found(monkeypatch):
    async def fake_get_user_banned_status_by_id(conn, user_id):
        return None

    monkeypatch.setattr(
        admin,
        "get_user_banned_status_by_id",
        fake_get_user_banned_status_by_id,
    )

    message = FakeMessage()
    command = SimpleNamespace(args="123")

    await admin.process_unban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert message.replies[0]["text"] == "No user"


@pytest.mark.asyncio
async def test_unban_command_replies_when_user_is_not_banned(monkeypatch):
    async def fake_get_user_banned_status_by_username(conn, username):
        return False

    monkeypatch.setattr(
        admin,
        "get_user_banned_status_by_username",
        fake_get_user_banned_status_by_username,
    )

    message = FakeMessage()
    command = SimpleNamespace(args="@tester")

    await admin.process_unban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert message.replies[0]["text"] == "Not banned"


@pytest.mark.asyncio
async def test_unban_command_unbans_user_by_username(monkeypatch):
    calls = []

    async def fake_get_user_banned_status_by_username(conn, username):
        return True

    async def fake_change_user_banned_status_by_username(conn, username, banned):
        calls.append((username, banned))

    monkeypatch.setattr(
        admin,
        "get_user_banned_status_by_username",
        fake_get_user_banned_status_by_username,
    )
    monkeypatch.setattr(
        admin,
        "change_user_banned_status_by_username",
        fake_change_user_banned_status_by_username,
    )

    message = FakeMessage()
    command = SimpleNamespace(args="@tester")

    await admin.process_unban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert calls == [("tester", False)]
    assert message.replies[0]["text"] == "Successfully unbanned"


@pytest.mark.asyncio
async def test_unban_command_unbans_user_by_id_currently_has_no_success_reply(monkeypatch):
    """
    Этот тест фиксирует текущее поведение.

    Сейчас при /unban 123 пользователь разбанивается,
    но сообщение об успешном разбане не отправляется.
    Похоже на баг в admin.py.
    """
    calls = []

    async def fake_get_user_banned_status_by_id(conn, user_id):
        return True

    async def fake_change_user_banned_status_by_id(conn, user_id, banned):
        calls.append((user_id, banned))

    monkeypatch.setattr(
        admin,
        "get_user_banned_status_by_id",
        fake_get_user_banned_status_by_id,
    )
    monkeypatch.setattr(
        admin,
        "change_user_banned_status_by_id",
        fake_change_user_banned_status_by_id,
    )

    message = FakeMessage()
    command = SimpleNamespace(args="123")

    await admin.process_unban_command(
        message=message,
        command=command,
        conn=object(),
        i18n=make_i18n(),
    )

    assert calls == [(123, False)]
    assert message.replies == []