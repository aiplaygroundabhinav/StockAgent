"""Unit tests for the Recommendation Agent's rule-based synthesis
(agents/recommendation_agent.py). No network/LLM calls — only exercises
`_rule_based_synthesis`, the deterministic fallback path."""

from agents.recommendation_agent import _rule_based_synthesis


def _signal(sig, bullets=None):
    return {"signal": sig, "bullets": bullets or [f"{sig} signal detail"]}


def test_all_bullish_yields_strong_buy():
    market_data = _signal("bullish")
    fundamentals = _signal("bullish")
    news = {"signal": "bullish", "bullets": ["positive catalyst"], "summary": "Good news."}
    risk = {"signal": "bullish", "level": "Low", "bullets": ["low risk"]}

    result = _rule_based_synthesis(market_data, fundamentals, news, risk)
    assert result["verdict"] == "Strong Buy"
    assert result["confidence"] >= 90
    assert result["used_llm"] is False


def test_all_bearish_yields_strong_sell():
    market_data = _signal("bearish")
    fundamentals = _signal("bearish")
    news = {"signal": "bearish", "bullets": ["negative catalyst"], "summary": "Bad news."}
    risk = {"signal": "bearish", "level": "High", "bullets": ["high risk"]}

    result = _rule_based_synthesis(market_data, fundamentals, news, risk)
    assert result["verdict"] == "Strong Sell"


def test_mixed_signals_yield_hold():
    market_data = _signal("bullish")
    fundamentals = _signal("bearish")
    news = {"signal": "neutral", "bullets": ["mixed catalyst"], "summary": "Mixed news."}
    risk = {"signal": "neutral", "level": "Medium", "bullets": ["moderate risk"]}

    result = _rule_based_synthesis(market_data, fundamentals, news, risk)
    assert result["verdict"] == "Hold"


def test_confidence_is_within_bounds():
    market_data = _signal("bullish")
    fundamentals = _signal("neutral")
    news = {"signal": "bearish", "bullets": ["x"], "summary": "y"}
    risk = {"signal": "neutral", "level": "Medium", "bullets": ["z"]}

    result = _rule_based_synthesis(market_data, fundamentals, news, risk)
    assert 50 <= result["confidence"] <= 95


def test_rationale_has_all_four_sections():
    market_data = _signal("bullish")
    fundamentals = _signal("bullish")
    news = {"signal": "neutral", "bullets": ["x"], "summary": "y"}
    risk = {"signal": "neutral", "level": "Medium", "bullets": ["z"]}

    result = _rule_based_synthesis(market_data, fundamentals, news, risk)
    assert set(result["rationale"].keys()) == {"technical", "fundamentals", "sentiment", "risk"}
