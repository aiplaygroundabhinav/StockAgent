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


def test_classify_fundamentals_pe_is_sector_relative():
    # A P/E of 25 would read "moderate" under flat thresholds, but relative
    # to Financial Services' ~13 average it's a notable premium.
    cheap_for_sector = {"sector": "Financial Services", "industry": "Banks", "trailing_pe": 9}
    rich_for_sector = {"sector": "Financial Services", "industry": "Banks", "trailing_pe": 25}

    cheap_signal, cheap_bullets = _classify_fundamentals(cheap_for_sector)
    rich_signal, rich_bullets = _classify_fundamentals(rich_for_sector)

    assert any("below the Financial Services sector average" in b for b in cheap_bullets)
    assert any("above the Financial Services sector average" in b for b in rich_bullets)


def test_classify_fundamentals_includes_analyst_consensus():
    bullish_data = {"sector": "Technology", "industry": "Software", "analyst_rating": "strong_buy",
                     "analyst_target_price": 250.0, "analyst_count": 30}
    signal, bullets = _classify_fundamentals(bullish_data)
    assert any("consensus is 'Strong Buy'" in b for b in bullets)

    unknown_data = {"sector": "Technology", "industry": "Software"}
    _, bullets2 = _classify_fundamentals(unknown_data)
    assert any("Analyst consensus rating not available" in b for b in bullets2)
