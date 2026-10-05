# =============================================================================
# StockSense Agent — Trace Capture
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Every specialist agent (Market Data, Fundamentals, News/Sentiment, Risk) and
# the Recommendation synthesis step report through `step()` / `record()` so
# the Agent Trace tab and the per-lookup "🔍 View agent trace" expander can
# render the exact same ordered sequence: what ran, in what order, with what
# latency and (when an LLM was used) token usage. This mirrors the
# PharmacyAgent `agent/callbacks.py` emit() pattern — one function is the
# single source of truth for "what happened".
# =============================================================================

import time
import uuid
from contextlib import contextmanager

STATUS_ICON = {
    "ok": "✅",
    "running": "⏳",
    "error": "⚠️",
    "mock": "🧪",
}


def new_trace():
    """Starts a fresh ordered trace list for one analysis run."""
    return []


def record(trace: list, *, agent: str, label: str, status: str = "ok",
           detail: str = "", latency_ms: float = None, tokens: int = None):
    """Appends one step to the trace. `agent` is the specialist name shown in
    the Agent Trace timeline (Market Data / Fundamentals / News & Sentiment /
    Risk / Recommendation)."""
    entry = {
        "step_no": len(trace) + 1,
        "agent": agent,
        "label": label,
        "status": status,
        "detail": detail,
        "latency_ms": latency_ms,
        "tokens": tokens,
        "time": time.strftime("%H:%M:%S"),
    }
    trace.append(entry)
    return entry


@contextmanager
def timed_step(trace: list, *, agent: str, label: str):
    """Context manager that records one trace step with measured latency.
    Usage::

        with timed_step(trace, agent="Market Data", label="Fetch + indicators") as finish:
            ... do work ...
            finish(detail="bullish", tokens=None)

    On exception, the step is recorded with status="error" and re-raised.
    """
    start = time.time()

    result = {"detail": "", "tokens": None, "status": "ok"}

    def finish(detail: str = "", tokens: int = None, status: str = "ok"):
        result["detail"] = detail
        result["tokens"] = tokens
        result["status"] = status

    try:
        yield finish
    except Exception as exc:  # noqa: BLE001 - we want to trace then re-raise
        latency_ms = round((time.time() - start) * 1000, 1)
        record(trace, agent=agent, label=label, status="error",
               detail=str(exc), latency_ms=latency_ms)
        raise
    else:
        latency_ms = round((time.time() - start) * 1000, 1)
        record(trace, agent=agent, label=label, status=result["status"],
               detail=result["detail"], latency_ms=latency_ms, tokens=result["tokens"])


def new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:8]}"
