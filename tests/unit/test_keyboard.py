from app.bot.keyboards.keyboard import MyCallback, get_lang_settings_kb


def test_my_callback_pack():
    callback_data = MyCallback(
        mydata="report",
        report_id=10,
        user_id=20,
    ).pack()

    assert callback_data == "my:report:10:20"


def test_get_lang_settings_kb_marks_checked_locale():
    i18n = {
        "ru": "Русский",
        "en": "English",
        "cancel_lang_button_text": "Отмена",
        "save_lang_button_text": "Сохранить",
    }

    keyboard = get_lang_settings_kb(
        i18n=i18n,
        locales=["default", "en", "ru"],
        checked="ru",
    )

    rows = keyboard.inline_keyboard

    assert rows[0][0].text == "⚪️ English"
    assert rows[0][0].callback_data == "en"

    assert rows[1][0].text == "🔘 Русский"
    assert rows[1][0].callback_data == "ru"

    assert rows[2][0].text == "Отмена"
    assert rows[2][0].callback_data == "cancel_lang_button_data"

    assert rows[2][1].text == "Сохранить"
    assert rows[2][1].callback_data == "save_lang_button_data"


def test_get_lang_settings_kb_skips_default_locale():
    i18n = {
        "default": "Default",
        "ru": "Русский",
        "cancel_lang_button_text": "Отмена",
        "save_lang_button_text": "Сохранить",
    }

    keyboard = get_lang_settings_kb(
        i18n=i18n,
        locales=["default", "ru"],
        checked="ru",
    )

    texts = [
        button.text
        for row in keyboard.inline_keyboard
        for button in row
    ]

    assert "Default" not in texts
    assert "🔘 Русский" in texts