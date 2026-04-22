from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from app.bot.keyboards.user_task_kb import TASKS_PER_PAGE
from psycopg import AsyncConnection
from app.infastructure.database.db import get_group_title_by_id, get_username_by_id


class ArchiveChoiseCallback(CallbackData, prefix="archive_choice"):
    page: int
    action: str  # "prev", "next", "self" "group_choice"
    group_id: int = 0


class ArchivePaginationCallback(CallbackData, prefix="archive_tasks"):
    page: int
    action: str  # "prev", "next", "appeal","group_click"
    task_id: int = 0


def get_choice_archive_kb(groups: list, page: int) -> InlineKeyboardMarkup:
    total_pages = (len(groups) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    page_groups = groups[start_idx:end_idx]

    # Строка навигации
    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=ArchiveChoiseCallback(action="prev", page=page).pack(),
            )
        )
    else:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="noop"))

    nav_row.append(
        InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="noop")
    )

    if page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton(
                text="➡️ Вперед",
                callback_data=ArchiveChoiseCallback(action="next", page=page).pack(),
            )
        )
    else:
        nav_row.append(InlineKeyboardButton(text="➡️ Вперед", callback_data="noop"))

    # Собираем все строки клавиатуры
    keyboard_rows = []  # первая строка – навигация

    # Строка с кнопкой "Мои задачи"
    keyboard_rows.append(
        [
            InlineKeyboardButton(
                text="Мои задачи",
                callback_data=ArchiveChoiseCallback(action="self", page=page).pack(),
            )
        ]
    )

    # Строки для каждой группы
    for grp in page_groups:
        keyboard_rows.append(
            [
                InlineKeyboardButton(
                    text=f"Группа: {grp['title']} ID:{grp['group_id']}",
                    callback_data=ArchiveChoiseCallback(
                        action="group_choice", page=page, group_id=grp["group_id"]
                    ).pack(),
                )
            ]
        )
    keyboard_rows.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


def get_user_tasks_keyboard(tasks: list, page: int) -> InlineKeyboardMarkup:
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    page_tasks = tasks[start_idx:end_idx]

    # Строка навигации (такая же)
    nav_row = [
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=ArchivePaginationCallback(action="prev", page=page).pack()
            if page > 0
            else "noop",
        ),
        InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="noop"),
        InlineKeyboardButton(
            text="➡️ Вперед",
            callback_data=ArchivePaginationCallback(action="next", page=page).pack()
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
                    text=f"⚠ ОБЖАЛОВАТЬ ⚠#{task['id']}",
                    callback_data=ArchivePaginationCallback(
                        action="appeal", page=page, task_id=task["id"]
                    ).pack(),
                ),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=task_rows + [nav_row])


async def build_archive_tasks_page_text(
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
        if task["user_id"]:
            username = await get_username_by_id(conn=conn, user_id=task["user_id"])
        else:
            username = task["user_id"]
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
            f"Исполнитель: {username}"
            f"{'─' * 25}\n"
        )
    return "\n".join(lines)
