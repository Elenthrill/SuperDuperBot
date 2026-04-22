from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from psycopg import AsyncConnection
import logging
from app.infastructure.database.db import get_user_groups
from app.bot.keyboards.task_history_kb import (
    ArchiveChoiseCallback,
    ArchivePaginationCallback,
    get_choice_archive_kb,
    get_user_tasks_keyboard,
    TASKS_PER_PAGE,
    build_archive_tasks_page_text,
)
from app.infastructure.database.db import (
    get_group_completed_tasks,
    get_user_complete_tasks,
    get_group_title_by_id,
)


logger = logging.getLogger(__name__)
archive_task_router = Router()


@archive_task_router.message(Command("archive"))
async def process_archive(message: Message, conn: AsyncConnection, i18n: dict):
    user_id = message.from_user.id
    groups = await get_user_groups(conn, user_id=user_id)
    if not groups:
        await message.answer(i18n.get("no_groups"))
        return

    page = 0
    keyboard = get_choice_archive_kb(groups, page)
    await message.answer(
        text=i18n.get("archive_choice"), reply_markup=keyboard, parse_mode="HTML"
    )


@archive_task_router.callback_query(
    ArchiveChoiseCallback.filter(F.action.in_(["prev", "next"]))
)
async def procces_choice_archive_pagination(
    callback: CallbackQuery,
    callback_data: ArchiveChoiseCallback,
    conn: AsyncConnection,
    i18n: dict,
):
    user_id = callback.from_user.id
    groups_row = await get_user_groups(user_id)
    if not groups_row:
        await callback.message.edit_text("no_groups")
        await callback.answer()
        return

    total_pages = (len(groups_row) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
    new_page = callback_data.page
    if callback_data.action == "prev":
        new_page = max(0, new_page - 1)
    else:
        new_page = min(total_pages - 1, new_page + 1)

    if new_page == callback_data.page:
        await callback.answer()
        return

    keyboard = get_choice_archive_kb(groups_row, new_page)
    await callback.message.edit_text(
        text=i18n.get("archive_choice"), reply_markup=keyboard, parse_mode="HTML"
    )
    await callback.answer()


@archive_task_router.callback_query(
    ArchiveChoiseCallback.filter(F.action.in_(["group_choice", "self"]))
)
async def process_show_archive(
    callback: CallbackQuery,
    callback_data: ArchiveChoiseCallback,
    conn: AsyncConnection,
    i18n: dict,
):
    user_id = callback.from_user.id
    if callback_data.action == "group_choice":
        task_row = await get_group_completed_tasks(
            conn, group_id=callback_data.group_id
        )
        text = i18n["btn_group_click"].format(
            id=callback_data.group_id,
            title=await get_group_title_by_id(conn, group_id=callback_data.group_id),
        )
    else:
        task_row = await get_user_complete_tasks(conn, user_id=user_id)
        text = i18n["bnt_self_click"]
    if not task_row:
        await callback.answer(i18n.get("no_task_in_archive"), show_alert=True)
        return
    page = 0
    keyboard = get_user_tasks_keyboard(task_row, page)
    text += "\n\n" + await build_archive_tasks_page_text(task_row, page, conn)
    await callback.message.edit_text(
        text=text, reply_markup=keyboard, parse_mode="HTML"
    )
