from aiogram.fsm.state import State, StatesGroup


class LangSg(StatesGroup):
    lang = State()


class DialogWithUser(StatesGroup):
    service_choice = State()
    user_report_start = State()
