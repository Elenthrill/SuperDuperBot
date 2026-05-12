from datetime import timedelta

import pytest

from app.bot.handlers import backend
from app.bot.handlers.backend import (
    find_group_id,
    get_group_id_for_task,
    get_groups_text,
    parse_clock_time,
    parse_user_time,
    str_to_timedelta,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1:30:45", timedelta(hours=1, minutes=30, seconds=45)),
        ("1:30", timedelta(hours=1, minutes=30)),
        ("2 days, 1:30:45", timedelta(days=2, hours=1, minutes=30, seconds=45)),
        ("2 days, 1:30", timedelta(days=2, hours=1, minutes=30)),
    ],
)
def test_str_to_timedelta_valid_formats(raw, expected):
    assert str_to_timedelta(raw) == expected


@pytest.mark.parametrize("raw", ["1", "1:2:3:4", "wrong"])
def test_str_to_timedelta_rejects_invalid_formats(raw):
    with pytest.raises(ValueError):
        str_to_timedelta(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1:30", (1, 30)),
        ("2ч", (2, 0)),
        ("30м", (0, 30)),
        ("2ч30м", (2, 30)),
        (" 2 Ч 30 М ", (2, 30)),
    ],
)
def test_parse_user_time_valid_values(raw, expected):
    assert parse_user_time(raw) == expected


def test_parse_user_time_unknown_format_returns_none_tuple():
    assert parse_user_time("wrong") == (None, None)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("09:30", (9, 30)),
        ("9:05", (9, 5)),
        ("23:59", (23, 59)),
        ("00:00", (0, 0)),
    ],
)
def test_parse_clock_time_valid_values(raw, expected):
    assert parse_clock_time(raw) == expected


@pytest.mark.parametrize("raw", ["24:00", "23:60", "wrong", "10", "10:20:30"])
def test_parse_clock_time_invalid_values(raw):
    assert parse_clock_time(raw) is None


def test_find_group_id_by_existing_id():
    groups = {
        100: "Home",
        200: "Work",
    }

    assert find_group_id("100", groups) == (100, "Home")


def test_find_group_id_returns_none_for_unknown_id():
    groups = {
        100: "Home",
    }

    assert find_group_id("999", groups) == (None, None)


def test_find_group_id_by_title_case_insensitive():
    groups = {
        100: "Home",
        200: "Work",
    }

    assert find_group_id("work", groups) == (200, "Work")


def test_find_group_id_returns_none_for_unknown_title():
    groups = {
        100: "Home",
    }

    assert find_group_id("Unknown", groups) == (None, None)


@pytest.mark.xfail(
    reason="BUG v1-012: выбор группы по неуникальному названию неоднозначен"
)
def test_bug_find_group_id_duplicate_titles_should_not_choose_first_silently():
    groups = {
        100: "Same title",
        200: "Same title",
    }

    group_id, title = find_group_id("Same title", groups)

    assert group_id is None
    assert title is None


@pytest.mark.asyncio
async def test_get_groups_text_returns_none_when_user_has_no_groups(monkeypatch):
    async def fake_get_user_groups(conn, user_id):
        return []

    monkeypatch.setattr(backend, "get_user_groups", fake_get_user_groups)

    result = await get_groups_text(conn=object(), user_id=123)

    assert result is None


@pytest.mark.asyncio
async def test_get_groups_text_formats_groups(monkeypatch):
    async def fake_get_user_groups(conn, user_id):
        return [
            {"group_id": 100, "title": "Home"},
            {"group_id": 200, "title": "Work"},
        ]

    monkeypatch.setattr(backend, "get_user_groups", fake_get_user_groups)

    result = await get_groups_text(conn=object(), user_id=123)

    assert result == "Группа: Home ID:100\nГруппа: Work ID:200"


@pytest.mark.asyncio
async def test_get_group_id_for_task_returns_none_when_no_groups(monkeypatch):
    async def fake_get_user_groups(conn, user_id):
        return []

    monkeypatch.setattr(backend, "get_user_groups", fake_get_user_groups)

    result = await get_group_id_for_task(
        conn=object(),
        user_id=123,
        user_input="Home",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_group_id_for_task_returns_matching_group(monkeypatch):
    async def fake_get_user_groups(conn, user_id):
        return [
            {"group_id": 100, "title": "Home"},
        ]

    monkeypatch.setattr(backend, "get_user_groups", fake_get_user_groups)

    result = await get_group_id_for_task(
        conn=object(),
        user_id=123,
        user_input="100",
    )

    assert result == (100, "Home")