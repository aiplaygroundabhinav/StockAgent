# =============================================================================
# StockSense Agent — Track Record Panel
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Phase 1 item 2: renders the backtested accuracy of every verdict this app
# has ever logged — hit rate by verdict type and confidence band, average
# excess return vs SPY, at 1/3/6-month horizons. Buckets under
# backtest_engine.MIN_SAMPLE_SIZE show "insufficient data" instead of a
# misleadingly precise percentage.
# =============================================================================

import streamlit as st

from agents import backtest_engine
from agents.market_data_agent import analyze_market_data, fetch_comparison_series

_HISTORY_PERIOD = "2y"  # long enough to judge even the oldest 6mo-ago verdicts


def _stock_history_lookup(ticker: str):
    return analyze_market_data(ticker, period=_HISTORY_PERIOD)["df"]


def _spy_history_lookup(ticker: str):
    df, _ = fetch_comparison_series(ticker, period=_HISTORY_PERIOD)
    return df


def _metric_row(label: str, stats: dict):
    cols = st.columns(3)
    cols[0].metric(f"{label} — sample size", stats["n"])
    hit_rate = stats.get("hit_rate_pct")
    cols[1].metric(f"{label} — hit rate", f"{hit_rate}%" if hit_rate is not None else "—")
    excess = stats.get("avg_excess_return_vs_spy_pct")
    cols[2].metric(f"{label} — avg excess return vs SPY", f"{excess:+.1f}%" if excess is not None else "—")
    if stats["insufficient_data"]:
        st.caption(f"⚠️ Insufficient data (n={stats['n']} < {backtest_engine.MIN_SAMPLE_SIZE}) — treat this figure as directional only, not reliable.")


def _breakdown_table(title: str, buckets: dict):
    if not buckets:
        st.caption(f"No evaluable verdicts yet for {title.lower()}.")
        return
    st.markdown(f"**{title}**")
    for key, stats in buckets.items():
        flag = " ⚠️ *insufficient data*" if stats["insufficient_data"] else ""
        excess = stats["avg_excess_return_vs_spy_pct"]
        st.markdown(
            f"- **{key}**: {stats['hit_rate_pct']}% hit rate, {excess:+.1f}% avg excess vs SPY "
            f"(n={stats['n']}){flag}"
        )


def render_track_record_tab():
    st.markdown('<span class="section-label">📒 Track Record — Backtested Accuracy</span>', unsafe_allow_html=True)
    st.caption(
        "Every verdict this app has issued, graded against what actually happened — not financial advice, "
        "for research/education only."
    )

    with st.spinner("Computing forward returns vs SPY..."):
        try:
            record = backtest_engine.get_track_record(_stock_history_lookup, _spy_history_lookup)
        except Exception as exc:
            st.error(f"Could not compute track record: {exc}")
            return

    if record["total_logged"] == 0:
        st.info("No verdicts logged yet. Run a Stock Lookup or Market Scan to start building a track record.")
        return

    st.caption(f"{record['total_logged']} verdict(s) logged in total. A verdict only counts toward a horizon once that much time has actually elapsed.")

    horizon_tabs = st.tabs(["1 Month", "3 Months", "6 Months"])
    for tab, horizon_label in zip(horizon_tabs, ["1mo", "3mo", "6mo"]):
        with tab:
            h = record["horizons"][horizon_label]
            if h["evaluable"] == 0:
                st.info(f"No verdicts are old enough yet to judge at the {horizon_label} horizon.")
                continue
            _metric_row("Overall", h["overall"])
            st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                _breakdown_table("By verdict type", h["by_verdict"])
            with col2:
                _breakdown_table("By confidence band", h["by_confidence_band"])
