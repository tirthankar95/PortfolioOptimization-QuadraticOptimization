"""Collect historical stock prices and compute daily returns."""

from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf


def collect_stock_prices(
    tickers: list[str],
    years: int = 3,
    end: date | str | None = None,
) -> pd.DataFrame:
    """Download adjusted daily closing prices for the last ``years`` years.

    Returns a DataFrame indexed by date with one column per ticker.
    """
    end_ts = pd.Timestamp(end) if end is not None else pd.Timestamp(date.today())
    start_ts = end_ts - pd.DateOffset(years=years)

    raw = yf.download(
        tickers,
        start=start_ts.strftime("%Y-%m-%d"),
        end=end_ts.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )
    if raw.empty:
        raise RuntimeError("yfinance returned no data; check network access and retry")
    prices = raw["Close"][tickers]

    # Tickers with no data at all would otherwise empty every row after dropna.
    no_data = [t for t in tickers if t not in prices.columns or prices[t].isna().all()]
    if no_data:
        raise ValueError(f"No usable price data for: {sorted(no_data)}")

    # Forward-fill market holidays / sporadic gaps, then drop rows still incomplete.
    prices = prices.sort_index().ffill().dropna(how="any")
    if prices.empty:
        raise RuntimeError("No overlapping price history across the requested tickers")
    return prices


def get_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute daily simple returns: r_t = (P_t - P_{t-1}) / P_{t-1}.

    Input and output are DataFrames indexed by date with one column per ticker.
    """
    return prices.pct_change().dropna(how="any")
