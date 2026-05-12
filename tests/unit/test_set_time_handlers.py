import pytest

from app.bot.handlers.set_time import (
    choose_day,
    cmd_set_time,
    process_end_time,
    process_start_time,
    week_current,
    week_next,
)


@pytest.mark.asyncio
async def test_cmd_set_time_sends_week_choice_keyboard(fake_message, fake_state):
    message = fake_message()
    state = fake_state()

    await cmd_set_time(message=message, state=state)

    assert message.answers[0]["text"] == "Выберите неделю:"
    assert message.answers[0]["kwargs"]["reply_markup"] is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("callback_data", "expected_text"),
    [
        ("week_current", "Выберите день текущей недели:"),
        ("week_next", "Выберите день следующей недели:"),
    ],
)
async def test_week_choice_edits_message_and_sets_state(
    fake_callback,
    fake_state,
    callback_data,
    expected_text,
):
    callback = fake_callback(data=callback_data)
    state = fake_state()
    handler = week_current if callback_data == "week_current" else week_next

    await handler(callback=callback, state=state)

    assert callback.message.edited_texts[0]["text"] == expected_text
    assert callback.message.edited_texts[0]["kwargs"]["reply_markup"] is not None
    assert state.state_values


@pytest.mark.asyncio
async def test_choose_day_saves_selected_date_and_asks_start_time(fake_callback, fake_state):
    callback = fake_callback(data="day_2026-04-24")
    state = fake_state()

    await choose_day(callback=callback, state=state)

    assert state.data["selected_date"] == "2026-04-24"
    assert "Теперь введите ВРЕМЯ НАЧАЛА" in callback.message.answers[0]["text"]
    assert state.state_values


@pytest.mark.asyncio
async def test_process_start_time_rejects_invalid_time(fake_message, fake_state):
    message = fake_message(text="25:99")
    state = fake_state()

    await process_start_time(message=message, state=state)

    assert message.answers[0]["text"] == (
        "❌ Неверный формат. Введите ЧЧ:ММ, например 09:30"
    )
    assert "start_time" not in state.data


@pytest.mark.asyncio
async def test_process_start_time_accepts_valid_time(fake_message, fake_state):
    message = fake_message(text="9:05")
    state = fake_state()

    await process_start_time(message=message, state=state)

    assert state.data["start_time"] == "09:05"
    assert message.answers[0]["text"] == (
        "Теперь введите ВРЕМЯ КОНЦА в формате ЧЧ:ММ\nНапример: 14:00"
    )
    assert state.state_values


@pytest.mark.asyncio
async def test_process_end_time_rejects_invalid_time(fake_message, fake_state):
    message = fake_message(text="wrong")
    state = fake_state(data={"selected_date": "2026-04-24", "start_time": "09:00"})

    await process_end_time(message=message, state=state)

    assert message.answers[0]["text"] == "❌ Неверный формат. Введите ЧЧ:ММ"
    assert state.cleared is False


@pytest.mark.asyncio
async def test_process_end_time_rejects_end_before_start(fake_message, fake_state):
    message = fake_message(text="08:59")
    state = fake_state(data={"selected_date": "2026-04-24", "start_time": "09:00"})

    await process_end_time(message=message, state=state)

    assert message.answers[0]["text"] == "❌ Время конца должно быть ПОЗЖЕ времени начала!"
    assert state.cleared is False


@pytest.mark.asyncio
async def test_process_end_time_saves_valid_interval_and_clears_state(
    fake_message,
    fake_state,
):
    message = fake_message(text="14:00")
    state = fake_state(data={"selected_date": "2026-04-24", "start_time": "09:00"})

    await process_end_time(message=message, state=state)

    assert "✔ Интервал сохранён!" in message.answers[0]["text"]
    assert "📅 Дата: 2026-04-24" in message.answers[0]["text"]
    assert "⏱ Время: 09:00 — 14:00" in message.answers[0]["text"]
    assert state.cleared is True
