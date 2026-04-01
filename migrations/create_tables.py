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
                                banned BOOLEAN NOT NULL,
                                raiting INT NOT NULL,
                                free_time INTERVAL
                            ); 
                        """
                    )
                    logger.info("создана таблица users")
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS groups(
                            id SERIAL PRIMARY KEY,
                            group_id BIGINT NOT NULL UNIQUE,
                            title TEXT,
                            name TEXT,
                            is_alive BOOLEAN NOT NULL,
                            banned BOOLEAN NOT NULL
                            );
                        """
                    )
                    logger.info("создана таблица groups")
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS tasks(
                                id SERIAL PRIMARY KEY,
                                description TEXT NOT NULL,
                                start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                duration INTERVAL NOT NULL,
                                reward INT NOT NULL,
                                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                                deadline TIMESTAMPTZ NOT NULL,
                                end_time TIMESTAMPTZ,
                                user_id BIGINT REFERENCES users(user_id),
                                group_id BIGINT REFERENCES groups(group_id)
                            ); 
                            CREATE INDEX idx_tasks_user_id ON tasks(user_id);
                            
                        """
                    )
                    logger.info("создана таблица tasks")
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS user_group(
                            user_id BIGINT NOT NULL,
                            group_id BIGINT NOT NULL,
                            PRIMARY KEY (user_id, group_id),
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                            FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE                      
                            );
                            """
                    )
                    logger.info("создана таблица user_group")
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
                    logger.info("создана таблица _messages")
                    await cursor.execute("""
                                        -- функция, которая устанавливает end_time при смене статуса на 'completed'
                                        CREATE OR REPLACE FUNCTION set_end_time_on_complete()
                                        RETURNS TRIGGER AS $$
                                        BEGIN
                                            IF NEW.status = 'completed' AND OLD.status != 'completed' AND NEW.end_time IS NULL THEN
                                                NEW.end_time = NOW();
                                            END IF;
                                            RETURN NEW;
                                        END;
                                        $$ LANGUAGE plpgsql;

                                        -- удаляем старый триггер, если он уже существует (чтобы избежать ошибки)
                                        DROP TRIGGER IF EXISTS trg_tasks_end_time ON tasks;

                                        -- создаём триггер, который срабатывает перед обновлением строки
                                        CREATE TRIGGER trg_tasks_end_time
                                            BEFORE UPDATE ON tasks
                                            FOR EACH ROW
                                            EXECUTE FUNCTION set_end_time_on_complete();
                                    """)
                    logger.info(
                        "добавлен функция и тригер для автоматического заполнения end_time"
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
