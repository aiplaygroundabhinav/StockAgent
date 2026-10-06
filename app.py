# =============================================================================
# StockSense Agent — Streamlit App
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# A multi-agent stock research & recommendation system. An orchestrator
# (LangChain LCEL — RunnableParallel, not LangGraph) fans a ticker out to
# Market Data, Fundamentals, and News/Sentiment specialist chains in
# parallel, then a Risk agent and a Recommendation synthesis chain complete
# the pipeline. Every step is traced for the Agent Trace tab.
#
# Same visual theme as the RAGDEMO / PharmacyAgent training series (dark
# navy / teal / purple, Space Mono + DM Sans).
#
# ⚠️ Not financial advice — for research/education only.
# =============================================================================

import os
import time

import streamlit as st
from dotenv import load_dotenv

from agents.orchestrator import run_stock_analysis, run_market_scan
from agents.news_agent import DEFAULT_RSS_FEEDS
from agents.market_data_agent import VALID_PERIODS
from agents import settings_store, scan_history, accuracy_log, alerts
from ui.theme import inject_css, render_hero, render_footer
from ui.lookup_panel import render_lookup_result
from ui.scan_panel import render_scan_results
from ui.trace_panel import render_trace_tab, push_trace_history
from ui.settings_panel import render_settings_tab
from ui.track_record_panel import render_track_record_tab

load_dotenv()

DEFAULT_WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM"]

