import logging
from psycopg.rows import dict_row
from datetime import datetime, timezone, timedelta
from typing import Any
from app.bot.entities.user import User
from app.bot.entities.task import Task
from app.bot.entities.group import Group
from app.bot.enums.roles import TaskStatus
from typing import List, Dict

from app.bot.enums.roles import UserRole
from psycopg import AsyncConnection


logger = logging.getLogger(__name__)


async def add_user(conn: AsyncConnection, *, user: User) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO users(user_id, username, language, role, is_alive, banned, free_time,raiting)
                VALUES(
                    %(user_id)s, 
                    %(username)s, 
                    %(language)s, 
                    %(role)s, 
                    %(is_alive)s, 
                    %(banned)s,
                   %(free_time)s,
                    %(raiting)s
                ) ON CONFLICT DO NOTHING;
            """,
            params={
                "user_id": user.user_id,
                "username": user.user_name,
                "language": user.lang,
                "role": user.role,
                "is_alive": user.is_alive,
                "banned": user.banned,
                "free_time": user.free_time_at_week,
                "raiting": user.raiting,
            },
        )
    logger.info(
        "User added. Table=`%s`, user_id=%d, created_at='%s', "
        "language='%s', role=%s, is_alive=%s, banned=%s, raiting=%s, free_time=%s",
        "users",
        user.user_id,
        datetime.now(timezone.utc),
        user.lang,
        user.role,
        user.is_alive,
        user.banned,
        user.raiting,
        user.free_time_at_week,
    )


# доделать логику с названием группы
async def get_group_free_tasks(
    conn: AsyncConnection,
    *,
    group_id: int,
) -> List[Dict[str, Any]]:
    async with conn.cursor(row_factory=dict_row) as cursor:
        await cursor.execute(
            """
            SELECT
                id,
                description,
                start_time,
                duration,
                reward,
                status,
                deadline,
                end_time,
                user_id,
                group_id
            FROM tasks
            WHERE group_id = %s AND status = %s
            ORDER BY deadline ASC
            """,
            (group_id, TaskStatus.PENDING),
        )
        rows = await cursor.fetchall()
    return rows


async def get_group_title_by_id(conn: AsyncConnection, *, group_id: int) -> str:
    async with conn.cursor(row_factory=dict_row) as cursor:
        try:
            await cursor.execute(
                """
                SELECT
                    title
                FROM groups
                Where group_id = %s
                """,
                (group_id,),
            )
            row = await cursor.fetchone()
            return row["title"] if row else None
        except Exception as e:
            logger.error(f"Не удалось найти имя: {e}", exc_info=True)
            raise


async def add_task_to_db(
    conn: AsyncConnection, *, task: Task
) -> tuple[Any, ...] | None:
    async with conn.cursor() as cursor:
        try:
            await cursor.execute(
                query="""
                    INSERT INTO tasks(description, duration, reward, status,deadline,user_id,group_id)
                    VALUES(
                        %(description)s,
                        %(duration)s,
                        %(reward)s,
                        %(status)s,
                        %(deadline)s,
                        %(user_id)s,
                        %(group_id)s
                    )
                    RETURNING id
                    """,
                params={
                    "description": task.description,
                    "duration": task.duration,
                    "reward": task.reward,
                    "status": task.status,
                    "deadline": task.deadline,
                    "user_id": task.user_id,
                    "group_id": task.group_id,
                },
            )
            row = await cursor.fetchone()
            if row:
                return row[0]  # или row['id']
            return None
        except Exception as e:
            logger.error(f"Не удалось вставить задачу: {e}", exc_info=True)
            raise


# async def get_task_by_task_id(conn: AsyncConnection,)


async def get_user_tasks(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> List[Dict[str, Any]]:
    async with conn.cursor(row_factory=dict_row) as cursor:
        await cursor.execute(
            """
            SELECT
                id,
                description,
                start_time,
                duration,
                reward,
                status,
                deadline,
                end_time,
                user_id,
                group_id
            FROM tasks
            WHERE user_id = %s
            ORDER BY deadline ASC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
    return rows


