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

VERDICTS = ["Strong Sell", "Sell", "Hold", "Buy", "Strong Buy"]

_SIGNAL_SCORE = {"bullish": 1, "neutral": 0, "bearish": -1}


def _rule_based_synthesis(market_data: dict, fundamentals: dict, news: dict, risk: dict) -> dict:
    weights = {"technical": 1.0, "fundamentals": 1.0, "sentiment": 0.8, "risk": 1.0}

    technical_score = _SIGNAL_SCORE[market_data["signal"]] * weights["technical"]
    fundamentals_score = _SIGNAL_SCORE[fundamentals["signal"]] * weights["fundamentals"]
    sentiment_score = _SIGNAL_SCORE[news["signal"]] * weights["sentiment"]
    risk_score = _SIGNAL_SCORE[risk["signal"]] * weights["risk"]

    total = technical_score + fundamentals_score + sentiment_score + risk_score
    max_total = sum(weights.values())

    normalized = total / max_total  # -1..1

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

    signals = [market_data["signal"], fundamentals["signal"], news["signal"], risk["signal"]]
    agreement = max(signals.count("bullish"), signals.count("neutral"), signals.count("bearish")) / len(signals)
    confidence = int(round(50 + agreement * 45))  # 50-95%

    rationale = {
        "technical": " ".join(market_data["bullets"][:3]),
        "fundamentals": " ".join(fundamentals["bullets"][:3]),
        "sentiment": news.get("summary", "") + " " + " ".join(news["bullets"][:2]),
        "risk": " ".join(risk["bullets"][:3]),
    }
    summary = (
        f"Rule-based synthesis: technical={market_data['signal']}, fundamentals={fundamentals['signal']}, "
        f"sentiment={news['signal']}, risk={risk['level']} risk level -> weighted score {normalized:+.2f}."
    )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "rationale": rationale,
        "summary": summary,
        "used_llm": False,
        "tokens": None,
    }


def _llm_synthesis(ticker: str, market_data: dict, fundamentals: dict, news: dict, risk: dict,
                    api_key: str, model: str) -> dict:
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


def synthesize_recommendation(ticker: str, market_data: dict, fundamentals: dict, news: dict, risk: dict,
                               api_key: str = "", model: str = "gpt-4o-mini") -> dict:
    start = time.time()
    try:
        if api_key:
            result = _llm_synthesis(ticker, market_data, fundamentals, news, risk, api_key, model)
        else:
            result = _rule_based_synthesis(market_data, fundamentals, news, risk)
    except Exception:
        result = _rule_based_synthesis(market_data, fundamentals, news, risk)

    result["latency_ms"] = round((time.time() - start) * 1000, 1)
    result["ticker"] = ticker
    return result
