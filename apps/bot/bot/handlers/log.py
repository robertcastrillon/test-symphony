import os
import shlex
from datetime import UTC, datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.api_client import BotApiClient, UnlinkedUserError

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

LINK_PROMPT = "Please link your account using /link <email>"


def parse_log_args(args: list[str]) -> tuple[float, str, str] | None:
    """Parse /log arguments: <hours> <project_name> <description>.

    Project name may be quoted (e.g. 'Project Alpha').
    Returns (hours, project_name, description) or None on parse error.
    """
    if not args:
        return None
    try:
        raw = " ".join(args)
        # Use shlex to handle quoted project names
        tokens = shlex.split(raw)
        if len(tokens) < 3:
            return None
        hours = float(tokens[0])
        project_name = tokens[1]
        description = " ".join(tokens[2:])
        return hours, project_name, description
    except (ValueError, IndexError):
        return None


async def log_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /log <hours> <project_name> <description> command.

    Creates a manual time entry session.
    """
    parsed = parse_log_args(context.args or [])
    if parsed is None:
        await update.message.reply_text(
            "Usage: /log <hours> <project_name> <description>\n"
            "Example: /log 2.5 'Project Alpha' Meeting notes"
        )
        return

    hours, project_name, description = parsed
    chat_id = update.effective_chat.id
    client = BotApiClient(API_BASE_URL)

    try:
        token = await client.authenticate(chat_id)
    except UnlinkedUserError:
        await update.message.reply_text(LINK_PROMPT)
        return

    now = datetime.now(UTC)
    started_at = now - timedelta(seconds=hours * 3600)

    session_data = {
        "project_name": project_name,
        "description": description,
        "started_at": started_at.isoformat(),
        "ended_at": now.isoformat(),
    }

    try:
        session = await client.create_manual_session(token, session_data)
        await update.message.reply_text(
            f"Logged {hours}h for '{project_name}':\n{description}\n"
            f"Session ID: {session.get('id', 'N/A')}"
        )
    except Exception:
        await update.message.reply_text("Failed to log time. Please try again later.")
