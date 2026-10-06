# =============================================================================
# StockSense Agent — Accuracy Log / Track Record
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Logs every verdict issued (ticker, verdict, confidence, price-at-call,
# timestamp) to the shared SQLite cache.db, then lets the Settings tab
# compute a simple directional accuracy dashboard: for calls old enough to
# judge, did the price move the way the verdict implied?
#
# This is intentionally simple (no position sizing, no annualized returns)
# — the goal is just an honest "is this tool calibrated at all" signal,
# which the app had zero of before.
# =============================================================================

import time

from agents.cache import get_cached, set_cached

_NAMESPACE = "accuracy_log"
_KEY = "entries"
_NEVER_EXPIRES = 10 ** 12
_MAX_ENTRIES = 1000

# A verdict is judged "correct" if the price moved at least this many percent
# in the implied direction by evaluation time; Hold is "correct" if price
# stayed within +/- this band.
_HOLD_BAND_PCT = 3.0
_MOVE_THRESHOLD_PCT = 1.0

_BUY_VERDICTS = {"Strong Buy", "Buy"}
_SELL_VERDICTS = {"Strong Sell", "Sell"}


def log_verdict(ticker: str, verdict: str, confidence: int, price: float,
                 agent_signals: dict = None, data_flags: dict = None):
    """`agent_signals` (e.g. {"technical": "bullish", ...}) and `data_flags`
    (e.g. {"market_data": False, "fundamentals": False, "news": True}) are
    optional and additive so existing 4-arg callers keep working; Phase 1
    items 1-2 (verdict log + backtest engine) use them to break accuracy
    down by signal agreement and to exclude/flag mock-data verdicts."""
    entries = get_cached(_NAMESPACE, _KEY, _NEVER_EXPIRES) or []
    entries.append({
        "ticker": ticker.upper(),
        "verdict": verdict,
        "confidence": confidence,
        "price_at_call": price,
        "logged_at": time.time(),
        "agent_signals": agent_signals or {},
        "data_flags": data_flags or {},
    })
    entries = entries[-_MAX_ENTRIES:]  # cap growth
    set_cached(_NAMESPACE, _KEY, entries)


def get_entries() -> list:
    """Raw logged verdicts (most recent `_MAX_ENTRIES`). Used by
    `agents.backtest_engine` to compute forward returns."""
    return get_cached(_NAMESPACE, _KEY, _NEVER_EXPIRES) or []


def _judge(verdict: str, return_pct: float) -> bool:
    if verdict in _BUY_VERDICTS:
        return return_pct >= _MOVE_THRESHOLD_PCT
    if verdict in _SELL_VERDICTS:
        return return_pct <= -_MOVE_THRESHOLD_PCT
    return abs(return_pct) <= _HOLD_BAND_PCT  # Hold


def get_accuracy_summary(min_age_days: float = 1.0, price_lookup=None) -> dict:
    """Evaluates every logged call at least `min_age_days` old against its
    current price (via `price_lookup(ticker) -> float`, typically
    `market_data_agent.analyze_market_data`'s latest_price) and returns an
    overall + per-verdict-bucket accuracy breakdown.

    `price_lookup` is injected so this module never imports yfinance
    directly and stays trivially unit-testable.
    """
    entries = get_cached(_NAMESPACE, _KEY, _NEVER_EXPIRES) or []
    now = time.time()
    min_age_seconds = min_age_days * 86400

    evaluable = [e for e in entries if now - e["logged_at"] >= min_age_seconds]
    pending = len(entries) - len(evaluable)

    if not evaluable or price_lookup is None:
        return {
            "total_logged": len(entries),
            "evaluable": 0,
            "pending": pending,
            "overall_accuracy_pct": None,
            "by_verdict": {},
            "recent": [],
        }

    results = []
    for e in evaluable:
        try:
            current_price = price_lookup(e["ticker"])
        except Exception:
            continue
        if not current_price or not e["price_at_call"]:
            continue
        return_pct = (current_price - e["price_at_call"]) / e["price_at_call"] * 100
        correct = _judge(e["verdict"], return_pct)
        results.append({**e, "current_price": current_price, "return_pct": round(return_pct, 2), "correct": correct})

    if not results:
        return {
            "total_logged": len(entries),
            "evaluable": 0,
            "pending": pending,
            "overall_accuracy_pct": None,
            "by_verdict": {},
            "recent": [],
        }

    overall_pct = round(100 * sum(r["correct"] for r in results) / len(results), 1)

    by_verdict = {}
    for verdict in ("Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"):
        bucket = [r for r in results if r["verdict"] == verdict]
        if bucket:
            by_verdict[verdict] = {
                "count": len(bucket),
                "accuracy_pct": round(100 * sum(r["correct"] for r in bucket) / len(bucket), 1),
            }

    results.sort(key=lambda r: r["logged_at"], reverse=True)

    return {
        "total_logged": len(entries),
        "evaluable": len(results),
        "pending": pending,
        "overall_accuracy_pct": overall_pct,
        "by_verdict": by_verdict,
        "recent": results[:15],
    }
