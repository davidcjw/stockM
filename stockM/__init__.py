import numpy as np

import yfinance as yf


def get_price_change(ticker: str, lookback: str = "2d") -> float:
    stock = yf.Ticker(ticker)
    hist = stock.history(period=lookback).Close.values
    pct_chng = ((hist[1] - hist[0]) / hist[0]) * 100
    return np.round(pct_chng, 2)

