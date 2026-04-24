import logging

from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.filters.chat_member_updated import KICKED, LEFT

logger = logging.getLogger(__name__)

group_events_router = Router()


@group_events_router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=KICKED | LEFT)
)
async def bot_removed_from_group(event: ChatMemberUpdated):
    """
    Срабатывает, когда бота удалили из группы / супер-группы
    """

    # Тестировал чтоб понять работает или нет
    print("HANDLER WORKED")

    chat_id = event.chat.id
    chat_title = event.chat.title

    logger.warning(
        "Бот был удалён из группы: %s (%s)",
        chat_title,
        chat_id
    )

    # Переменная для сохранения в бд
    removed_group_id = chat_id

    print(f"DELETE GROUP FROM DB: {removed_group_id}")