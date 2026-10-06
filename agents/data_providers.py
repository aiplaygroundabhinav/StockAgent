# =============================================================================
# StockSense Agent — Data Provider Abstraction
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Phase 1 item 5: abstracts "get me a live quote" behind a small provider
# interface so yfinance isn't the only path to a price. yfinance stays the
# primary/default provider everywhere else in the app (no behavior change);
# this module adds one optional free-tier fallback (Finnhub) used only to
# cross-check the latest price and flag material disagreement between
# sources, which the Mock-Data Guard / Top Picks screen treat as a data
# quality signal.
#
# Finnhub is entirely optional: with no FINNHUB_API_KEY configured, every
# function here is a no-op and the app behaves exactly as before.
# =============================================================================

import os
import time
from abc import ABC, abstractmethod
from typing import Optional

from agents.cache import get_cached, set_cached

QUOTE_CACHE_TTL_SECONDS = 5 * 60
DISAGREEMENT_THRESHOLD_PCT = 5.0


class DataProvider(ABC):
    """Minimal provider interface: a source need only answer "what's the
    latest price for this ticker" to participate in cross-checking."""

    name: str = "unknown"

    @abstractmethod
    def get_quote(self, ticker: str) -> Optional[float]:
        """Returns the latest price for `ticker`, or None if unavailable."""
        raise NotImplementedError


class YFinanceProvider(DataProvider):
    name = "yfinance"

    def get_quote(self, ticker: str) -> Optional[float]:
        try:
            import yfinance as yf

            fast = yf.Ticker(ticker).fast_info
            try:
                price = fast["last_price"]
            except (KeyError, TypeError):
                price = getattr(fast, "last_price", None)
            return float(price) if price else None
        except Exception:
            return None


class FinnhubProvider(DataProvider):
    """Free-tier fallback via Finnhub's REST quote endpoint. Requires
    FINNHUB_API_KEY in the environment (.env); otherwise disabled."""

    name = "Finnhub"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY", "")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def get_quote(self, ticker: str) -> Optional[float]:
        if not self.enabled:
            return None
        try:
            import requests

            resp = requests.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": ticker.upper(), "token": self.api_key},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            price = data.get("c")  # "current price"
            return float(price) if price else None
        except Exception:
            return None


def cross_check_price(ticker: str, primary_price: float) -> Optional[dict]:
    """Compares `primary_price` (from yfinance, the primary provider)
    against the Finnhub fallback, caching the fallback quote briefly to
    respect rate limits. Returns None when no fallback provider is
    configured (the common case), otherwise a dict with the disagreement
    percentage and a `flag` set when sources differ by more than
    DISAGREEMENT_THRESHOLD_PCT."""
    ticker = ticker.upper().strip()
    provider = FinnhubProvider()
    if not provider.enabled or not primary_price:
        return None

    cache_key = f"finnhub_quote::{ticker}"
    cached_price = get_cached("data_providers", cache_key, QUOTE_CACHE_TTL_SECONDS)
    if cached_price is None:
        fallback_price = provider.get_quote(ticker)
        if fallback_price is not None:
            set_cached("data_providers", cache_key, fallback_price)
    else:
        fallback_price = cached_price

    if fallback_price is None:
        return None

    disagreement_pct = (primary_price - fallback_price) / fallback_price * 100
    return {
        "fallback_source": provider.name,
        "fallback_price": round(fallback_price, 2),
        "disagreement_pct": round(disagreement_pct, 2),
        "flag": abs(disagreement_pct) > DISAGREEMENT_THRESHOLD_PCT,
        "checked_at": time.time(),
    }
