# =============================================================================
# StockSense Agent — Orchestrator
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Routes a ticker request to the four specialist agents in parallel (LCEL
# RunnableParallel — no LangGraph), then feeds their outputs into the
# Recommendation synthesis chain. Every step is captured into an ordered
# trace: Market Data -> Fundamentals -> News/Sentiment -> Risk ->
# Recommendation, with per-step latency (and tokens, where an LLM ran).
# =============================================================================

import time
from concurrent.futures import ThreadPoolExecutor

from langchain_core.runnables import RunnableLambda, RunnableParallel

from agents.callbacks import new_trace, record
from agents.market_data_agent import analyze_market_data
from agents.fundamentals_agent import analyze_fundamentals
from agents.news_agent import analyze_news
from agents.risk_agent import analyze_risk
from agents.recommendation_agent import synthesize_recommendation


def _build_specialist_graph(rss_urls, api_key, model, period="6mo", include_benchmark=False):
    """Builds the RunnableParallel of the three independent specialists that
    don't depend on each other's output (market data, fundamentals, news).
    Risk runs after, since it consumes market data + fundamentals."""
    market_data_chain = RunnableLambda(lambda ticker: analyze_market_data(ticker, period, include_benchmark))
    fundamentals_chain = RunnableLambda(lambda ticker: analyze_fundamentals(ticker))
    news_chain = RunnableLambda(lambda ticker: analyze_news(ticker, rss_urls, api_key, model))

    return RunnableParallel(
        market_data=market_data_chain,
        fundamentals=fundamentals_chain,
        news=news_chain,
    )


def run_stock_analysis(ticker: str, rss_urls: list = None, risk_tolerance: int = 50,
                        api_key: str = "", model: str = "gpt-4o-mini",
                        watchlist_sectors: list = None, period: str = "6mo",
                        include_benchmark: bool = True) -> dict:
    """Runs the full multi-agent pipeline for one ticker and returns the
    aggregated result plus an ordered trace for the Agent Trace tab.

    `period` sets the price-history lookback (1mo/3mo/6mo/1y/2y). Market
    Scan calls this with the default so scans stay fast; Stock Lookup lets
    the user pick a longer window and overlays a SPY benchmark chart."""
    ticker = ticker.upper().strip()
    trace = new_trace()
    overall_start = time.time()

    record(trace, agent="Orchestrator", label=f"Received request for {ticker}", status="ok")

    graph = _build_specialist_graph(rss_urls, api_key, model, period, include_benchmark)

    t0 = time.time()
    parallel_results = graph.invoke(ticker)
    parallel_latency = round((time.time() - t0) * 1000, 1)

    market_data = parallel_results["market_data"]
    fundamentals = parallel_results["fundamentals"]
    news = parallel_results["news"]

    record(trace, agent="Market Data", label="Fetch price history + compute SMA/EMA/RSI/MACD/Bollinger",
           status="mock" if market_data["is_mock"] else "ok",
           detail=f"signal={market_data['signal']} · last close=${market_data['latest_price']:.2f}"
                  + (" (mock data — yfinance unreachable)" if market_data["is_mock"] else ""),
           latency_ms=market_data["latency_ms"])

    record(trace, agent="Fundamentals", label="Fetch valuation/growth/leverage metrics",
           status="mock" if fundamentals["is_mock"] else "ok",
           detail=f"signal={fundamentals['signal']}"
                  + (" (mock data — yfinance info unavailable)" if fundamentals["is_mock"] else ""),
           latency_ms=fundamentals["latency_ms"])

    record(trace, agent="News & Sentiment", label="Ingest RSS feeds + score sentiment",
           status="ok", detail=f"signal={news['signal']} · used_llm={news['used_llm']} · headlines={len(news['headlines'])}",
           latency_ms=news["latency_ms"], tokens=news.get("tokens"))

    risk = analyze_risk(ticker, market_data, fundamentals, watchlist_sectors, risk_tolerance)
    record(trace, agent="Risk", label="Flag volatility/beta/concentration/earnings risk",
           status="ok", detail=f"level={risk['level']} · volatility={risk['volatility_pct']}%",
           latency_ms=risk["latency_ms"])

    recommendation = synthesize_recommendation(ticker, market_data, fundamentals, news, risk, api_key, model)
    record(trace, agent="Recommendation", label="Synthesize final verdict",
           status="ok", detail=f"verdict={recommendation['verdict']} · confidence={recommendation['confidence']}%"
                                + (" (LLM synthesis)" if recommendation["used_llm"] else " (rule-based synthesis — no API key)"),
           latency_ms=recommendation["latency_ms"], tokens=recommendation.get("tokens"))

    total_latency_ms = round((time.time() - overall_start) * 1000, 1)
    record(trace, agent="Orchestrator", label="Pipeline complete", status="ok",
           detail=f"parallel specialists took {parallel_latency}ms · total {total_latency_ms}ms")

    return {
        "ticker": ticker,
        "market_data": market_data,
        "fundamentals": fundamentals,
        "news": news,
        "risk": risk,
        "recommendation": recommendation,
        "trace": trace,
        "total_latency_ms": total_latency_ms,
    }


def run_market_scan(watchlist: list, rss_urls: list = None, risk_tolerance: int = 50,
                     api_key: str = "", model: str = "gpt-4o-mini", max_workers: int = 4) -> list:
    """Runs the full pipeline across a watchlist in parallel threads (each
    ticker's own pipeline still runs its specialists via RunnableParallel)."""
    # First pass: lightweight sector lookup for concentration-risk context.
    from agents.fundamentals_agent import analyze_fundamentals as _af
    sectors = []
    for t in watchlist:
        try:
            sectors.append(_af(t)["metrics"].get("sector", "Unknown"))
        except Exception:
            sectors.append("Unknown")

    def _run_one(t):
        try:
            return run_stock_analysis(t, rss_urls, risk_tolerance, api_key, model,
                                       watchlist_sectors=sectors, include_benchmark=False)
        except Exception as exc:
            return {"ticker": t.upper(), "error": str(exc)}

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(_run_one, watchlist):
            results.append(result)
    return results
