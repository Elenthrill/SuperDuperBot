import logging

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
)
from app.bot.filters.filters import UserRoleFilter
from app.bot.enums.roles import UserRole
from app.infastructure.database.db import update_report
from app.bot.keyboards.keyboard import MyCallback

from psycopg import AsyncConnection

logger = logging.getLogger(__name__)

service_worker_router = Router()
service_worker_router.message.filter(UserRoleFilter(UserRole.SERVICE_WORKER))


@service_worker_router.callback_query(
    MyCallback.filter(F.mydata == "btn_report_accept")
)
async def process_btn_accept_click(
    callback: CallbackQuery,
    conn: AsyncConnection,
    callback_data: MyCallback,
    i18n: dict[str, str],
    bot: Bot,
):
    user_id = callback_data.user_id
    report_id = callback_data.report_id
    print(f"NNNNNNNNNNNNNNNNNN {report_id} NNNNNNNNNNNNNNNNNNN")
    service_worker_id = callback.from_user.id
    await callback.message.edit_text(
        text=i18n.get("report_accept_service_worker_answer")
    )
    await update_report(
        conn,
        report_id=report_id,
        service_worker_id=service_worker_id,
        status="accepted",
    )
    await bot.send_message(chat_id=user_id, text=i18n.get("report_accepted"))


@service_worker_router.callback_query(
    MyCallback.filter(F.mydata == "btn_report_cancel")
)
async def process_btn_cancel_click(
    callback: CallbackQuery,
    conn: AsyncConnection,
    callback_data: MyCallback,
    i18n: dict[str, str],
    bot: Bot,
):
    print("NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN")
    user_id = callback_data.user_id
    report_id = callback_data.report_id
    service_worker_id = callback.from_user.id
    await callback.message.edit_text(
        text=i18n.get("report_cancel_service_worker_answer")
    )
    await update_report(
        conn,
        report_id=report_id,
        service_worker_id=service_worker_id,
        status="canceled",
    )
    await bot.send_message(chat_id=user_id, text=i18n.get("report_canceled"))
