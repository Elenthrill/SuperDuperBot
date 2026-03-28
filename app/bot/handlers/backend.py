import logging
from psycopg import AsyncConnection
from app.bot.enums.roles import UserRole
from app.bot.entities.user import User
from app.infastructure.database.db import change_user_alive_status, add_user, get_user
from typing import Union
from aiogram.types import Message, ChatMemberUpdated, User as TgUSer

logger = logging.getLogger(__name__)


def get_user_from_event(event: Union[Message, ChatMemberUpdated]) -> TgUSer:
    if isinstance(event, Message):
        return event.from_user
    elif isinstance(event, ChatMemberUpdated):
        return event.from_user
    else:
        raise TypeError("Unsupported event type")


async def add_user_from_event(
    event: Union[Message, ChatMemberUpdated], conn: AsyncConnection
):
    user_obj = get_user_from_event(event)
    logger.info(f"id юзера {user_obj.id}")
    user_row = await get_user(conn, user_id=user_obj.id)
    if user_row is None:
        user = User(
            user_id=user_obj.id,
            user_name=user_obj.username,
            lang=user_obj.language_code,  # для ChatMemberUpdated может быть None
            role=UserRole.USER,
        )
        await add_user(conn, user=user)
    else:
        await change_user_alive_status(
            conn,
            is_alive=True,
            user_id=user_obj.id,
        )
