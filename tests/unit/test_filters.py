from types import SimpleNamespace

import pytest
from aiogram.types import CallbackQuery

from app.bot.enums.roles import UserRole
from app.bot.filters import filters
from app.bot.filters.filters import LocaleFilter, UserRoleFilter


def make_callback_query(data: str) -> CallbackQuery:
    return CallbackQuery(
        id="callback-id",
        from_user={
            "id": 123,
            "is_bot": False,
            "first_name": "Test",
        },
        chat_instance="chat-instance",
        data=data,
    )


@pytest.mark.asyncio
async def test_locale_filter_returns_true_for_allowed_locale():
    locale_filter = LocaleFilter()
    callback = make_callback_query("ru")

    result = await locale_filter(callback, locales=["ru", "en"])

    assert result is True


@pytest.mark.asyncio
async def test_locale_filter_returns_false_for_unknown_locale():
    locale_filter = LocaleFilter()
    callback = make_callback_query("de")

    result = await locale_filter(callback, locales=["ru", "en"])

    assert result is False


@pytest.mark.asyncio
async def test_locale_filter_raises_error_for_wrong_event_type():
    locale_filter = LocaleFilter()

    with pytest.raises(ValueError, match="expected 'CallbackQuery'"):
        await locale_filter(object(), locales=["ru", "en"])


def test_user_role_filter_requires_at_least_one_role():
    with pytest.raises(ValueError, match="At least one role"):
        UserRoleFilter()


def test_user_role_filter_accepts_string_roles():
    role_filter = UserRoleFilter("admin")

    assert role_filter.roles == frozenset({UserRole.ADMIN})


def test_user_role_filter_accepts_enum_roles():
    role_filter = UserRoleFilter(UserRole.USER)

    assert role_filter.roles == frozenset({UserRole.USER})


@pytest.mark.asyncio
async def test_user_role_filter_returns_false_when_event_has_no_user():
    role_filter = UserRoleFilter(UserRole.USER)

    event = SimpleNamespace(from_user=None)

    result = await role_filter(event, conn=object())

    assert result is False


@pytest.mark.asyncio
async def test_user_role_filter_returns_true_for_allowed_role(monkeypatch):
    async def fake_get_user_role(conn, user_id):
        return UserRole.ADMIN

    monkeypatch.setattr(filters, "get_user_role", fake_get_user_role)

    role_filter = UserRoleFilter(UserRole.ADMIN)
    event = SimpleNamespace(from_user=SimpleNamespace(id=123))

    result = await role_filter(event, conn=object())

    assert result is True


@pytest.mark.asyncio
async def test_user_role_filter_returns_false_for_different_role(monkeypatch):
    async def fake_get_user_role(conn, user_id):
        return UserRole.USER

    monkeypatch.setattr(filters, "get_user_role", fake_get_user_role)

    role_filter = UserRoleFilter(UserRole.ADMIN)
    event = SimpleNamespace(from_user=SimpleNamespace(id=123))

    result = await role_filter(event, conn=object())

    assert result is False


@pytest.mark.asyncio
async def test_user_role_filter_returns_false_when_role_not_found(monkeypatch):
    async def fake_get_user_role(conn, user_id):
        return None

    monkeypatch.setattr(filters, "get_user_role", fake_get_user_role)

    role_filter = UserRoleFilter(UserRole.ADMIN)
    event = SimpleNamespace(from_user=SimpleNamespace(id=123))

    result = await role_filter(event, conn=object())

    assert result is False
    