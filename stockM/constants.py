# Constants
DEFAULT_PORT = {
    "AMZN": 200,
    "BABA": 50
}
VERB = ["rose", "fell"]
CHOICE_MAP = {
    "update stock portfolio": "portfolio",
    "update watchlist": "watchlist"
}
REPLY_KEYBOARD = [
    ["Update stock portfolio", "Update watchlist"],
    ["Portfolio updates", "Watchlist updates"],
    ["Done"]
]

CHOOSING, UPDATED = range(2)
