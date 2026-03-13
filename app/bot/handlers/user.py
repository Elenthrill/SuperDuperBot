import logging
from contextlib import suppress

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
from aiogram.fsm.state import default_state
from aiogram.types import (
    BotCommandScopeChat,
    ChatMemberUpdated,
    Message,
    CallbackQuery,
    ContentType,
)
from app.bot.enums.roles import UserRole
from app.bot.keyboards.menu_button import get_main_menu_commands
from app.bot.keyboards.keyboard import get_service_choice_kb, get_report_kb
from app.bot.states.states import LangSg, DialogWithUser
from app.bot.filters.filters import UserRoleFilter
from app.infastructure.database.db import (
    add_user,
    change_user_alive_status,
    get_user,
    get_user_lang,
    add_report,
)

from psycopg import AsyncConnection

logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(CommandStart())
async def process_comand_start(
    message: Message,
    conn: AsyncConnection,
    bot: Bot,
    i18n: dict[str, str],
    state: FSMContext,
    admin_ids: list[int],
    translations: dict,
):
    user_row = await get_user(conn, user_id=message.from_user.id)
    if user_row is None:
        if message.from_user.id in admin_ids:
            user_role = UserRole.ADMIN
        else:
            user_role = UserRole.USER

        await add_user(
            conn,
            user_id=message.from_user.id,
            username=message.from_user.username,
            language=message.from_user.language_code,
            role=user_role,
        )
    else:
        user_role = UserRole(user_row[4])
        await change_user_alive_status(
            conn,
            is_alive=True,
            user_id=message.from_user.id,
        )

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
    elif state.get_state() == DialogWithUser.user_report_start:
        data = await state.get_data()
        with suppress(TelegramBadRequest):
            msg_id = data.get("report_kb_msg_id")
            if msg_id:
                await bot.edit_message_reply_markup(
                    chat_id=message.from_user.id, message_id=msg_id
                )
    await bot.set_my_commands(
        commands=get_main_menu_commands(i18n=i18n, role=user_role),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT, chat_id=message.from_user.id
        ),
    )

    await message.answer(text=i18n.get("/start"))
    await state.clear()


@user_router.message(Command(commands="help"))
async def process_help_command(message: Message, i18n: dict[str, str]):
    await message.answer(text=i18n.get("/help"))


@user_router.message(StateFilter(DialogWithUser.service_choice), ~CommandStart())
async def process_any_message_when_service_choice(
    message: Message,
    bot: Bot,
    i18n: dict[str, str],
    state: FSMContext,
):
    user_id = message.from_user.id
    data = await state.get_data()

    with suppress(TelegramBadRequest):
        msg_id = data.get("report_kb_msg_id")
        if msg_id:
            await bot.edit_message_reply_markup(chat_id=user_id, message_id=msg_id)

    msg = await message.answer(
        text=i18n.get("report"), reply_markup=get_service_choice_kb(i18n=i18n)
    )
    await state.update_data(report_kb_msg_id=msg.message_id)


# @user_router.message(StateFilter(DialogWithUser.user_report_start), ~CommandStart())
# async def process_answer_on_user_report(
#     message: Message,
#     i18n: dict[str, str],
#     conn: AsyncConnection,
#     state: FSMContexwt,
#     bot: Bot,
# ):
#     data = await state.get_data()
#     await message.answer(text=i18n.get("report_sending_answer"))
#     group_id = data.get("group_id")
#     if message.content_type == ContentType.TEXT:
#         text = message.text
#         await bot.send_message(
#             chat_id=group_id, text=text, reply_markup=get_report_kb(i18n=i18n)
#         )
#     elif message.content_type == ContentType.PHOTO:
#         await bot.send_photo(
#             chat_id=group_id,
#             photo=message.photo[-1].file_id,
#             caption=message.caption,
#             reply_markup=get_report_kb(i18n=i18n),
#         )
#     elif message.content_type == ContentType.VIDEO:
#         await bot.send_video(
#             chat_id=group_id,
#             video=message.video.file_id,
#             caption=message.caption,
#             reply_markup=get_report_kb(i18n=i18n),
#         )
#     await state.set_state()


