from types import SimpleNamespace

import pytest

from app.bot.handlers import group, group_events
from app.bot.handlers.group import group_title_changed, on_bot_added
from app.bot.handlers.group_events import bot_removed_from_group


class FakeBot:
    def __init__(self):
        self.sent_messages = []

    async def get_me(self):
        return SimpleNamespace(username="SuperDuperBot")

    async def send_message(self, chat_id, text):
        self.sent_messages.append({"chat_id": chat_id, "text": text})


class FakeChat:
    def __init__(self, chat_id=-100, title="Test Group", username="test_group"):
        self.id = chat_id
        self.title = title
        self.username = username


class FakeChatMemberUpdated:
    def __init__(self):
        self.from_user = SimpleNamespace(id=123, username="tester")
        self.chat = FakeChat()
        self.bot = FakeBot()


class FakeMessage:
    def __init__(self):
        self.new_chat_title = "New Group Title"
        self.chat = SimpleNamespace(id=-100)


@pytest.mark.asyncio
async def test_on_bot_added_creates_new_group_and_user_group_link(monkeypatch):
    calls = {
        "add_user_from_event": 0,
        "add_group": 0,
        "add_to_user_group_table": 0,
    }

    async def fake_add_user_from_event(conn, event):
        calls["add_user_from_event"] += 1

    async def fake_get_group(conn, group_id):
        return None

    async def fake_add_group(conn, group):
        calls["add_group"] += 1
        assert group.group_id == -100
        assert group.title == "Test Group"
        assert group.name == "test_group"

    async def fake_add_to_user_group_table(conn, user_id, group_id):
        calls["add_to_user_group_table"] += 1
        assert user_id == 123
        assert group_id == -100

    monkeypatch.setattr(group, "add_user_from_event", fake_add_user_from_event)
    monkeypatch.setattr(group, "get_group", fake_get_group)
    monkeypatch.setattr(group, "add_group", fake_add_group)
    monkeypatch.setattr(group, "add_to_user_group_table", fake_add_to_user_group_table)

    event = FakeChatMemberUpdated()
    i18n = {
        "add_to_group": "Привет, ",
    }

    await on_bot_added(event=event, i18n=i18n, conn=object())

    assert calls == {
        "add_user_from_event": 1,
        "add_group": 1,
        "add_to_user_group_table": 1,
    }
    assert event.bot.sent_messages[0]["chat_id"] == -100
    assert "https://t.me/SuperDuperBot?start=group_-100" in event.bot.sent_messages[0]["text"]


@pytest.mark.asyncio
async def test_on_bot_added_existing_group_does_not_create_duplicate(monkeypatch):
    calls = {
        "add_group": 0,
        "add_to_user_group_table": 0,
    }

    async def fake_add_user_from_event(conn, event):
        return None

    async def fake_get_group(conn, group_id):
        return {"group_id": group_id}

    async def fake_add_group(conn, group):
        calls["add_group"] += 1

    async def fake_add_to_user_group_table(conn, user_id, group_id):
        calls["add_to_user_group_table"] += 1

    monkeypatch.setattr(group, "add_user_from_event", fake_add_user_from_event)
    monkeypatch.setattr(group, "get_group", fake_get_group)
    monkeypatch.setattr(group, "add_group", fake_add_group)
    monkeypatch.setattr(group, "add_to_user_group_table", fake_add_to_user_group_table)

    event = FakeChatMemberUpdated()

    await on_bot_added(
        event=event,
        i18n={"add_to_group": "Привет, "},
        conn=object(),
    )

    assert calls["add_group"] == 0
    assert calls["add_to_user_group_table"] == 0
    assert event.bot.sent_messages


@pytest.mark.asyncio
async def test_group_title_changed_updates_group_title(monkeypatch):
    calls = {}

    async def fake_set_group_title(conn, group_id, new_title):
        calls["group_id"] = group_id
        calls["new_title"] = new_title

    monkeypatch.setattr(group, "set_group_title", fake_set_group_title)

    message = FakeMessage()

    await group_title_changed(
        message=message,
        conn=object(),
        i18n={},
    )

    assert calls == {
        "group_id": -100,
        "new_title": "New Group Title",
    }


@pytest.mark.asyncio
async def test_bot_removed_from_group_deletes_group(monkeypatch):
    calls = {}

    async def fake_delete_group(conn, group_id):
        calls["group_id"] = group_id

    monkeypatch.setattr(group_events, "delete_group", fake_delete_group)

    event = SimpleNamespace(
        chat=SimpleNamespace(id=-100, title="Test Group"),
    )

    await bot_removed_from_group(event=event, conn=object())

    assert calls["group_id"] == -100