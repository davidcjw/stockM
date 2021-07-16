import os
import ast
from datetime import date

import telegram
from sqlalchemy.orm import sessionmaker

from stockM import Ticker as T
from stockM.database import get_subscribers, db

TOKEN = os.getenv("TOKEN")

Session = sessionmaker(db)
session = Session()

bot = telegram.Bot(token=TOKEN)

today = date.today().strftime("%B %d, %Y")
VERB = ["🔴", "🟢"]


def update_users(event, context):
    subscribers = get_subscribers(session)
    for subscriber in subscribers:
        print(f"Getting info for {subscriber.user_id}")
        summary = f"📈 Here is your market close summary for {today}\n\n" \
                  f"🗂 *Portfolio Updates*:\n"
        # Send out updates for each subscriber
        port, watchlist = subscriber.portfolio, subscriber.watchlist

        # Portfolio updates
        if port:
            port = ast.literal_eval(port)
            for _, stock in enumerate(port):
                pct_chng, hist = T.get_price_change(stock)
                if isinstance(pct_chng, float):
                    summary += (
                        f"\n{VERB[pct_chng > 0]} {stock.upper()}: {hist[-1]} "
                        f"({pct_chng}%)"
                    )
                else:
                    summary += f"\n{pct_chng}"
        else:
            summary += "\nNo updates for your portfolio as no stocks found!"

        # Watchlist updates
        summary += "\n\n🔖 *Watchlist updates*:\n"
        if watchlist:
            watchlist = ast.literal_eval(watchlist)
            for _, stock in enumerate(watchlist):
                pct_chng, hist = T.get_price_change(stock)
                if isinstance(pct_chng, float):
                    summary += (
                        f"\n{VERB[pct_chng > 0]} {stock.upper()}: {hist[-1]} "
                        f"({pct_chng}%)"
                    )
                else:
                    summary += f"\n{pct_chng}"
        else:
            summary += "\nNo updates for your watchlist as no stocks found!"

        try:
            bot.send_message(chat_id=subscriber.user_id, text=summary,
                             parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception:
            print(f"{subscriber.user_id} blocked bot!")
