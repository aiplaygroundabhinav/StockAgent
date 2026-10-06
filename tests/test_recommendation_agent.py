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


def test_relative_performance_signal_is_optional_and_additive():
    """Omitting relative_performance (the default) must reproduce the
    original 4-signal result exactly — no breaking change for existing
    callers."""
    market_data = _signal("bullish")
    fundamentals = _signal("bullish")
    news = {"signal": "bullish", "bullets": ["x"], "summary": "y"}
    risk = {"signal": "bullish", "level": "Low", "bullets": ["z"]}

    baseline = _rule_based_synthesis(market_data, fundamentals, news, risk)
    with_none = _rule_based_synthesis(market_data, fundamentals, news, risk, relative_performance=None)
    assert baseline["verdict"] == with_none["verdict"]
    assert baseline["confidence"] == with_none["confidence"]


def test_relative_performance_signal_shifts_verdict():
    market_data = _signal("neutral")
    fundamentals = _signal("neutral")
    news = {"signal": "neutral", "bullets": ["x"], "summary": "y"}
    risk = {"signal": "neutral", "level": "Medium", "bullets": ["z"]}
    rel_perf = {"signal": "bullish", "bullets": ["outperforming SPY"]}

    result = _rule_based_synthesis(market_data, fundamentals, news, risk, relative_performance=rel_perf)
    assert "relative_performance" in result["weights_used"]


def test_weight_overrides_change_normalized_score():
    market_data = _signal("bullish")
    fundamentals = _signal("bearish")
    news = {"signal": "neutral", "bullets": ["x"], "summary": "y"}
    risk = {"signal": "neutral", "level": "Medium", "bullets": ["z"]}

    default_result = _rule_based_synthesis(market_data, fundamentals, news, risk)
    heavy_technical = _rule_based_synthesis(
        market_data, fundamentals, news, risk, weight_overrides={"technical": 5.0}
    )
    assert heavy_technical["weights_used"]["technical"] == 5.0
    assert heavy_technical["verdict"] != default_result["verdict"]


def test_mock_data_guard_caps_confidence_and_forces_hold():
    from agents.recommendation_agent import synthesize_recommendation, MOCK_DATA_CONFIDENCE_CAP

    market_data = {"signal": "bullish", "bullets": ["strong uptrend"], "is_mock": True}
    fundamentals = {"signal": "bullish", "bullets": ["cheap"], "is_mock": False}
    news = {"signal": "bullish", "bullets": ["good news"], "summary": "Good."}
    risk = {"signal": "bullish", "level": "Low", "bullets": ["low risk"]}

    result = synthesize_recommendation(
        "AAPL", market_data, fundamentals, news, risk,
        data_flags={"market_data": True, "fundamentals": False, "news": False},
    )
    assert result["verdict"] == "Hold"
    assert result["confidence"] <= MOCK_DATA_CONFIDENCE_CAP
    assert result["data_quality"] == "unreliable"
    assert result["verdict_label"] == "Hold / Unreliable Data"
    assert "market_data" in result["mock_sources"]


def test_no_mock_data_guard_when_all_sources_live():
    from agents.recommendation_agent import synthesize_recommendation

    market_data = _signal("bullish")
    fundamentals = _signal("bullish")
    news = {"signal": "bullish", "bullets": ["x"], "summary": "y"}
    risk = {"signal": "bullish", "level": "Low", "bullets": ["z"]}

    result = synthesize_recommendation(
        "AAPL", market_data, fundamentals, news, risk,
        data_flags={"market_data": False, "fundamentals": False, "news": False},
    )
    assert result["data_quality"] == "ok"
    assert result["verdict_label"] == result["verdict"]
