import logging
from aiogram import Router
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER
from aiogram.types import ChatMemberUpdated
from app.infastructure.database.db import add_group, add_to_user_group_table, get_group
from app.bot.entities.group import Group
from psycopg import AsyncConnection
from app.bot.handlers.backend import add_user_from_event

logger = logging.getLogger(__name__)
group_router = Router()


# Хендлер на добавление бота в группу
@group_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=(IS_MEMBER)))
async def on_bot_added(event: ChatMemberUpdated, i18n: dict, conn: AsyncConnection):
    logger.info(f"Пользователь{event.from_user.username} добавил бота в группу")
    bot_username = (await event.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start=group_{event.chat.id}"
    await add_user_from_event(conn=conn, event=event)
    group = Group(
        group_id=event.chat.id,
        title=event.chat.title,
        name=event.chat.username,
    )
    data_row = await get_group(conn, group_id=group.group_id)
    if data_row == None:
        await add_group(conn, group=group)
        await add_to_user_group_table(
            conn, user_id=event.from_user.id, group_id=group.group_id
        )
    await event.bot.send_message(
        chat_id=event.chat.id,
        text=i18n.get("add_to_group")
        + f"{event.from_user.full_name} + напиши мне: {deep_link}.",
    )
