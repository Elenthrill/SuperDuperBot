import logging
from typing import Optional, Tuple
from psycopg import AsyncConnection
from app.bot.enums.roles import UserRole
from app.bot.entities.user import User
from app.infastructure.database.db import (
    change_user_alive_status,
    add_user,
    get_user,
    get_user_groups,
)
from typing import Union
from aiogram.types import Message, ChatMemberUpdated, User as TgUSer
import re

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


def parse_user_time(text: str) -> Optional[Tuple[int, int]]:
    h_index = text.find("h")
    if h_index == -1:
        return None

    try:
        hours = int(text[:h_index])
    except ValueError:
        return None

    m_str = text[h_index + 1 :]
    if not m_str.endswith("m"):
        return None

    try:
        minutes = int(m_str[:-1])
    except ValueError:
        return None

    return hours, minutes


async def get_groups_text(conn: AsyncConnection, user_id: int) -> str:
    groups = await get_user_groups(conn, user_id=user_id)
    if not groups:
        return "У вас нет групп."
    lines = [f"Группа: {group['title']} ID:{group['group_id']}" for group in groups]
    return "\n".join(lines)

def parse_user_time(text: str):
    text = text.lower().replace(" ", "")

    # Форматы:
    #  "2ч30м"
    #  "2ч"
    #  "30м"
    #  "1:45"
    #  "150м"
    #  "1h 20m"

    # 1) 1:30
    if ":" in text:
        h, m = text.split(":")
        return int(h), int(m)

    # 2) Только часы
    if "ч" in text and "м" not in text:
        h = int(text.replace("ч", ""))
        return h, 0

    # 3) Только минуты
    if "м" in text and "ч" not in text:
        m = int(text.replace("м", ""))
        return 0, m

    # 4) Формат 2ч30м
    match = re.match(r"(\d+)ч(\d+)м", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    return None, None
