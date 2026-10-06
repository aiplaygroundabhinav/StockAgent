# =============================================================================
# StockSense Agent — Relative Performance Agent
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Phase 1 item 4: compares a stock's own return over 1/3/6/12 months to the
# SPY benchmark and to its GICS sector's SPDR Select Sector ETF, so the
# Recommendation agent can tell "up 8%" apart from "up 8% while the market
# is up 15%". Feeds an optional 5th signal into synthesize_recommendation.
# =============================================================================

import time
from typing import Optional

import pandas as pd

from agents.market_data_agent import fetch_comparison_series, PERIOD_TRADING_DAYS

# GICS sector -> SPDR Select Sector ETF, reused alongside
# fundamentals_agent.SECTOR_AVG_PE's sector naming.
SECTOR_ETF = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Communication Services": "XLC",
    "Real Estate": "XLRE",
    "Basic Materials": "XLB",
}

WINDOWS_TRADING_DAYS = {"1mo": 21, "3mo": 63, "6mo": 126, "12mo": 252}


def _trailing_return_pct(df: pd.DataFrame, trading_days: int) -> Optional[float]:
    """Return % over the last `trading_days` rows of `df`, or None if the
    dataframe doesn't cover that far back."""
    if df is None or df.empty or len(df) <= trading_days:
        return None
    start_price = float(df["Close"].iloc[-(trading_days + 1)])
    end_price = float(df["Close"].iloc[-1])
    if not start_price:
        return None
    return round((end_price - start_price) / start_price * 100, 2)


def analyze_relative_performance(ticker: str, market_data: dict, sector: str = "Unknown") -> dict:
    """Uses the already-fetched `market_data["df"]` (so no extra fetch for
    the stock itself) plus a SPY and sector-ETF comparison series to judge
    relative strength. Windows that don't fit in the available history
    (e.g. asking for 12mo returns off a 6mo lookback) are skipped and
    noted rather than guessed at."""
    start = time.time()
    ticker = ticker.upper().strip()
    stock_df = market_data["df"]
    period = market_data.get("period", "6mo")

    spy_df, spy_is_mock = fetch_comparison_series("SPY", period)
    sector_etf = SECTOR_ETF.get(sector)
    sector_df, sector_is_mock = (None, False)
    if sector_etf and sector_etf != ticker:
        sector_df, sector_is_mock = fetch_comparison_series(sector_etf, period)

    bullets = []
    windows = {}
    beats_spy_count = 0
    evaluated_count = 0

    for label, days in WINDOWS_TRADING_DAYS.items():
        if days > PERIOD_TRADING_DAYS.get(period, 126) * 1.05:
            continue  # lookback window doesn't cover this horizon at all
        stock_ret = _trailing_return_pct(stock_df, days)
        spy_ret = _trailing_return_pct(spy_df, days)
        if stock_ret is None or spy_ret is None:
            continue
        evaluated_count += 1
        excess_vs_spy = round(stock_ret - spy_ret, 2)
        entry = {"stock_return_pct": stock_ret, "spy_return_pct": spy_ret, "excess_vs_spy_pct": excess_vs_spy}

        if sector_df is not None:
            sector_ret = _trailing_return_pct(sector_df, days)
            if sector_ret is not None:
                entry["sector_return_pct"] = sector_ret
                entry["excess_vs_sector_pct"] = round(stock_ret - sector_ret, 2)

        windows[label] = entry
        if excess_vs_spy > 0:
            beats_spy_count += 1
        lean = "outperforming" if excess_vs_spy > 0 else ("underperforming" if excess_vs_spy < 0 else "in line with")
        bullets.append(
            f"{label}: {ticker} {stock_ret:+.1f}% vs SPY {spy_ret:+.1f}% — {lean} the market by "
            f"{abs(excess_vs_spy):.1f}pt."
        )

    if not windows:
        signal = "neutral"
        bullets.append(f"Not enough price history ({period} lookback) to compute relative performance.")
    else:
        beat_ratio = beats_spy_count / evaluated_count
        if beat_ratio >= 0.6:
            signal = "bullish"
        elif beat_ratio <= 0.3:
            signal = "bearish"
        else:
            signal = "neutral"

    latency_ms = round((time.time() - start) * 1000, 1)

    return {
        "ticker": ticker,
        "sector": sector,
        "sector_etf": sector_etf,
        "signal": signal,
        "bullets": bullets,
        "windows": windows,
        "is_mock": spy_is_mock or sector_is_mock,
        "latency_ms": latency_ms,
    }
