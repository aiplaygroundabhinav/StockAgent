# =============================================================================
# StockSense Agent — Shared Theme
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Same visual theme family as RAGDEMO / PharmacyAgent (teal / purple accents,
# Space Mono + DM Sans) so this app feels like part of the same training
# series. Supports a dark (default) and light palette, toggled from the
# top-right of the app and persisted via settings_store.
# =============================================================================

from string import Template

import streamlit as st

from agents import settings_store

# Each palette drives both the CSS custom properties (:root) and the plotly
# chart colors in ui/lookup_panel.py, so switching themes recolors every
# surface — cards, badges, alerts, charts — consistently in one place.
THEMES = {
    "dark": dict(
        bg="#080C14", surface="#0D1320", card="#131C2E", border="#253450",
        accent="#00D4AA", purple="#8B7FFF", amber="#F5A623", green="#4ADE80", red="#FF6B6B",
        text="#F0F2FF", sub="#A8B4CC", muted="#6A7A96",
        info_bg="#253450", info_border="#3A5080", info_text="#A8B4CC",
        success_bg="#0D2A1E", success_border="#1A5C38", success_text="#4ADE80",
        warning_bg="#2A1E00", warning_border="#5C3D00", warning_text="#F5A623",
        error_bg="#2A0D0D", error_border="#5C1A1A", error_text="#FF6B6B",
        vb_strong_buy_bg="#0D2A1E", vb_strong_buy_border="#1A5C38", vb_strong_buy_text="#1FD97A",
        vb_buy_bg="#102A1C", vb_buy_border="#235C3A", vb_buy_text="#4ADE80",
        vb_hold_bg="#1C2130", vb_hold_border="#3A4260", vb_hold_text="#A8B4CC",
        vb_sell_bg="#2A1E00", vb_sell_border="#5C3D00", vb_sell_text="#F5A623",
        vb_strong_sell_bg="#2A0D0D", vb_strong_sell_border="#5C1A1A", vb_strong_sell_text="#FF6B6B",
        badge_bullish_bg="#0D2A1E", badge_bullish_border="#1A5C38", badge_bullish_text="#4ADE80",
        badge_neutral_bg="#1C2130", badge_neutral_border="#3A4260", badge_neutral_text="#A8B4CC",
        badge_bearish_bg="#2A0D0D", badge_bearish_border="#5C1A1A", badge_bearish_text="#FF6B6B",
        badge_mock_bg="#2A1E00", badge_mock_border="#5C3D00", badge_mock_text="#F5A623",
        change_upgraded_bg="#0D2A1E", change_upgraded_border="#1A5C38", change_upgraded_text="#4ADE80",
        change_downgraded_bg="#2A0D0D", change_downgraded_border="#5C1A1A", change_downgraded_text="#FF6B6B",
        change_unchanged_bg="#1C2130", change_unchanged_border="#3A4260", change_unchanged_text="#6A7A96",
        change_new_bg="#1A1430", change_new_border="#3A2A6A", change_new_text="#8B7FFF",
        bb_fill="rgba(106,122,150,0.08)",
        chart_paper="#131C2E", chart_plot="#131C2E", chart_font="#F0F2FF",
        chart_template="plotly_dark", chart_grid="#253450",
    ),
    "light": dict(
        bg="#F4F6FB", surface="#FFFFFF", card="#FFFFFF", border="#E1E7F2",
        accent="#009E82", purple="#6C5CE7", amber="#B8700A", green="#1C9A5B", red="#D64545",
        text="#121826", sub="#48526B", muted="#7A869E",
        info_bg="#E8EEFC", info_border="#B9C7E8", info_text="#34507A",
        success_bg="#E3F8EC", success_border="#A7E2C2", success_text="#1C8F55",
        warning_bg="#FDF2DC", warning_border="#F0CF8E", warning_text="#9A6A0B",
        error_bg="#FDE7E7", error_border="#F0B3B3", error_text="#C23B3B",
        vb_strong_buy_bg="#E3F8EC", vb_strong_buy_border="#8FDBB2", vb_strong_buy_text="#148A4E",
        vb_buy_bg="#EAF8EE", vb_buy_border="#A8E0BC", vb_buy_text="#1C9A5B",
        vb_hold_bg="#EEF1F7", vb_hold_border="#D3D9E6", vb_hold_text="#4B5468",
        vb_sell_bg="#FDF2DC", vb_sell_border="#F0CF8E", vb_sell_text="#9A6A0B",
        vb_strong_sell_bg="#FDE7E7", vb_strong_sell_border="#F0B3B3", vb_strong_sell_text="#C23B3B",
        badge_bullish_bg="#E3F8EC", badge_bullish_border="#A7E2C2", badge_bullish_text="#1C8F55",
        badge_neutral_bg="#EEF1F7", badge_neutral_border="#D3D9E6", badge_neutral_text="#4B5468",
        badge_bearish_bg="#FDE7E7", badge_bearish_border="#F0B3B3", badge_bearish_text="#C23B3B",
        badge_mock_bg="#FDF2DC", badge_mock_border="#F0CF8E", badge_mock_text="#9A6A0B",
        change_upgraded_bg="#E3F8EC", change_upgraded_border="#A7E2C2", change_upgraded_text="#1C8F55",
        change_downgraded_bg="#FDE7E7", change_downgraded_border="#F0B3B3", change_downgraded_text="#C23B3B",
        change_unchanged_bg="#EEF1F7", change_unchanged_border="#D3D9E6", change_unchanged_text="#7A869E",
        change_new_bg="#F1EDFC", change_new_border="#CCC0F5", change_new_text="#6C5CE7",
        bb_fill="rgba(135,146,168,0.10)",
        chart_paper="#FFFFFF", chart_plot="#FFFFFF", chart_font="#121826",
        chart_template="plotly_white", chart_grid="#E1E7F2",
    ),
}

DEFAULT_THEME = "dark"


def resolve_theme(name: str) -> str:
    """Normalizes an arbitrary theme name to one of the known THEMES keys,
    defaulting to dark for anything unrecognized (e.g. stale persisted data)."""
    return name if name in THEMES else DEFAULT_THEME


CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap');

:root {
    --bg:      $bg;
    --surface: $surface;
    --card:    $card;
    --border:  $border;
    --accent:  $accent;
    --purple:  $purple;
    --amber:   $amber;
    --green:   $green;
    --red:     $red;
    --text:    $text;
    --sub:     $sub;
    --muted:   $muted;
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
    background: linear-gradient(135deg, $accent, $purple) !important;
    color: $bg !important;
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

/* Theme toggle — kept compact + secondary so it doesn't compete with the
   primary teal/purple action buttons. */
[data-testid="stToggle"] { display: flex; justify-content: flex-end; }

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

[data-testid="stInfo"]    { background:$info_bg!important;border:1px solid $info_border!important;color:$info_text!important; }
[data-testid="stSuccess"] { background:$success_bg!important;border:1px solid $success_border!important;color:$success_text!important; }
[data-testid="stWarning"] { background:$warning_bg!important;border:1px solid $warning_border!important;color:$warning_text!important; }
[data-testid="stError"]   { background:$error_bg!important;border:1px solid $error_border!important;color:$error_text!important; }

/* ── Verdict badges ── */
.verdict-badge {
    display:inline-block; font-family: var(--mono); font-size: 22px; font-weight:700; letter-spacing: 1.5px;
    padding: 12px 28px; border-radius: 16px; text-transform: uppercase;
}
.verdict-strong-buy  { background:$vb_strong_buy_bg; border:2px solid $vb_strong_buy_border; color:$vb_strong_buy_text; }
.verdict-buy          { background:$vb_buy_bg; border:2px solid $vb_buy_border; color:$vb_buy_text; }
.verdict-hold         { background:$vb_hold_bg; border:2px solid $vb_hold_border; color:$vb_hold_text; }
.verdict-sell         { background:$vb_sell_bg; border:2px solid $vb_sell_border; color:$vb_sell_text; }
.verdict-strong-sell  { background:$vb_strong_sell_bg; border:2px solid $vb_strong_sell_border; color:$vb_strong_sell_text; }

.badge { display:inline-block; font-family: var(--mono); font-size: 11px; letter-spacing: 1px;
         padding: 4px 10px; border-radius: 20px; margin: 2px 6px 2px 0; text-transform: uppercase; }
.badge-bullish { background:$badge_bullish_bg; border:1px solid $badge_bullish_border; color:$badge_bullish_text; }
.badge-neutral { background:$badge_neutral_bg; border:1px solid $badge_neutral_border; color:$badge_neutral_text; }
.badge-bearish { background:$badge_bearish_bg; border:1px solid $badge_bearish_border; color:$badge_bearish_text; }
.badge-mock    { background:$badge_mock_bg; border:1px solid $badge_mock_border; color:$badge_mock_text; }

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
    background: linear-gradient(90deg, $accent, $purple);
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
.change-upgraded   { background:$change_upgraded_bg; border:1px solid $change_upgraded_border; color:$change_upgraded_text; }
.change-downgraded { background:$change_downgraded_bg; border:1px solid $change_downgraded_border; color:$change_downgraded_text; }
.change-unchanged  { background:$change_unchanged_bg; border:1px solid $change_unchanged_border; color:$change_unchanged_text; }
.change-new        { background:$change_new_bg; border:1px solid $change_new_border; color:$change_new_text; }

/* ── Onboarding quick-ticker chips (Stock Lookup empty state) ── */
.chip-hint { font-size: 12.5px; color: var(--muted); margin: 0.75rem 0 0.4rem; }
</style>
"""


def inject_css(theme: str = DEFAULT_THEME):
    """Injects the full app stylesheet for the given theme ('dark' or
    'light'). Call once near the top of app.py, after st.set_page_config."""
    palette = THEMES[resolve_theme(theme)]
    st.markdown(Template(CSS_TEMPLATE).substitute(palette), unsafe_allow_html=True)


def get_chart_theme(theme: str = DEFAULT_THEME) -> dict:
    """Returns the plotly layout colors matching the given theme, so price
    charts stay legible and on-brand whichever theme the user has picked."""
    palette = THEMES[resolve_theme(theme)]
    return {
        "template": palette["chart_template"],
        "paper_bgcolor": palette["chart_paper"],
        "plot_bgcolor": palette["chart_plot"],
        "font_color": palette["chart_font"],
        "gridcolor": palette["chart_grid"],
        "bb_fill": palette["bb_fill"],
    }


def render_theme_toggle():
    """Renders a compact light/dark toggle in the top-right of the page and
    returns the active theme name ('dark' or 'light'). Persists the choice
    via settings_store so it survives app restarts."""
    _, toggle_col = st.columns([6, 1])
    with toggle_col:
        is_light = st.toggle(
            "☀️ Light",
            value=resolve_theme(st.session_state.get("theme", DEFAULT_THEME)) == "light",
            key="theme_toggle",
            help="Switch between dark and light mode.",
        )
    new_theme = "light" if is_light else "dark"
    if new_theme != st.session_state.get("theme"):
        st.session_state.theme = new_theme
        settings_store.save_settings(theme=new_theme)
        st.rerun()
    return new_theme


def render_hero():
    st.markdown("""
    <div style="text-align:center; padding:1rem 1rem 1.5rem;">
        <div style="display:inline-block; background:var(--surface); border:1px solid var(--border);
                    border-radius:30px; padding:6px 20px; margin-bottom:1.2rem;">
            <span style="font-family:'Space Mono',monospace; font-size:11px;
                         letter-spacing:3px; color:var(--accent); text-transform:uppercase;">
                📈 Multi-Agent Research · Technical · Fundamental · Sentiment · Risk
            </span>
        </div>
        <div class="hero-title">StockSense Agent</div>
        <div class="hero-sub">Orchestrated specialist agents turn a ticker into a research-backed verdict — watch every agent's reasoning in real time</div>
        <div style="display:inline-block; background:var(--surface); border:1px solid var(--border);
                    border-radius:40px; padding:10px 28px;">
            <span style="font-family:'Space Mono',monospace; font-size:12px; color:var(--muted); letter-spacing:1px;">Built by &nbsp;</span>
            <span style="font-family:'Space Mono',monospace; font-size:14px; font-weight:700; color:var(--accent); letter-spacing:1px;">Abhinav Rawat</span>
            <span style="font-family:'Space Mono',monospace; font-size:12px; color:var(--muted); letter-spacing:1px;">&nbsp;·&nbsp;AI Playground</span>
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


def render_verdict_badge(verdict: str, confidence: int, label: str = None):
    cls = VERDICT_CLASS.get(verdict, "verdict-hold")
    display_label = label or verdict
    st.markdown(
        f'<div class="verdict-badge {cls}">{display_label}</div>'
        f'<div style="margin-top:10px;color:var(--sub);font-family:var(--mono,monospace);font-size:13px;">'
        f'Confidence: <b style="color:var(--accent);">{confidence}%</b></div>',
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
