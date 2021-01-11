import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from omegaconf import OmegaConf as oc
from telegram import (
    InlineQueryResultArticle,
    ParseMode,
    InputTextMessageContent,
    Update
)
from telegram.ext import (
    Updater,
    InlineQueryHandler,
    CommandHandler,
    CallbackContext
)
from telegram.utils.helpers import escape_markdown

from stockM import Ticker as T

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Uncomment this if running locally with a .env file,
# otherwise ensure that TOKEN has been exported to $PATH
# env_path = Path(".") / ".env"
# load_dotenv(dotenv_path=env_path, verbose=True)

PORT = int(os.environ.get("PORT", 5000))
TOKEN = os.getenv("TOKEN")
DEFAULT_PORT = oc.load("config.yml")["DEFAULT_PORT"]
VERB = ["rose", "fell"]
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update
# and context. Error handlers also receive the raised TelegramError object
# in error.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        "Hi! Welcome to Stock Updates Slave. "
        "To start using, use the `/` commands to explore the list of build "
        "in commands.",
    )


def get_px_change(update: Update,
                  context: CallbackContext,
                  stocks: str = None) -> None:
    if not stocks:
        stocks = update.message.text.split("/get_px_change")[1].strip()
        stocks = stocks.split()

    for _, stock in enumerate(stocks):
        pct_chng, hist = T.get_price_change(stock)
        if isinstance(pct_chng, float):
            update.message.reply_text(
                f"{stock.upper()} closed at {hist[-1]} ({pct_chng}%)"
            )
        else:
            logger.error(f"No history found for {stock}")
            update.message.reply_text(f"{pct_chng}")


def get_default_port(update: Update, context: CallbackContext) -> None:
    port = T(DEFAULT_PORT)

    # Stock level updates
    get_px_change(update, context, DEFAULT_PORT)

    # Portfolio level updates
    port_change, pctg_port_change, new_port_val = port.get_portfolio_change()
    update.message.reply_text(
        f"Your portfolio of {len(port)} stocks {VERB[int(port_change < 0)]} "
        f"by {port_change} ({pctg_port_change}%).\n\n Your portfolio value "
        f"is now {new_port_val}."
    )


def main() -> None:
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("get_px_change", get_px_change))
    dispatcher.add_handler(CommandHandler("default", get_default_port))
    # dispatcher.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    # `start_polling` for local dev; webhook for production
    # updater.start_polling()
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://telegram-stockm.herokuapp.com/" + TOKEN)

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
