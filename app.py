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

import streamlit as st
from dotenv import load_dotenv

from agents.orchestrator import run_stock_analysis, run_market_scan
from agents.news_agent import DEFAULT_RSS_FEEDS
from ui.theme import inject_css, render_hero, render_footer
from ui.lookup_panel import render_lookup_result
from ui.scan_panel import render_scan_results
from ui.trace_panel import render_trace_tab, push_trace_history
from ui.settings_panel import render_settings_tab

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
for key, default in {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "watchlist": list(DEFAULT_WATCHLIST),
    "rss_urls": list(DEFAULT_RSS_FEEDS),
    "risk_tolerance": 50,
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
        if new_rss:
            st.session_state.rss_urls = new_rss

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
            )
            st.session_state.lookup_result = result
            push_trace_history(result["ticker"], "Stock Lookup", result["trace"])
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
            st.session_state.scan_results = results
            for r in results:
                if "error" not in r:
                    push_trace_history(r["ticker"], "Market Scan", r["trace"])
            st.toast(f"✅ Market scan complete for {len(results)} tickers", icon="✅")
        except Exception as exc:
            st.toast(f"❌ Market scan failed: {exc}", icon="❌")
            st.error(f"Market scan failed: {exc}")

# =============================================================================
# TABS
# =============================================================================
tab_lookup, tab_scan, tab_trace, tab_settings = st.tabs(
    ["🔎 Stock Lookup", "📊 Market Scan", "🧠 Agent Trace", "⚙️ Settings"]
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

with tab_settings:
    render_settings_tab()

render_footer()
