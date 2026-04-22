import logging

import psycopg_pool
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from app.bot.handlers.admin import admin_router
from app.bot.handlers.other import others_router
from app.bot.handlers.settings import settings_router
from app.bot.handlers.user import user_router
from app.bot.handlers.group import group_router
from app.bot.handlers.free_task import task_router
from app.bot.handlers.user_task import user_task_router
from app.bot.handlers.task_history import archive_task_router
from app.bot.i18n.translator import get_tranlations
from app.bot.midlewares.database import DataBaseMiddleware
from app.bot.midlewares.i18n import TranslatorMiddleware
from app.bot.midlewares.lang_settings import LangSettingsMiddleware
from app.bot.midlewares.shadow_ban import ShadowBanMiddleware
from app.bot.handlers.set_time import set_time_router
from app.bot.midlewares.add_user_msg_in_db import AddUserMessageInDatabase
from app.infastructure.database.connection import get_pg_pool
from app.bot.handlers.group_events import group_events_router
from config.config import Config
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main(config: Config) -> None:
    logger.info("Starting bot...")
    # Инициализируем хранилище
    storage = RedisStorage(
        redis=Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password,
            username=config.redis.username,
        )
    )

    # Инициализируем бот и диспетчер
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Создаём пул соединений с Postgres
    db_pool: psycopg_pool.AsyncConnectionPool = await get_pg_pool(
        db_name=config.db.name,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )

    # Получаем словарь с переводами
    translations = get_tranlations()
    # формируем список локалей из ключей словаря с переводами
    locales = list(translations.keys())

    # Подключаем роутеры в нужном порядке
    logger.info("Including routers...")
    dp.include_routers(
        settings_router,
        admin_router,
        user_router,
        group_router,
        others_router,
        set_time_router,
        task_router,
        user_task_router,
        archive_task_router,
        group_events_router
    )

    # Подключаем миддлвари в нужном порядке
    logger.info("Including middlewares...")
    dp.update.middleware(DataBaseMiddleware())
    dp.update.middleware(ShadowBanMiddleware())
    dp.update.middleware(LangSettingsMiddleware())
    dp.update.middleware(TranslatorMiddleware())
    dp.update.middleware(AddUserMessageInDatabase())

    # Запускаем поллинг
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            db_pool=db_pool,
            translations=translations,
            locales=locales,
        )
    except Exception as e:
        logger.exception(e)
    finally:
        # Закрываем пул соединений
        await db_pool.close()
        logger.info("Connection to Postgres closed")
