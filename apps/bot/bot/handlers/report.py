import os

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.api_client import BotApiClient, UnlinkedUserError

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

LINK_PROMPT = "Please link your account using /link <email>"


def format_report(report: dict) -> str:
    """Format the report data as a readable text summary."""
    total_hours = report.get("total_hours", 0)
    projects = report.get("projects", [])

    lines = [
        "Weekly Report Summary",
        "=" * 20,
        f"Total hours: {total_hours:.1f}h",
        "",
        "Top projects:",
    ]

    if not projects:
        lines.append("  No projects tracked this week.")
    else:
        top_3 = sorted(projects, key=lambda p: p.get("hours", 0), reverse=True)[:3]
        for i, proj in enumerate(top_3, start=1):
            name = proj.get("name", "Unknown")
            hours = proj.get("hours", 0)
            lines.append(f"  {i}. {name}: {hours:.1f}h")

    return "\n".join(lines)


async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /report command — show weekly time summary."""
    chat_id = update.effective_chat.id
    client = BotApiClient(API_BASE_URL)

    try:
        token = await client.authenticate(chat_id)
    except UnlinkedUserError:
        await update.message.reply_text(LINK_PROMPT)
        return

    try:
        report = await client.get_report(token, period="week")
    except Exception:
        await update.message.reply_text(
            "Failed to retrieve report. Please try again later."
        )
        return

    await update.message.reply_text(format_report(report))
