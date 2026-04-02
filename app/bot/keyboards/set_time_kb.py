from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime

RU_DAYS = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}

def kb_choose_week():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Текущая неделя", callback_data="week_current")],
        [InlineKeyboardButton(text="➡️ Следующая неделя", callback_data="week_next")],
    ])

def kb_current_week_days():
    today = datetime.date.today()
    weekday = today.weekday()

    # сколько дней до воскресенья
    days_until_sunday = 6 - weekday

    keyboard = []

    for offset in range(0, days_until_sunday + 1):
        day_date = today + datetime.timedelta(days=offset)
        day_name = RU_DAYS[day_date.weekday()]
        day_str = day_date.strftime("%d.%m")

        keyboard.append([
            InlineKeyboardButton(
                text=f"{day_name} ({day_str})",
                callback_data=f"day_{day_date.isoformat()}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def kb_next_week_days():
    today = datetime.date.today()
    weekday = today.weekday()

    # понедельник следующей недели
    next_monday = today + datetime.timedelta(days=(7 - weekday))

    keyboard = []

    for i in range(7):
        day_date = next_monday + datetime.timedelta(days=i)
        day_name = RU_DAYS[day_date.weekday()]
        day_str = day_date.strftime("%d.%m")

        keyboard.append([
            InlineKeyboardButton(
                text=f"{day_name} ({day_str})",
                callback_data=f"day_{day_date.isoformat()}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def generate_week_days(week_offset: int = 0):
    """
    week_offset = 0 → текущая неделя
    week_offset = 1 → следующая
    """
    today = datetime.now()

    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)

    kb = InlineKeyboardBuilder()

    for i in range(7):
        day = start_of_week + timedelta(days=i)
        readable = day.strftime("%a %d.%m")       
        value = day.strftime("%Y-%m-%d")           

        kb.button(
            text=readable,
            callback_data=f"day_{value}"
        )

    kb.adjust(2)  
    return kb.as_markup()
