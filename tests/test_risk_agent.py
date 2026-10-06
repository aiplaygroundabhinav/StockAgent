"""Unit tests for the Risk Agent's weighted scoring (agents/risk_agent.py).
No network access — `_earnings_proximity_days` hits yfinance internally, so
these tests patch it out to keep the suite offline and deterministic."""

import agents.risk_agent as risk_agent


def _market_data(df):
    return {"df": df}


def _fundamentals(beta=1.0, sector="Technology"):
    return {"metrics": {"beta": beta, "sector": sector}}


def test_analyze_risk_low_for_calm_low_beta_stock(monkeypatch, uptrend_df):
    monkeypatch.setattr(risk_agent, "_annualized_volatility", lambda df: 15.0)
    monkeypatch.setattr(risk_agent, "_earnings_proximity_days", lambda ticker: 30)

    result = risk_agent.analyze_risk(
        "AAPL", _market_data(uptrend_df), _fundamentals(beta=0.6), watchlist_sectors=["Technology", "Healthcare"],
    )
    assert result["level"] == "Low"
    assert result["signal"] == "bullish"
    assert -1.0 <= result["weighted_score"] <= 1.0


def test_analyze_risk_high_for_volatile_concentrated_stock(monkeypatch, downtrend_df):
    monkeypatch.setattr(risk_agent, "_annualized_volatility", lambda df: 90.0)
    monkeypatch.setattr(risk_agent, "_earnings_proximity_days", lambda ticker: 3)

    result = risk_agent.analyze_risk(
        "XYZ", _market_data(downtrend_df), _fundamentals(beta=2.0, sector="Energy"),
        watchlist_sectors=["Energy", "Energy", "Energy", "Technology"],
    )
    assert result["level"] == "High"
    assert result["signal"] == "bearish"


def test_analyze_risk_handles_missing_beta_and_sectors(monkeypatch, uptrend_df):
    monkeypatch.setattr(risk_agent, "_annualized_volatility", lambda df: 25.0)
    monkeypatch.setattr(risk_agent, "_earnings_proximity_days", lambda ticker: -1)

    result = risk_agent.analyze_risk(
        "AAPL", _market_data(uptrend_df), {"metrics": {}}, watchlist_sectors=None,
    )
    assert result["level"] in {"Low", "Medium", "High"}
    assert any("not available" in b for b in result["bullets"])


def test_weighted_score_is_bounded(monkeypatch, uptrend_df):
    monkeypatch.setattr(risk_agent, "_annualized_volatility", lambda df: 5.0)
    monkeypatch.setattr(risk_agent, "_earnings_proximity_days", lambda ticker: 365)

    result = risk_agent.analyze_risk(
        "AAPL", _market_data(uptrend_df), _fundamentals(beta=0.3), watchlist_sectors=["Technology"],
    )
    assert -1.0 <= result["weighted_score"] <= 1.0
