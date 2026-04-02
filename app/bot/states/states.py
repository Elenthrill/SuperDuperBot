from aiogram.fsm.state import State, StatesGroup


class LangSg(StatesGroup):
    lang = State()


class DialogWithUser(StatesGroup):
    user_ad_time_start = State()
    user_ad_task_start = State()

class SetTimeStates(StatesGroup):
    choosing_day = State()
    input_duration = State()

class CreateTaskStates(StatesGroup):
    waiting_group_id = State()
    waiting_description = State()
    waiting_start_time = State()
    waiting_duration = State()
    waiting_deadline = State()
    waiting_reward = State()
    aprove_task = State()
