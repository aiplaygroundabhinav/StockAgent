# =============================================================================
# StockSense Agent — Theme Tests
# Author : Abhinav Rawat · AI Architect · AI Playground
# =============================================================================

from string import Template

from ui.theme import CSS_TEMPLATE, DEFAULT_THEME, THEMES, get_chart_theme, resolve_theme


def test_resolve_theme_known_names():
    assert resolve_theme("dark") == "dark"
    assert resolve_theme("light") == "light"


def test_resolve_theme_unknown_falls_back_to_default():
    assert resolve_theme("solarized") == DEFAULT_THEME
    assert resolve_theme("") == DEFAULT_THEME
    assert resolve_theme(None) == DEFAULT_THEME


def test_both_palettes_render_css_without_missing_placeholders():
    for name in THEMES:
        css = Template(CSS_TEMPLATE).substitute(THEMES[name])
        assert "$" not in css
        assert ":root" in css


def test_get_chart_theme_returns_distinct_palettes_per_theme():
    dark = get_chart_theme("dark")
    light = get_chart_theme("light")
    assert dark["template"] == "plotly_dark"
    assert light["template"] == "plotly_white"
    assert dark["paper_bgcolor"] != light["paper_bgcolor"]
    assert set(dark.keys()) == set(light.keys())


def test_get_chart_theme_falls_back_for_unknown_theme():
    assert get_chart_theme("not-a-theme") == get_chart_theme(DEFAULT_THEME)
