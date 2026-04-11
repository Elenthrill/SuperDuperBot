from aiogram import Bot, Router, types, F
import asyncio
from psycopg import AsyncConnection
from aiogram.filters import Command
from app.bot.keyboards.free_task_kb import TasksPaginationCallback
from app.bot.enums.roles import TaskStatus
from app.bot.keyboards.free_task_kb import (
    get_tasks_keyboard,
    build_tasks_page_text,
    TASKS_PER_PAGE,
)
from app.infastructure.database.db import (
    get_user_groups,
    get_group_free_tasks,
    user_accept_task,
)
from datetime import timedelta


task_router = Router()


@task_router.message(Command("free_tasks"))
async def show_tasks(message: types.Message, conn: AsyncConnection, i18n: dict):
    # --- получение списка задач (как было ранее) ---
    user_groups = await get_user_groups(conn, user_id=message.from_user.id)
    if not user_groups:
        await message.answer(text=i18n.get("no_groups"))
        return

    coroutines = [
        get_group_free_tasks(conn, group_id=group["group_id"]) for group in user_groups
    ]
    results_of_groups = await asyncio.gather(*coroutines)
    tasks = [task for group_tasks in results_of_groups for task in group_tasks]

    if not tasks:
        await message.answer(i18n.get("no_free_tasks", "У вас нет доступных задач."))
        return

    # --- формирование текста для первой страницы ---
    page = 0
    text = await build_tasks_page_text(tasks, page, conn=conn)

    keyboard = get_tasks_keyboard(tasks, page)

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@task_router.callback_query(
    TasksPaginationCallback.filter(F.action.in_(["prev", "next"]))
)
async def process_pagination(
    callback: types.CallbackQuery,
    callback_data: TasksPaginationCallback,
    conn: AsyncConnection,
    i18n: dict,
):
    # Заново получаем актуальный список задач (можно кэшировать при необходимости)
    user_groups = await get_user_groups(conn, user_id=callback.from_user.id)
    if not user_groups:
        await callback.answer(i18n.get("no_groups"), show_alert=True)
        return

    coroutines = [
        get_group_free_tasks(conn, group_id=group["group_id"]) for group in user_groups
    ]
    results_of_groups = await asyncio.gather(*coroutines)
    tasks = [task for group_tasks in results_of_groups for task in group_tasks]

    if not tasks:
        await callback.message.edit_text(i18n.get("no_free_tasks"))
        await callback.answer()
        return

    # Определяем новую страницу
    old_page = callback_data.page
    if callback_data.action == "prev":
        new_page = max(0, old_page - 1)
    else:  # "next"
        total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
        new_page = min(total_pages - 1, old_page + 1)

    if new_page == old_page:
        await callback.answer("Эта страница уже текущая", show_alert=False)
        return

    # Формируем обновлённый текст и клавиатуру
    new_text = build_tasks_page_text(tasks, new_page)
    new_keyboard = get_tasks_keyboard(tasks, new_page)

    await callback.message.edit_text(
        new_text, reply_markup=new_keyboard, parse_mode="HTML"
    )
    await callback.answer()


@task_router.callback_query(TasksPaginationCallback.filter(F.action == "accept"))
async def process_accept_task(
    callback: types.CallbackQuery,
    callback_data: TasksPaginationCallback,
    conn: AsyncConnection,
    i18n: dict,
):
    task_id = callback_data.task_id
    user_id = callback.from_user.id

    # Здесь ваша логика назначения задачи
    success = await user_accept_task(
        conn=conn,
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
        user_id=user_id,
    )
    if success:
        await callback.answer("✅ Задача принята!", show_alert=True)
        # После принятия можно либо обновить список (убрать задачу), либо удалить сообщение
        # Например, перезагружаем ту же страницу
        await process_pagination(callback, callback_data, conn, i18n=i18n)  # если нужно
    else:
        await callback.answer("❌ Не удалось принять задачу.", show_alert=True)