# async def get_tasks_by_group_id


async def get_user(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> tuple[Any, ...] | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT 
                    id,
                    user_id,
                    username,
                    language,
                    role,
                    is_alive,
                    banned,
                    raiting,
                    free_time
                    FROM users WHERE user_id = %s;
            """,
            params=(user_id,),
        )
        row = await data.fetchone()
    logger.info("Row is %s", row)
    return row if row else None


async def get_user_groups(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> List[Dict[Any, ...]]:
    async with conn.cursor(row_factory=dict_row) as cursor:
        await cursor.execute(
            """
            SELECT
                g.id,
                g.group_id,
                g.title,
                g.name,
                g.is_alive,
                g.banned
            FROM user_group ug
            JOIN groups g ON ug.group_id = g.group_id
            WHERE ug.user_id = %s
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
    logger.info("Fetched %d groups for user_id=%s", len(rows), user_id)
    return rows


async def change_user_alive_status(
    conn: AsyncConnection,
    *,
    is_alive: bool,
    user_id: int,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET is_alive = %s
                WHERE user_id = %s;
            """,
            params=(is_alive, user_id),
        )
    logger.info("Updated `is_alive` status to `%s` for user %d", is_alive, user_id)


async def change_user_banned_status_by_id(
    conn: AsyncConnection,
    *,
    banned: bool,
    user_id: int,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET banned = %s
                WHERE user_id = %s
            """,
            params=(banned, user_id),
        )
    logger.info("Updated `banned` status to `%s` for user %d", banned, user_id)


async def change_user_banned_status_by_username(
    conn: AsyncConnection,
    *,
    banned: bool,
    username: str,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET banned = %s
                WHERE username = %s
            """,
            params=(banned, username),
        )
    logger.info("Updated `banned` status to `%s` for username %s", banned, username)


async def update_user_lang(
    conn: AsyncConnection,
    *,
    language: str,
    user_id: int,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET language = %s
                WHERE user_id = %s
            """,
            params=(language, user_id),
        )
    logger.info("The language `%s` is set for the user `%s`", language, user_id)


async def update_user_time(
    conn: AsyncConnection,
    *,
    time: timedelta,
    user_id: int,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET free_time = %s
                WHERE user_id = %s
            """,
            params=(time, user_id),
        )
    logger.info("The time interval `%s` is set for the user `%s`", timedelta, user_id)


async def get_user_lang(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> str | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT language FROM users WHERE user_id = %s;
            """,
            params=(user_id,),
        )
        row = await data.fetchone()
    if row:
        logger.info("The user with `user_id`=%s has the language %s", user_id, row[0])
    else:
        logger.warning("No user with `user_id`=%s found in the database", user_id)
    return row[0] if row else None


async def get_user_alive_status(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> bool | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT is_alive FROM users WHERE user_id = %s;
            """,
            params=(user_id,),
        )
        row = await data.fetchone()
    if row:
        logger.info(
            "The user with `user_id`=%s has the is_alive status is %s", user_id, row[0]
        )
    else:
        logger.warning("No user with `user_id`=%s found in the database", user_id)
    return row[0] if row else None


async def get_user_banned_status_by_id(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> bool | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT banned FROM users WHERE user_id = %s;
            """,
            params=(user_id,),
        )
        row = await data.fetchone()
    if row:
        logger.info(
            "The user with `user_id`=%s has the banned status is %s", user_id, row[0]
        )
    else:
        logger.warning("No user with `user_id`=%s found in the database", user_id)
    return row[0] if row else None


async def get_user_banned_status_by_username(
    conn: AsyncConnection,
    *,
    username: str,
) -> bool | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT banned FROM users WHERE username = %s;
            """,
            params=(username,),
        )
        row = await data.fetchone()
    if row:
        logger.info(
            "The user with `username`=%s has the banned status is %s", username, row[0]
        )
    else:
        logger.warning("No user with `username`=%s found in the database", username)
    return row[0] if row else None


async def get_user_role(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> UserRole | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT role FROM users WHERE user_id = %s;
            """,
            params=(user_id,),
        )
        row = await data.fetchone()
    if row:
        logger.info("The user with `user_id`=%s has the role is %s", user_id, row[0])
    else:
        logger.warning("No user with `user_id`=%s found in the database", user_id)
    return UserRole(row[0]) if row else None


