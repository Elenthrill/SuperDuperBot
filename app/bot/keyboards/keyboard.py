from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


class MyCallback(CallbackData, prefix="my"):
    mydata: str
    report_id: int
    user_id: int


def get_lang_settings_kb(
    i18n: dict, locales: list[str], checked: str
) -> InlineKeyboardMarkup:
    buttons = []
    for locale in sorted(locales):
        if locale == "default":
            continue
        if locale == checked:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"🔘 {i18n.get(locale)}", callback_data=locale
                    )
                ]
            )
        else:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"⚪️ {i18n.get(locale)}", callback_data=locale
                    )
                ]
            )
    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("cancel_lang_button_text"),
                callback_data="cancel_lang_button_data",
            ),
            InlineKeyboardButton(
                text=i18n.get("save_lang_button_text"),
                callback_data="save_lang_button_data",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_service_choice_kb(i18n: dict) -> InlineKeyboardMarkup:
    buttons = []
    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("btn_police_text"),
                callback_data="btn_police",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("btn_fire_department_text"),
                callback_data="btn_fire_department",
            ),
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("btn_traffic_police_text"),
                callback_data="btn_traffic_police",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_report_kb(i18n: dict, user_id, report_id) -> InlineKeyboardMarkup:
    buttons = []
    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("btn_report_accept_text"),
                callback_data=MyCallback(
                    mydata="btn_report_accept", user_id=user_id, report_id=report_id
                ).pack(),  # "btn_report_accept",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("btn_report_cancel_text"),
                callback_data=MyCallback(
                    mydata="btn_report_cancel", user_id=user_id, report_id=report_id
                ).pack(),
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
