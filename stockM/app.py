import os
import logging
import locale
from typing import Dict
from pathlib import Path

from telegram.ext.messagehandler import MessageHandler
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from telegram import ParseMode
from telegram import (
    Update,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    Filters
)

from stockM import Ticker as T
from stockM.database import get_user, update_userdb, db

# Set locale & enable logging
locale.setlocale(locale.LC_ALL, '')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Uncomment this if running locally with a .env file,
# otherwise ensure that TOKEN has been exported to $PATH
# env_path = Path(".") / ".env"
# load_dotenv(dotenv_path=env_path, verbose=True)

PORT = int(os.environ.get("PORT", 5000))
TOKEN = os.getenv("TOKEN")
VERB = ["rose", "fell"]

DEFAULT_PORT = {
    "AMZN": 200,
    "BABA": 50
}
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)
CHOICE_MAP = {
    "update stock portfolio": "portfolio",
    "update watchlist": "watchlist"
}
reply_keyboard = [
    ["Update stock portfolio", "Update watchlist"],
    ["Portfolio updates", "Watchlist updates"],
    ["Subscribe/Unsubscribe to daily updates", "Done"]
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
Session = sessionmaker(db)
session = Session()


# Define a few command handlers. These usually take the two arguments update
# and context. Error handlers also receive the raised TelegramError object
# in error.
def get_px_change(update: Update,
                  context: CallbackContext,
                  stocks: str = None,
                  type: str = "command") -> None:
    if type == "command":
        if not stocks:
            stocks = update.message.text.split("/get_px_change")[1].strip()
            stocks = stocks.split()
    elif type == "conversation":
        if not stocks:
            update.message.reply_text("No stocks found!")
            return
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


def get_default_port(update: Update, context: CallbackContext,
                     portfolio: Dict = None) -> None:
    # Set portfolio
    port = T(portfolio) if portfolio else T(DEFAULT_PORT)

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


def start(update: Update, context: CallbackContext) -> None:
    reply_text = "Hi! I am your personal stock slave, Dobby 🤖.\n"

    user_id = update.message.from_user["id"]
    user = get_user(session, user_id)

    if not (user.portfolio or user.watchlist):
        reply_text += (
            "\nYou have not informed me of your stock portfolio and/or "
            f"watchlist."
        )
    else:
        context.user_data.update(user())
        reply_text += (
            f"\nYour watchlist is: {user.watchlist}"
            f"\nYour portfolio is: {user.portfolio}"
        )

    reply_text += "\n\nHow may I be of service today?"
    update.message.reply_text(reply_text, reply_markup=markup)
    return CHOOSING


def done(update: Update, context: CallbackContext) -> None:
    if 'choice' in context.user_data:
        del context.user_data['choice']

    update.message.reply_text(
        f"Thank you for using Stock Bot Slave 😊 ! "
        f"To update or get updates on your portfolio/watchlist again, "
        f"please select /start."
    )
    return ConversationHandler.END


def update_user(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()
    context.user_data['choice'] = CHOICE_MAP[text]
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
    stocks = context.user_data[text.split()[0]]
    get_px_change(update=update, context=context, stocks=stocks,
                  type="conversation")
    update.message.reply_text(
        "What would you like to do next?",
        reply_markup=markup
    )

    return CHOOSING


def received_information(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    category = context.user_data['choice']
    context.user_data[category] = text.lower()
    del context.user_data['choice']

    # Update the database
    user_id = update.message.from_user["id"]
    user = get_user(session, user_id)
    setattr(user, category, text.lower())
    update_userdb(session, user)

    update.message.reply_text(
        "Neat! Just so you know, this is what you already told me:\n"
        f"{facts_to_str(context.user_data)}\n"
        "You can tell me more, or change your opinion on "
        "something.",
        reply_markup=markup,
    )

    return CHOOSING


def toggle_subscription(update: Update, context: CallbackContext) -> None:
    # Get user & subscription status
    user_id = update.message.from_user["id"]
    user = get_user(session, user_id)
    filler = "" if user.is_subscribed else " not"
    toggle = "off" if user.is_subscribed else "on"
    db_update = False if user.is_subscribed else True

    # Update is_subscribed status in DB
    try:
        setattr(user, "is_subscribed", db_update)
        update_userdb(session, user)

        update.message.reply_text(
            f"📲 *What are daily updates?*\n"
            f"Daily updates are push notifications informing you of end of "
            f"day price changes to your portfolio/watchlist stocks. They are "
            f"sent out daily at 8 PM UTC and 9 AM UTC. These times correspond"
            f" to US and Singapore market closing times.\n\n"
            f"Looks like you are{filler} subscribed to daily "
            f"portfolio/watchlist updates. Toggling subscription status "
            f"{toggle}.",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(e)
        update.message.reply_text("Failed to update your subscription status.")


def main() -> None:
    updater = Updater(TOKEN, use_context=True)

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
                        '^(Portfolio updates|Watchlist updates)$'
                        ),
                    provide_updates
                ),
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
        allow_reentry=True,
    )

    # on different commands - answer in Telegram
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(MessageHandler(
        Filters.regex(
            '^Subscribe/Unsubscribe to daily updates$'
        ), toggle_subscription
    ))
    dispatcher.add_handler(CommandHandler("get_px_change", get_px_change))
    dispatcher.add_handler(CommandHandler("default", get_default_port))

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
