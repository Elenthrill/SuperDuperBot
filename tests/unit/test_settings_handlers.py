import pytest

from app.bot.enums.roles import UserRole
from app.bot.handlers import settings
from app.bot.handlers.settings import (
    process_cancel_clic,
    process_lang_click,
    process_lang_command,
    process_save_click,
)


def make_i18n():
    return {
        "/lang": "Выберите язык",
        "lang_saved": "Язык сохранён",
        "lang_cancelled": "Смена языка отменена: {}",
        "ru": "Русский",
        "en": "English",
        "cancel_lang_button_text": "Отмена",
        "save_lang_button_text": "Сохранить",
        "/start_description": "Start",
        "/lang_description": "Language",
        "/help_description": "Help",
        "/set_time_description": "Set time",
        "/new_task_description": "New task",
        "/free_tasks_description": "Free tasks",
        "/my_tasks_description": "My tasks",
        "/my_groups_description": "My groups",
        "/archive_description": "Archive",
        "/ban_description": "Ban",
        "/unban_description": "Unban",
        "/statistics_description": "Statistics",
    }


@pytest.mark.asyncio
async def test_process_lang_command_sets_state_and_sends_keyboard(
    monkeypatch,
    fake_message,
    fake_state,
):
    async def fake_get_user_lang(conn, user_id):
        return "ru"

    monkeypatch.setattr(settings, "get_user_lang", fake_get_user_lang)

    message = fake_message(user_id=123)
    state = fake_state()

    await process_lang_command(
        message=message,
        conn=object(),
        i18n=make_i18n(),
        state=state,
        locales=["ru", "en"],
    )

    assert state.state_values
    assert state.data["lang_settings_msg_id"] == 777
    assert state.data["user_lang"] == "ru"
    assert message.answers[0]["text"] == "Выберите язык"
    assert message.answers[0]["kwargs"]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_process_lang_click_edits_keyboard_for_selected_locale(fake_callback):
    callback = fake_callback(data="en")

    await process_lang_click(
        callback=callback,
        i18n=make_i18n(),
        locales=["ru", "en"],
    )

    edited = callback.message.edited_texts[0]

    assert edited["text"] == "Выберите язык"
    assert edited["kwargs"]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_process_cancel_click_resets_language_state(
    monkeypatch,
    fake_callback,
    fake_state,
):
    async def fake_get_user_lang(conn, user_id):
        return "ru"

    monkeypatch.setattr(settings, "get_user_lang", fake_get_user_lang)

    callback = fake_callback(data="cancel_lang_button_data")
    state = fake_state(data={"user_lang": "en", "lang_settings_msg_id": 777})

    await process_cancel_clic(
        callback=callback,
        conn=object(),
        i18n=make_i18n(),
        state=state,
    )

    assert "Смена языка отменена" in callback.message.edited_texts[0]["text"]
    assert state.data["user_lang"] is None
    assert state.data["lang_settings_msg_id"] is None
    assert state.state_values[-1] is None


@pytest.mark.asyncio
async def test_process_save_click_updates_language_and_commands(
    monkeypatch,
    fake_callback,
    fake_state,
    fake_bot,
):
    calls = {}

    async def fake_update_user_lang(conn, language, user_id):
        calls["language"] = language
        calls["user_id"] = user_id

    async def fake_get_user_role(conn, user_id):
        return UserRole.USER

    monkeypatch.setattr(settings, "update_user_lang", fake_update_user_lang)
    monkeypatch.setattr(settings, "get_user_role", fake_get_user_role)

    callback = fake_callback(data="save_lang_button_data", user_id=123)
    state = fake_state(data={"user_lang": "en", "lang_settings_msg_id": 777})
    bot = fake_bot()

    await process_save_click(
        callback=callback,
        bot=bot,
        conn=object(),
        i18n=make_i18n(),
        state=state,
    )

    assert calls == {"language": "en", "user_id": 123}
    assert callback.message.edited_texts[0]["text"] == "Язык сохранён"
    assert bot.commands_calls
    assert state.data["user_lang"] is None
    assert state.state_values[-1] is None


@pytest.mark.xfail(
    reason="BUG v2-008: при сохранении языка очищается lanf_settings_msg_id вместо lang_settings_msg_id",
    strict=True,
)
@pytest.mark.asyncio
async def test_bug_save_click_should_clear_lang_settings_msg_id(
    monkeypatch,
    fake_callback,
    fake_state,
    fake_bot,
):
    async def fake_update_user_lang(conn, language, user_id):
        return None

    async def fake_get_user_role(conn, user_id):
        return UserRole.USER

    monkeypatch.setattr(settings, "update_user_lang", fake_update_user_lang)
    monkeypatch.setattr(settings, "get_user_role", fake_get_user_role)

    callback = fake_callback(data="save_lang_button_data", user_id=123)
    state = fake_state(data={"user_lang": "en", "lang_settings_msg_id": 777})
    bot = fake_bot()

    await process_save_click(
        callback=callback,
        bot=bot,
        conn=object(),
        i18n=make_i18n(),
        state=state,
    )

    assert state.data["lang_settings_msg_id"] is None
