import os

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.api_client import BotApiClient, UnlinkedUserError

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

LINK_PROMPT = "Please link your account using /link <email>"


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command — show active session info or 'No active session'."""
    chat_id = update.effective_chat.id
    client = BotApiClient(API_BASE_URL)

    try:
        token = await client.authenticate(chat_id)
    except UnlinkedUserError:
        await update.message.reply_text(LINK_PROMPT)
        return

    try:
        session = await client.get_active_session(token)
    except Exception:
        await update.message.reply_text(
            "Failed to retrieve session status. Please try again later."
        )
        return

    if session is None:
        await update.message.reply_text("No active session.")
    else:
        project = session.get("project_name", "Unknown project")
        started_at = session.get("started_at", "Unknown time")
        session_id = session.get("id", "N/A")
        await update.message.reply_text(
            f"Active session:\n"
            f"Project: {project}\n"
            f"Started: {started_at}\n"
            f"Session ID: {session_id}"
        )
