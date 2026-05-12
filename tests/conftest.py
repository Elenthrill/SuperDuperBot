from types import SimpleNamespace

import pytest


class FakeMessage:
    def __init__(
        self,
        text: str = "",
        user_id: int = 123,
        username: str = "tester",
        language_code: str | None = "ru",
        chat_type: str = "private",
        answer_message_id: int = 777,
    ):
        self.text = text
        self.from_user = SimpleNamespace(
            id=user_id,
            username=username,
            language_code=language_code,
        )
        self.chat = SimpleNamespace(type=chat_type)
        self.answers = []
        self.replies = []
        self.answer_message_id = answer_message_id

    async def answer(self, text=None, **kwargs):
        self.answers.append({"text": text, "kwargs": kwargs})
        return SimpleNamespace(message_id=self.answer_message_id)

    async def reply(self, text=None, **kwargs):
        self.replies.append({"text": text, "kwargs": kwargs})


class FakeCallbackMessage:
    def __init__(self):
        self.edited_texts = []
        self.answers = []

    async def edit_text(self, text=None, **kwargs):
        self.edited_texts.append({"text": text, "kwargs": kwargs})

    async def answer(self, text=None, **kwargs):
        self.answers.append({"text": text, "kwargs": kwargs})


class FakeCallback:
    def __init__(self, data: str = "", user_id: int = 123):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id)
        self.message = FakeCallbackMessage()
        self.answers = []

    async def answer(self, text=None, *args, **kwargs):
        self.answers.append({"text": text, "args": args, "kwargs": kwargs})


class FakeState:
    def __init__(self, data=None):
        self.data = data or {}
        self.updated_data = {}
        self.state = None
        self.state_values = []
        self.cleared = False
        self.set_data_calls = []

    async def update_data(self, **kwargs):
        self.updated_data.update(kwargs)
        self.data.update(kwargs)

    async def get_data(self):
        return self.data

    async def set_data(self, data):
        self.data = data
        self.set_data_calls.append(data)

    async def set_state(self, state=None):
        self.state = state
        self.state_values.append(state)

    async def clear(self):
        self.cleared = True


class FakeBot:
    def __init__(self):
        self.commands_calls = []
        self.sent_messages = []

    async def set_my_commands(self, **kwargs):
        self.commands_calls.append(kwargs)

    async def send_message(self, chat_id, text):
        self.sent_messages.append({"chat_id": chat_id, "text": text})


@pytest.fixture
def fake_message():
    return FakeMessage


@pytest.fixture
def fake_callback():
    return FakeCallback


@pytest.fixture
def fake_state():
    return FakeState


@pytest.fixture
def fake_bot():
    return FakeBot


@pytest.fixture
def fake_conn():
    return object()