async def add_user_message(
    conn: AsyncConnection,
    *,
    user_id: int,
    text: str,
    photo: bytes | None = None,
    video: bytes | None = None,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO user_messages(user_id, text, photo, video)
                VALUES(
                    %(user_id)s, 
                    %(text)s, 
                    %(photo)s, 
                    %(video)s 
                ) ON CONFLICT DO NOTHING;
            """,
            params={
                "user_id": user_id,
                "text": text,
                "photo": photo,
                "video": video,
            },
        )


async def get_group(
    conn: AsyncConnection,
    *,
    group_id: int,
) -> tuple[Any, ...] | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT 
                    id,
                    group_id,
                    title,
                    name
                FROM groups 
                WHERE group_id = %s;
            """,
            params=(group_id,),
        )
        row = await data.fetchone()
    logger.info("Group row is %s", row)
    return row if row else None


async def add_to_user_group_table(
    conn: AsyncConnection,
    *,
    user_id: int,
    group_id: int,
):
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO user_group (user_id, group_id) 
                VALUES (
                    %(user_id)s,
                    %(group_id)s
                    );
                """,
            params={"user_id": user_id, "group_id": group_id},
        )
        logger.info(
            f"пользователь с id{user_id} и группа с id {group_id} добавлены в таблицу user_group"
        )


async def add_group(conn: AsyncConnection, group: Group):
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO groups (group_id, title, name, is_alive, banned)
                VALUES (
                    %(group_id)s,
                    %(title)s,
                    %(name)s,
                    %(is_alive)s,
                    %(banned)s);
                """,
            params={
                "group_id": group.group_id,
                "title": group.title,
                "name": group.name,
                "is_alive": group.is_alive,
                "banned": group.banned,
            },
        )
        logger.info(
            f"группа {group.name} с id {group.group_id} добавлена в таблицу groups"
        )


async def user_accept_task(
    conn: AsyncConnection,
    *,
    task_id: int,
    status: str,
    user_id: int,
) -> None:
    """
    Обновляет статус и назначенного пользователя для задачи.

    Args:
        conn: Асинхронное соединение с БД.
        task_id: Идентификатор задачи (id).
        status: Новый статус задачи (например, 'in_progress', 'completed').
        user_id: Идентификатор пользователя, которому назначается задача.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE tasks
                SET status = %s, user_id = %s
                WHERE id = %s
            """,
            params=(status, user_id, task_id),
        )
    logger.info(
        "Task `%s` updated: status = '%s', user_id = %s", task_id, status, user_id
    )
    return True


async def user_cancel_task(
    conn: AsyncConnection,
    *,
    task_id: int,
    status: str,
    user_id: int,
) -> None:
    """
    Обновляет статус и назначенного пользователя для задачи.

    Args:
        conn: Асинхронное соединение с БД.
        task_id: Идентификатор задачи (id).
        status: Новый статус задачи (например, 'in_progress', 'completed').
        user_id: Идентификатор пользователя, которому назначается задача.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE tasks
                SET status = %s, user_id = %s
                WHERE id = %s
            """,
            params=(status, None, task_id),
        )
    logger.info(
        "Task `%s` updated: status = '%s', user_id = %s", task_id, status, user_id
    )
    return True
