import logging
from datetime import timedelta
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


def parse_duration(text: str) -> timedelta:
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

    return timedelta(hours=hours, minutes=minutes)


async def get_group_id_for_task(
    conn: AsyncConnection, user_id: int, user_input: str
) -> Optional[Tuple[int, str]]:
    groups = await get_user_groups(conn, user_id=user_id)
    if not groups:
        return None
    rows = {group["group_id"]: group["title"] for group in groups}
    id, title = find_group_id(user_input=user_input, groups_dict=rows)
    return id, title


def str_to_timedelta(s: str) -> timedelta:
    """
    Преобразует строку из str(timedelta) обратно в timedelta.
    Поддерживает форматы:
        - "HH:MM:SS"
        - "D days, HH:MM:SS"
        - "HH:MM" (если секунды не указаны)
    """
    if ", " in s:
        # Формат с днями: "2 days, 1:30:45"
        days_part, time_part = s.split(", ")
        days = int(days_part.split()[0])
        time_parts = list(map(int, time_part.split(":")))
        if len(time_parts) == 3:
            hours, minutes, seconds = time_parts
        elif len(time_parts) == 2:
            hours, minutes = time_parts
            seconds = 0
        else:
            raise ValueError(f"Неверный формат времени: {time_part}")
        return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    else:
        # Формат без дней: "1:30:45" или "1:30"
        parts = list(map(int, s.split(":")))
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours, minutes = parts
            seconds = 0
        else:
            raise ValueError(f"Неверный формат времени: {s}")
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)


async def get_groups_text(conn: AsyncConnection, user_id: int) -> Optional[str]:
    groups = await get_user_groups(conn, user_id=user_id)
    if not groups:
        return None
    lines = [f"Группа: {group['title']} ID:{group['group_id']}" for group in groups]
    return "\n".join(lines)


def find_group_id(
    user_input: str, groups_dict: dict[int, str]
) -> Optional[Tuple[int, str]]:
    """
    Возвращает group_id, если пользователь ввёл существующий group_id или название группы.
    Если ничего не найдено, возвращает None.

    Аргументы:
        user_input (str): строка, введённая пользователем.
        groups_dict (dict[int, str]): словарь вида {group_id: title}.

    Возвращает:
        Optional[int]: найденный group_id или None.
        Сломаеться если название группы являеться int
    """
    # Попытка интерпретировать ввод как число (group_id)
    try:
        group_id = int(user_input)
        if group_id in groups_dict:
            return group_id, groups_dict[group_id]
        # Число есть, но такого ID нет — прекращаем поиск
        return None, None
    except ValueError:
        # Не число — ищем по названию (без учёта регистра)
        user_input_lower = user_input.lower()
        for gid, title in groups_dict.items():
            if title.lower() == user_input_lower:
                return gid, groups_dict[gid]
        return None, None
