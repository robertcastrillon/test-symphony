import logging
import os
import sys

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler

from bot.handlers.link import link_handler
from bot.handlers.log import log_handler
from bot.handlers.report import report_handler
from bot.handlers.start import start_handler
from bot.handlers.status import status_handler
from bot.handlers.stop import stop_handler

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.warning("TELEGRAM_TOKEN is not set. Exiting without starting the bot.")
        sys.exit(0)

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("link", link_handler))
    application.add_handler(CommandHandler("log", log_handler))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler("report", report_handler))
    application.add_handler(CommandHandler("stop", stop_handler))

    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    if webhook_url:
        port = int(os.getenv("PORT", "8443"))
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=f"{webhook_url}/{token}",
        )
    else:
        application.run_polling()


if __name__ == "__main__":
    main()
