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
                        query="""
                            CREATE TABLE IF NOT EXISTS users(
                                id SERIAL PRIMARY KEY,
                                user_id BIGINT NOT NULL UNIQUE,
                                username VARCHAR(50),
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                language VARCHAR(10) NOT NULL,
                                role VARCHAR(30) NOT NULL,
                                is_alive BOOLEAN NOT NULL,
                                banned BOOLEAN NOT NULL
                            ); 
                        """
                    )
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS activity(
                                id SERIAL PRIMARY KEY,
                                user_id BIGINT REFERENCES users(user_id),
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
                                actions INT NOT NULL DEFAULT 1
                            );
                            CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_user_day
                            ON activity (user_id, activity_date);
                        """
                    )
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS user_messages(
                                id SERIAL PRIMARY KEY,
                                user_id BIGINT REFERENCES users(user_id),
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                text VARCHAR(500) NULL,
                                photo BYTEA NULL,
                                video BYTEA NULL
                            );
                        """
                    )
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS reports(
                                id SERIAL PRIMARY KEY,
                                user_id BIGINT REFERENCES users(user_id),
                                service_worker_id BIGINT NULL,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                agency VARCHAR(50) NOT NULL,
                                status VARCHAR(50) NOT NULL,
                                text VARCHAR(500) NULL,
                                photo BYTEA NULL,
                                video BYTEA NULL
                            );
                        """
                    )
                    logger.info(
                        "Tables 'users' and 'activity' and 'user_messages' and 'reports' were successfully created"
                    )
    except Error as db_error:
        logger.exception("Database-specific error: %s", db_error)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
    finally:
        if connection:
            await connection.close()
            logger.info("Connection to postgres closed")


asyncio.run(main())
