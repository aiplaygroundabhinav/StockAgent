"""Unit tests for the Market Data Agent's indicator math and trend
classification (agents/market_data_agent.py). No network access."""

from agents.market_data_agent import _classify_trend, _compute_indicators, _rsi


def test_rsi_is_bounded(uptrend_df):
    rsi = _rsi(uptrend_df["Close"])
    assert (rsi >= 0).all()
    assert (rsi <= 100).all()


def test_rsi_high_in_strong_uptrend(uptrend_df):
    rsi = _rsi(uptrend_df["Close"])
    # A steady, low-noise uptrend should push RSI well above neutral (50)
    # by the end of the series.
    assert rsi.iloc[-1] > 60


def test_compute_indicators_adds_expected_columns(uptrend_df):
    enriched = _compute_indicators(uptrend_df)
    expected_cols = {
        "SMA20", "SMA50", "EMA12", "EMA26", "MACD", "MACD_signal",
        "RSI14", "BB_mid", "BB_upper", "BB_lower",
    }
    assert expected_cols.issubset(enriched.columns)
    # Bollinger bands should bracket the midline.
    assert (enriched["BB_upper"] >= enriched["BB_mid"]).all()
    assert (enriched["BB_lower"] <= enriched["BB_mid"]).all()


def test_classify_trend_bullish_on_uptrend(uptrend_df):
    enriched = _compute_indicators(uptrend_df)
    signal, bullets = _classify_trend(enriched)
    assert signal == "bullish"
    assert len(bullets) >= 3


def test_classify_trend_bearish_on_downtrend(downtrend_df):
    enriched = _compute_indicators(downtrend_df)
    signal, bullets = _classify_trend(enriched)
    assert signal == "bearish"
    assert len(bullets) >= 3
