# =============================================================================
# StockSense Agent — Scan History / Change Detection
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Remembers each ticker's verdict from its most recent scan so the next
# Market Scan can flag "upgraded"/"downgraded" tickers instead of just
# reporting a flat snapshot. Backed by the shared SQLite cache.db.
# =============================================================================

from agents.cache import get_cached, set_cached

_NAMESPACE = "scan_history"
_NEVER_EXPIRES = 10 ** 12

_VERDICT_RANK = {"Strong Sell": 1, "Sell": 2, "Hold": 3, "Buy": 4, "Strong Buy": 5}


def get_previous_verdict(ticker: str):
    """Returns the {"verdict":..., "confidence":..., "scanned_at":...} dict
    from the ticker's last recorded scan, or None if it has never been
    scanned before."""
    return get_cached(_NAMESPACE, ticker.upper(), _NEVER_EXPIRES)


def record_scan(ticker: str, verdict: str, confidence: int, scanned_at: float):
    set_cached(_NAMESPACE, ticker.upper(), {
        "verdict": verdict, "confidence": confidence, "scanned_at": scanned_at,
    })


def classify_change(previous: dict, verdict: str) -> str:
    """Returns "upgraded", "downgraded", "unchanged", or "new" by comparing
    the previous scan's verdict rank to the current one."""
    if previous is None:
        return "new"
    prev_rank = _VERDICT_RANK.get(previous.get("verdict"), 3)
    cur_rank = _VERDICT_RANK.get(verdict, 3)
    if cur_rank > prev_rank:
        return "upgraded"
    if cur_rank < prev_rank:
        return "downgraded"
    return "unchanged"