st.set_page_config(
    page_title="StockSense Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# =============================================================================
# SESSION STATE
# =============================================================================
# Persisted (non-secret) settings survive app restarts via settings_store's
# SQLite-backed cache; the API key stays env/session-only and is never
# written to disk.
_persisted = settings_store.load_settings()

for key, default in {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": _persisted.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
    "watchlist": _persisted.get("watchlist", list(DEFAULT_WATCHLIST)),
    "rss_urls": _persisted.get("rss_urls", list(DEFAULT_RSS_FEEDS)),
    "risk_tolerance": _persisted.get("risk_tolerance", 50),
    "alert_webhook_url": _persisted.get("alert_webhook_url", ""),
    "lookup_period": "6mo",
    "ticker_input": "AAPL",
    "lookup_result": None,
    "scan_results": None,
    "trace_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

render_hero()

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙ Controls</div>', unsafe_allow_html=True)

    st.markdown('<span class="section-label">🔎 Ticker Lookup</span>', unsafe_allow_html=True)
    ticker_query = st.text_input(
        "Ticker", label_visibility="collapsed", value=st.session_state.ticker_input,
        placeholder="e.g. AAPL", key="ticker_search_box",
    )
    period = st.selectbox(
        "Lookback period", options=list(VALID_PERIODS),
        index=list(VALID_PERIODS).index(st.session_state.lookup_period),
        help="How far back to chart price history + the SPY benchmark overlay.",
        key="lookup_period_select",
    )
    st.session_state.lookup_period = period
    run_lookup = st.button("Analyze ticker", key="run_lookup_btn")

    st.markdown('<hr style="border-color:#253450;margin:1.2rem 0;">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">📊 Market Scan</span>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:12px;color:#6A7A96;">Watchlist: {", ".join(st.session_state.watchlist)}</p>',
        unsafe_allow_html=True,
    )
    run_scan = st.button("Run market scan", key="run_scan_btn")

    st.markdown('<hr style="border-color:#253450;margin:1.2rem 0;">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">📰 News Sources</span>', unsafe_allow_html=True)
    with st.expander("Edit RSS feed URLs", expanded=False):
        rss_text = st.text_area(
            "RSS URLs", label_visibility="collapsed",
            value="\n".join(st.session_state.rss_urls), height=100, key="sidebar_rss_edit",
        )
        new_rss = [u.strip() for u in rss_text.splitlines() if u.strip()]
        if new_rss and new_rss != st.session_state.rss_urls:
            st.session_state.rss_urls = new_rss
            settings_store.save_settings(rss_urls=new_rss)

    st.markdown('<hr style="border-color:#253450;margin:1.2rem 0;">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:12.5px;color:#6A7A96;line-height:1.9;">
        <b style="color:#A8B4CC;font-size:13px;">Pipeline:</b><br>
        🔎 Market Data → 💰 Fundamentals →<br>
        📰 News/Sentiment → ⚠️ Risk →<br>
        🧠 Recommendation synthesis
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# ANALYSIS TRIGGERS
# =============================================================================
if run_lookup and ticker_query.strip():
    st.session_state.ticker_input = ticker_query.strip().upper()
    with st.spinner(f"Running multi-agent analysis for {st.session_state.ticker_input}..."):
        try:
            result = run_stock_analysis(
                st.session_state.ticker_input,
                rss_urls=st.session_state.rss_urls,
                risk_tolerance=st.session_state.risk_tolerance,
                api_key=st.session_state.api_key,
                model=st.session_state.model,
                period=st.session_state.lookup_period,
                include_benchmark=True,
            )
            st.session_state.lookup_result = result
            push_trace_history(result["ticker"], "Stock Lookup", result["trace"])
            accuracy_log.log_verdict(
                result["ticker"], result["recommendation"]["verdict"],
                result["recommendation"]["confidence"], result["market_data"]["latest_price"],
                agent_signals={
                    "technical": result["market_data"]["signal"],
                    "fundamentals": result["fundamentals"]["signal"],
                    "sentiment": result["news"]["signal"],
                    "risk": result["risk"]["signal"],
                },
                data_flags={
                    "market_data": result["market_data"]["is_mock"],
                    "fundamentals": result["fundamentals"]["is_mock"],
                    "news": result["news"].get("is_mock", False) or result["news"].get("is_general_fallback", False),
                },
            )
            st.toast(f"✅ Analysis complete for {result['ticker']} — {result['recommendation']['verdict']}", icon="✅")
        except Exception as exc:
            st.toast(f"❌ Analysis failed: {exc}", icon="❌")
            st.error(f"Analysis failed for {st.session_state.ticker_input}: {exc}")

if run_scan:
    with st.spinner(f"Scanning {len(st.session_state.watchlist)} tickers across all agents..."):
        try:
            results = run_market_scan(
                st.session_state.watchlist,
                rss_urls=st.session_state.rss_urls,
                risk_tolerance=st.session_state.risk_tolerance,
                api_key=st.session_state.api_key,
                model=st.session_state.model,
            )
            alerts_fired = 0
            for r in results:
                if "error" in r:
                    continue
                push_trace_history(r["ticker"], "Market Scan", r["trace"])
                verdict = r["recommendation"]["verdict"]
                confidence = r["recommendation"]["confidence"]
                price = r["market_data"]["latest_price"]

                previous = scan_history.get_previous_verdict(r["ticker"])
                change = scan_history.classify_change(previous, verdict)
                r["change"] = change
                scan_history.record_scan(r["ticker"], verdict, confidence, time.time())

                accuracy_log.log_verdict(
                    r["ticker"], verdict, confidence, price,
                    agent_signals={
                        "technical": r["market_data"]["signal"],
                        "fundamentals": r["fundamentals"]["signal"],
                        "sentiment": r["news"]["signal"],
                        "risk": r["risk"]["signal"],
                    },
                    data_flags={
                        "market_data": r["market_data"]["is_mock"],
                        "fundamentals": r["fundamentals"]["is_mock"],
                        "news": r["news"].get("is_mock", False) or r["news"].get("is_general_fallback", False),
                    },
                )

                if st.session_state.alert_webhook_url and alerts.should_alert(change, verdict):
                    fired = alerts.send_verdict_alert(
                        st.session_state.alert_webhook_url, r["ticker"], verdict, confidence,
                        r["recommendation"].get("summary", ""),
                    )
                    alerts_fired += int(fired)

            st.session_state.scan_results = results
            toast_msg = f"✅ Market scan complete for {len(results)} tickers"
            if alerts_fired:
                toast_msg += f" · {alerts_fired} alert(s) sent"
            st.toast(toast_msg, icon="✅")
        except Exception as exc:
            st.toast(f"❌ Market scan failed: {exc}", icon="❌")
            st.error(f"Market scan failed: {exc}")

# =============================================================================
# TABS
# =============================================================================
tab_lookup, tab_scan, tab_trace, tab_track_record, tab_settings = st.tabs(
    ["🔎 Stock Lookup", "📊 Market Scan", "🧠 Agent Trace", "📒 Track Record", "⚙️ Settings"]
)

with tab_lookup:
    if st.session_state.lookup_result:
        render_lookup_result(st.session_state.lookup_result)
    else:
        st.info("Enter a ticker in the sidebar and click **Analyze ticker** to run the multi-agent pipeline.")

with tab_scan:
    if st.session_state.scan_results:
        render_scan_results(st.session_state.scan_results)
    else:
        st.info("Click **Run market scan** in the sidebar to evaluate your whole watchlist.")

with tab_trace:
    render_trace_tab()

with tab_track_record:
    render_track_record_tab()

with tab_settings:
    render_settings_tab()

render_footer()

