import logging
from typing import Dict

from sqlalchemy.orm import Session
from telegram.ext.messagehandler import MessageHandler
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
from stockM.database import get_user, update_userdb
from stockM.constants import (
    DEFAULT_PORT,
    REPLY_KEYBOARD,
    VERB,
    CHOICE_MAP,
    UPDATED,
    CHOOSING
)

# Add logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
markup = ReplyKeyboardMarkup(REPLY_KEYBOARD, one_time_keyboard=False)


def start(update: Update, context: CallbackContext,
          session: Session) -> None:
    reply_text = "Hi! I am your personal stock slave, Dobby 🤖.\n"

    user_id = update.message.from_user["id"]
    user = get_user(session, user_id)

    if not (user.portfolio or user.watchlist):
        reply_text += (
            "\nIt looks like you're new here! I did not find your stock "
            "portfolio and/or watchlist. Please use the keyboard commands"
            "to assist you in setting up your portfolio and/or watchlist."
        )
    else:
        context.user_data.update(user())
        reply_text += (
            f"\nYour watchlist is: {user.watchlist}"
            f"\nYour portfolio is: {user.portfolio}"
        )

    reply_text += "\n\nHow may I be of service today?"
    update.message.reply_text(reply_text, reply_markup=markup)


def update_user(update: Update, context: CallbackContext,
                session: Session) -> None:
    user_id = update.message.from_user["id"]
    user = get_user(session, user_id)
    context.user_data.update(user())

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

    return UPDATED


def received_information(update: Update, context: CallbackContext,
                         session: Session) -> None:
    text = update.message.text
    category = context.user_data['choice']
    context.user_data[category] = text.lower()
    del context.user_data['choice']

    # Update the database
    user = update.message.from_user["id"]
    user_to_update = get_user(session, user)
    setattr(user_to_update, category, text.lower())
    update_userdb(session, user_to_update)

    update.message.reply_text(
        "Neat! Just so you know, this is what you already told me:\n"
        f"{facts_to_str(context.user_data)}\n"
        "You can tell me more, or change your opinion on "
        "something.",
        reply_markup=markup,
    )

    return CHOOSING


def provide_updates(update: Update, context: CallbackContext,
                    session: Session) -> None:
    user_id = update.message.from_user["id"]
    user = get_user(session, user_id)
    context.user_data.update(user())

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


def done(update: Update, context: CallbackContext) -> None:
    if 'choice' in context.user_data:
        del context.user_data['choice']

    update.message.reply_text(
        f"Thank you for using Stock Bot Slave 😊 ! "
        f"To update or get updates on your portfolio/watchlist again, "
        f"please select /start."
    )
    return ConversationHandler.END


def get_px_change(update: Update, stocks: str = None,
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


def get_default_port(update: Update, portfolio: Dict = None) -> None:
    # Set portfolio
    port = T(portfolio) if portfolio else T(DEFAULT_PORT)

    # Stock level updates
    get_px_change(update, DEFAULT_PORT.keys())

    # Portfolio level updates
    port_change, pctg_port_change, new_port_val = port.get_portfolio_change()
    update.message.reply_text(
        f"Your portfolio of {len(port)} stocks {VERB[int(port_change < 0)]} "
        f"by {port_change:.2f} ({pctg_port_change:.2f}%).\n\n Your "
        f"portfolio value is now {int(new_port_val):n}."
    )


def clear_portfolio(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Your portfolio has been cleared!",
        reply_markup=markup
    )


def facts_to_str(user_data: Dict):
    facts = list()

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])
