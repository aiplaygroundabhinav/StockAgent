"""Unit tests for the News & Sentiment Agent's keyword fallback and ticker
matching (agents/news_agent.py). No network access — feedparser is never
invoked; entries are constructed directly."""

from agents.news_agent import _keyword_sentiment, _matches_ticker


def test_matches_ticker_by_symbol():
    entry = {"title": "AAPL beats earnings expectations", "summary": "Strong quarter."}
    assert _matches_ticker(entry, "AAPL")


def test_matches_ticker_by_company_hint():
    entry = {"title": "Apple unveils new iPhone", "summary": "Record sales expected."}
    assert _matches_ticker(entry, "AAPL", company_hint="Apple")


def test_matches_ticker_false_when_unrelated():
    entry = {"title": "Oil prices rise on supply concerns", "summary": ""}
    assert not _matches_ticker(entry, "AAPL", company_hint="Apple")


def test_keyword_sentiment_bullish():
    entries = [
        {"title": "Stock surges after earnings beat", "summary": "Record profit and strong growth."},
        {"title": "Analysts upgrade rating", "summary": "Bullish outlook on rally."},
    ]
    sentiment, bullets, summary = _keyword_sentiment(entries)
    assert sentiment == "bullish"
    assert bullets


def test_keyword_sentiment_bearish():
    entries = [
        {"title": "Stock plunges after guidance cut", "summary": "Warns of declining sales."},
        {"title": "Downgrade issued amid lawsuit", "summary": "Investigation into losses."},
    ]
    sentiment, bullets, summary = _keyword_sentiment(entries)
    assert sentiment == "bearish"


def test_keyword_sentiment_neutral_with_no_signal_words():
    entries = [{"title": "Company holds annual meeting", "summary": "Routine corporate update."}]
    sentiment, bullets, summary = _keyword_sentiment(entries)
    assert sentiment == "neutral"
