from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List
import numpy as np

import yfinance as yf

TEST_DICT = {
    "AMZN": 10,
    "MSFT": 100,
    "BABA": 10
}


@dataclass
class Ticker:

    portfolio: Optional[Dict]

    def __post_init__(self):
        if not isinstance(self.portfolio, Dict):
            raise TypeError("portfolio specified should be a dictionary!")

    def __len__(self):
        return len(self.portfolio)

    @staticmethod
    def get_price_change(ticker: str,
                         lookback: str = "2d"
                         ) -> Tuple[float, List]:
        """Gets price change for a particular ticker

        Args:
            ticker (str): Ticker of interest. E.g., BABA or Y92.SI
            lookback (str, optional): Price change period to evaluate on.
                Defaults to "2d".

        Returns:
            Tuple[float, List]: Percentage change in float.
        """
        stock = yf.Ticker(ticker)
        hist = stock.history(period=lookback).Close.values.tolist()
        if len(hist) != int(lookback[0]):
            lookback = f"{int(lookback[0])+1}d"
            hist = stock.history(period=lookback).Close.values.tolist()

        if not hist:
            return f"Couldn't find history for ticker {ticker}", None
        pct_chng = ((hist[-1] - hist[0]) / hist[0]) * 100
        return np.round(pct_chng, 2), np.round(hist, 2)

    @classmethod
    def construct_portfolio(cls, stocks: Dict = TEST_DICT):
        """Class method to init this class. Used mainly for dev
        purposes to construct an artificial portfolio

        Args:
            stocks (Dict, optional): Defaults to TEST_DICT.

        Returns:
            Ticker: instance of this class
        """
        return cls(stocks)

    def get_portfolio_change(self, lookback: str = "2d") -> Tuple[int, float]:
        """Returns portfolio dollar and percentage change based on
        self.portfolio dictionary

        Args:
            lookback (str, optional): Defaults to "2d".

        Returns:
            Tuple[int, float]: dollar and percentage change
        """
        original_port_val, new_port_val = 0, 0
        for ticker, holdings in self.portfolio.items():
            _, hist = self.get_price_change(ticker, lookback=lookback)
            original_port_val += holdings * hist[0]
            new_port_val += holdings * hist[1]

        port_change = new_port_val - original_port_val
        pct_port_change = (port_change / original_port_val) * 100

        return port_change, pct_port_change, new_port_val
