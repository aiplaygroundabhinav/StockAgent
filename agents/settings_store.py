# =============================================================================
# StockSense Agent — Settings Persistence
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Persists non-secret user settings (watchlist, RSS sources, risk tolerance,
# model, alert webhook) to the same SQLite cache.db used elsewhere, so they
# survive app restarts instead of resetting every session. The OpenAI API
# key is intentionally NEVER persisted here — it stays env/session only.
# =============================================================================

from agents.cache import get_cached, set_cached

_NAMESPACE = "settings"
_KEY = "app_settings"
_NEVER_EXPIRES = 10 ** 12  # effectively permanent for TTL-cache purposes

PERSISTED_KEYS = (
    "watchlist", "rss_urls", "risk_tolerance", "model", "alert_webhook_url",
    "portfolios",
)


def load_settings() -> dict:
    """Returns persisted settings, or {} if nothing has been saved yet."""
    return get_cached(_NAMESPACE, _KEY, _NEVER_EXPIRES) or {}


def save_settings(**kwargs) -> dict:
    """Merges kwargs (restricted to PERSISTED_KEYS) into the persisted
    settings blob and writes it back. Returns the merged dict."""
    current = load_settings()
    for k, v in kwargs.items():
        if k in PERSISTED_KEYS:
            current[k] = v
    set_cached(_NAMESPACE, _KEY, current)
    return current


def combine_portfolios(portfolios: dict, selected_names: list) -> tuple:
    """Merges the ticker lists of the named `portfolios` in `selected_names`
    into one deduplicated, order-preserving ticker list, plus a
    `{ticker: [portfolio_name, ...]}` map recording which selected
    portfolio(s) each ticker came from — so a combined scan can still show
    "this buy idea came from your Growth list" rather than losing the
    source once lists are merged.

    Lets Market Scan surface buy suggestions across several portfolios at
    once instead of being limited to one fixed watchlist."""
    tickers: list = []
    ticker_portfolios: dict = {}
    for name in selected_names:
        for raw_ticker in portfolios.get(name, []):
            ticker = raw_ticker.strip().upper()
            if not ticker:
                continue
            if ticker not in ticker_portfolios:
                tickers.append(ticker)
                ticker_portfolios[ticker] = []
            if name not in ticker_portfolios[ticker]:
                ticker_portfolios[ticker].append(name)
    return tickers, ticker_portfolios
