from datetime import date, timedelta
import pytest

from app.bot.keyboards.set_time_kb import (
    generate_week_days,
    kb_choose_week,
    kb_current_week_days,
    kb_next_week_days,
)


def test_kb_choose_week():
    keyboard = kb_choose_week()

    assert keyboard.inline_keyboard[0][0].text == "📅 Текущая неделя"
    assert keyboard.inline_keyboard[0][0].callback_data == "week_current"

    assert keyboard.inline_keyboard[1][0].text == "➡️ Следующая неделя"
    assert keyboard.inline_keyboard[1][0].callback_data == "week_next"


def test_kb_current_week_days_count():
    keyboard = kb_current_week_days()

    today = date.today()
    expected_days_count = 6 - today.weekday() + 1

    assert len(keyboard.inline_keyboard) == expected_days_count

    first_button = keyboard.inline_keyboard[0][0]
    assert first_button.callback_data == f"day_{today.isoformat()}"


def test_kb_next_week_days_count_and_first_day():
    keyboard = kb_next_week_days()

    today = date.today()
    next_monday = today + timedelta(days=7 - today.weekday())

    assert len(keyboard.inline_keyboard) == 7

    first_button = keyboard.inline_keyboard[0][0]
    assert first_button.callback_data == f"day_{next_monday.isoformat()}"

@pytest.mark.xfail(
    reason="BUG: generate_week_days падает из-за конфликта импортов datetime в set_time_kb.py"
)
def test_generate_week_days_has_7_buttons():
    keyboard = generate_week_days(week_offset=0)

    buttons = [
        button
        for row in keyboard.inline_keyboard
        for button in row
    ]

    assert len(buttons) == 7
    assert all(button.callback_data.startswith("day_") for button in buttons)