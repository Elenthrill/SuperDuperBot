from datetime import datetime, timedelta

import pytest

from app.bot.keyboards import task_history_kb
from app.bot.keyboards.task_history_kb import (
    ArchiveChoiseCallback,
    ArchivePaginationCallback,
    build_archive_tasks_page_text,
    get_choice_archive_kb,
    get_user_tasks_keyboard,
)


def make_group(group_id: int, title: str):
    return {
        "group_id": group_id,
        "title": title,
    }


def make_task(task_id: int, user_id: int | None = 123, group_id: int = 777):
    return {
        "id": task_id,
        "description": f"Task {task_id}",
        "start_time": datetime(2026, 4, 24, 10, 30),
        "duration": timedelta(minutes=45),
        "reward": 10,
        "deadline": datetime(2026, 4, 25, 18, 0),
        "group_id": group_id,
        "user_id": user_id,
    }


def test_archive_choice_callback_pack():
    callback_data = ArchiveChoiseCallback(
        page=1,
        action="group_choice",
        group_id=777,
    ).pack()

    assert callback_data == "archive_choice:1:group_choice:777"


def test_archive_pagination_callback_pack():
    callback_data = ArchivePaginationCallback(
        page=2,
        action="appeal",
        task_id=10,
    ).pack()

    assert callback_data == "archive_tasks:2:appeal:10"


def test_get_choice_archive_kb_contains_self_and_groups():
    groups = [
        make_group(1, "Group 1"),
        make_group(2, "Group 2"),
    ]

    keyboard = get_choice_archive_kb(groups, page=0)

    rows = keyboard.inline_keyboard

    assert rows[0][0].text == "Мои задачи"
    assert rows[0][0].callback_data == "archive_choice:0:self:0"

    assert rows[1][0].text == "Группа: Group 1 ID:1"
    assert rows[1][0].callback_data == "archive_choice:0:group_choice:1"

    assert rows[2][0].text == "Группа: Group 2 ID:2"
    assert rows[2][0].callback_data == "archive_choice:0:group_choice:2"

    nav_row = rows[-1]
    assert nav_row[0].callback_data == "noop"
    assert nav_row[1].text == "📄 1/1"
    assert nav_row[2].callback_data == "noop"


def test_get_choice_archive_kb_second_page_navigation():
    groups = [
        make_group(1, "Group 1"),
        make_group(2, "Group 2"),
        make_group(3, "Group 3"),
        make_group(4, "Group 4"),
    ]

    keyboard = get_choice_archive_kb(groups, page=1)

    nav_row = keyboard.inline_keyboard[-1]

    assert nav_row[0].callback_data == "archive_choice:1:prev:0"
    assert nav_row[1].text == "📄 2/2"
    assert nav_row[2].callback_data == "noop"


def test_get_archive_user_tasks_keyboard_has_appeal_button():
    tasks = [make_task(1)]

    keyboard = get_user_tasks_keyboard(tasks, page=0)

    task_row = keyboard.inline_keyboard[0]
    nav_row = keyboard.inline_keyboard[-1]

    assert task_row[0].text == "⚠ ОБЖАЛОВАТЬ ⚠#1"
    assert task_row[0].callback_data == "archive_tasks:0:appeal:1"

    assert nav_row[0].callback_data == "noop"
    assert nav_row[1].text == "📄 1/1"
    assert nav_row[2].callback_data == "noop"


@pytest.mark.asyncio
async def test_build_archive_tasks_page_text(monkeypatch):
    async def fake_get_group_title_by_id(conn, group_id):
        return f"Group {group_id}"

    async def fake_get_username_by_id(conn, user_id):
        return f"user_{user_id}"

    monkeypatch.setattr(
        task_history_kb,
        "get_group_title_by_id",
        fake_get_group_title_by_id,
    )
    monkeypatch.setattr(
        task_history_kb,
        "get_username_by_id",
        fake_get_username_by_id,
    )

    text = await build_archive_tasks_page_text(
        tasks=[make_task(1, user_id=123, group_id=777)],
        page=0,
        conn=object(),
    )

    assert "📌 <b>Ваши задачи (страница 1)</b>" in text
    assert "<b>#1</b>" in text
    assert "💰 Награда: 10" in text
    assert "⏳ Дедлайн: 25.04.2026 18:00" in text
    assert "Группа: Group 777" in text
    assert "Исполнитель: user_123" in text


@pytest.mark.asyncio
async def test_build_archive_tasks_page_text_uses_dash_when_group_missing(monkeypatch):
    async def fake_get_group_title_by_id(conn, group_id):
        return None

    async def fake_get_username_by_id(conn, user_id):
        return f"user_{user_id}"

    monkeypatch.setattr(
        task_history_kb,
        "get_group_title_by_id",
        fake_get_group_title_by_id,
    )
    monkeypatch.setattr(
        task_history_kb,
        "get_username_by_id",
        fake_get_username_by_id,
    )

    text = await build_archive_tasks_page_text(
        tasks=[make_task(1, user_id=123, group_id=777)],
        page=0,
        conn=object(),
    )

    assert "Группа: -" in text