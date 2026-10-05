# =============================================================================
# StockSense Agent — Agent Trace Panel
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Renders the ordered agent sequence (Market Data -> Fundamentals ->
# News/Sentiment -> Risk -> Recommendation synthesis) with per-step status,
# latency, and token usage. Used both inline (per-lookup "View agent trace"
# expander) and in the standalone Agent Trace tab, which lets you pick any
# past query from this session's history.
# =============================================================================

import streamlit as st

from agents.callbacks import STATUS_ICON

STATUS_CLASS = {"ok": "step-ok", "mock": "step-mock", "error": "step-error"}


def render_trace_timeline(trace: list):
    if not trace:
        st.markdown('<p style="font-size:12px;color:#6A7A96;">No trace available.</p>', unsafe_allow_html=True)
        return

    total_latency = sum(s["latency_ms"] for s in trace if s.get("latency_ms"))
    total_tokens = sum(s["tokens"] for s in trace if s.get("tokens"))
    st.markdown(
        f'<p style="font-size:12px;color:#6A7A96;">'
        f'{len(trace)} steps · {round(total_latency)}ms total'
        + (f' · ~{total_tokens} tokens' if total_tokens else '')
        + '</p>',
        unsafe_allow_html=True,
    )

    rows = []
    for s in trace:
        icon = STATUS_ICON.get(s["status"], "•")
        cls = STATUS_CLASS.get(s["status"], "step-ok")
        lat = f' · {s["latency_ms"]}ms' if s.get("latency_ms") else ""
        tok = f' · {s["tokens"]} tokens' if s.get("tokens") else ""
        rows.append(
            f'<div class="pipeline-step {cls}">'
            f'<span class="pipeline-label">{icon} {s["step_no"]}. [{s["agent"]}] {s["label"]}</span>'
            f'<div class="pipeline-detail">{s.get("detail", "")}{lat}{tok}</div>'
            f'</div>'
        )
    st.markdown('<div class="pipeline-box">' + "".join(rows) + '</div>', unsafe_allow_html=True)


def render_trace_tab():
    st.markdown('<span class="section-label">🧠 Agent Trace — Query History</span>', unsafe_allow_html=True)

    history = st.session_state.get("trace_history", [])
    if not history:
        st.info("Run a Stock Lookup or Market Scan to see the agent pipeline trace here.")
        return

    options = [f"{i + 1}. {h['ticker']} — {h['kind']} @ {h['timestamp']}" for i, h in enumerate(history)]
    choice = st.selectbox("Select a past query", options=list(reversed(options)), label_visibility="collapsed")
    idx = len(options) - 1 - options[::-1].index(choice) if choice else len(options) - 1
    selected = history[idx]

    st.markdown(
        f'<p style="color:#A8B4CC;">Ticker: <b style="color:#00D4AA;">{selected["ticker"]}</b> · '
        f'Mode: {selected["kind"]} · Ran at {selected["timestamp"]}</p>',
        unsafe_allow_html=True,
    )
    render_trace_timeline(selected["trace"])


def push_trace_history(ticker: str, kind: str, trace: list):
    import datetime
    history = st.session_state.setdefault("trace_history", [])
    history.append({
        "ticker": ticker,
        "kind": kind,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "trace": trace,
    })
    # Keep the most recent 20 queries so session state doesn't grow unbounded.
    st.session_state["trace_history"] = history[-20:]
