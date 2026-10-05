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


def _to_dataframe(scan_results: list) -> pd.DataFrame:
    rows = []
    for r in scan_results:
        if "error" in r:
            rows.append({
                "Ticker": r["ticker"], "Verdict": "Error", "Confidence": 0,
                "Price": None, "Technical": "-", "Fundamentals": "-", "Sentiment": "-", "Risk": "-",
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
        })
    return pd.DataFrame(rows)


_VERDICT_ORDER = {"Strong Buy": 5, "Buy": 4, "Hold": 3, "Sell": 2, "Strong Sell": 1, "Error": 0}


def render_scan_results(scan_results: list):
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
