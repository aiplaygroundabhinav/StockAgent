# =============================================================================
# StockSense Agent — Backtest Engine (Track Record)
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Phase 1 item 2: for every verdict logged by agents.accuracy_log, computes
# forward returns at 1/3/6 months and compares them to SPY over the same
# window, then buckets hit rate by verdict type and by confidence band.
# Small sample sizes are flagged as "insufficient data" (n < MIN_SAMPLE_SIZE)
# rather than shown as a misleadingly precise percentage.
#
# `price_history_lookup` is injected (like accuracy_log's `price_lookup`) so
# this module never imports yfinance directly and stays trivially testable
# with synthetic price series.
# =============================================================================

import time
from typing import Callable, Optional

import pandas as pd

from agents import accuracy_log

HORIZON_DAYS = {"1mo": 30, "3mo": 91, "6mo": 182}
MIN_SAMPLE_SIZE = 20
CONFIDENCE_BANDS = [(0, 50, "0-50%"), (50, 70, "50-70%"), (70, 85, "70-85%"), (85, 101, "85-100%")]

PriceHistoryLookup = Callable[[str], Optional[pd.DataFrame]]


def _confidence_band(confidence: int) -> str:
    for low, high, label in CONFIDENCE_BANDS:
        if low <= confidence < high:
            return label
    return CONFIDENCE_BANDS[-1][2]


def _price_at_or_after(df: pd.DataFrame, target_ts: float) -> Optional[float]:
    """Finds the first close on/after `target_ts` (unix seconds) in `df`,
    which must be indexed by datetime. Returns None if `df` doesn't reach
    that far forward yet (the horizon hasn't elapsed in the data)."""
    if df is None or df.empty:
        return None
    target = pd.Timestamp.fromtimestamp(target_ts)
    on_or_after = df[df.index >= target]
    if on_or_after.empty:
        return None
    return float(on_or_after["Close"].iloc[0])


def _forward_return(entry: dict, horizon_days: int, price_history_lookup: PriceHistoryLookup,
                     spy_history_lookup: PriceHistoryLookup) -> Optional[dict]:
    logged_at = entry["logged_at"]
    target_ts = logged_at + horizon_days * 86400
    if time.time() < target_ts:
        return None  # horizon hasn't elapsed yet

    try:
        stock_df = price_history_lookup(entry["ticker"])
        spy_df = spy_history_lookup("SPY")
    except Exception:
        return None

    future_price = _price_at_or_after(stock_df, target_ts)
    future_spy_price = _price_at_or_after(spy_df, target_ts)
    entry_spy_price = _price_at_or_after(spy_df, logged_at)
    if future_price is None or future_spy_price is None or entry_spy_price is None:
        return None
    if not entry["price_at_call"] or not entry_spy_price:
        return None

    stock_return_pct = (future_price - entry["price_at_call"]) / entry["price_at_call"] * 100
    spy_return_pct = (future_spy_price - entry_spy_price) / entry_spy_price * 100
    return {
        "stock_return_pct": round(stock_return_pct, 2),
        "spy_return_pct": round(spy_return_pct, 2),
        "excess_return_pct": round(stock_return_pct - spy_return_pct, 2),
        "hit": accuracy_log._judge(entry["verdict"], stock_return_pct),
    }


def _summarize(rows: list, key: str) -> dict:
    """Groups `rows` (each with a `hit` bool and `excess_return_pct`) by
    `key` and returns per-bucket hit rate / avg excess return, with an
    `insufficient_data` flag for buckets under MIN_SAMPLE_SIZE."""
    buckets: dict = {}
    for r in rows:
        buckets.setdefault(r[key], []).append(r)

    out = {}
    for bucket_key, bucket_rows in buckets.items():
        n = len(bucket_rows)
        out[bucket_key] = {
            "n": n,
            "insufficient_data": n < MIN_SAMPLE_SIZE,
            "hit_rate_pct": round(100 * sum(r["hit"] for r in bucket_rows) / n, 1),
            "avg_excess_return_vs_spy_pct": round(sum(r["excess_return_pct"] for r in bucket_rows) / n, 2),
        }
    return out


def get_track_record(price_history_lookup: PriceHistoryLookup, spy_history_lookup: PriceHistoryLookup,
                      min_sample_size: int = MIN_SAMPLE_SIZE) -> dict:
    """Returns, for each horizon (1mo/3mo/6mo), a breakdown by verdict type
    and by confidence band of hit rate and average excess return vs SPY,
    plus overall sample sizes. Verdicts too recent to judge at a given
    horizon are simply excluded from that horizon's rows (not an error)."""
    entries = accuracy_log.get_entries()
    result = {"total_logged": len(entries), "min_sample_size": min_sample_size, "horizons": {}}

    for horizon_label, days in HORIZON_DAYS.items():
        rows = []
        for entry in entries:
            fwd = _forward_return(entry, days, price_history_lookup, spy_history_lookup)
            if fwd is None:
                continue
            rows.append({
                **entry,
                **fwd,
                "confidence_band": _confidence_band(entry["confidence"]),
            })

        result["horizons"][horizon_label] = {
            "evaluable": len(rows),
            "by_verdict": _summarize(rows, "verdict"),
            "by_confidence_band": _summarize(rows, "confidence_band"),
            "overall": (
                {
                    "n": len(rows),
                    "insufficient_data": len(rows) < min_sample_size,
                    "hit_rate_pct": round(100 * sum(r["hit"] for r in rows) / len(rows), 1),
                    "avg_excess_return_vs_spy_pct": round(sum(r["excess_return_pct"] for r in rows) / len(rows), 2),
                }
                if rows else {"n": 0, "insufficient_data": True, "hit_rate_pct": None,
                               "avg_excess_return_vs_spy_pct": None}
            ),
        }

    return result
