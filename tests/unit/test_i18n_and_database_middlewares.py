from types import SimpleNamespace

import pytest
from aiogram.enums import UpdateType
from aiogram.types import ContentType

from app.bot.midlewares import i18n as i18n_middleware
from app.bot.midlewares import add_user_msg_in_db
from app.bot.midlewares.database import DataBaseMiddleware
from app.bot.midlewares.i18n import TranslatorMiddleware
from app.bot.midlewares.add_user_msg_in_db import AddUserMessageInDatabase


class FakeState:
    def __init__(self, data=None):
        self.data = data or {}

    async def get_data(self):
        return self.data


class FakeMessage:
    def __init__(
        self,
        text="hello",
        caption=None,
        content_type=ContentType.TEXT,
        user_id=123,
    ):
        self.text = text
        self.caption = caption
        self.content_type = content_type
        self.from_user = SimpleNamespace(id=user_id)
        self.photo = None
        self.video = None


class FakeUpdate:
    def __init__(self, message=None, event_type=UpdateType.MESSAGE):
        self.message = message
        self.event_type = event_type


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self):
        self.transaction_started = False

    def transaction(self):
        self.transaction_started = True
        return FakeTransaction()


class FakePoolConnectionContext:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, tb):
        return False

class FakePool:
    def __init__(self, connection):
        self._connection = connection

    def connection(self):
        return FakePoolConnectionContext(self._connection)

@pytest.mark.asyncio
async def test_translator_uses_lang_from_state_without_db_call():
    middleware = TranslatorMiddleware()
    handler_called = False

    async def handler(event, data):
        nonlocal handler_called
        handler_called = True
        return "OK"

    data = {
        "event_from_user": SimpleNamespace(id=123, language_code="ru"),
        "state": FakeState({"user_lang": "en"}),
        "translations": {
            "default": "ru",
            "ru": {"hello": "Привет"},
            "en": {"hello": "Hello"},
        },
        "conn": object(),
    }

    result = await middleware(handler, event=object(), data=data)

    assert result == "OK"
    assert handler_called is True
    assert data["i18n"] == {"hello": "Hello"}


@pytest.mark.asyncio
async def test_translator_uses_lang_from_database(monkeypatch):
    async def fake_get_user_lang(conn, user_id):
        return "ru"

    monkeypatch.setattr(i18n_middleware, "get_user_lang", fake_get_user_lang)

    middleware = TranslatorMiddleware()

    async def handler(event, data):
        return "OK"

    data = {
        "event_from_user": SimpleNamespace(id=123, language_code="en"),
        "state": FakeState({}),
        "translations": {
            "default": "en",
            "ru": {"hello": "Привет"},
            "en": {"hello": "Hello"},
        },
        "conn": object(),
    }

    result = await middleware(handler, event=object(), data=data)

    assert result == "OK"
    assert data["i18n"] == {"hello": "Привет"}


@pytest.mark.asyncio
async def test_translator_falls_back_to_default_translation(monkeypatch):
    async def fake_get_user_lang(conn, user_id):
        return "unknown"

    monkeypatch.setattr(i18n_middleware, "get_user_lang", fake_get_user_lang)

    middleware = TranslatorMiddleware()

    async def handler(event, data):
        return "OK"

    data = {
        "event_from_user": SimpleNamespace(id=123, language_code="unknown"),
        "state": FakeState({}),
        "translations": {
            "default": "ru",
            "ru": {"hello": "Привет"},
        },
        "conn": object(),
    }

    await middleware(handler, event=object(), data=data)

    assert data["i18n"] == {"hello": "Привет"}


@pytest.mark.asyncio
async def test_translator_raises_when_conn_missing():
    middleware = TranslatorMiddleware()

    async def handler(event, data):
        return "OK"

    data = {
        "event_from_user": SimpleNamespace(id=123, language_code="ru"),
        "state": FakeState({}),
        "translations": {
            "default": "ru",
            "ru": {"hello": "Привет"},
        },
    }

    with pytest.raises(RuntimeError, match="Missing database connection"):
        await middleware(handler, event=object(), data=data)


@pytest.mark.asyncio
async def test_database_middleware_adds_connection_to_data():
    connection = FakeConnection()
    middleware = DataBaseMiddleware()
    handler_called = False

    async def handler(event, data):
        nonlocal handler_called
        handler_called = True
        assert data["conn"] is connection
        return "OK"

    result = await middleware(
        handler=handler,
        event=object(),
        data={"db_pool": FakePool(connection)},
    )

    assert result == "OK"
    assert handler_called is True
    assert connection.transaction_started is True


@pytest.mark.asyncio
async def test_database_middleware_raises_when_pool_missing():
    middleware = DataBaseMiddleware()

    async def handler(event, data):
        return "OK"

    with pytest.raises(RuntimeError, match="Missing db_pool"):
        await middleware(handler=handler, event=object(), data={})


@pytest.mark.asyncio
async def test_add_user_message_middleware_saves_text_message(monkeypatch):
    saved = {}

    async def fake_add_user_message(conn, user_id, text, photo, video):
        saved["conn"] = conn
        saved["user_id"] = user_id
        saved["text"] = text
        saved["photo"] = photo
        saved["video"] = video

    monkeypatch.setattr(
        add_user_msg_in_db,
        "add_user_message",
        fake_add_user_message,
    )

    middleware = AddUserMessageInDatabase()

    async def handler(event, data):
        return "HANDLER_RESULT"

    message = FakeMessage(text="hello", user_id=555)
    update = FakeUpdate(message=message)

    result = await middleware(
        handler=handler,
        event=update,
        data={"conn": object()},
    )

    assert result == "HANDLER_RESULT"
    assert saved["user_id"] == 555
    assert saved["text"] == "hello"
    assert saved["photo"] is None
    assert saved["video"] is None


@pytest.mark.asyncio
async def test_add_user_message_middleware_raises_when_conn_missing():
    middleware = AddUserMessageInDatabase()

    async def handler(event, data):
        return "OK"

    message = FakeMessage(text="hello", user_id=555)
    update = FakeUpdate(message=message)

    with pytest.raises(RuntimeError, match="Missing database connection"):
        await middleware(
            handler=handler,
            event=update,
            data={},
        )