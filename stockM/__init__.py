import numpy as np

import yfinance as yf


class Ticker:

    def __init__(self, ticker):
        self.ticker = ticker

    def get_price_change(self, lookback: str = "2d") -> float:
        stock = yf.Ticker(self.ticker)
        hist = stock.history(period=lookback).Close.values.tolist()
        if len(hist) != int(lookback[0]):
            lookback = f"{int(lookback[0])+1}d"
            hist = stock.history(period=lookback).Close.values

        if not hist:
            return f"Couldn't find history for ticker {self.ticker}"
        pct_chng = ((hist[1] - hist[0]) / hist[0]) * 100
        return np.round(pct_chng, 2)
    