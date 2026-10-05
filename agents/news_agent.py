# =============================================================================
# StockSense Agent — News & Sentiment Agent
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Ingests a configurable list of RSS feeds (feedparser), filters for entries
# that mention the ticker/company, and scores sentiment. When an
# OPENAI_API_KEY is configured, an LLM summarizes catalysts and classifies
# sentiment; otherwise a keyword-based scorer provides a deterministic
# fallback so the app still works offline / without a key.
# =============================================================================

import time

from agents.cache import get_cached, set_cached

CACHE_TTL_SECONDS = 30 * 60

DEFAULT_RSS_FEEDS = [
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://finance.yahoo.com/news/rssindex",
]

_POSITIVE_WORDS = [
    "beat", "beats", "surge", "surges", "soar", "soars", "upgrade", "upgraded",
    "growth", "record", "strong", "rally", "rallies", "outperform", "bullish",
    "profit", "gain", "gains", "expand", "expansion", "breakthrough", "raises guidance",
]
_NEGATIVE_WORDS = [
    "miss", "misses", "plunge", "plunges", "downgrade", "downgraded", "lawsuit",
    "decline", "declines", "cut", "cuts", "warns", "warning", "bearish", "slump",
    "recall", "investigation", "layoffs", "loss", "losses", "sell-off", "selloff",
]


def _fetch_entries(rss_urls: list) -> list:
    import feedparser

    entries = []
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                entries.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "link": entry.get("link", ""),
                    "source": url,
                })
        except Exception:
            continue
    return entries


def _matches_ticker(entry: dict, ticker: str, company_hint: str = "") -> bool:
    text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
    needles = [ticker.lower()]
    if company_hint:
        needles.append(company_hint.lower())
    return any(n in text for n in needles if n)


def _keyword_sentiment(entries: list) -> tuple[str, list, str]:
    pos = neg = 0
    bullets = []
    for e in entries[:8]:
        text = f"{e['title']} {e.get('summary', '')}".lower()
        p = sum(text.count(w) for w in _POSITIVE_WORDS)
        n = sum(text.count(w) for w in _NEGATIVE_WORDS)
        pos += p
        neg += n
        if p or n:
            lean = "bullish-leaning" if p > n else ("bearish-leaning" if n > p else "mixed")
            bullets.append(f"\"{e['title'].strip()}\" — {lean}.")

    if not bullets:
        for e in entries[:3]:
            bullets.append(f"\"{e['title'].strip()}\" (no strong sentiment keywords detected).")

    if pos - neg >= 2:
        sentiment = "bullish"
    elif neg - pos >= 2:
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    summary = f"Keyword scan of recent headlines: {pos} positive vs {neg} negative signal words."
    return sentiment, bullets, summary


def _llm_sentiment(entries: list, ticker: str, api_key: str, model: str) -> tuple[str, list, str, int]:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from pydantic import BaseModel, Field
    from typing import Literal

    class NewsSentiment(BaseModel):
        sentiment: Literal["bullish", "neutral", "bearish"] = Field(description="Overall sentiment for the stock")
        bullets: list[str] = Field(description="3-5 short bullet points on recent catalysts / news driving sentiment")
        summary: str = Field(description="One-sentence overall summary")

    headlines_text = "\n".join(f"- {e['title']}: {e.get('summary', '')[:200]}" for e in entries[:10])
    if not headlines_text:
        headlines_text = "(no recent headlines found for this ticker)"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a financial news analyst. Given recent headlines about a stock, "
                   "summarize the key catalysts and classify overall sentiment. Be concise and factual."),
        ("human", "Ticker: {ticker}\n\nRecent headlines:\n{headlines}"),
    ])

    llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)
    structured_llm = llm.with_structured_output(NewsSentiment)
    chain = prompt | structured_llm
    result: NewsSentiment = chain.invoke({"ticker": ticker, "headlines": headlines_text})

    # Token usage isn't exposed through with_structured_output; estimate via a
    # cheap heuristic (chars/4) so the trace still shows a non-null figure.
    approx_tokens = (len(headlines_text) + len(str(result))) // 4

    return result.sentiment, result.bullets, result.summary, approx_tokens


def analyze_news(ticker: str, rss_urls: list = None, api_key: str = "", model: str = "gpt-4o-mini") -> dict:
    start = time.time()
    ticker = ticker.upper().strip()
    rss_urls = rss_urls or DEFAULT_RSS_FEEDS

    cache_key = f"headlines::{','.join(sorted(rss_urls))}"
    all_entries = get_cached("news", cache_key, CACHE_TTL_SECONDS)
    if all_entries is None:
        all_entries = _fetch_entries(rss_urls)
        set_cached("news", cache_key, all_entries)

    matched = [e for e in all_entries if _matches_ticker(e, ticker)]
    is_general_fallback = False
    if not matched:
        matched = all_entries[:8]
        is_general_fallback = True

    used_llm = False
    tokens = None
    try:
        if api_key:
            sentiment, bullets, summary, tokens = _llm_sentiment(matched, ticker, api_key, model)
            used_llm = True
        else:
            sentiment, bullets, summary = _keyword_sentiment(matched)
    except Exception:
        sentiment, bullets, summary = _keyword_sentiment(matched)

    if is_general_fallback:
        bullets.insert(0, f"No ticker-specific headlines found — showing general market context instead.")

    latency_ms = round((time.time() - start) * 1000, 1)

    return {
        "ticker": ticker,
        "headlines": matched[:8],
        "signal": sentiment,
        "bullets": bullets,
        "summary": summary,
        "used_llm": used_llm,
        "tokens": tokens,
        "is_general_fallback": is_general_fallback,
        "is_mock": len(all_entries) == 0,
        "latency_ms": latency_ms,
    }
