from telegram import Update
from telegram.ext import ContextTypes

WELCOME_MESSAGE = """Welcome to ChronoTrack! ⏱

Here are the available commands:

/start — Show this help message
/link <email> — Link your ChronoTrack account
/status — Check your active session
/log <hours> <project> <description> — Log time manually
/report — View your weekly summary
/stop — Stop your active session

To get started, link your account with /link <your@email.com>
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command — send welcome message with command list."""
    await update.message.reply_text(WELCOME_MESSAGE)
