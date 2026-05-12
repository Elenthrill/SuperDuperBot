from datetime import datetime, timedelta

import pytest

from app.bot.keyboards import user_task_kb
from app.bot.keyboards.user_task_kb import (
    UserTasksPaginationCallback,
    build_user_tasks_page_text,
    get_user_tasks_keyboard,
)


def make_task(task_id: int, group_id: int = 100):
    return {
        "id": task_id,
        "description": f"Task {task_id}",
        "start_time": datetime(2026, 4, 24, 10, 30),
        "duration": timedelta(minutes=45),
        "reward": 15,
        "deadline": datetime(2026, 4, 25, 18, 0),
        "group_id": group_id,
    }


def test_user_tasks_pagination_callback_pack_cancel_action():
    callback_data = UserTasksPaginationCallback(
        action="cancel",
        page=1,
        task_id=42,
    ).pack()

    assert callback_data == "my_tasks_pag:1:cancel:42"


def test_get_user_tasks_keyboard_task_buttons():
    tasks = [make_task(1)]

    keyboard = get_user_tasks_keyboard(tasks, page=0)

    first_task_row = keyboard.inline_keyboard[0]

    assert first_task_row[0].text == "❌ Отказаться от #1"
    assert first_task_row[0].callback_data == "my_tasks_pag:0:cancel:1"

    assert first_task_row[1].text == "✅ Завершить #1"
    assert first_task_row[1].callback_data == "my_tasks_pag:0:complete:1"


def test_get_user_tasks_keyboard_navigation_for_single_page():
    tasks = [make_task(1)]

    keyboard = get_user_tasks_keyboard(tasks, page=0)

    nav_row = keyboard.inline_keyboard[-1]

    assert nav_row[0].callback_data == "noop"
    assert nav_row[1].text == "📄 1/1"
    assert nav_row[2].callback_data == "noop"


def test_get_user_tasks_keyboard_navigation_for_second_page():
    tasks = [make_task(i) for i in range(1, 5)]

    keyboard = get_user_tasks_keyboard(tasks, page=1)

    nav_row = keyboard.inline_keyboard[-1]

    assert nav_row[0].callback_data == "my_tasks_pag:1:prev:0"
    assert nav_row[1].text == "📄 2/2"
    assert nav_row[2].callback_data == "noop"


@pytest.mark.asyncio
async def test_build_user_tasks_page_text(monkeypatch):
    async def fake_get_group_title_by_id(conn, group_id):
        return f"Group {group_id}"

    monkeypatch.setattr(
        user_task_kb,
        "get_group_title_by_id",
        fake_get_group_title_by_id,
    )

    text = await build_user_tasks_page_text(
        tasks=[make_task(1, group_id=777)],
        page=0,
        conn=object(),
    )

    assert "📌 <b>Ваши задачи (страница 1)</b>" in text
    assert "<b>#1</b>" in text
    assert "💰 Награда: 15" in text
    assert "⏳ Дедлайн: 25.04.2026 18:00" in text
    assert "Группа: Group 777" in text

@pytest.mark.asyncio
async def test_build_user_tasks_page_text_uses_dash_when_group_title_missing(monkeypatch):
    async def fake_get_group_title_by_id(conn, group_id):
        return None

    monkeypatch.setattr(
        user_task_kb,
        "get_group_title_by_id",
        fake_get_group_title_by_id,
    )

    text = await build_user_tasks_page_text(
        tasks=[make_task(1, group_id=777)],
        page=0,
        conn=object(),
    )

    assert "Группа: -" in text

@pytest.mark.xfail(
    reason="BUG v2-006: в списке взятых задач вместо описания отображается продолжительность задачи"
)

@pytest.mark.asyncio
async def test_bug_user_tasks_page_text_should_show_task_description(monkeypatch):
    async def fake_get_group_title_by_id(conn, group_id):
        return f"Group {group_id}"

    monkeypatch.setattr(
        user_task_kb,
        "get_group_title_by_id",
        fake_get_group_title_by_id,
    )

    text = await build_user_tasks_page_text(
        tasks=[make_task(1, group_id=777)],
        page=0,
        conn=object(),
    )

    assert "Task 1" in text