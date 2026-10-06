# =============================================================================
# StockSense Agent — Recommendation Agent (Synthesis)
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Merges the Market Data, Fundamentals, News/Sentiment, and Risk agents'
# outputs into a single verdict: Strong Buy / Buy / Hold / Sell / Strong
# Sell, with a confidence score and a rationale broken down per signal
# source. Uses an LLM synthesis chain when an API key is available;
# otherwise falls back to a deterministic weighted-vote rule so the pipeline
# always produces a complete answer.
# =============================================================================

import time
from typing import Optional

VERDICTS = ["Strong Sell", "Sell", "Hold", "Buy", "Strong Buy"]

_SIGNAL_SCORE = {"bullish": 1, "neutral": 0, "bearish": -1}

# Default rule-based weights. Phase 3 (investor profile) can override this via
# `synthesize_recommendation(..., weight_overrides={...})` without changing
# the function signature every specialist agent already calls.
DEFAULT_WEIGHTS = {"technical": 1.0, "fundamentals": 1.0, "sentiment": 0.8, "risk": 1.0, "relative_performance": 0.8}

# Mock/stale data is never allowed to drive a confident Buy/Sell call — this
# is Phase 1 item 3's "mock-data guard".
MOCK_DATA_CONFIDENCE_CAP = 40
UNRELIABLE_VERDICT_LABEL = "Hold / Unreliable Data"


def _rule_based_synthesis(market_data: dict, fundamentals: dict, news: dict, risk: dict,
                           relative_performance: Optional[dict] = None,
                           weight_overrides: Optional[dict] = None) -> dict:
    """`relative_performance` (Phase 1 item 4) is an optional 5th signal —
    a dict with a `signal` key like the other four — comparing the stock to
    SPY/sector ETF. It's additive: omitting it (the default) reproduces the
    original 4-signal behavior exactly, so existing callers/tests are
    unaffected. `weight_overrides` lets an investor profile (Phase 3 item 11)
    re-weight signals without changing this function's signature again."""
    weights = dict(DEFAULT_WEIGHTS)
    if weight_overrides:
        weights.update(weight_overrides)

    active_weights = {"technical": weights["technical"], "fundamentals": weights["fundamentals"],
                       "sentiment": weights["sentiment"], "risk": weights["risk"]}
    signals = {"technical": market_data["signal"], "fundamentals": fundamentals["signal"],
               "sentiment": news["signal"], "risk": risk["signal"]}

    if relative_performance is not None:
        active_weights["relative_performance"] = weights["relative_performance"]
        signals["relative_performance"] = relative_performance["signal"]

    total = sum(_SIGNAL_SCORE[sig] * active_weights[name] for name, sig in signals.items())
    max_total = sum(active_weights.values())

    normalized = total / max_total if max_total else 0.0  # -1..1

    if normalized >= 0.6:
        verdict = "Strong Buy"
    elif normalized >= 0.2:
        verdict = "Buy"
    elif normalized <= -0.6:
        verdict = "Strong Sell"
    elif normalized <= -0.2:
        verdict = "Sell"
    else:
        verdict = "Hold"

    signal_values = list(signals.values())
    agreement = max(signal_values.count("bullish"), signal_values.count("neutral"),
                     signal_values.count("bearish")) / len(signal_values)
    confidence = int(round(50 + agreement * 45))  # 50-95%

    rationale = {
        "technical": " ".join(market_data["bullets"][:3]),
        "fundamentals": " ".join(fundamentals["bullets"][:3]),
        "sentiment": news.get("summary", "") + " " + " ".join(news["bullets"][:2]),
        "risk": " ".join(risk["bullets"][:3]),
    }
    if relative_performance is not None:
        rationale["risk"] += " " + " ".join(relative_performance.get("bullets", [])[:2])

    summary = (
        f"Rule-based synthesis: technical={market_data['signal']}, fundamentals={fundamentals['signal']}, "
        f"sentiment={news['signal']}, risk={risk['level']} risk level"
        + (f", relative_performance={relative_performance['signal']}" if relative_performance is not None else "")
        + f" -> weighted score {normalized:+.2f}."
    )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "rationale": rationale,
        "summary": summary,
        "used_llm": False,
        "tokens": None,
        "weights_used": active_weights,
    }


