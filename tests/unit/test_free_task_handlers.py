import pytest

from app.bot.handlers import free_task
from app.bot.handlers.free_task import (
    process_accept_task,
    process_pagination,
    show_tasks,
)
from app.bot.keyboards.free_task_kb import TasksPaginationCallback


@pytest.mark.asyncio
async def test_show_tasks_answers_no_groups(monkeypatch, fake_message):
    async def fake_get_user_groups(conn, user_id):
        return []

    monkeypatch.setattr(free_task, "get_user_groups", fake_get_user_groups)

    message = fake_message(user_id=123)
    i18n = {
        "no_groups": "Нет групп",
    }

    await show_tasks(message=message, conn=object(), i18n=i18n)

    assert message.answers[0]["text"] == "Нет групп"


@pytest.mark.asyncio
async def test_show_tasks_answers_no_free_tasks(monkeypatch, fake_message):
    async def fake_get_user_groups(conn, user_id):
        return [{"group_id": 777}]

    async def fake_get_group_free_tasks(conn, group_id):
        return []

    monkeypatch.setattr(free_task, "get_user_groups", fake_get_user_groups)
    monkeypatch.setattr(free_task, "get_group_free_tasks", fake_get_group_free_tasks)

    message = fake_message(user_id=123)
    i18n = {
        "no_free_tasks": "Нет свободных задач",
    }

    await show_tasks(message=message, conn=object(), i18n=i18n)

    assert message.answers[0]["text"] == "Нет свободных задач"


@pytest.mark.asyncio
async def test_show_tasks_sends_tasks_page(monkeypatch, fake_message):
    async def fake_get_user_groups(conn, user_id):
        return [{"group_id": 777}]

    async def fake_get_group_free_tasks(conn, group_id):
        return [{"id": 1, "group_id": group_id}]

    async def fake_build_tasks_page_text(tasks, page, conn):
        return "TASKS PAGE TEXT"

    def fake_get_tasks_keyboard(tasks, page):
        return "TASKS_KEYBOARD"

    monkeypatch.setattr(free_task, "get_user_groups", fake_get_user_groups)
    monkeypatch.setattr(free_task, "get_group_free_tasks", fake_get_group_free_tasks)
    monkeypatch.setattr(free_task, "build_tasks_page_text", fake_build_tasks_page_text)
    monkeypatch.setattr(free_task, "get_tasks_keyboard", fake_get_tasks_keyboard)

    message = fake_message(user_id=123)

    await show_tasks(message=message, conn=object(), i18n={})

    assert message.answers[0]["text"] == "TASKS PAGE TEXT"
    assert message.answers[0]["kwargs"]["reply_markup"] == "TASKS_KEYBOARD"
    assert message.answers[0]["kwargs"]["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_process_pagination_edits_message_to_next_page(monkeypatch, fake_callback):
    async def fake_get_user_groups(conn, user_id):
        return [{"group_id": 777}]

    async def fake_get_group_free_tasks(conn, group_id):
        return [
            {"id": 1, "group_id": group_id},
            {"id": 2, "group_id": group_id},
            {"id": 3, "group_id": group_id},
            {"id": 4, "group_id": group_id},
        ]

    async def fake_build_tasks_page_text(tasks, page, conn):
        return f"TASKS PAGE {page}"

    def fake_get_tasks_keyboard(tasks, page):
        return f"KEYBOARD {page}"

    monkeypatch.setattr(free_task, "get_user_groups", fake_get_user_groups)
    monkeypatch.setattr(free_task, "get_group_free_tasks", fake_get_group_free_tasks)
    monkeypatch.setattr(free_task, "build_tasks_page_text", fake_build_tasks_page_text)
    monkeypatch.setattr(free_task, "get_tasks_keyboard", fake_get_tasks_keyboard)

    callback = fake_callback(user_id=123)
    callback_data = TasksPaginationCallback(action="next", page=0, task_id=0)

    await process_pagination(
        callback=callback,
        callback_data=callback_data,
        conn=object(),
        i18n={},
    )

    assert callback.message.edited_texts[0]["text"] == "TASKS PAGE 1"
    assert callback.message.edited_texts[0]["kwargs"]["reply_markup"] == "KEYBOARD 1"
    assert callback.message.edited_texts[0]["kwargs"]["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_process_accept_task_success_updates_list(monkeypatch, fake_callback):
    pagination_called = False

    async def fake_user_accept_task(conn, task_id, status, user_id):
        assert task_id == 10
        assert user_id == 123
        assert status.value == "in_progress"
        return True

    async def fake_process_pagination(callback, callback_data, conn, i18n):
        nonlocal pagination_called
        pagination_called = True

    monkeypatch.setattr(free_task, "user_accept_task", fake_user_accept_task)
    monkeypatch.setattr(free_task, "process_pagination", fake_process_pagination)

    callback = fake_callback(user_id=123)
    callback_data = TasksPaginationCallback(action="accept", page=0, task_id=10)

    await process_accept_task(
        callback=callback,
        callback_data=callback_data,
        conn=object(),
        i18n={},
    )

    assert callback.answers[0]["text"] == "✅ Задача принята!"
    assert callback.answers[0]["kwargs"]["show_alert"] is True
    assert pagination_called is True


@pytest.mark.asyncio
async def test_process_accept_task_failure_shows_error(monkeypatch, fake_callback):
    async def fake_user_accept_task(conn, task_id, status, user_id):
        return False

    monkeypatch.setattr(free_task, "user_accept_task", fake_user_accept_task)

    callback = fake_callback(user_id=123)
    callback_data = TasksPaginationCallback(action="accept", page=0, task_id=10)

    await process_accept_task(
        callback=callback,
        callback_data=callback_data,
        conn=object(),
        i18n={},
    )

    assert callback.answers[0]["text"] == "❌ Не удалось принять задачу."
    assert callback.answers[0]["kwargs"]["show_alert"] is True
