import os

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.api_client import BotApiClient

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /link <email> command.

    Links the user's Telegram account to their ChronoTrack account.
    """
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /link <email>\nExample: /link user@example.com"
        )
        return

    email = context.args[0]
    chat_id = update.effective_chat.id

    client = BotApiClient(API_BASE_URL)
    response = await client.link_account(email, chat_id)

    if response.status_code == 200:
        await update.message.reply_text(
            f"Successfully linked your account ({email})!\n"
            "You can now use all ChronoTrack commands."
        )
    elif response.status_code == 404:
        await update.message.reply_text(
            f"No account found with email: {email}\n"
            "Please check your email address and try again."
        )
    else:
        await update.message.reply_text(
            "Failed to link your account. Please try again later."
        )
