"""Unit tests for the Relative Performance agent
(agents/relative_performance_agent.py). fetch_comparison_series is
monkeypatched with synthetic series so no network/cache I/O happens."""

import numpy as np
import pandas as pd

import agents.relative_performance_agent as rpa


def _flat_series(n_days, start_price=100.0, daily_growth=0.0):
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n_days)
    close = start_price * np.cumprod(1 + np.full(n_days, daily_growth))
    return pd.DataFrame({"Close": close}, index=dates)


def test_outperformance_yields_bullish_signal(monkeypatch):
    stock_df = _flat_series(130, daily_growth=0.01)  # strong stock uptrend
    spy_df = _flat_series(130, daily_growth=0.001)    # flat-ish market

    monkeypatch.setattr(rpa, "fetch_comparison_series",
                         lambda ticker, period: (spy_df, False))

    market_data = {"df": stock_df, "period": "6mo"}
    result = rpa.analyze_relative_performance("AAPL", market_data, sector="Unknown")

    assert result["signal"] == "bullish"
    assert "1mo" in result["windows"]
    assert result["windows"]["1mo"]["excess_vs_spy_pct"] > 0


def test_underperformance_yields_bearish_signal(monkeypatch):
    stock_df = _flat_series(130, daily_growth=-0.01)
    spy_df = _flat_series(130, daily_growth=0.001)

    monkeypatch.setattr(rpa, "fetch_comparison_series",
                         lambda ticker, period: (spy_df, False))

    market_data = {"df": stock_df, "period": "6mo"}
    result = rpa.analyze_relative_performance("AAPL", market_data, sector="Unknown")
    assert result["signal"] == "bearish"


def test_insufficient_history_skips_window(monkeypatch):
    stock_df = _flat_series(10, daily_growth=0.01)  # too short for any window
    spy_df = _flat_series(10, daily_growth=0.001)

    monkeypatch.setattr(rpa, "fetch_comparison_series",
                         lambda ticker, period: (spy_df, False))

    market_data = {"df": stock_df, "period": "1mo"}
    result = rpa.analyze_relative_performance("AAPL", market_data, sector="Unknown")
    assert result["windows"] == {}
    assert result["signal"] == "neutral"


def test_sector_etf_lookup_adds_sector_comparison(monkeypatch):
    stock_df = _flat_series(130, daily_growth=0.01)
    spy_df = _flat_series(130, daily_growth=0.001)
    sector_df = _flat_series(130, daily_growth=0.002)

    def _fake_fetch(ticker, period):
        if ticker == "SPY":
            return spy_df, False
        return sector_df, False

    monkeypatch.setattr(rpa, "fetch_comparison_series", _fake_fetch)

    market_data = {"df": stock_df, "period": "6mo"}
    result = rpa.analyze_relative_performance("AAPL", market_data, sector="Technology")
    assert result["sector_etf"] == "XLK"
    assert "sector_return_pct" in result["windows"]["1mo"]
