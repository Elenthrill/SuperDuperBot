import pytest

from app.bot.enums.roles import TaskStatus
from app.bot.handlers import user_task
from app.bot.handlers.user_task import (
    process_complete_or_cancel_task,
    show_my_tasks,
)
from app.bot.keyboards.user_task_kb import UserTasksPaginationCallback


@pytest.mark.asyncio
async def test_show_my_tasks_answers_when_list_is_empty(monkeypatch, fake_message):
    async def fake_get_user_tasks(conn, user_id):
        return []

    monkeypatch.setattr(user_task, "get_user_tasks", fake_get_user_tasks)

    message = fake_message(user_id=123)
    i18n = {
        "no_my_tasks": "У вас нет взятых задач",
    }

    await show_my_tasks(message=message, conn=object(), i18n=i18n)

    assert message.answers[0]["text"] == "У вас нет взятых задач"


@pytest.mark.asyncio
async def test_show_my_tasks_sends_tasks_page(monkeypatch, fake_message):
    async def fake_get_user_tasks(conn, user_id):
        return [{"id": 1, "group_id": 777}]

    async def fake_build_user_tasks_page_text(tasks, page, conn):
        return "MY TASKS PAGE TEXT"

    def fake_get_user_tasks_keyboard(tasks, page):
        return "MY_TASKS_KEYBOARD"

    monkeypatch.setattr(user_task, "get_user_tasks", fake_get_user_tasks)
    monkeypatch.setattr(
        user_task,
        "build_user_tasks_page_text",
        fake_build_user_tasks_page_text,
    )
    monkeypatch.setattr(
        user_task,
        "get_user_tasks_keyboard",
        fake_get_user_tasks_keyboard,
    )

    message = fake_message(user_id=123)

    await show_my_tasks(message=message, conn=object(), i18n={})

    assert message.answers[0]["text"] == "MY TASKS PAGE TEXT"
    assert message.answers[0]["kwargs"]["reply_markup"] == "MY_TASKS_KEYBOARD"
    assert message.answers[0]["kwargs"]["parse_mode"] == "HTML"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "action",
        "expected_db_user_id",
        "expected_status",
        "i18n_key",
        "expected_alert_text",
    ),
    [
        (
            "cancel",
            None,
            TaskStatus.PENDING,
            "user_cancel_task",
            "Вы отказались от задачи",
        ),
        (
            "complete",
            123,
            TaskStatus.COMPLETED,
            "user_complete_task",
            "Задача завершена",
        ),
    ],
)
async def test_process_complete_or_cancel_task_sets_expected_status(
    monkeypatch,
    fake_callback,
    action,
    expected_db_user_id,
    expected_status,
    i18n_key,
    expected_alert_text,
):
    calls = {}

    async def fake_set_status_to_task(conn, task_id, user_id, status):
        calls["task_id"] = task_id
        calls["user_id"] = user_id
        calls["status"] = status
        return True

    async def fake_get_user_tasks(conn, user_id):
        return []

    monkeypatch.setattr(user_task, "set_status_to_task", fake_set_status_to_task)
    monkeypatch.setattr(user_task, "get_user_tasks", fake_get_user_tasks)

    callback = fake_callback(user_id=123)
    callback_data = UserTasksPaginationCallback(action=action, page=0, task_id=10)
    i18n = {
        i18n_key: expected_alert_text,
    }

    await process_complete_or_cancel_task(
        callback=callback,
        callback_data=callback_data,
        conn=object(),
        i18n=i18n,
    )

    assert calls == {
        "task_id": 10,
        "user_id": expected_db_user_id,
        "status": expected_status,
    }
    assert callback.answers[0]["text"] == expected_alert_text

    if action == "cancel":
        assert (
            callback.message.edited_texts[0]["text"]
            == "У вас больше нет принятых задач."
        )


@pytest.mark.xfail(
    reason="BUG v2-001: при завершении задачи не передаётся и не сохраняется время окончания",
    strict=True,
)
@pytest.mark.asyncio
async def test_bug_complete_task_should_fix_end_time(monkeypatch, fake_callback):
    calls = {}

    async def fake_set_status_to_task(conn, task_id, user_id, status, end_time=None):
        calls["end_time"] = end_time
        return True

    async def fake_get_user_tasks(conn, user_id):
        return []

    monkeypatch.setattr(user_task, "set_status_to_task", fake_set_status_to_task)
    monkeypatch.setattr(user_task, "get_user_tasks", fake_get_user_tasks)

    callback = fake_callback(user_id=123)
    callback_data = UserTasksPaginationCallback(action="complete", page=0, task_id=10)
    i18n = {
        "user_complete_task": "Задача завершена",
    }

    await process_complete_or_cancel_task(
        callback=callback,
        callback_data=callback_data,
        conn=object(),
        i18n=i18n,
    )

    assert calls["end_time"] is not None
