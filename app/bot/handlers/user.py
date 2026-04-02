import logging
from contextlib import suppress
from datetime import timedelta
from aiogram import Bot, Router, F
from aiogram.enums import BotCommandScopeType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import (
    KICKED,
    ChatMemberUpdatedFilter,
    Command,
    CommandStart,
    StateFilter,
)
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BotCommandScopeChat,
    ChatMemberUpdated,
    Message,
)
from app.bot.entities.user import User, Task
from datetime import datetime, timedelta
from app.bot.enums.roles import UserRole, TaskStatus
from app.bot.keyboards.menu_button import get_main_menu_commands
from app.bot.states.states import LangSg, DialogWithUser, CreateTaskStates
from app.bot.handlers.backend import (
    add_user_from_event,
    get_groups_text,
    parse_duration,
    get_group_id_for_task,
    str_to_timedelta,
)
from app.infastructure.database.db import (
    change_user_alive_status,
    get_user_lang,
    update_user_time,
    add_to_user_group_table,
    get_user_groups,
    get_group,
    add_task_to_db,
)

from psycopg import AsyncConnection

logger = logging.getLogger(__name__)

user_router = Router()


# пользователь кликнул на ссылку
@user_router.message(CommandStart(deep_link=True))
async def cmd_start_deep(
    message: Message, command: CommandStart, conn: AsyncConnection
):
    command_str: str = command.args
    if command_str and command_str.startswith("group_"):
        try:
            target_group_id = int(command_str[6:])
        except ValueError:
            logger.exception("Неверный формат ссылки")
            return

        await add_user_from_event(message, conn=conn)
        user_groups = await get_user_groups(conn, user_id=message.from_user.id)
        for group in user_groups:
            if group["group_id"] == target_group_id:
                break
        else:
            await add_to_user_group_table(
                conn, user_id=message.from_user.id, group_id=target_group_id
            )
        group_row = await get_group(conn, group_id=target_group_id)
    await message.answer(
        f"Добро пожаловать в бота, вы стали участником группы : {group_row[2]}"
    )


@user_router.message(CommandStart())
async def process_comand_start(
    message: Message,
    conn: AsyncConnection,
    bot: Bot,
    i18n: dict[str, str],
    state: FSMContext,
    translations: dict,
):
    await add_user_from_event(conn=conn, event=message)
    if await state.get_state() == LangSg.lang:
        data = await state.get_data()
        with suppress(TelegramBadRequest):
            msg_id = data.get("lang_settings_msg_id")
            if msg_id:
                await bot.edit_message_reply_markup(
                    chat_id=message.from_user.id, message_id=msg_id
                )
        user_lang = await get_user_lang(conn, user_id=message.from_user.id)
        i18n = translations.get(user_lang)
    await bot.set_my_commands(
        commands=get_main_menu_commands(i18n=i18n, role=UserRole.USER),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT, chat_id=message.from_user.id
        ),
    )
    await message.answer(text=i18n.get("/start"))
    await state.clear()


# @user_router.message(Command(commands="set_time"))
#async def process_comand_set_time(
##    message: Message,
#    conn: AsyncConnection,
#    bot: Bot,
#    i18n: dict[str, str],
#    state: FSMContext,
#):
#    await state.set_state(DialogWithUser.user_ad_time_start)
#   await message.answer(i18n.get("/set_time"))


@user_router.message(Command(commands="my_groups"))
async def process_comand_my_groups(
    message: Message, i18n: dict[str, str], conn: AsyncConnection
):
    text = await get_groups_text(conn, user_id=message.from_user.id)
    await message.answer(text=text)


@user_router.message(StateFilter(DialogWithUser.user_ad_time_start), ~CommandStart())
async def process_ad_user_time(
    message: Message,
    conn: AsyncConnection,
    bot: Bot,
    i18n: dict[str, str],
    state: FSMContext,
):
    text = message.text.strip()
    duration = parse_duration(text)
    if not duration:
        await message.answer(text=i18n.get("bad_time_format"))
        return
    try:
        await update_user_time(conn, time=duration, user_id=message.from_user.id)
        await message.answer(text=i18n.get("succes_user_time_update"))
        await state.set_state()
    except:
        await message.answer(text=i18n.get("eror"))


@user_router.message(Command(commands="help"))
async def process_help_command(message: Message, i18n: dict[str, str]):
    await message.answer(text=i18n.get("/help"))


# @user_router.message(Command(commands="my_tasks"))
# async def process_my_tasks_command(
#     message: Message,
#     conn: AsyncConnection,
#     i18n: dict,
# ):
#     lines = []
#     groups = await get_user_tasks(conn, user_id=message.from_user.id)
#     for group in groups:
#         lines.append(f"Группа: {group['title']} ID:{group['group_id']}")
#     result = "\n".join(lines)
#     await message.answer(text=result)


