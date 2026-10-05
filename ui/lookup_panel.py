# =============================================================================
# StockSense Agent — Stock Lookup Panel
# Author : Abhinav Rawat · AI Architect · AI Playground
# =============================================================================

import plotly.graph_objects as go
import streamlit as st

from ui.theme import render_verdict_badge, signal_badge, mock_badge
from ui.trace_panel import render_trace_timeline


def _build_chart(result: dict):
    df = result["market_data"]["df"]
    ticker = result["ticker"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(color="#00D4AA", width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA 20", line=dict(color="#8B7FFF", width=1.2)))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50", line=dict(color="#F5A623", width=1.2)))
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA12"], name="EMA 12", line=dict(color="#4ADE80", width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], name="BB Upper", line=dict(color="#6A7A96", width=1, dash="dash")))
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], name="BB Lower", line=dict(color="#6A7A96", width=1, dash="dash"),
                              fill="tonexty", fillcolor="rgba(106,122,150,0.08)"))

    fig.update_layout(
        title=f"{ticker} — Price with SMA/EMA/Bollinger Bands",
        template="plotly_dark",
        paper_bgcolor="#131C2E", plot_bgcolor="#131C2E",
        font=dict(family="DM Sans, sans-serif", color="#F0F2FF"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=10),
        height=440,
    )
    return fig


def _rationale_section(title: str, text: str, mock: bool = False):
    badge = mock_badge() if mock else ""
    st.markdown(
        f'<div class="rationale-card"><h4>{title} {badge}</h4>{text}</div>',
        unsafe_allow_html=True,
    )


def render_lookup_result(result: dict):
    rec = result["recommendation"]
    md, fd, news, risk = result["market_data"], result["fundamentals"], result["news"], result["risk"]

    col1, col2 = st.columns([1, 2])
    with col1:
        render_verdict_badge(rec["verdict"], rec["confidence"])
    with col2:
        badges_html = " ".join([
            signal_badge("Technical", md["signal"]),
            signal_badge("Fundamentals", fd["signal"]),
            signal_badge("Sentiment", news["signal"]),
            signal_badge("Risk", risk["signal"]),
        ])
        st.markdown(f'<div style="margin-top:8px;">{badges_html}</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#A8B4CC;margin-top:12px;">{rec["summary"]}</p>', unsafe_allow_html=True)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">Rationale Breakdown</span>', unsafe_allow_html=True)
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        _rationale_section("📈 Technical Signals", rec["rationale"]["technical"], mock=md["is_mock"])
        _rationale_section("📰 News / Sentiment", rec["rationale"]["sentiment"])
    with rcol2:
        _rationale_section("💰 Fundamentals", rec["rationale"]["fundamentals"], mock=fd["is_mock"])
        _rationale_section("⚠️ Risk Flags", rec["rationale"]["risk"])

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown('<span class="section-label">Price Chart</span>', unsafe_allow_html=True)
    st.plotly_chart(_build_chart(result), width="stretch", key=f"chart_{result['ticker']}")

    with st.expander("🔍 View agent trace"):
        render_trace_timeline(result["trace"])
