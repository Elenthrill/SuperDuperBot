from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from aiogram.types import Message
from app.bot.enums.roles import UserRole
from app.bot.handlers import backend
from app.bot.handlers.backend import add_user_from_event, parse_duration
from app.bot.handlers.user import (
    process_deadline,
    process_description,
    process_duration,
    process_reward,
)


class FakeMessage:
    def __init__(self, text: str, user_id: int = 123, username: str = "tester", language_code: str | None = "ru"):
        self.text = text
        self.from_user = SimpleNamespace(
            id=user_id,
            username=username,
            language_code=language_code,
        )
        self.answers = []

    async def answer(self, text: str, **kwargs):
        self.answers.append(text)


class FakeState:
    def __init__(self, data=None):
        self.data = data or {}
        self.updated_data = {}
        self.state = None
        self.cleared = False

    async def update_data(self, **kwargs):
        self.updated_data.update(kwargs)
        self.data.update(kwargs)

    async def get_data(self):
        return self.data

    async def set_state(self, state=None):
        self.state = state

    async def clear(self):
        self.cleared = True


def test_parse_duration_accepts_valid_lowercase_format():
    assert parse_duration("1h30m") == timedelta(hours=1, minutes=30)


@pytest.mark.xfail(reason="BUG-018: Продолжительность задачи в формате 1H30M не принимается, потому что программа различает большие и маленькие буквы. Ожидалось, что H/M и h/m будут обрабатываться одинаково. Продолжительность задачи с пробелами в начале или конце не принимается. Ожидалось, что программа будет убирать лишние пробелы перед проверкой формата.")
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1H30M", timedelta(hours=1, minutes=30)),
        (" 1h30m ", timedelta(hours=1, minutes=30)),
    ],
)
def test_bug_18_parse_duration_should_be_case_insensitive_and_trim_spaces(raw, expected):
    assert parse_duration(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "abc",
        "1 час",
        "1h",
        "h30m",
        "1x30m",
        "1h30",
        "",
    ],
)
def test_bug_17_parse_duration_returns_none_for_invalid_format(raw):
    assert parse_duration(raw) is None


@pytest.mark.asyncio
async def test_bug_17_process_duration_shows_error_for_invalid_duration():
    message = FakeMessage("wrong-format")
    state = FakeState()
    i18n = {
        "invalid_duration": "Некорректная продолжительность",
    }

    await process_duration(message=message, state=state, i18n=i18n)

    assert message.answers == ["Некорректная продолжительность"]
    assert state.updated_data == {}


@pytest.mark.asyncio
async def test_bug_16_process_duration_rejects_zero_duration():
    message = FakeMessage("0h0m")
    state = FakeState()
    i18n = {
        "invalid_duration": "Некорректная продолжительность",
    }

    await process_duration(message=message, state=state, i18n=i18n)

    assert message.answers == ["❌ Длительность должна быть положительной."]
    assert state.updated_data == {}


@pytest.mark.asyncio
async def test_bug_16_process_duration_rejects_too_long_duration():
    message = FakeMessage("13h0m")
    state = FakeState()
    i18n = {
        "invalid_duration": "Некорректная продолжительность",
    }

    await process_duration(message=message, state=state, i18n=i18n)

    assert message.answers == ["❌ Длительность должна быть не более 12 часов."]
    assert state.updated_data == {}


@pytest.mark.asyncio
async def test_bug_16_process_duration_accepts_valid_duration():
    message = FakeMessage("1h30m")
    state = FakeState()
    i18n = {
        "ask_deadline": "Введите дедлайн",
    }

    await process_duration(message=message, state=state, i18n=i18n)

    assert state.data["duration"] == "1:30:00"
    assert message.answers == ["Введите дедлайн"]


@pytest.mark.asyncio
async def test_bug_14_process_description_rejects_non_breaking_spaces_only():
    message = FakeMessage("\u00a0\u00a0\u00a0")
    state = FakeState()
    i18n = {
        "ask_task_duration": "Введите продолжительность",
    }

    await process_description(message=message, state=state, i18n=i18n)

    assert message.answers == ["❌ Описание должно содержать хотя бы 3 символа."]
    assert "description" not in state.data

@pytest.mark.xfail(reason="BUG-021: Описание задачи длиннее 500 символов принимается программой, хотя должно отклоняться с понятным сообщением об ошибке.")
@pytest.mark.asyncio
async def test_bug_21_process_description_rejects_more_than_500_chars():
    message = FakeMessage("a" * 501)
    state = FakeState()
    i18n = {
        "ask_task_duration": "Введите продолжительность",
    }

    await process_description(message=message, state=state, i18n=i18n)

    assert message.answers == ["❌ Описание должно содержать не более 500 символов."]
    assert "description" not in state.data


@pytest.mark.asyncio
async def test_process_description_accepts_normal_description():
    message = FakeMessage("Нужно вынести мусор")
    state = FakeState()
    i18n = {
        "ask_task_duration": "Введите продолжительность",
    }

    await process_description(message=message, state=state, i18n=i18n)

    assert state.data["description"] == "Нужно вынести мусор"
    assert message.answers == ["Введите продолжительность"]


@pytest.mark.asyncio
async def test_bug_15_process_deadline_shows_error_for_invalid_datetime():
    message = FakeMessage("2026-99-99 25:99")
    state = FakeState(data={"duration": "1:00:00"})
    i18n = {
        "invalid_time": "Некорректный дедлайн",
    }

    await process_deadline(message=message, state=state, i18n=i18n)

    assert message.answers == ["Некорректный дедлайн"]
    assert "deadline" not in state.data


