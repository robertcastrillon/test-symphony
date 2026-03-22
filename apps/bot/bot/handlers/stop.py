import os
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.api_client import BotApiClient, UnlinkedUserError

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

LINK_PROMPT = "Please link your account using /link <email>"


def calculate_duration(started_at: str, ended_at: str) -> str:
    """Calculate human-readable duration from ISO datetime strings."""
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
        delta = end - start
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except (ValueError, AttributeError):
        return "unknown duration"


async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stop command — stop the active session and report duration."""
    chat_id = update.effective_chat.id
    client = BotApiClient(API_BASE_URL)

    try:
        token = await client.authenticate(chat_id)
    except UnlinkedUserError:
        await update.message.reply_text(LINK_PROMPT)
        return

    try:
        session = await client.stop_session(token)
    except Exception as exc:
        error_msg = str(exc)
        if "404" in error_msg or "no active session" in error_msg.lower():
            await update.message.reply_text("No active session to stop.")
        else:
            await update.message.reply_text(
                "Failed to stop session. Please try again later."
            )
        return

    started_at = session.get("started_at", "")
    ended_at = session.get("ended_at", "")
    project = session.get("project_name", "Unknown project")
    duration = calculate_duration(started_at, ended_at)

    await update.message.reply_text(
        f"Session stopped!\n" f"Project: {project}\n" f"Duration: {duration}"
    )
