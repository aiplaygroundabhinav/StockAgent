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
        title=f"{ticker} — Price with SMA/EMA/Bollinger Bands ({result['market_data'].get('period', '6mo')})",
        template="plotly_dark",
        paper_bgcolor="#131C2E", plot_bgcolor="#131C2E",
        font=dict(family="DM Sans, sans-serif", color="#F0F2FF"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=10),
        height=440,
    )
    return fig


def _build_benchmark_chart(result: dict):
    """Normalizes both the ticker and SPY to 100 at the start of the window
    so "am I beating the market" is a direct visual read regardless of
    each instrument's absolute price."""
    benchmark = result["market_data"].get("benchmark")
    if not benchmark or benchmark.get("df") is None or benchmark["df"].empty:
        return None

    stock_df = result["market_data"]["df"]
    bench_df = benchmark["df"]
    ticker = result["ticker"]

    stock_norm = stock_df["Close"] / stock_df["Close"].iloc[0] * 100
    bench_norm = bench_df["Close"] / bench_df["Close"].iloc[0] * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock_norm.index, y=stock_norm, name=ticker, line=dict(color="#00D4AA", width=2)))
    fig.add_trace(go.Scatter(x=bench_norm.index, y=bench_norm, name=benchmark["ticker"],
                              line=dict(color="#8B7FFF", width=1.8, dash="dot")))

    fig.update_layout(
        title=f"{ticker} vs {benchmark['ticker']} — normalized to 100",
        template="plotly_dark",
        paper_bgcolor="#131C2E", plot_bgcolor="#131C2E",
        font=dict(family="DM Sans, sans-serif", color="#F0F2FF"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=10),
        height=300,
    )
    return fig


def _rationale_section(title: str, text: str, mock: bool = False):
    badge = mock_badge() if mock else ""
    st.markdown(
        f'<div class="rationale-card"><h4>{title} {badge}</h4>{text}</div>',
        unsafe_allow_html=True,
    )


def _render_data_freshness(result: dict):
    """Phase 1 item 3: per-source "data as of" timestamps so a user can
    see how fresh (or stale) each agent's inputs were at call time."""
    import datetime

    sources = [
        ("Market Data", result["market_data"].get("fetched_at")),
        ("Fundamentals", result["fundamentals"].get("fetched_at")),
        ("News/Sentiment", result["news"].get("fetched_at")),
    ]
    parts = []
    for label, ts in sources:
        if ts:
            stamp = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            parts.append(f"{label}: {stamp}")
    if parts:
        st.markdown(
            f'<p style="font-size:11.5px;color:#6A7A96;margin-top:6px;">Data as of — {" · ".join(parts)}</p>',
            unsafe_allow_html=True,
        )
    disagreement = result["market_data"].get("source_disagreement")
    if disagreement and disagreement.get("flag"):
        st.warning(
            f"⚠️ Source disagreement: yfinance ${result['market_data']['latest_price']:.2f} vs "
            f"{disagreement['fallback_source']} ${disagreement['fallback_price']:.2f} "
            f"({disagreement['disagreement_pct']:+.1f}%)."
        )


_ANALYST_LEAN = {
    "strong_buy": "bullish", "buy": "bullish",
    "hold": "neutral", "none": "neutral",
    "sell": "bearish", "strong_sell": "bearish",
}


def _analyst_consensus_badge(fd: dict) -> str:
    metrics = fd.get("metrics", {})
    rating = (metrics.get("analyst_rating") or "").lower()
    lean = _ANALYST_LEAN.get(rating)
    if not lean:
        return ""
    verdict_lean = {"bullish": "bullish", "neutral": "neutral", "bearish": "bearish"}.get(fd["signal"])
    agree = "✅ agrees" if lean == verdict_lean else "⚠️ differs from"
    label = rating.replace("_", " ").title()
    target = metrics.get("analyst_target_price")
    target_note = f" · target ${target:.2f}" if target else ""
    return (
        f'<div style="margin-top:6px;font-size:12.5px;color:#A8B4CC;">'
        f"Analyst consensus: <b>{label}</b>{target_note} — {agree} with our Fundamentals signal."
        f"</div>"
    )


def render_lookup_result(result: dict):
    rec = result["recommendation"]
    md, fd, news, risk = result["market_data"], result["fundamentals"], result["news"], result["risk"]
    rel_perf = result.get("relative_performance")

    if rec.get("data_quality") == "unreliable":
        st.warning(
            "⚠️ Mock/stale data was used for one or more agents on this call — confidence has been capped "
            f"and the verdict forced to Hold ({', '.join(rec.get('mock_sources', []))})."
        )

    col1, col2 = st.columns([1, 2])
    with col1:
        render_verdict_badge(rec["verdict"], rec["confidence"], label=rec.get("verdict_label"))
    with col2:
        badges = [
            signal_badge("Technical", md["signal"]),
            signal_badge("Fundamentals", fd["signal"]),
            signal_badge("Sentiment", news["signal"]),
            signal_badge("Risk", risk["signal"]),
        ]
        if rel_perf:
            badges.append(signal_badge("vs SPY/Sector", rel_perf["signal"]))
        st.markdown(f'<div style="margin-top:8px;">{" ".join(badges)}</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#A8B4CC;margin-top:12px;">{rec["summary"]}</p>', unsafe_allow_html=True)
        consensus_html = _analyst_consensus_badge(fd)
        if consensus_html:
            st.markdown(consensus_html, unsafe_allow_html=True)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown('<span class="section-label">Rationale Breakdown</span>', unsafe_allow_html=True)
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        _rationale_section("📈 Technical Signals", rec["rationale"]["technical"], mock=md["is_mock"])
        _rationale_section("📰 News / Sentiment", rec["rationale"]["sentiment"])
    with rcol2:
        _rationale_section("💰 Fundamentals", rec["rationale"]["fundamentals"], mock=fd["is_mock"])
        _rationale_section("⚠️ Risk Flags", rec["rationale"]["risk"])

    if rel_perf and rel_perf.get("bullets"):
        _rationale_section("📐 Relative Performance vs SPY/Sector", " ".join(rel_perf["bullets"]), mock=rel_perf.get("is_mock", False))

    _render_data_freshness(result)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown('<span class="section-label">Price Chart</span>', unsafe_allow_html=True)
    st.plotly_chart(_build_chart(result), width="stretch", key=f"chart_{result['ticker']}")

    benchmark_fig = _build_benchmark_chart(result)
    if benchmark_fig is not None:
        st.plotly_chart(benchmark_fig, width="stretch", key=f"bench_chart_{result['ticker']}")

    with st.expander("🔍 View agent trace"):
        render_trace_timeline(result["trace"])
