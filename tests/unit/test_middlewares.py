from types import SimpleNamespace

import pytest

from app.bot.midlewares import lang_settings, shadow_ban
from app.bot.midlewares.lang_settings import LangSettingsMiddleware
from app.bot.midlewares.shadow_ban import ShadowBanMiddleware


class FakeCallbackQuery:
    def __init__(self, data: str):
        self.data = data
        self.answered = False

    async def answer(self):
        self.answered = True


class FakeEvent:
    def __init__(self, callback_query=None):
        self.callback_query = callback_query


class FakeState:
    def __init__(self, data=None):
        self.data = data or {}
        self.set_data_calls = []

    async def get_data(self):
        return self.data

    async def set_data(self, data):
        self.data = data
        self.set_data_calls.append(data)


@pytest.mark.asyncio
async def test_shadow_ban_calls_handler_when_no_user():
    middleware = ShadowBanMiddleware()
    handler_called = False

    async def handler(event, data):
        nonlocal handler_called
        handler_called = True
        return "OK"

    result = await middleware(
        handler=handler,
        event=FakeEvent(),
        data={},
    )

    assert result == "OK"
    assert handler_called is True


@pytest.mark.asyncio
async def test_shadow_ban_raises_error_when_conn_missing():
    middleware = ShadowBanMiddleware()

    async def handler(event, data):
        return "OK"

    data = {
        "event_from_user": SimpleNamespace(id=123),
    }

    with pytest.raises(RuntimeError, match="Missing database connection"):
        await middleware(
            handler=handler,
            event=FakeEvent(),
            data=data,
        )


@pytest.mark.asyncio
async def test_shadow_ban_blocks_banned_user(monkeypatch):
    async def fake_get_user_banned_status_by_id(conn, user_id):
        return True

    monkeypatch.setattr(
        shadow_ban,
        "get_user_banned_status_by_id",
        fake_get_user_banned_status_by_id,
    )

    middleware = ShadowBanMiddleware()
    callback_query = FakeCallbackQuery(data="anything")
    event = FakeEvent(callback_query=callback_query)
    handler_called = False

    async def handler(event, data):
        nonlocal handler_called
        handler_called = True
        return "OK"

    result = await middleware(
        handler=handler,
        event=event,
        data={
            "event_from_user": SimpleNamespace(id=123),
            "conn": object(),
        },
    )

    assert result is None
    assert callback_query.answered is True
    assert handler_called is False


@pytest.mark.asyncio
async def test_shadow_ban_allows_not_banned_user(monkeypatch):
    async def fake_get_user_banned_status_by_id(conn, user_id):
        return False

    monkeypatch.setattr(
        shadow_ban,
        "get_user_banned_status_by_id",
        fake_get_user_banned_status_by_id,
    )

    middleware = ShadowBanMiddleware()
    handler_called = False

    async def handler(event, data):
        nonlocal handler_called
        handler_called = True
        return "OK"

    result = await middleware(
        handler=handler,
        event=FakeEvent(),
        data={
            "event_from_user": SimpleNamespace(id=123),
            "conn": object(),
        },
    )

    assert result == "OK"
    assert handler_called is True


@pytest.mark.asyncio
async def test_lang_settings_calls_handler_when_no_user():
    middleware = LangSettingsMiddleware()
    handler_called = False

    async def handler(event, data):
        nonlocal handler_called
        handler_called = True
        return "OK"

    result = await middleware(
        handler=handler,
        event=FakeEvent(callback_query=FakeCallbackQuery("ru")),
        data={},
    )

    assert result == "OK"
    assert handler_called is True


@pytest.mark.asyncio
async def test_lang_settings_sets_user_lang_from_callback():
    middleware = LangSettingsMiddleware()
    state = FakeState(data={"user_lang": "ru"})

    async def handler(event, data):
        return "OK"

    result = await middleware(
        handler=handler,
        event=FakeEvent(callback_query=FakeCallbackQuery("en")),
        data={
            "event_from_user": SimpleNamespace(id=123),
            "locales": ["ru", "en"],
            "state": state,
        },
    )

    assert result == "OK"
    assert state.data["user_lang"] == "en"


@pytest.mark.asyncio
async def test_lang_settings_cancel_resets_user_lang():
    middleware = LangSettingsMiddleware()
    state = FakeState(data={"user_lang": "en"})

    async def handler(event, data):
        return "OK"

    result = await middleware(
        handler=handler,
        event=FakeEvent(callback_query=FakeCallbackQuery("cancel_lang_button_data")),
        data={
            "event_from_user": SimpleNamespace(id=123),
            "locales": ["ru", "en"],
            "state": state,
        },
    )

    assert result == "OK"
    assert state.data["user_lang"] is None