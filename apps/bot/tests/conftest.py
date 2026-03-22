from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Chat, Message, Update, User


def make_update(
    text: str = "/start",
    chat_id: int = 12345,
    args: list[str] | None = None,
) -> tuple[Update, MagicMock]:
    """Create a mock Telegram Update and context."""
    user = MagicMock(spec=User)
    user.id = chat_id
    user.first_name = "Test"

    chat = MagicMock(spec=Chat)
    chat.id = chat_id

    message = MagicMock(spec=Message)
    message.text = text
    message.chat = chat
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.effective_chat = chat
    update.message = message

    context = MagicMock()
    context.args = args or []

    return update, context


@pytest.fixture
def mock_update_factory():
    """Factory fixture for creating mock Updates."""
    return make_update


@pytest.fixture
def start_update():
    return make_update("/start")


@pytest.fixture
def linked_chat_id():
    return 12345
