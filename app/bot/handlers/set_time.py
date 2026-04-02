from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.bot.keyboards.set_time_kb import (
    kb_choose_week,
    kb_current_week_days,
    kb_next_week_days
)

from app.bot.states.states import SetTimeStates
from app.bot.handlers.backend import parse_user_time

set_time_router = Router()


@set_time_router.message(Command("set_time"))
async def cmd_set_time(message: Message, state: FSMContext):
    await message.answer(
        "Выберите неделю:",
        reply_markup=kb_choose_week()
    )

@set_time_router.callback_query(F.data == "week_current")
async def week_current(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите день текущей недели:",
        reply_markup=kb_current_week_days()
    )
    await state.set_state(SetTimeStates.choosing_day)


@set_time_router.callback_query(F.data == "week_next")
async def week_next(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите день следующей недели:",
        reply_markup=kb_next_week_days()
    )
    await state.set_state(SetTimeStates.choosing_day)


@set_time_router.callback_query(F.data.startswith("day_"))
async def choose_day(callback: CallbackQuery, state: FSMContext):
    date = callback.data.replace("day_", "")
    await state.update_data(selected_date=date)

    await callback.message.answer(
        f"Вы выбрали {date}\nВведите количество свободного времени (например: 2ч 30м):"
    )

    await state.set_state(SetTimeStates.input_duration)

@set_time_router.message(SetTimeStates.input_duration)
async def input_duration_handler(message: Message, state: FSMContext):
    text = message.text.strip()

    hours, minutes = parse_user_time(text)

    if hours is None and minutes is None:
        return await message.answer("❌ Неверный формат. Пример: 1ч 30м или 90м")

    data = await state.get_data()
    selected_date = data.get("selected_date")

    # пока что не делал
    # update_user_time(conn, user_id, selected_date, hours, minutes)

    await message.answer(f"✔ Свободное время на {selected_date} сохранено: {hours}ч {minutes}м")

    await state.clear()