from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.link import link_handler
from bot.handlers.log import log_handler, parse_log_args
from bot.handlers.report import report_handler
from bot.handlers.start import WELCOME_MESSAGE, start_handler
from bot.handlers.status import status_handler
from bot.handlers.stop import stop_handler
from bot.services.api_client import UnlinkedUserError
from tests.conftest import make_update

# ---------------------------------------------------------------------------
# /start handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_handler():
    """Assert /start sends the welcome message."""
    update, context = make_update("/start")
    await start_handler(update, context)
    update.message.reply_text.assert_awaited_once_with(WELCOME_MESSAGE)


# ---------------------------------------------------------------------------
# /link handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_link_handler_success():
    """Mock API returning 200 — assert success message sent."""
    update, context = make_update("/link", args=["user@example.com"])

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch(
        "bot.handlers.link.BotApiClient.link_account",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        await link_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "Successfully linked" in reply


@pytest.mark.asyncio
async def test_link_handler_invalid_email():
    """Mock API returning 404 — assert error message sent."""
    update, context = make_update("/link", args=["notfound@example.com"])

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch(
        "bot.handlers.link.BotApiClient.link_account",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        await link_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "No account found" in reply


@pytest.mark.asyncio
async def test_link_handler_no_args():
    """No email arg — assert usage hint sent."""
    update, context = make_update("/link", args=[])
    await link_handler(update, context)
    reply = update.message.reply_text.await_args[0][0]
    assert "Usage:" in reply


# ---------------------------------------------------------------------------
# /log handler — argument parsing
# ---------------------------------------------------------------------------


def test_log_handler_parsing():
    """Test that '/log 2.5 'Project Alpha' Meeting notes' parses correctly.

    Telegram keeps quoted strings as single tokens, so args arrives as
    ["2.5", "'Project Alpha'", "Meeting", "notes"].
    """
    result = parse_log_args(["2.5", "'Project Alpha'", "Meeting", "notes"])
    assert result is not None
    hours, project, description = result
    assert hours == 2.5
    assert project == "Project Alpha"
    assert description == "Meeting notes"


def test_log_handler_parsing_quoted():
    """Test quoted project name parsing via shlex."""
    result = parse_log_args(["2.5", "'Project Alpha'", "Meeting notes"])
    assert result is not None
    hours, project, description = result
    assert hours == 2.5
    assert project == "Project Alpha"
    assert description == "Meeting notes"


def test_log_handler_parsing_invalid():
    """Insufficient args returns None."""
    assert parse_log_args([]) is None
    assert parse_log_args(["2.5"]) is None
    assert parse_log_args(["2.5", "Project"]) is None


@pytest.mark.asyncio
async def test_log_handler_api_call():
    """Mock create_manual_session — assert called with correct args."""
    update, context = make_update(
        "/log", args=["2.5", "'Project Alpha'", "Meeting", "notes"]
    )

    mock_session = {"id": "abc123", "project_name": "Project Alpha"}

    with (
        patch(
            "bot.handlers.log.BotApiClient.authenticate",
            new_callable=AsyncMock,
            return_value="test-token",
        ),
        patch(
            "bot.handlers.log.BotApiClient.create_manual_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ) as mock_create,
    ):
        await log_handler(update, context)

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args
    _, session_data = call_kwargs[0]  # positional: (token, data)
    assert session_data["project_name"] == "Project Alpha"
    assert session_data["description"] == "Meeting notes"
    assert "started_at" in session_data
    assert "ended_at" in session_data


@pytest.mark.asyncio
async def test_log_handler_no_args():
    """No args — assert usage hint sent."""
    update, context = make_update("/log", args=[])
    await log_handler(update, context)
    reply = update.message.reply_text.await_args[0][0]
    assert "Usage:" in reply


# ---------------------------------------------------------------------------
# /status handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_status_handler_active_session():
    """Mock active session returned — assert session info in reply."""
    update, context = make_update("/status")

    mock_session = {
        "id": "sess-1",
        "project_name": "My Project",
        "started_at": "2026-03-22T09:00:00+00:00",
    }

    with (
        patch(
            "bot.handlers.status.BotApiClient.authenticate",
            new_callable=AsyncMock,
            return_value="test-token",
        ),
        patch(
            "bot.handlers.status.BotApiClient.get_active_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
    ):
        await status_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "My Project" in reply
    assert "Active session" in reply


@pytest.mark.asyncio
async def test_status_handler_no_session():
    """Mock no active session — assert 'No active session' reply."""
    update, context = make_update("/status")

    with (
        patch(
            "bot.handlers.status.BotApiClient.authenticate",
            new_callable=AsyncMock,
            return_value="test-token",
        ),
        patch(
            "bot.handlers.status.BotApiClient.get_active_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        await status_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "No active session" in reply


# ---------------------------------------------------------------------------
# /stop handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_handler_success():
    """Mock stop session — assert duration shown."""
    update, context = make_update("/stop")

    mock_session = {
        "id": "sess-1",
        "project_name": "My Project",
        "started_at": "2026-03-22T09:00:00+00:00",
        "ended_at": "2026-03-22T10:30:00+00:00",
    }

    with (
        patch(
            "bot.handlers.stop.BotApiClient.authenticate",
            new_callable=AsyncMock,
            return_value="test-token",
        ),
        patch(
            "bot.handlers.stop.BotApiClient.stop_session",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
    ):
        await stop_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "Session stopped" in reply
    assert "1h 30m" in reply


# ---------------------------------------------------------------------------
# Unlinked user rejection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unlinked_user_rejected():
    """Any command from unlinked user should receive /link prompt."""
    update, context = make_update("/status")

    with patch(
        "bot.handlers.status.BotApiClient.authenticate",
        new_callable=AsyncMock,
        side_effect=UnlinkedUserError("not linked"),
    ):
        await status_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "/link" in reply


@pytest.mark.asyncio
async def test_unlinked_user_rejected_log():
    """Unlinked user using /log should receive /link prompt."""
    update, context = make_update(
        "/log", args=["2.5", "Project Alpha", "Meeting", "notes"]
    )

    with patch(
        "bot.handlers.log.BotApiClient.authenticate",
        new_callable=AsyncMock,
        side_effect=UnlinkedUserError("not linked"),
    ):
        await log_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "/link" in reply


@pytest.mark.asyncio
async def test_unlinked_user_rejected_report():
    """Unlinked user using /report should receive /link prompt."""
    update, context = make_update("/report")

    with patch(
        "bot.handlers.report.BotApiClient.authenticate",
        new_callable=AsyncMock,
        side_effect=UnlinkedUserError("not linked"),
    ):
        await report_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "/link" in reply


@pytest.mark.asyncio
async def test_unlinked_user_rejected_stop():
    """Unlinked user using /stop should receive /link prompt."""
    update, context = make_update("/stop")

    with patch(
        "bot.handlers.stop.BotApiClient.authenticate",
        new_callable=AsyncMock,
        side_effect=UnlinkedUserError("not linked"),
    ):
        await stop_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "/link" in reply


# ---------------------------------------------------------------------------
# /report handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_report_handler_success():
    """Mock report data — assert formatted summary sent."""
    update, context = make_update("/report")

    mock_report = {
        "total_hours": 32.5,
        "projects": [
            {"name": "Project A", "hours": 15.0},
            {"name": "Project B", "hours": 10.0},
            {"name": "Project C", "hours": 7.5},
        ],
    }

    with (
        patch(
            "bot.handlers.report.BotApiClient.authenticate",
            new_callable=AsyncMock,
            return_value="test-token",
        ),
        patch(
            "bot.handlers.report.BotApiClient.get_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ),
    ):
        await report_handler(update, context)

    reply = update.message.reply_text.await_args[0][0]
    assert "32.5" in reply
    assert "Project A" in reply