@user_router.message(StateFilter(DialogWithUser.user_report_start), ~CommandStart())
async def process_answer_on_user_report(
    message: Message,
    i18n: dict[str, str],
    conn: AsyncConnection,
    state: FSMContext,
    bot: Bot,
):
    text = None
    photo_bytes = None
    video_bytes = None
    data = await state.get_data()
    await message.answer(text=i18n.get("report_sending_answer"))
    group_id = data.get("group_id")
    agency = data.get("agency")
    if message.content_type == ContentType.TEXT:
        text = message.text
    elif message.content_type == ContentType.PHOTO:
        bot: Bot = data["bot"]
        text = message.caption
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        photo_data = await bot.download_file(file.file_path)
        photo_bytes = photo_data.read()
    elif message.content_type == ContentType.VIDEO:
        bot: Bot = data["bot"]
        text = message.caption
        video = message.video
        file = await bot.get_file(video.file_id)
        video_data = await bot.download_file(file.file_path)
        video_bytes = video_data.read()
    report_id = await add_report(
        conn,
        user_id=message.from_user.id,
        agency=agency,
        text=text,
        video=video_bytes,
        photo=photo_bytes,
        status="processing",
        service_worker_id=None,
    )
    print(f"CCCCCCCCCCCC{report_id}CCCCCCCCCCCCCC")
    user_id = message.from_user.id
    if message.content_type == ContentType.TEXT:
        text = message.text
        await bot.send_message(
            chat_id=group_id,
            text=text,
            reply_markup=get_report_kb(i18n=i18n, report_id=report_id, user_id=user_id),
        )
    elif message.content_type == ContentType.PHOTO:
        await bot.send_photo(
            chat_id=group_id,
            photo=message.photo[-1].file_id,
            caption=message.caption,
            reply_markup=get_report_kb(i18n=i18n, report_id=report_id, user_id=user_id),
        )
    elif message.content_type == ContentType.VIDEO:
        await bot.send_video(
            chat_id=group_id,
            video_bytes=message.video.file_id,
            caption=message.caption,
            reply_markup=get_report_kb(i18n=i18n, report_id=report_id, user_id=user_id),
        )
    await state.set_state()


@user_router.message(Command(commands="report"))
async def process_report_command(
    message: Message,
    i18n: dict[str, str],
    state: FSMContext,
):
    await state.set_state(DialogWithUser.service_choice)
    msg = await message.answer(
        text=i18n.get("/report"),
        reply_markup=get_service_choice_kb(i18n=i18n),
    )
    await state.update_data(report_kb_msg_id=msg.message_id)


@user_router.callback_query(F.data == "btn_police")
async def process_btn_police_click(
    callback: CallbackQuery,
    i18n: dict[str, str],
    state: FSMContext,
    pollice_group_id: int,
):
    print(f"AAAAAAAAAAAA{pollice_group_id}AAAAAAAAAAA")
    await state.set_state(DialogWithUser.user_report_start)
    await callback.message.edit_text(text=i18n.get("report_pollice_answer"))
    await state.update_data(group_id=pollice_group_id, agency="pollice")


@user_router.callback_query(F.data == "btn_fire_department")
async def process_btn_fire_department_click(
    callback: CallbackQuery,
    i18n: dict[str, str],
    state: FSMContext,
    fire_department_group_id: int,
):
    await state.set_state(DialogWithUser.user_report_start)
    print(f"AAAAAAAAAAAAA{fire_department_group_id} aaaaaaaaaaaaaaaaa")
    await callback.message.edit_text(text=i18n.get("report_fire_department_answer"))
    await state.update_data(group_id=fire_department_group_id, agency="fire_department")


@user_router.callback_query(F.data == "btn_traffic_police")
async def process_btn_traffic_police_click(
    callback: CallbackQuery,
    i18n: dict[str, str],
    state: FSMContext,
    traffic_police_group_id: int,
):
    await state.set_state(DialogWithUser.user_report_start)
    await callback.message.edit_text(text=i18n.get("report_traffic_pollice_answer"))
    print(f"AAAAAAAAAAAAA{traffic_police_group_id} aaaaaaaaaaaaaaaaa")
    await state.update_data(group_id=traffic_police_group_id, agency="traffic_police")


@user_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated, conn: AsyncConnection):
    logger.info("User %d has blocked the bot", event.from_user.id)
    await change_user_alive_status(conn, user_id=event.from_user.id, is_alive=False)
