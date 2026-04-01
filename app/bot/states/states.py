from aiogram.fsm.state import State, StatesGroup


class LangSg(StatesGroup):
    lang = State()


class DialogWithUser(StatesGroup):
    user_ad_time_start = State()
    user_ad_task_start = State()

class SetTimeStates(StatesGroup):
    choosing_day = State()
    input_duration = State()