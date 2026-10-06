"""Unit tests for the pure data-shaping logic in ui/scan_panel.py
(_to_dataframe). Streamlit widget rendering itself isn't exercised here —
see the AppTest smoke run for that — this only covers the dataframe/column
construction, including the new portfolio-tagging column."""

from ui.scan_panel import _to_dataframe


def _ok_result(ticker, verdict="Buy", confidence=70):
    return {
        "ticker": ticker,
        "recommendation": {"verdict": verdict, "verdict_label": verdict, "confidence": confidence},
        "market_data": {"latest_price": 100.0, "signal": "bullish"},
        "fundamentals": {"signal": "bullish"},
        "news": {"signal": "neutral"},
        "risk": {"level": "Low"},
    }


def test_to_dataframe_without_portfolio_map_shows_dash():
    df = _to_dataframe([_ok_result("AAPL")])
    assert df.iloc[0]["Portfolio(s)"] == "-"


def test_to_dataframe_tags_ticker_with_source_portfolios():
    portfolio_map = {"AAPL": ["My Watchlist", "Growth"]}
    df = _to_dataframe([_ok_result("AAPL")], portfolio_map=portfolio_map)
    assert df.iloc[0]["Portfolio(s)"] == "My Watchlist, Growth"


def test_to_dataframe_error_row_still_tagged():
    portfolio_map = {"BADTICK": ["My Watchlist"]}
    df = _to_dataframe([{"ticker": "BADTICK", "error": "boom"}], portfolio_map=portfolio_map)
    assert df.iloc[0]["Verdict"] == "Error"
    assert df.iloc[0]["Portfolio(s)"] == "My Watchlist"
