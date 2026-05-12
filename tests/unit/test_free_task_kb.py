from datetime import datetime, timedelta

import pytest

from app.bot.keyboards import free_task_kb
from app.bot.keyboards.free_task_kb import (
    TASKS_PER_PAGE,
    TasksPaginationCallback,
    build_tasks_page_text,
    get_tasks_keyboard,
)


def make_task(task_id: int, group_id: int = 100):
    return {
        "id": task_id,
        "description": f"Task {task_id}",
        "start_time": datetime(2026, 4, 24, 10, 30),
        "duration": timedelta(minutes=45),
        "reward": 10,
        "deadline": datetime(2026, 4, 25, 18, 0),
        "group_id": group_id,
    }


def test_tasks_pagination_callback_pack_accept_action():
    callback_data = TasksPaginationCallback(
        action="accept",
        page=2,
        task_id=15,
    ).pack()

    assert callback_data == "tasks_pag:2:accept:15"


def test_get_tasks_keyboard_first_page_has_no_prev_and_has_next():
    tasks = [make_task(i) for i in range(1, 5)]

    keyboard = get_tasks_keyboard(tasks, page=0)

    nav_row = keyboard.inline_keyboard[0]

    assert nav_row[0].text == "⬅️ Назад"
    assert nav_row[0].callback_data == "noop"

    assert nav_row[1].text == "📄 1/2"
    assert nav_row[1].callback_data == "noop"

    assert nav_row[2].text == "➡️ Вперед"
    assert nav_row[2].callback_data == "tasks_pag:0:next:0"


def test_get_tasks_keyboard_second_page_has_prev_and_no_next():
    tasks = [make_task(i) for i in range(1, 5)]

    keyboard = get_tasks_keyboard(tasks, page=1)

    nav_row = keyboard.inline_keyboard[0]

    assert nav_row[0].callback_data == "tasks_pag:1:prev:0"
    assert nav_row[1].text == "📄 2/2"
    assert nav_row[2].callback_data == "noop"


def test_get_tasks_keyboard_shows_only_tasks_from_current_page():
    tasks = [make_task(i) for i in range(1, 7)]

    keyboard = get_tasks_keyboard(tasks, page=1)

    task_rows = keyboard.inline_keyboard[1:]

    assert len(task_rows) == TASKS_PER_PAGE
    assert task_rows[0][0].text == "✅ Принять #4"
    assert task_rows[1][0].text == "✅ Принять #5"
    assert task_rows[2][0].text == "✅ Принять #6"


@pytest.mark.asyncio
async def test_build_tasks_page_text(monkeypatch):
    async def fake_get_group_title_by_id(conn, group_id):
        return f"Group {group_id}"

    monkeypatch.setattr(
        free_task_kb,
        "get_group_title_by_id",
        fake_get_group_title_by_id,
    )

    text = await build_tasks_page_text(
        tasks=[make_task(1, group_id=777)],
        page=0,
        conn=object(),
    )

    assert "📋 <b>Доступные задачи (страница 1)</b>" in text
    assert "<b>#1</b> — Task 1" in text
    assert "💰 Награда: 10" in text
    assert "⏳ Дедлайн: 25.04.2026 18:00" in text
    assert "Группа: Group 777" in text