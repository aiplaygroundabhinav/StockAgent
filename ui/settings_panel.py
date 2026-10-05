# =============================================================================
# StockSense Agent — Settings Panel
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# API key, watchlist editor, RSS source editor, and risk tolerance slider.
# Everything here writes straight into st.session_state so the sidebar and
# other tabs pick up changes immediately.
# =============================================================================

import streamlit as st

from agents.news_agent import DEFAULT_RSS_FEEDS


def render_settings_tab():
    st.markdown('<span class="section-label">🔑 OpenAI API Key</span>', unsafe_allow_html=True)
    key_input = st.text_input(
        "OpenAI API Key", label_visibility="collapsed", type="password",
        value=st.session_state.api_key, placeholder="sk-proj-...", key="settings_api_key_input",
    )
    if key_input != st.session_state.api_key:
        st.session_state.api_key = key_input
    st.caption(
        "Stored only in this session. Without a key, the News/Sentiment and Recommendation agents "
        "fall back to deterministic rule-based logic instead of LLM reasoning."
    )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">📋 Watchlist</span>', unsafe_allow_html=True)
    watchlist_text = st.text_area(
        "Watchlist", label_visibility="collapsed",
        value=", ".join(st.session_state.watchlist),
        help="Comma-separated tickers used by Market Scan.",
        key="settings_watchlist_input",
    )
    new_watchlist = [t.strip().upper() for t in watchlist_text.split(",") if t.strip()]
    if new_watchlist and new_watchlist != st.session_state.watchlist:
        st.session_state.watchlist = new_watchlist

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">📰 News Source URLs</span>', unsafe_allow_html=True)
    rss_text = st.text_area(
        "RSS URLs", label_visibility="collapsed",
        value="\n".join(st.session_state.rss_urls),
        help="One RSS feed URL per line, fed into the News & Sentiment agent.",
        height=120,
        key="settings_rss_input",
    )
    new_rss = [u.strip() for u in rss_text.splitlines() if u.strip()]
    if new_rss and new_rss != st.session_state.rss_urls:
        st.session_state.rss_urls = new_rss
    if st.button("↺ Reset to default feeds"):
        st.session_state.rss_urls = list(DEFAULT_RSS_FEEDS)
        st.rerun()

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">⚖️ Risk Tolerance</span>', unsafe_allow_html=True)
    risk_tolerance = st.slider(
        "Risk tolerance", min_value=0, max_value=100, value=st.session_state.risk_tolerance,
        label_visibility="collapsed",
        help="0 = very conservative (flags risk more aggressively), 100 = very aggressive (more tolerant of volatility).",
        key="settings_risk_slider",
    )
    st.session_state.risk_tolerance = risk_tolerance
    st.caption(f"Current setting: {risk_tolerance}/100")
