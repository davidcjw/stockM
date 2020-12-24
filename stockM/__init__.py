from dataclasses import dataclass
from typing import Optional
import numpy as np

import yfinance as yf


@dataclass
class Ticker:

    portfolio: Optional[str]

    def __len__(self):
        return len(self.portfolio)

    @staticmethod
    def get_price_change(ticker: str, lookback: str = "2d") -> float:
        """Gets price change for a particular ticker

        Args:
            ticker (str): Ticker of interest. E.g., BABA or Y92.SI
            lookback (str, optional): Price change period to evaluate on.
                Defaults to "2d".

        Returns:
            float: Percentage change in float.
        """
        stock = yf.Ticker(ticker)
        hist = stock.history(period=lookback).Close.values.tolist()
        if len(hist) != int(lookback[0]):
            lookback = f"{int(lookback[0])+1}d"
            hist = stock.history(period=lookback).Close.values.tolist()

        if not hist:
            return f"Couldn't find history for ticker {ticker}"
        pct_chng = ((hist[1] - hist[0]) / hist[0]) * 100
        return np.round(pct_chng, 2)
    
    def get_portfolio_change(self) -> int:
        raise NotImplementedError
