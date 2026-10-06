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
from agents import settings_store, accuracy_log
from agents.market_data_agent import analyze_market_data


def render_settings_tab():
    st.markdown('<span class="section-label">🔑 OpenAI API Key</span>', unsafe_allow_html=True)
    key_input = st.text_input(
        "OpenAI API Key", label_visibility="collapsed", type="password",
        value=st.session_state.api_key, placeholder="sk-proj-...", key="settings_api_key_input",
    )
    if key_input != st.session_state.api_key:
        st.session_state.api_key = key_input
    st.caption(
        "Stored only in this session — never written to disk. Without a key, the News/Sentiment and "
        "Recommendation agents fall back to deterministic rule-based logic instead of LLM reasoning."
    )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">📋 Watchlist</span>', unsafe_allow_html=True)
    watchlist_text = st.text_area(
        "Watchlist", label_visibility="collapsed",
        value=", ".join(st.session_state.watchlist),
        help="Comma-separated tickers used by Market Scan. Saved automatically.",
        key="settings_watchlist_input",
    )
    new_watchlist = [t.strip().upper() for t in watchlist_text.split(",") if t.strip()]
    if new_watchlist and new_watchlist != st.session_state.watchlist:
        st.session_state.watchlist = new_watchlist
        settings_store.save_settings(watchlist=new_watchlist)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">📰 News Source URLs</span>', unsafe_allow_html=True)
    rss_text = st.text_area(
        "RSS URLs", label_visibility="collapsed",
        value="\n".join(st.session_state.rss_urls),
        help="One RSS feed URL per line, fed into the News & Sentiment agent. Saved automatically.",
        height=120,
        key="settings_rss_input",
    )
    new_rss = [u.strip() for u in rss_text.splitlines() if u.strip()]
    if new_rss and new_rss != st.session_state.rss_urls:
        st.session_state.rss_urls = new_rss
        settings_store.save_settings(rss_urls=new_rss)
    if st.button("↺ Reset to default feeds"):
        st.session_state.rss_urls = list(DEFAULT_RSS_FEEDS)
        settings_store.save_settings(rss_urls=list(DEFAULT_RSS_FEEDS))
        st.rerun()

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">⚖️ Risk Tolerance</span>', unsafe_allow_html=True)
    risk_tolerance = st.slider(
        "Risk tolerance", min_value=0, max_value=100, value=st.session_state.risk_tolerance,
        label_visibility="collapsed",
        help="0 = very conservative (flags risk more aggressively), 100 = very aggressive (more tolerant of volatility).",
        key="settings_risk_slider",
    )
    if risk_tolerance != st.session_state.risk_tolerance:
        st.session_state.risk_tolerance = risk_tolerance
        settings_store.save_settings(risk_tolerance=risk_tolerance)
    st.caption(f"Current setting: {risk_tolerance}/100")

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">🔔 Alert Webhook</span>', unsafe_allow_html=True)
    webhook_input = st.text_input(
        "Webhook URL", label_visibility="collapsed",
        value=st.session_state.alert_webhook_url, placeholder="https://hooks.slack.com/services/...",
        key="settings_webhook_input",
    )
    if webhook_input != st.session_state.alert_webhook_url:
        st.session_state.alert_webhook_url = webhook_input
        settings_store.save_settings(alert_webhook_url=webhook_input)
    st.caption(
        "When set, a Market Scan that finds a ticker upgraded into Buy/Strong Buy posts a JSON alert here "
        "(e.g. a Slack/Discord incoming webhook). ⚠️ Scope note: this fires only during a scan you run — "
        "Streamlit has no background scheduler, so this is not true unattended time-based monitoring."
    )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">🎯 Accuracy Track Record</span>', unsafe_allow_html=True)
    _render_accuracy_dashboard()


def _render_accuracy_dashboard():
    summary = accuracy_log.get_accuracy_summary(min_age_days=1.0, price_lookup=_price_lookup)

    if summary["total_logged"] == 0:
        st.info("No verdicts logged yet. Run a Stock Lookup or Market Scan to start building a track record.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Verdicts logged", summary["total_logged"])
    c2.metric("Evaluable (≥1 day old)", summary["evaluable"])
    overall = summary["overall_accuracy_pct"]
    c3.metric("Overall accuracy", f"{overall}%" if overall is not None else "—")

    if summary["pending"]:
        st.caption(f"{summary['pending']} verdict(s) are too recent (<1 day) to judge yet.")

    if summary["by_verdict"]:
        st.markdown("**By verdict bucket**")
        for verdict, stats in summary["by_verdict"].items():
            st.markdown(
                f"- **{verdict}**: {stats['accuracy_pct']}% correct ({stats['count']} calls)"
            )

    if summary["recent"]:
        with st.expander("Recent evaluated calls"):
            for r in summary["recent"]:
                icon = "✅" if r["correct"] else "❌"
                st.markdown(
                    f"{icon} **{r['ticker']}** — {r['verdict']} · "
                    f"${r['price_at_call']:.2f} → ${r['current_price']:.2f} ({r['return_pct']:+.2f}%)"
                )


def _price_lookup(ticker: str) -> float:
    return analyze_market_data(ticker)["latest_price"]
