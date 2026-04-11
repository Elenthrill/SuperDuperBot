from aiogram import Bot, Router, types, F
import asyncio
import logging
from psycopg import AsyncConnection
from aiogram.filters import Command
from app.bot.keyboards.user_task_kb import UserTasksPaginationCallback
from app.bot.enums.roles import TaskStatus
from app.bot.keyboards.user_task_kb import (
    get_user_tasks_keyboard,
    build_user_tasks_page_text,
    TASKS_PER_PAGE,
)
from app.infastructure.database.db import (
    get_user_tasks,
    user_cancel_task,
)
from datetime import timedelta

logger = logging.getLogger(__name__)
user_task_router = Router()


@user_task_router.message(Command("my_tasks"))
async def show_my_tasks(message: types.Message, conn: AsyncConnection, i18n: dict):
    user_id = message.from_user.id
    # Получаем задачи, где user_id == текущий пользователь
    my_tasks = await get_user_tasks(conn, user_id=user_id)

    if not my_tasks:
        await message.answer(i18n.get("no_my_tasks"))
        return

    page = 0
    text = await build_user_tasks_page_text(my_tasks, page, conn)
    keyboard = get_user_tasks_keyboard(my_tasks, page)

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@user_task_router.callback_query(
    UserTasksPaginationCallback.filter(F.action.in_(["prev", "next"]))
)
async def process_my_tasks_pagination(
    callback: types.CallbackQuery,
    callback_data: UserTasksPaginationCallback,
    conn: AsyncConnection,
):
    # Проверяем, что сообщение относится к "my_tasks" (можно добавить флаг в callback или проверять текст)
    # Здесь простой вариант: загружаем задачи пользователя
    user_id = callback.from_user.id
    my_tasks = await get_user_tasks(conn, user_id=user_id)
    logger.info(f"user_id={user_id}")
    if not my_tasks:
        await callback.message.edit_text("У вас нет принятых задач.")
        await callback.answer()
        return

    total_pages = (len(my_tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
    new_page = callback_data.page
    if callback_data.action == "prev":
        new_page = max(0, new_page - 1)
    else:
        new_page = min(total_pages - 1, new_page + 1)

    if new_page == callback_data.page:
        await callback.answer()
        return

    text = await build_user_tasks_page_text(my_tasks, new_page, conn=conn)
    keyboard = get_user_tasks_keyboard(my_tasks, new_page)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Если задача просрочена, то снова поставит в ожидание
@user_task_router.callback_query(
    UserTasksPaginationCallback.filter(F.action == "cancel")
)
async def process_cancel_task(
    callback: types.CallbackQuery,
    callback_data: UserTasksPaginationCallback,
    conn: AsyncConnection,
):
    task_id = callback_data.task_id
    user_id = callback.from_user.id

    success = await user_cancel_task(
        conn, task_id=task_id, user_id=user_id, status=TaskStatus.PENDING
    )
    if success:
        await callback.answer("✅ Вы отказались от задачи.", show_alert=True)
        # Обновляем список задач на той же странице (или переходим на предыдущую, если страница опустела)
        my_tasks = await get_user_tasks(conn, user_id=user_id)
        total_pages = (len(my_tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
        new_page = min(callback_data.page, total_pages - 1) if total_pages > 0 else 0

        if my_tasks:
            text = await build_user_tasks_page_text(my_tasks, new_page, conn=conn)
            keyboard = get_user_tasks_keyboard(my_tasks, new_page)
            await callback.message.edit_text(
                text, reply_markup=keyboard, parse_mode="HTML"
            )
        else:
            await callback.message.edit_text("У вас больше нет принятых задач.")
    else:
        await callback.answer("❌ Не удалось отказаться от задачи.", show_alert=True)
    await callback.answer()