def _llm_synthesis(ticker: str, market_data: dict, fundamentals: dict, news: dict, risk: dict,
                    api_key: str, model: str, relative_performance: Optional[dict] = None) -> dict:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from pydantic import BaseModel, Field
    from typing import Literal

    class Rationale(BaseModel):
        technical: str = Field(description="1-2 sentences on technical signals driving the call")
        fundamentals: str = Field(description="1-2 sentences on fundamentals driving the call")
        sentiment: str = Field(description="1-2 sentences on news/sentiment driving the call")
        risk: str = Field(description="1-2 sentences on risk flags driving the call")

    class Recommendation(BaseModel):
        verdict: Literal["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
        confidence: int = Field(ge=0, le=100, description="Confidence in this call, 0-100")
        rationale: Rationale
        summary: str = Field(description="One-sentence overall thesis")

    context = (
        f"Ticker: {ticker}\n\n"
        f"TECHNICAL ({market_data['signal']}):\n- " + "\n- ".join(market_data["bullets"]) + "\n\n"
        f"FUNDAMENTALS ({fundamentals['signal']}):\n- " + "\n- ".join(fundamentals["bullets"]) + "\n\n"
        f"NEWS/SENTIMENT ({news['signal']}):\n- " + "\n- ".join(news["bullets"]) + "\n\n"
        f"RISK ({risk['level']} risk):\n- " + "\n- ".join(risk["bullets"])
    )
    if relative_performance is not None:
        context += (
            f"\n\nRELATIVE PERFORMANCE vs SPY/sector ETF ({relative_performance['signal']}):\n- "
            + "\n- ".join(relative_performance.get("bullets", []))
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Recommendation Agent of a multi-agent stock research system. "
                   "You receive structured signals from four specialist agents (technical, fundamentals, "
                   "news/sentiment, risk) and must synthesize ONE final call: Strong Buy, Buy, Hold, Sell, "
                   "or Strong Sell, with a confidence score and a rationale citing which signals drove it. "
                   "Be balanced — do not ignore risk flags even if technical/fundamentals are strong. "
                   "This is for research/education only, not financial advice."),
        ("human", "{context}"),
    ])

    llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)
    structured_llm = llm.with_structured_output(Recommendation)
    chain = prompt | structured_llm
    result: Recommendation = chain.invoke({"context": context})

    approx_tokens = (len(context) + len(str(result))) // 4

    return {
        "verdict": result.verdict,
        "confidence": result.confidence,
        "rationale": result.rationale.model_dump(),
        "summary": result.summary,
        "used_llm": True,
        "tokens": approx_tokens,
    }


def _apply_mock_data_guard(result: dict, data_flags: Optional[dict]) -> dict:
    """Phase 1 item 3: if any upstream agent used mock/stale data, the
    verdict can't be trusted enough to drive a confident Buy/Sell call.
    Caps confidence, forces the verdict to Hold, and labels it so the UI
    (and Top Picks, in Phase 4) can exclude/flag it rather than silently
    presenting a fabricated-data call as real research."""
    mock_sources = [name for name, is_mock in (data_flags or {}).items() if is_mock]
    if not mock_sources:
        result["data_quality"] = "ok"
        result["verdict_label"] = result["verdict"]
        return result

    if result["verdict"] != "Hold":
        result["original_verdict"] = result["verdict"]
    result["verdict"] = "Hold"
    result["verdict_label"] = UNRELIABLE_VERDICT_LABEL
    result["confidence"] = min(result["confidence"], MOCK_DATA_CONFIDENCE_CAP)
    result["data_quality"] = "unreliable"
    result["mock_sources"] = mock_sources
    flag_note = (
        f"⚠️ Data quality: {', '.join(s.replace('_', ' ') for s in mock_sources)} unavailable/mock — "
        f"confidence capped at {MOCK_DATA_CONFIDENCE_CAP}% and verdict forced to Hold until live data "
        f"is available. "
    )
    result["rationale"]["risk"] = flag_note + result["rationale"].get("risk", "")
    result["summary"] = flag_note + result.get("summary", "")
    return result


def synthesize_recommendation(ticker: str, market_data: dict, fundamentals: dict, news: dict, risk: dict,
                               api_key: str = "", model: str = "gpt-4o-mini",
                               relative_performance: Optional[dict] = None,
                               data_flags: Optional[dict] = None,
                               weight_overrides: Optional[dict] = None) -> dict:
    """`relative_performance` (Phase 1 item 4), `data_flags` (Phase 1 item 3
    mock-data guard, e.g. {"market_data": bool, "fundamentals": bool,
    "news": bool}), and `weight_overrides` (Phase 3 investor-profile
    weighting) are all optional and additive — omitting them reproduces the
    original behavior exactly, so no existing caller needs to change."""
    start = time.time()
    try:
        if api_key:
            result = _llm_synthesis(ticker, market_data, fundamentals, news, risk, api_key, model,
                                     relative_performance)
        else:
            result = _rule_based_synthesis(market_data, fundamentals, news, risk, relative_performance,
                                            weight_overrides)
    except Exception:
        result = _rule_based_synthesis(market_data, fundamentals, news, risk, relative_performance,
                                        weight_overrides)

    result = _apply_mock_data_guard(result, data_flags)
    result["latency_ms"] = round((time.time() - start) * 1000, 1)
    result["ticker"] = ticker
    return result
