import pytest

from app.bot.handlers import task_history
from app.bot.handlers.task_history import (
    process_archive,
    process_show_archive,
)
from app.bot.keyboards.task_history_kb import ArchiveChoiseCallback


@pytest.mark.asyncio
async def test_process_archive_answers_no_groups(monkeypatch, fake_message):
    async def fake_get_user_groups(conn, user_id):
        return []

    monkeypatch.setattr(task_history, "get_user_groups", fake_get_user_groups)

    message = fake_message(user_id=123)
    i18n = {
        "no_groups": "Нет групп",
    }

    await process_archive(message=message, conn=object(), i18n=i18n)

    assert message.answers[0]["text"] == "Нет групп"


@pytest.mark.asyncio
async def test_process_archive_sends_choice_keyboard(monkeypatch, fake_message):
    async def fake_get_user_groups(conn, user_id):
        return [
            {"group_id": 777, "title": "Test Group"},
        ]

    monkeypatch.setattr(task_history, "get_user_groups", fake_get_user_groups)

    message = fake_message(user_id=123)
    i18n = {
        "archive_choice": "Выберите архив",
    }

    await process_archive(message=message, conn=object(), i18n=i18n)

    assert message.answers[0]["text"] == "Выберите архив"
    assert message.answers[0]["kwargs"]["reply_markup"] is not None
    assert message.answers[0]["kwargs"]["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_process_show_archive_self_answers_when_no_tasks(monkeypatch, fake_callback):
    async def fake_get_user_complete_tasks(conn, user_id):
        return []

    monkeypatch.setattr(
        task_history,
        "get_user_complete_tasks",
        fake_get_user_complete_tasks,
    )

    callback = fake_callback(user_id=123)
    callback_data = ArchiveChoiseCallback(action="self", page=0, group_id=0)
    i18n = {
        "bnt_self_click": "Мои завершённые задачи",
        "no_task_in_archive": "Архив пуст",
    }

    await process_show_archive(
        callback=callback,
        callback_data=callback_data,
        conn=object(),
        i18n=i18n,
    )

    assert callback.answers[0]["text"] == "Архив пуст"
    assert callback.answers[0]["kwargs"]["show_alert"] is True


@pytest.mark.asyncio
async def test_process_show_archive_self_edits_message_with_tasks(monkeypatch, fake_callback):
    async def fake_get_user_complete_tasks(conn, user_id):
        return [{"id": 1, "group_id": 777}]

    async def fake_build_archive_tasks_page_text(tasks, page, conn):
        return "ARCHIVE TASKS TEXT"

    def fake_get_user_tasks_keyboard(tasks, page):
        return "ARCHIVE_KEYBOARD"

    monkeypatch.setattr(
        task_history,
        "get_user_complete_tasks",
        fake_get_user_complete_tasks,
    )
    monkeypatch.setattr(
        task_history,
        "build_archive_tasks_page_text",
        fake_build_archive_tasks_page_text,
    )
    monkeypatch.setattr(
        task_history,
        "get_user_tasks_keyboard",
        fake_get_user_tasks_keyboard,
    )

    callback = fake_callback(user_id=123)
    callback_data = ArchiveChoiseCallback(action="self", page=0, group_id=0)
    i18n = {
        "bnt_self_click": "Мои завершённые задачи",
        "no_task_in_archive": "Архив пуст",
    }

    await process_show_archive(
        callback=callback,
        callback_data=callback_data,
        conn=object(),
        i18n=i18n,
    )

    edited = callback.message.edited_texts[0]

    assert "Мои завершённые задачи" in edited["text"]
    assert "ARCHIVE TASKS TEXT" in edited["text"]
    assert edited["kwargs"]["reply_markup"] == "ARCHIVE_KEYBOARD"
    assert edited["kwargs"]["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_process_show_archive_group_edits_message_with_tasks(monkeypatch, fake_callback):
    async def fake_get_group_completed_tasks(conn, group_id):
        return [{"id": 1, "group_id": group_id}]

    async def fake_get_group_title_by_id(conn, group_id):
        return "Test Group"

    async def fake_build_archive_tasks_page_text(tasks, page, conn):
        return "GROUP ARCHIVE TASKS TEXT"

    def fake_get_user_tasks_keyboard(tasks, page):
        return "GROUP_ARCHIVE_KEYBOARD"

    monkeypatch.setattr(
        task_history,
        "get_group_completed_tasks",
        fake_get_group_completed_tasks,
    )
    monkeypatch.setattr(
        task_history,
        "get_group_title_by_id",
        fake_get_group_title_by_id,
    )
    monkeypatch.setattr(
        task_history,
        "build_archive_tasks_page_text",
        fake_build_archive_tasks_page_text,
    )
    monkeypatch.setattr(
        task_history,
        "get_user_tasks_keyboard",
        fake_get_user_tasks_keyboard,
    )

    callback = fake_callback(user_id=123)
    callback_data = ArchiveChoiseCallback(
        action="group_choice",
        page=0,
        group_id=777,
    )
    i18n = {
        "btn_group_click": "Архив группы {title} #{id}",
        "no_task_in_archive": "Архив пуст",
    }

    await process_show_archive(
        callback=callback,
        callback_data=callback_data,
        conn=object(),
        i18n=i18n,
    )

    edited = callback.message.edited_texts[0]

    assert "Архив группы Test Group #777" in edited["text"]
    assert "GROUP ARCHIVE TASKS TEXT" in edited["text"]
    assert edited["kwargs"]["reply_markup"] == "GROUP_ARCHIVE_KEYBOARD"
