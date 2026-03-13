import logging
from typing import Any, Awaitable, Callable
from aiogram import Bot

from aiogram import BaseMiddleware
from psycopg import AsyncConnection
from aiogram.types import ContentType, Update, Message
from app.infastructure.database.db import add_user_message
from aiogram.enums import UpdateType

logger = logging.getLogger(__name__)


class AddUserMessageInDatabase(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        result = await handler(event, data)
        conn: AsyncConnection = data.get("conn")
        if conn is None:
            logger.error("No database connection found in middleware data.")
            raise RuntimeError(
                "Missing database connection for add user message in database."
            )
        update = event.event_type
        if update == UpdateType.MESSAGE:
            message: Message = event.message
            if (
                message.content_type == ContentType.TEXT
                or message.content_type == ContentType.VIDEO
                or message.content_type == ContentType.PHOTO
            ):
                photo_bytes = None
                video_bytes = None
                if message.text:
                    text = message.text
                else:
                    text = message.caption
                if message.photo:
                    bot: Bot = data["bot"]
                    photo = message.photo[-1]
                    file = await bot.get_file(photo.file_id)
                    photo_data = await bot.download_file(file.file_path)
                    photo_bytes = photo_data.read()
                if message.video:
                    bot: Bot = data["bot"]
                    video = message.video
                    file = await bot.get_file(video.file_id)
                    video_data = await bot.download_file(file.file_path)
                    video_bytes = video_data.read()

                await add_user_message(
                    conn,
                    user_id=message.from_user.id,
                    text=text,
                    photo=photo_bytes,
                    video=video_bytes,
                )
        return result
