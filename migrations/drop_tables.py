import asyncio
import logging
import os
import sys

from app.infastructure.database.connection import get_pg_connection
from config.config import Config, load_config
from psycopg import AsyncConnection, Error

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format,
)

logger = logging.getLogger(__name__)

if sys.platform.startswith("win") or os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    connection: AsyncConnection | None = None
    logger.info("вошли в main")
    try:
        connection = await get_pg_connection(
            db_name=config.db.name,
            host=config.db.host,
            port=config.db.port,
            user=config.db.user,
            password=config.db.password,
        )
        async with connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        "DROP TRIGGER IF EXISTS trg_tasks_end_time ON tasks;"
                    )
                    await cursor.execute(
                        "DROP FUNCTION IF EXISTS set_end_time_on_complete();"
                    )
                    await cursor.execute("DROP TABLE IF EXISTS user_group CASCADE;")
                    await cursor.execute("DROP TABLE IF EXISTS tasks CASCADE;")
                    await cursor.execute("DROP TABLE IF EXISTS user_messages CASCADE;")
                    await cursor.execute("DROP TABLE IF EXISTS users CASCADE;")
                    await cursor.execute("DROP TABLE IF EXISTS groups CASCADE;")
    except Error as db_error:
        logger.exception("Database-specific error: %s", db_error)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
    finally:
        if connection:
            await connection.close()
            logger.info("Connection to postgres closed")


asyncio.run(main())
