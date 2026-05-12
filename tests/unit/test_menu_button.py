from app.bot.enums.roles import UserRole
from app.bot.keyboards.menu_button import get_main_menu_commands


def make_i18n():
    return {
        "/start_description": "Start",
        "/lang_description": "Language",
        "/help_description": "Help",
        "/set_time_description": "Set time",
        "/new_task_description": "New task",
        "/free_tasks_description": "Free tasks",
        "/my_tasks_description": "My tasks",
        "/my_groups_description": "My groups",
        "/archive_description": "Archive",
        "/ban_description": "Ban",
        "/unban_description": "Unban",
        "/statistics_description": "Statistics",
    }


def test_get_main_menu_commands_for_user():
    commands = get_main_menu_commands(make_i18n(), UserRole.USER)

    command_names = [command.command for command in commands]

    assert command_names == [
        "/start",
        "/lang",
        "/help",
        "/set_time",
        "/new_task",
        "/free_tasks",
        "/my_tasks",
        "/my_groups",
        "/archive",
    ]


def test_get_main_menu_commands_for_admin():
    commands = get_main_menu_commands(make_i18n(), UserRole.ADMIN)

    command_names = [command.command for command in commands]

    assert command_names == [
        "/start",
        "/lang",
        "/help",
        "/ban",
        "/unban",
        "/statistics",
    ]


def test_get_main_menu_commands_for_service_worker_returns_empty_list():
    commands = get_main_menu_commands(make_i18n(), UserRole.SERVICE_WORKER)

    assert commands is None

def test_get_main_menu_commands_for_user_descriptions():
    commands = get_main_menu_commands(make_i18n(), UserRole.USER)

    assert commands[0].description == "Start"
    assert commands[1].description == "Language"