from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from psycopg import AsyncConnection
from app.infastructure.database.db import get_group_title_by_id

TASKS_PER_PAGE = 3


class TasksPaginationCallback(CallbackData, prefix="tasks_pag"):
    page: int  # текущая страница (начиная с 0)
    action: str  # "prev", "next", "accept", "page_info"
    task_id: int = 0  # используется только при action="accept"


def get_tasks_keyboard(tasks: list, page: int) -> InlineKeyboardMarkup:
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    page_tasks = tasks[start_idx:end_idx]

    # 1. Собираем строку навигации (всегда 3 кнопки в одном списке)
    nav_row = []
    # Назад
    nav_row.append(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=TasksPaginationCallback(action="prev", page=page).pack()
            if page > 0
            else "noop",
        )
    )
    # Инфо
    nav_row.append(
        InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="noop")
    )
    # Вперед
    nav_row.append(
        InlineKeyboardButton(
            text="➡️ Вперед",
            callback_data=TasksPaginationCallback(action="next", page=page).pack()
            if page < total_pages - 1
            else "noop",
        )
    )

    # 2. Собираем ряды для кнопок задач (каждая задача в отдельной строке)
    task_rows = []
    for task in page_tasks:
        task_rows.append(
            [
                InlineKeyboardButton(
                    text=f"✅ Принять #{task['id']}",
                    callback_data=TasksPaginationCallback(
                        action="accept", page=page, task_id=task["id"]
                    ).pack(),
                )
            ]
        )

    # 3. Формируем итоговую клавиатуру: первая строка — навигация, затем задачи
    inline_keyboard = [nav_row] + task_rows
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def build_tasks_page_text(tasks: list, page: int, conn: AsyncConnection) -> str:
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    page_tasks = tasks[start_idx:end_idx]

    lines = [f"📋 <b>Доступные задачи (страница {page + 1})</b>\n"]
    for task in page_tasks:
        start_str = (
            task["start_time"].strftime("%H:%M") if task.get("start_time") else "—"
        )
        deadline_str = (
            task["deadline"].strftime("%d.%m.%Y %H:%M") if task.get("deadline") else "—"
        )
        title = await get_group_title_by_id(conn=conn, group_id=task["group_id"])
        if not title:
            title = "-"
        duration_str = str(task["duration"])
        lines.append(
            f"<b>#{task['id']}</b> — {task['description']}\n"
            f"⏱ Старт: {start_str}  |  ⌛️ {duration_str[:-3]} мин.\n"
            f"💰 Награда: {task['reward']}\n"
            f"⏳ Дедлайн: {deadline_str}\n"
            f"   Группа: {title}\n"
            f"{'─' * 25}\n"
        )
    return "\n".join(lines)
