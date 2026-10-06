"""Unit tests for the Fundamentals Agent's classification logic
(agents/fundamentals_agent.py). No network access — operates on
hand-built metric dicts, the same shape `_fetch_fundamentals`/
`_mock_fundamentals` produce."""

from agents.fundamentals_agent import _classify_fundamentals, _mock_fundamentals


def test_mock_fundamentals_is_deterministic():
    a = _mock_fundamentals("AAPL")
    b = _mock_fundamentals("AAPL")
    assert a == b
    assert a["is_mock"] is True


def test_mock_fundamentals_differs_by_ticker():
    a = _mock_fundamentals("AAPL")
    b = _mock_fundamentals("MSFT")
    assert a != b


def test_classify_fundamentals_bullish_profile():
    data = {
        "sector": "Technology",
        "industry": "Software",
        "trailing_pe": 15,
        "eps_growth": 0.25,
        "revenue_growth": 0.20,
        "debt_to_equity": 30,
        "profit_margin": 0.25,
    }
    signal, bullets = _classify_fundamentals(data)
    assert signal == "bullish"
    assert len(bullets) >= 4


def test_classify_fundamentals_bearish_profile():
    data = {
        "sector": "Energy",
        "industry": "Oil & Gas",
        "trailing_pe": 55,
        "eps_growth": -0.15,
        "revenue_growth": -0.10,
        "debt_to_equity": 220,
        "profit_margin": -0.05,
    }
    signal, bullets = _classify_fundamentals(data)
    assert signal == "bearish"


def test_classify_fundamentals_handles_missing_fields():
    data = {"sector": "Unknown", "industry": "Unknown"}
    signal, bullets = _classify_fundamentals(data)
    assert signal == "neutral"
    assert any("not available" in b for b in bullets)