@user_router.message(Command(commands="new_task"))
async def process_new_task_command(
    message: Message,
    conn: AsyncConnection,
    i18n: dict,
    state: FSMContext,
):
    text = await get_groups_text(conn, message.from_user.id)
    if text == None:
        await message.answer(i18n.get("no_groups"))
        return
    await state.set_state(CreateTaskStates.waiting_group_id)
    await message.answer(i18n.get("/new_task"))
    await message.answer(text=text)


@user_router.message(~CommandStart(), StateFilter(CreateTaskStates.waiting_group_id))
async def process_add_group_id_to_task(
    message: Message, conn: AsyncConnection, state: FSMContext, i18n: dict
):

    group_id, title = await get_group_id_for_task(
        conn, user_id=message.from_user.id, user_input=message.text
    )
    logger.info(title)
    if not group_id or not title:
        await message.answer(i18n.get("invalid_group"))
        return

    await state.update_data(group_id=group_id, title=title)
    await state.set_state(CreateTaskStates.waiting_description)
    await message.answer(i18n.get("task_description"))


@user_router.message(CreateTaskStates.waiting_description, F.text)
async def process_description(message: Message, state: FSMContext, i18n: dict):
    description = message.text.strip()
    if len(description) < 3:
        await message.answer("❌ Описание должно содержать хотя бы 3 символа.")
        return
    await state.update_data(description=description)
    await state.set_state(CreateTaskStates.waiting_duration)
    await message.answer(i18n.get("ask_task_duration"))


@user_router.message(CreateTaskStates.waiting_duration, F.text, ~CommandStart())
async def process_duration(
    message: Message,
    state: FSMContext,
    i18n: dict,
):
    try:
        duration = parse_duration(message.text.strip())
        dur_str = str(duration)
    except ValueError:
        await message.answer(i18n.get("invalid_duration"))
        return

    if duration.total_seconds() <= 0:
        await message.answer("❌ Длительность должна быть положительной.")
        return

    await state.update_data(duration=dur_str)
    await state.set_state(CreateTaskStates.waiting_deadline)
    await message.answer(i18n.get("ask_deadline"))


@user_router.message(CreateTaskStates.waiting_deadline, F.text, ~CommandStart())
async def process_deadline(message: Message, state: FSMContext, i18n: dict):
    try:
        deadline = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer(i18n("invalid_time"))
        return
    start_time = datetime.now()
    data = await state.get_data()
    if deadline <= start_time:
        await message.answer("❌ Дедлайн должен быть позже времени начала задачи.")
        return
    await state.update_data(
        deadline=deadline.isoformat(), start_time=start_time.isoformat()
    )
    await state.set_state(CreateTaskStates.waiting_reward)
    await message.answer(i18n.get("ask_reward"))


@user_router.message(CreateTaskStates.waiting_reward, F.text)
async def process_reward(message: Message, i18n: dict, state: FSMContext):
    try:
        reward = int(message.text.strip())
        if reward <= 0:
            raise ValueError
    except ValueError:
        await message.answer(i18n.get("invalid_reward"))
        return
    await state.update_data(reward=reward)
    data = await state.get_data()
    task = Task(
        id=0,  # временно, БД присвоит настоящий
        description=data["description"],
        start_time=datetime.fromisoformat(data["start_time"]),
        duration=str_to_timedelta(data["duration"]),
        deadline=datetime.fromisoformat(data["deadline"]),
        reward=data["reward"],
        user_id=message.from_user.id,
        group_id=data["group_id"],
        status=TaskStatus.PENDING,
        end_time=None,
    )
    await state.set_state(CreateTaskStates.aprove_task)
    await message.answer(
        i18n["ask_aprove"].format(
            description=task.description,
            start_time=task.start_time,
            duration=task.duration,
            deadline=task.deadline,
            reward=task.reward,
            group_title=data["title"],
        )
    )


@user_router.message(CreateTaskStates.aprove_task, Command("yes"), ~CommandStart())
async def process_aprove_task(
    message: Message, state: FSMContext, conn: AsyncConnection, i18n: dict
):
    data = await state.get_data()
    task = Task(
        id=0,  # временно, БД присвоит настоящий
        description=data["description"],
        start_time=datetime.fromisoformat(data["start_time"]),
        duration=str_to_timedelta(data["duration"]),
        deadline=datetime.fromisoformat(data["deadline"]),
        reward=data["reward"],
        user_id=message.from_user.id,
        group_id=data["group_id"],
        status=TaskStatus.PENDING,
        end_time=None,
    )
    try:
        task_id = await add_task_to_db(conn, task=task)
    except Exception as e:
        logger.error("Ошибка при попытке добавить задачу в бд")
        await message.answer(f"❌ Ошибка при сохранении задачи: {e}")
        await state.clear()
        return

    await state.clear()
    await message.answer(i18n.get("task_aprove"))


@user_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated, conn: AsyncConnection):
    logger.info("User %d has blocked the bot", event.from_user.id)
    await change_user_alive_status(conn, user_id=event.from_user.id, is_alive=False)
