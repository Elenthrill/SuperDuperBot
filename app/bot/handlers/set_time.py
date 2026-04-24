from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.bot.keyboards.set_time_kb import (
    kb_choose_week,
    kb_current_week_days,
    kb_next_week_days,
)

from app.bot.states.states import SetTimeStates
from app.bot.handlers.backend import parse_user_time

set_time_router = Router()
set_time_router.message.filter(lambda msg: msg.chat.type == "private")


@set_time_router.message(Command("set_time"))
async def cmd_set_time(message: Message, state: FSMContext):
    await message.answer("Выберите неделю:", reply_markup=kb_choose_week())


@set_time_router.callback_query(F.data == "week_current")
async def week_current(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите день текущей недели:", reply_markup=kb_current_week_days()
    )
    await state.set_state(SetTimeStates.choosing_day)


@set_time_router.callback_query(F.data == "week_next")
async def week_next(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите день следующей недели:", reply_markup=kb_next_week_days()
    )
    await state.set_state(SetTimeStates.choosing_day)


@set_time_router.callback_query(F.data.startswith("day_"))
async def choose_day(callback: CallbackQuery, state: FSMContext):
    date = callback.data.replace("day_", "")
    await state.update_data(selected_date=date)

    await callback.message.answer(
        f"Вы выбрали {date}\nТеперь введите ВРЕМЯ НАЧАЛА в формате ЧЧ:ММ\nНапример: 09:30"
    )

    await state.set_state(SetTimeStates.input_start_time)


@set_time_router.message(SetTimeStates.input_start_time)
async def process_start_time(message: Message, state: FSMContext):
    from app.bot.handlers.backend import parse_clock_time

    parsed = parse_clock_time(message.text)

    if parsed is None:
        return await message.answer("❌ Неверный формат. Введите ЧЧ:ММ, например 09:30")

    h, m = parsed

    await state.update_data(start_time=f"{h:02d}:{m:02d}")

    await message.answer("Теперь введите ВРЕМЯ КОНЦА в формате ЧЧ:ММ\nНапример: 14:00")

    await state.set_state(SetTimeStates.input_end_time)


@set_time_router.message(SetTimeStates.input_end_time)
async def process_end_time(message: Message, state: FSMContext):
    from app.bot.handlers.backend import parse_clock_time

    parsed = parse_clock_time(message.text)

    if parsed is None:
        return await message.answer("❌ Неверный формат. Введите ЧЧ:ММ")

    h, m = parsed
    end_time = f"{h:02d}:{m:02d}"

    data = await state.get_data()
    date = data["selected_date"]
    start_time = data["start_time"]

    if end_time <= start_time:
        return await message.answer("❌ Время конца должно быть ПОЗЖЕ времени начала!")

    # СЮДА вставляешь СВОЁ сохранение в БД
    # await save_interval(conn, user_id, date, start_time, end_time)

    await message.answer(
        f"✔ Интервал сохранён!\n📅 Дата: {date}\n⏱ Время: {start_time} — {end_time}"
    )

    await state.clear()
