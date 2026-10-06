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

PERSISTED_KEYS = ("watchlist", "rss_urls", "risk_tolerance", "model", "alert_webhook_url")


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
