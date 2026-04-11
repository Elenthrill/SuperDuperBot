from aiogram.types import BotCommand
from app.bot.enums.roles import UserRole


def get_main_menu_commands(i18n: dict[str, str], role: UserRole):
    if role == UserRole.USER:
        return [
            BotCommand(command="/start", description=i18n.get("/start_description")),
            BotCommand(command="/lang", description=i18n.get("/lang_description")),
            BotCommand(command="/help", description=i18n.get("/help_description")),
            BotCommand(
                command="/set_time", description=i18n.get("/set_time_description")
            ),
            BotCommand(
                command="/new_task", description=i18n.get("/new_task_description")
            ),
            BotCommand(
                command="/free_tasks", description=i18n.get("/free_tasks_description")
            ),
            BotCommand(
                command="/my_tasks", description=i18n.get("/my_tasks_description")
            ),
            BotCommand(
                command="/my_groups", description=i18n.get("/my_groups_description")
            ),
        ]
    elif role == UserRole.ADMIN:
        return [
            BotCommand(command="/start", description=i18n.get("/start_description")),
            BotCommand(command="/lang", description=i18n.get("/lang_description")),
            BotCommand(command="/help", description=i18n.get("/help_description")),
            BotCommand(command="/ban", description=i18n.get("/ban_description")),
            BotCommand(command="/unban", description=i18n.get("/unban_description")),
            BotCommand(
                command="/statistics", description=i18n.get("/statistics_description")
            ),
        ]
