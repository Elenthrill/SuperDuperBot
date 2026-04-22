from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from psycopg import AsyncConnection
from app.infastructure.database.db import get_group_title_by_id

TASKS_PER_PAGE = 3


class UserTasksPaginationCallback(CallbackData, prefix="my_tasks_pag"):
    page: int
    action: str  # "prev", "next", "accept", "cancel", "page_info"
    task_id: int = 0


def get_user_tasks_keyboard(tasks: list, page: int) -> InlineKeyboardMarkup:
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    page_tasks = tasks[start_idx:end_idx]

    # Строка навигации (такая же)
    nav_row = [
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=UserTasksPaginationCallback(action="prev", page=page).pack()
            if page > 0
            else "noop",
        ),
        InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="noop"),
        InlineKeyboardButton(
            text="➡️ Вперед",
            callback_data=UserTasksPaginationCallback(action="next", page=page).pack()
            if page < total_pages - 1
            else "noop",
        ),
    ]

    # Кнопки отказа от задач
    task_rows = []
    for task in page_tasks:
        task_rows.append(
            [
                InlineKeyboardButton(
                    text=f"❌ Отказаться от #{task['id']}",
                    callback_data=UserTasksPaginationCallback(
                        action="cancel", page=page, task_id=task["id"]
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=f"✅ Завершить #{task['id']}",
                    callback_data=UserTasksPaginationCallback(
                        action="complete", page=page, task_id=task["id"]
                    ).pack(),
                ),
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=task_rows + [nav_row])


async def build_user_tasks_page_text(
    tasks: list, page: int, conn: AsyncConnection
) -> str:
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    page_tasks = tasks[start_idx:end_idx]

    lines = [f"📌 <b>Ваши задачи (страница {page + 1})</b>\n"]
    for task in page_tasks:
        start_str = (
            task["start_time"].strftime("%H:%M") if task.get("start_time") else "—"
        )
        deadline_str = (
            task["deadline"].strftime("%d.%m.%Y %H:%M") if task.get("deadline") else "—"
        )
        duration_str = str(task["duration"])
        title = await get_group_title_by_id(conn=conn, group_id=task["group_id"])
        if not title:
            title = "-"
        lines.append(
            f"<b>#{task['id']}</b> — {duration_str[:-3]}\n"
            f"⏱ Старт: {start_str}  |  ⌛️ {task['duration']} мин.\n"
            f"💰 Награда: {task['reward']}\n"
            f"⏳ Дедлайн: {deadline_str}\n"
            f"Группа: {title}\n"
            f"{'─' * 25}\n"
        )
    return "\n".join(lines)
