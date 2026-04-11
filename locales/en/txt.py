EN: dict[str, str] = {
    "/start": "Hello!\n\nI am a Telegram bot for helping with household task distribution,\ndeveloped by BSUIR students of the POIT department, group 351004. The bot is under development\n"
    "together with <code>aiogram</code>!\n\n"
    "If you want, you can send me something or "
    "use the /help command",
    "/help": "I am a bot created for task distribution using "
    "<b>PostgreSQL</b> and the <code>aiogram</code> library. I can save your selected "
    "interface language and also send your messages back to you!\n\n"
    "Available commands:\n\n"
    "/start - restart the bot\n"
    "/lang - set the interface language\n"
    "/help - view this help\n"
    "/my_groups - view groups I am a member of\n"
    "/new_task - add a task (you need to be a member of at least one group)\n"
    "/free_tasks - view available tasks\n"
    "/my_tasks - your tasks\n",
    "/help_admin": "I am a bot created to demonstrate the collaboration of a relational database "
    "<b>PostgreSQL</b> and the <code>aiogram</code> library. I can save your selected "
    "interface language and also send your messages back to you!\n\nYour role in the "
    "system is <code>ADMIN</code>, so you have access to an extended list of commands:\n\n"
    "/start - restart the bot\n"
    "/lang - set the interface language\n"
    "/help - view this help\n"
    "/ban - ban a user\n"
    "/unban - unban a user\n"
    "/statistics - view user activity statistics",
    "/lang": "Choose language",
    "no_echo": "This update type is not supported by the send_copy method",
    "ru": "🇷🇺 Russian",
    "en": "🇬🇧 English",
    "save_lang_button_text": "✅ Save",
    "cancel_lang_button_text": "Cancel",
    "btn_police_text": "text for the button to contact the police",
    "btn_fire_department_text": "text for the button to contact the fire department",
    "btn_traffic_police_text": "text for the button to contact the traffic police",
    "report_pollice_answer": "text for the response when the btn_police button is pressed",
    "report_fire_department_answer": "text for the response when the btn_fire_department button is pressed",
    "report_traffic_pollice_answer": "text for the response when the btn_traffic_police button is pressed",
    "report_sending_answer": "text for the response to a citizen's statement submission",
    "/report": "text for the report command",
    "report_accepted": "text sent to the user when their request is accepted",
    "report_canceled": "text sent to the user when their request is rejected",
    "report_accept_service_worker_answer": "text for the response when btn_accept is pressed",
    "report_cancel_service_worker_answer": "text for the response when cancel is pressed",
    "btn_report_cancel_text": "text for btn_report_cancel",
    "btn_report_accept_text": "text for btn_report_accept button",
    "lang_saved": "Language successfully set and will be used for the bot's interface "
    "from now on!\n\nIf you want, you can send me something or "
    "use the /help command",
    "lang_cancelled": "Alright, your language is still: {}.\n\nIf you want, you can send me something "
    "or use the /help command",
    "/start_description": "Restart the bot",
    "/lang_description": "Set the interface language",
    "/help_description": "View help on how to use the bot",
    "/ban_description": "Ban a user (requires user_id or username)",
    "/unban_description": "Unban a user (requires user_id or username)",
    "/statistics_description": "View user activity statistics",
    "empty_ban_answer": "❗ Please specify a user ID or @username.",
    "incorrect_ban_arg": "⚠️ <b>Invalid format.</b>\n\nUse: /ban <code>ID</code> "
    "or /ban <code>@username</code>",
    "already_banned": "❗ User is already banned!",
    "successfully_banned": "⚠️ User has been successfully banned!",
    "no_user": "❗ No such user in the database!",
    "empty_unban_answer": "❗ Please specify a user ID or @username.",
    "incorrect_unban_arg": "⚠️ <b>Invalid format.</b>\n\nUse: /unban <code>ID</code> "
    "or /unban <code>@username</code>",
    "not_banned": "❗ User was not banned!",
    "successfully_unbanned": "⚠️ User has been successfully unbanned!",
    "statistics": "📊 <b>User action statistics:</b>\n\n{}",
    "bad_time_format": "Invalid time format entered. Please enter a message in the format: XXhXXm, e.g., 0h30m",
    "succes_user_time_update": "Your free time has been successfully updated",
    "/set_time": "Please enter the time in the format XXhXXm, e.g., 2h30m",
    "add_to_group": "Hello, I am a bot for helping with household task distribution",
    "/new_task": "You have started the task creation process. First, select the group for which you want to create a task (currently enter the id or name of one of your teams)",
    "no_groups": "You are not a member of any group at the moment",
    "invalid_group": "This group does not exist",
    "task_description": "Enter a text description of the task",
    "ask_task_duration": "Please enter the approximate task duration in the format XXhXXm, e.g., 2h30m",
    "ask_reward": "Enter the number of points for this task",
    "ask_aprove": "You have created a task with the following parameters:\nDescription: {description}\nDuration: {duration}\nDeadline: {deadline}\nReward: {reward}\nGroup: {group_title}\nTo confirm, press /yes, to cancel, press /start",
    "ask_deadline": "Enter the task deadline in the format YYYY-MM-DD HH:MM, e.g.:\n2026-04-05 14:30",
    "/new_task_description": "add a task to a group, you need to be a group member to add",
    "/set_time_description": "set your available free time per week",
    "task_aprove": "Task successfully added",
    "no_free_tasks": "There are no available tasks at the moment",
    "/free_tasks_description": "available tasks in the groups you belong to",
    "/my_tasks_description": "your current tasks",
    "/my_groups_description": "groups you are a member of",
}