@pytest.mark.asyncio
async def test_bug_1_process_deadline_rejects_deadline_before_task_can_finish():
    now = datetime.now()
    too_early_deadline = now + timedelta(minutes=30)

    message = FakeMessage(too_early_deadline.strftime("%Y-%m-%d %H:%M"))
    state = FakeState(data={"duration": "1:00:00"})
    i18n = {
        "invalid_time": "Некорректный дедлайн",
    }

    await process_deadline(message=message, state=state, i18n=i18n)

    assert message.answers == ["❌ Дедлайн должен быть позже времени начала задачи."]
    assert "deadline" not in state.data


@pytest.mark.asyncio
async def test_process_deadline_accepts_deadline_after_task_can_finish():
    valid_deadline = datetime.now() + timedelta(hours=2)

    message = FakeMessage(valid_deadline.strftime("%Y-%m-%d %H:%M"))
    state = FakeState(data={"duration": "1:00:00"})
    i18n = {
        "ask_reward": "Введите награду",
    }

    await process_deadline(message=message, state=state, i18n=i18n)

    assert "deadline" in state.data
    assert "start_time" in state.data
    assert message.answers == ["Введите награду"]


@pytest.mark.xfail(reason="BUG-008: Если у нового пользователя Telegram не определён язык, программа пытается сохранить пользователя с language=None. Это может привести к ошибке БД, потому что поле языка обязательное.")
@pytest.mark.asyncio
async def test_bug_8_add_user_from_event_sets_default_language_when_language_code_is_none(monkeypatch):
    saved_user = None

    async def fake_get_user(conn, user_id):
        return None

    async def fake_add_user(conn, user):
        nonlocal saved_user
        saved_user = user

    monkeypatch.setattr(backend, "get_user", fake_get_user)
    monkeypatch.setattr(backend, "add_user", fake_add_user)

    message = make_aiogram_message(
        text="/start",
        user_id=555,
        username="new_user",
        language_code=None,
    )

    await add_user_from_event(event=message, conn=object())

    assert saved_user is not None
    assert saved_user.user_id == 555
    assert saved_user.user_name == "new_user"
    assert saved_user.lang == "ru"
    assert saved_user.role == UserRole.USER

@pytest.mark.xfail(reason="BUG-020: HTML-подобные теги в описании задачи не экранируются перед отправкой сообщения в Telegram. Из-за этого описание вроде <script>alert(1)</script> может сломать отправку сообщения с HTML-разметкой.")
@pytest.mark.asyncio
async def test_bug_20_process_reward_escapes_html_like_description():
    message = FakeMessage("5")
    state = FakeState(
        data={
            "description": "<script>alert(1)</script>",
            "start_time": datetime(2026, 4, 24, 10, 0).isoformat(),
            "duration": "1:00:00",
            "deadline": datetime(2026, 4, 24, 12, 0).isoformat(),
            "group_id": 777,
            "title": "Test Group",
        }
    )
    i18n = {
        "invalid_reward": "Некорректная награда",
        "ask_aprove": (
            "Описание: {description}\n"
            "Начало: {start_time}\n"
            "Длительность: {duration}\n"
            "Дедлайн: {deadline}\n"
            "Награда: {reward}\n"
            "Группа: {group_title}"
        ),
    }

    await process_reward(message=message, i18n=i18n, state=state)

    answer = message.answers[0]

    assert "<script>" not in answer
    assert "</script>" not in answer
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in answer

@pytest.mark.xfail(reason="BUG: Программа принимает награду 0, хотя количество баллов за задачу должно быть положительным. рограмма принимает отрицательную награду, например -1, хотя количество баллов за задачу не должно быть меньше нуля.")
@pytest.mark.asyncio
@pytest.mark.parametrize("reward", ["0", "-1"])
async def test_bug_process_reward_rejects_zero_and_negative_reward(reward):
    message = FakeMessage(reward)
    state = FakeState(
        data={
            "description": "Task",
            "start_time": datetime(2026, 4, 24, 10, 0).isoformat(),
            "duration": "1:00:00",
            "deadline": datetime(2026, 4, 24, 12, 0).isoformat(),
            "group_id": 777,
            "title": "Test Group",
        }
    )
    i18n = {
        "invalid_reward": "Некорректная награда",
        "ask_aprove": (
            "Описание: {description}\n"
            "Начало: {start_time}\n"
            "Длительность: {duration}\n"
            "Дедлайн: {deadline}\n"
            "Награда: {reward}\n"
            "Группа: {group_title}"
        ),
    }

    await process_reward(message=message, i18n=i18n, state=state)

    assert message.answers == ["Некорректная награда"]


@pytest.mark.asyncio
@pytest.mark.parametrize("reward", ["11", "abc"])
async def test_process_reward_rejects_invalid_reward_that_is_currently_handled(reward):
    message = FakeMessage(reward)
    state = FakeState(
        data={
            "description": "Task",
            "start_time": datetime(2026, 4, 24, 10, 0).isoformat(),
            "duration": "1:00:00",
            "deadline": datetime(2026, 4, 24, 12, 0).isoformat(),
            "group_id": 777,
            "title": "Test Group",
        }
    )
    i18n = {
        "invalid_reward": "Некорректная награда",
    }

    await process_reward(message=message, i18n=i18n, state=state)

    assert message.answers == ["Некорректная награда"]

def make_aiogram_message(
    text: str = "/start",
    user_id: int = 555,
    username: str = "new_user",
    language_code: str | None = None,
) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(),
        chat={
            "id": user_id,
            "type": "private",
        },
        from_user={
            "id": user_id,
            "is_bot": False,
            "first_name": "Test",
            "username": username,
            "language_code": language_code,
        },
        text=text,
    )