# =============================================================================
# StockSense Agent — Shared Theme
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Same visual theme family as RAGDEMO / PharmacyAgent (dark navy / teal /
# purple, Space Mono + DM Sans) so this app feels like part of the same
# training series.
# =============================================================================

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap');

:root {
    --bg:      #080C14;
    --surface: #0D1320;
    --card:    #131C2E;
    --border:  #253450;
    --accent:  #00D4AA;
    --purple:  #8B7FFF;
    --amber:   #F5A623;
    --green:   #4ADE80;
    --red:     #FF6B6B;
    --text:    #F0F2FF;
    --sub:     #A8B4CC;
    --muted:   #6A7A96;
    --mono:    'Space Mono', monospace;
    --sans:    'DM Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--sans) !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.stApp { background-color: var(--bg) !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem !important; max-width: 1200px !important; }

section[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1.25rem !important; }

label, .stTextInput label, .stTextArea label, .stRadio label, .stSlider label,
[data-testid="stWidgetLabel"] p {
    color: var(--sub) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    font-family: var(--sans) !important;
    margin-bottom: 6px !important;
}

.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: var(--card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus { border-color: var(--accent) !important; }
input[type="password"] { font-family: var(--mono) !important; letter-spacing: 3px !important; }

.stButton > button {
    background: linear-gradient(135deg, #00D4AA, #8B7FFF) !important;
    color: #080C14 !important;
    font-family: var(--mono) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    width: 100% !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--muted) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--card) !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 0 12px 12px !important;
    padding: 1.25rem !important;
}

.section-label {
    font-family: var(--mono); font-size: 11px; letter-spacing: 2.5px;
    color: var(--accent); text-transform: uppercase;
    margin-bottom: 0.5rem; margin-top: 1rem; display: block;
}
.sidebar-header {
    font-family: var(--mono); font-size: 11px; letter-spacing: 2.5px;
    color: var(--accent); text-transform: uppercase;
    padding-bottom: 10px; border-bottom: 1px solid var(--border); margin-bottom: 1rem;
}
.custom-divider {
    border: none; height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.5rem 0;
}
.hero-title { font-family: var(--mono); font-size: 2.4rem; font-weight: 700; color: var(--accent); margin: 0 0 0.5rem; line-height: 1.1; }
.hero-sub { font-size: 16px; color: var(--sub); font-weight: 400; margin: 0 0 1.5rem; }

.stats-row { display: flex; gap: 1rem; margin: 1.2rem 0; flex-wrap: wrap; }
.stat-card { flex: 1; min-width: 120px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; text-align: center; }
.stat-value { font-family: var(--mono); font-size: 1.6rem; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 12px; color: var(--muted); margin-top: 4px; }

[data-testid="stInfo"]    { background:#253450!important;border:1px solid #3A5080!important;color:var(--sub)!important; }
[data-testid="stSuccess"] { background:#0D2A1E!important;border:1px solid #1A5C38!important;color:#4ADE80!important; }
[data-testid="stWarning"] { background:#2A1E00!important;border:1px solid #5C3D00!important;color:#F5A623!important; }
[data-testid="stError"]   { background:#2A0D0D!important;border:1px solid #5C1A1A!important;color:#FF6B6B!important; }

/* ── Verdict badges ── */
.verdict-badge {
    display:inline-block; font-family: var(--mono); font-size: 22px; font-weight:700; letter-spacing: 1.5px;
    padding: 12px 28px; border-radius: 16px; text-transform: uppercase;
}
.verdict-strong-buy  { background:#0D2A1E; border:2px solid #1A5C38; color:#1FD97A; }
.verdict-buy          { background:#102A1C; border:2px solid #235C3A; color:#4ADE80; }
.verdict-hold         { background:#1C2130; border:2px solid #3A4260; color:#A8B4CC; }
.verdict-sell         { background:#2A1E00; border:2px solid #5C3D00; color:#F5A623; }
.verdict-strong-sell  { background:#2A0D0D; border:2px solid #5C1A1A; color:#FF6B6B; }

.badge { display:inline-block; font-family: var(--mono); font-size: 11px; letter-spacing: 1px;
         padding: 4px 10px; border-radius: 20px; margin: 2px 6px 2px 0; text-transform: uppercase; }
.badge-bullish { background:#0D2A1E; border:1px solid #1A5C38; color:#4ADE80; }
.badge-neutral { background:#1C2130; border:1px solid #3A4260; color:#A8B4CC; }
.badge-bearish { background:#2A0D0D; border:1px solid #5C1A1A; color:#FF6B6B; }
.badge-mock    { background:#2A1E00; border:1px solid #5C3D00; color:#F5A623; }

/* ── Agent trace timeline ── */
.pipeline-box { display: flex; flex-direction: column; gap: 6px; margin-top: 4px; }
.pipeline-step {
    background: var(--card); border: 1px solid var(--border); border-left: 3px solid var(--muted);
    border-radius: 8px; padding: 8px 12px;
}
.pipeline-step.step-ok      { border-left-color: var(--green); }
.pipeline-step.step-mock    { border-left-color: var(--amber); }
.pipeline-step.step-error   { border-left-color: var(--red); }
.pipeline-label { font-family: var(--mono); font-size: 12.5px; font-weight: 700; color: var(--text); }
.pipeline-detail { font-size: 11.5px; color: var(--muted); margin-top: 2px; padding-left: 20px; word-break: break-word; }

.rationale-card {
    background: var(--card); border: 1px solid var(--border); border-left: 3px solid var(--accent);
    border-radius: 14px; padding: 1.1rem 1.4rem; margin: 0.6rem 0; line-height: 1.7; font-size: 14.5px; color: var(--text);
}
.rationale-card h4 { font-family: var(--mono); font-size: 13px; letter-spacing: 1.5px; color: var(--purple); text-transform: uppercase; margin: 0 0 0.5rem; }

.disclaimer-footer {
    text-align:center; padding: 2rem 1rem 1rem; color: var(--muted); font-size: 12px; line-height: 1.8;
}

/* ── Top picks (Market Scan) ── */
.pick-card {
    position: relative; background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; padding: 1rem 1.2rem 1.1rem; height: 100%;
    overflow: hidden;
}
.pick-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #00D4AA, #8B7FFF);
}
.pick-rank { font-family: var(--mono); font-size: 11px; color: var(--muted); letter-spacing: 1.5px; }
.pick-ticker { font-family: var(--mono); font-size: 20px; font-weight: 700; color: var(--text); margin: 2px 0 6px; }
.pick-verdict { display:inline-block; font-family: var(--mono); font-size: 12px; font-weight:700; letter-spacing: 1px;
                padding: 3px 12px; border-radius: 12px; text-transform: uppercase; margin-bottom: 8px; }
.pick-confidence { font-size: 12.5px; color: var(--sub); margin-bottom: 6px; }
.pick-summary { font-size: 13px; color: var(--sub); line-height: 1.55; }

/* ── Scan change-detection badges ── */
.change-badge { display:inline-block; font-family: var(--mono); font-size: 10.5px; font-weight:700;
                letter-spacing: 0.5px; padding: 2px 9px; border-radius: 10px; text-transform: uppercase; }
.change-upgraded   { background:#0D2A1E; border:1px solid #1A5C38; color:#4ADE80; }
.change-downgraded { background:#2A0D0D; border:1px solid #5C1A1A; color:#FF6B6B; }
.change-unchanged  { background:#1C2130; border:1px solid #3A4260; color:#6A7A96; }
.change-new        { background:#1A1430; border:1px solid #3A2A6A; color:#8B7FFF; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def render_hero():
    st.markdown("""
    <div style="text-align:center; padding:2.5rem 1rem 1.5rem;">
        <div style="display:inline-block; background:#0D1320; border:1px solid #253450;
                    border-radius:30px; padding:6px 20px; margin-bottom:1.2rem;">
            <span style="font-family:'Space Mono',monospace; font-size:11px;
                         letter-spacing:3px; color:#00D4AA; text-transform:uppercase;">
                📈 Multi-Agent Research · Technical · Fundamental · Sentiment · Risk
            </span>
        </div>
        <div class="hero-title">StockSense Agent</div>
        <div class="hero-sub">Orchestrated specialist agents turn a ticker into a research-backed verdict — watch every agent's reasoning in real time</div>
        <div style="display:inline-block; background:#0D1320; border:1px solid #253450;
                    border-radius:40px; padding:10px 28px;">
            <span style="font-family:'Space Mono',monospace; font-size:12px; color:#6A7A96; letter-spacing:1px;">Built by &nbsp;</span>
            <span style="font-family:'Space Mono',monospace; font-size:14px; font-weight:700; color:#00D4AA; letter-spacing:1px;">Abhinav Rawat</span>
            <span style="font-family:'Space Mono',monospace; font-size:12px; color:#6A7A96; letter-spacing:1px;">&nbsp;·&nbsp;AI Playground</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)


def render_footer():
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div class="disclaimer-footer">
        ⚠️ <b>Not financial advice — for research/education only.</b> StockSense Agent synthesizes public data
        and LLM reasoning; it can be wrong, stale, or biased. Always do your own due diligence.<br>
        Built by Abhinav Rawat · AI Playground
    </div>
    """, unsafe_allow_html=True)


VERDICT_CLASS = {
    "Strong Buy": "verdict-strong-buy",
    "Buy": "verdict-buy",
    "Hold": "verdict-hold",
    "Sell": "verdict-sell",
    "Strong Sell": "verdict-strong-sell",
}


def render_verdict_badge(verdict: str, confidence: int):
    cls = VERDICT_CLASS.get(verdict, "verdict-hold")
    st.markdown(
        f'<div class="verdict-badge {cls}">{verdict}</div>'
        f'<div style="margin-top:10px;color:#A8B4CC;font-family:var(--mono,monospace);font-size:13px;">'
        f'Confidence: <b style="color:#00D4AA;">{confidence}%</b></div>',
        unsafe_allow_html=True,
    )


def signal_badge(label: str, signal: str) -> str:
    variant = {"bullish": "bullish", "neutral": "neutral", "bearish": "bearish"}.get(signal, "neutral")
    return f'<span class="badge badge-{variant}">{label}: {signal}</span>'


def mock_badge() -> str:
    return '<span class="badge badge-mock">🧪 mock data</span>'


_CHANGE_LABELS = {
    "upgraded": "▲ Upgraded",
    "downgraded": "▼ Downgraded",
    "unchanged": "— Unchanged",
    "new": "✦ New",
}


def change_badge(change: str) -> str:
    label = _CHANGE_LABELS.get(change, change)
    return f'<span class="change-badge change-{change}">{label}</span>'
