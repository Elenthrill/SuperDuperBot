from datetime import datetime
import logging
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


async def check_expiring_tasks(bot, db_pool):
    """
    Проверка задач, у которых осталось 1/3 времени до дедлайна
    """

    async with db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            query = """
                SELECT id, user_id, description, start_time, deadline, status, notified
                FROM tasks
                WHERE status != 'completed'
                  AND notified = FALSE
            """

            await cursor.execute(query)
            tasks = await cursor.fetchall()

            now = datetime.now()

            for task in tasks:
                task_id = task["id"]
                user_id = task["user_id"]
                description = task["description"]
                start_time = task["start_time"]
                deadline = task["deadline"]

                now = datetime.now(deadline.tzinfo)

                total_delta = deadline - start_time
                reminder_time = deadline - total_delta / 3

                if now >= reminder_time:
                    await bot.send_message(
                        user_id,
                        f"⚠️ Задача скоро истекает!\n"
                        f"📝 {description}\n"
                        f"⏳ Осталась 1/3 времени до дедлайна."
                    )

                    await cursor.execute(
                        """
                        UPDATE tasks
                        SET notified = TRUE
                        WHERE id = %s
                        """,
                        (task_id,)
                    )

                    logger.info(
                        "Notification sent for task %s",
                        task_id
                    )