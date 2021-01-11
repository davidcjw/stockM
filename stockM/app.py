import os
import logging
import locale
from pathlib import Path

from telegram.ext.messagehandler import MessageHandler
from dotenv import load_dotenv

from omegaconf import OmegaConf as oc
from telegram import (
    Update,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    PicklePersistence,
    ConversationHandler,
    Filters
)

from stockM import Ticker as T

# Set locale & enable logging
locale.setlocale(locale.LC_ALL, '')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Uncomment this if running locally with a .env file,
# otherwise ensure that TOKEN has been exported to $PATH
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path, verbose=True)

PORT = int(os.environ.get("PORT", 5000))
TOKEN = os.getenv("TOKEN")
DEFAULT_PORT = oc.load("config.yml")["DEFAULT_PORT"]
VERB = ["rose", "fell"]
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update
# and context. Error handlers also receive the raised TelegramError object
# in error.
# def start(update: Update, context: CallbackContext) -> None:
#     """Send a message when the command /start is issued."""
#     update.message.reply_text(
#         "Hi! Welcome to Stock Updates Slave. "
#         "To start using, use the `/` commands to explore the list of build "
#         "in commands.",
#     )


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
        f"by {port_change:.2f} ({pctg_port_change:.2f}%).\n\n Your "
        f"portfolio value is now {int(new_port_val):n}."
    )


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])

reply_keyboard = [
    ["Update stock portfolio", "Update watchlist"],
    ["Portfolio updates", "Watchlist updates"],
    ["Check individual stocks", "Done"]
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)
def start(update: Update, context: CallbackContext) -> None:
    reply_text = "Hi! I am your personal stock slave Dobby.\n\n"
    print(context.user_data)
    if context.user_data:
        reply_text += (
            f"Your stock portfolio is {', '.join(context.user_data.keys())}"
        )
    else:
        reply_text += (
            "You have not informed me of your stock portfolio and/or "
            f"watchlist. What would you like me to do?"
        )
    update.message.reply_text(reply_text, reply_markup=markup)
    return CHOOSING


def done(update: Update, context: CallbackContext) -> None:
    if 'choice' in context.user_data:
        del context.user_data['choice']

    update.message.reply_text(
        "I learned these facts about you:" f"{facts_to_str(context.user_data)}"
    )
    return ConversationHandler.END


def update_user(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()
    context.user_data['choice'] = text
    if context.user_data.get(text):
        reply_text = (
            f'Your {text}, I already know the following about that: '
            f'{context.user_data[text]}'
        )
    else:
        reply_text = (
            f'You want to {text}? Please let me know of your '
            f'portfolio/watchlist in the following format: '
            f'Use ticker(s) only, separated by space. Example:\n\n'
            f'AMZN TSLA BABA'
        )

    update.message.reply_text(reply_text)

    return TYPING_REPLY


def provide_updates(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()
    context.user_data['choice'] = text
    if context.user_data.get(text):
        reply_text = (
            f'Your {text}, I already know the following about that: '
            f'{context.user_data[text]}'
        )
    else:
        reply_text = (
            f'You want to {text}? Please let me know of your '
            f'portfolio/watchlist in the following format: '
            f'Use ticker(s) only, separated by space. Example:\n\n'
            f'AMZN TSLA BABA'
        )

    update.message.reply_text(reply_text)

    return TYPING_REPLY


def custom_choice(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Alright, please send me the category first, ' 'for example "Most impressive skill"'
    )

    return TYPING_CHOICE


def received_information(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    print(context.user_data)
    category = context.user_data['choice']
    context.user_data[category] = text.lower()
    del context.user_data['choice']

    update.message.reply_text(
        "Neat! Just so you know, this is what you already told me:"
        f"{facts_to_str(context.user_data)}"
        "You can tell me more, or change your opinion on "
        "something.",
        reply_markup=markup,
    )

    return CHOOSING



def main() -> None:
    pp = PicklePersistence(filename="conversationbot")
    updater = Updater(TOKEN, persistence=pp, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler to ask for user's stock portfolio/watchlist
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex(
                        '^(Update stock portfolio|Update watchlist)$'
                        ),
                    update_user
                ),
                MessageHandler(
                    Filters.regex(
                        '^Something else...$'
                        ),
                    custom_choice
                ),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    Filters.regex(
                        '^(Portfolio updates|Watchlist updates)$'
                        ),
                    provide_updates
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
        name="get_portfolio",
        persistent=True,
        allow_reentry=True,
    )

    # on different commands - answer in Telegram
    dispatcher.add_handler(conv_handler)
    # dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("get_px_change", get_px_change))
    dispatcher.add_handler(CommandHandler("default", get_default_port))
    # dispatcher.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    # `start_polling` for local dev; webhook for production
    updater.start_polling()
    # updater.start_webhook(listen="0.0.0.0",
    #                       port=int(PORT),
    #                       url_path=TOKEN)
    # updater.bot.setWebhook("https://telegram-stockm.herokuapp.com/" + TOKEN)

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
