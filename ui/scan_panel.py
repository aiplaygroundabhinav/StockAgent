# =============================================================================
# StockSense Agent — Market Scan Panel
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Renders the watchlist scan results as a sortable table of recommendation
# badges. Selecting a row drills into a full lookup-style card (badge,
# rationale, chart, trace) right below the table.
# =============================================================================

import pandas as pd
import streamlit as st

from ui.lookup_panel import render_lookup_result
from ui.theme import VERDICT_CLASS


def _to_dataframe(scan_results: list) -> pd.DataFrame:
    rows = []
    for r in scan_results:
        if "error" in r:
            rows.append({
                "Ticker": r["ticker"], "Verdict": "Error", "Confidence": 0,
                "Price": None, "Technical": "-", "Fundamentals": "-", "Sentiment": "-", "Risk": "-",
                "Change": "-",
            })
            continue
        rec = r["recommendation"]
        rows.append({
            "Ticker": r["ticker"],
            "Verdict": rec["verdict"],
            "Confidence": rec["confidence"],
            "Price": round(r["market_data"]["latest_price"], 2),
            "Technical": r["market_data"]["signal"],
            "Fundamentals": r["fundamentals"]["signal"],
            "Sentiment": r["news"]["signal"],
            "Risk": r["risk"]["level"],
            "Change": _CHANGE_TEXT.get(r.get("change"), "-"),
        })
    return pd.DataFrame(rows)


_VERDICT_ORDER = {"Strong Buy": 5, "Buy": 4, "Hold": 3, "Sell": 2, "Strong Sell": 1, "Error": 0}

_BUY_VERDICTS = {"Strong Buy", "Buy"}
TOP_PICKS_LIMIT = 3

_CHANGE_TEXT = {
    "upgraded": "▲ Upgraded",
    "downgraded": "▼ Downgraded",
    "unchanged": "— Unchanged",
    "new": "✦ New",
}


def _render_top_picks(scan_results: list):
    """Surfaces the strongest Buy / Strong Buy calls from today's scan,
    ranked by verdict strength then confidence, so the watchlist scan
    answers "what should I look at first" rather than just reporting a
    flat table."""
    candidates = [
        r for r in scan_results
        if "error" not in r and r["recommendation"]["verdict"] in _BUY_VERDICTS
    ]
    candidates.sort(
        key=lambda r: (_VERDICT_ORDER[r["recommendation"]["verdict"]], r["recommendation"]["confidence"]),
        reverse=True,
    )
    top = candidates[:TOP_PICKS_LIMIT]

    st.markdown('<span class="section-label">🏆 Top Picks to Buy — Today\'s Scan</span>', unsafe_allow_html=True)

    if not top:
        best = max(scan_results, key=lambda r: r["recommendation"]["confidence"] if "error" not in r else -1,
                   default=None)
        best_note = (
            f" Best signal today is {best['ticker']} ({best['recommendation']['verdict']})."
            if best and "error" not in best else ""
        )
        st.info(f"No Buy-rated calls in this scan.{best_note} Everything is landing Hold or weaker — "
                f"consider waiting for a clearer setup rather than forcing a trade.")
        return

    cols = st.columns(len(top))
    for i, (col, r) in enumerate(zip(cols, top)):
        verdict = r["recommendation"]["verdict"]
        confidence = r["recommendation"]["confidence"]
        price = r["market_data"]["latest_price"]
        summary = r["recommendation"].get("summary", "")
        cls = VERDICT_CLASS.get(verdict, "verdict-hold")
        with col:
            st.markdown(
                f'<div class="pick-card">'
                f'<div class="pick-rank">#{i + 1} PICK</div>'
                f'<div class="pick-ticker">{r["ticker"]}</div>'
                f'<div class="pick-verdict {cls}">{verdict}</div>'
                f'<div class="pick-confidence">Confidence: <b style="color:#00D4AA;">{confidence}%</b>'
                f' &nbsp;·&nbsp; ${price:.2f}</div>'
                f'<div class="pick-summary">{summary}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.caption("Ranked by verdict strength, then confidence. Not financial advice — for research/education only.")
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)


def render_scan_results(scan_results: list):
    _render_top_picks(scan_results)

    df = _to_dataframe(scan_results)
    df["_order"] = df["Verdict"].map(_VERDICT_ORDER)
    df = df.sort_values("_order", ascending=False).drop(columns="_order")

    st.markdown('<span class="section-label">📊 Watchlist Scan Results</span>', unsafe_allow_html=True)
    event = st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="scan_table",
    )

    selected_rows = event.selection.rows if hasattr(event, "selection") else []
    if selected_rows:
        selected_ticker = df.iloc[selected_rows[0]]["Ticker"]
        matching = next((r for r in scan_results if r.get("ticker") == selected_ticker and "error" not in r), None)
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        if matching:
            st.markdown(f'<span class="section-label">🔍 Drill-in: {selected_ticker}</span>', unsafe_allow_html=True)
            render_lookup_result(matching)
        else:
            st.error(f"No detailed result available for {selected_ticker} (analysis failed).")
    else:
        st.caption("Select a row above to drill into its full recommendation, rationale, and chart.")
