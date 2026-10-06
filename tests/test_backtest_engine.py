"""Unit tests for the backtest engine / Track Record logic
(agents/backtest_engine.py). Uses synthetic price-history dataframes
injected via price_history_lookup/spy_history_lookup, and monkeypatches
accuracy_log.get_entries so no real SQLite cache is touched."""

import time

import numpy as np
import pandas as pd

import agents.accuracy_log as accuracy_log
import agents.backtest_engine as backtest_engine


def _history(n_days, start_price, daily_growth, end_ts):
    """A daily-close dataframe ending at `end_ts` (unix seconds)."""
    end = pd.Timestamp.fromtimestamp(end_ts)
    dates = pd.date_range(end=end, periods=n_days, freq="D")
    close = start_price * np.cumprod(1 + np.full(n_days, daily_growth))
    return pd.DataFrame({"Close": close}, index=dates)


def _make_entry(ticker, verdict, confidence, price_at_call, days_ago):
    return {
        "ticker": ticker,
        "verdict": verdict,
        "confidence": confidence,
        "price_at_call": price_at_call,
        "logged_at": time.time() - days_ago * 86400,
    }


def test_insufficient_sample_flagged_below_min_size(monkeypatch):
    now = time.time()
    entries = [_make_entry("AAPL", "Buy", 80, 100.0, days_ago=40) for _ in range(5)]
    monkeypatch.setattr(accuracy_log, "get_entries", lambda: entries)

    def price_lookup(ticker):
        return _history(100, start_price=100.0, daily_growth=0.002, end_ts=now)

    result = backtest_engine.get_track_record(price_lookup, price_lookup)
    horizon = result["horizons"]["1mo"]
    assert horizon["evaluable"] == 5
    assert horizon["overall"]["insufficient_data"] is True


def test_sufficient_sample_computes_hit_rate(monkeypatch):
    now = time.time()
    entries = [_make_entry("AAPL", "Buy", 80, 100.0, days_ago=40) for _ in range(25)]
    monkeypatch.setattr(accuracy_log, "get_entries", lambda: entries)

    def stock_lookup(ticker):
        return _history(100, start_price=100.0, daily_growth=0.01, end_ts=now)  # strong gain -> Buy hits

    def spy_lookup(ticker):
        return _history(100, start_price=100.0, daily_growth=0.0005, end_ts=now)

    result = backtest_engine.get_track_record(stock_lookup, spy_lookup)
    horizon = result["horizons"]["1mo"]
    assert horizon["overall"]["insufficient_data"] is False
    assert horizon["overall"]["n"] == 25
    assert horizon["overall"]["hit_rate_pct"] == 100.0
    assert horizon["overall"]["avg_excess_return_vs_spy_pct"] > 0


def test_horizon_not_elapsed_excluded(monkeypatch):
    entries = [_make_entry("AAPL", "Buy", 80, 100.0, days_ago=2)]  # logged 2 days ago
    monkeypatch.setattr(accuracy_log, "get_entries", lambda: entries)

    def price_lookup(ticker):
        return _history(10, start_price=100.0, daily_growth=0.0, end_ts=time.time())

    result = backtest_engine.get_track_record(price_lookup, price_lookup)
    assert result["horizons"]["1mo"]["evaluable"] == 0


def test_by_verdict_and_confidence_band_breakdown(monkeypatch):
    now = time.time()
    entries = (
        [_make_entry("AAPL", "Buy", 90, 100.0, days_ago=40) for _ in range(21)]
        + [_make_entry("MSFT", "Sell", 55, 100.0, days_ago=40) for _ in range(21)]
    )
    monkeypatch.setattr(accuracy_log, "get_entries", lambda: entries)

    def stock_lookup(ticker):
        return _history(100, start_price=100.0, daily_growth=0.01, end_ts=now)

    def spy_lookup(ticker):
        return _history(100, start_price=100.0, daily_growth=0.0005, end_ts=now)

    result = backtest_engine.get_track_record(stock_lookup, spy_lookup)
    by_verdict = result["horizons"]["1mo"]["by_verdict"]
    assert by_verdict["Buy"]["n"] == 21
    assert by_verdict["Sell"]["n"] == 21
    assert by_verdict["Buy"]["insufficient_data"] is False

    by_band = result["horizons"]["1mo"]["by_confidence_band"]
    assert by_band["85-100%"]["n"] == 21
    assert by_band["50-70%"]["n"] == 21
