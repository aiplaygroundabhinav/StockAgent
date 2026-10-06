"""Unit tests for settings persistence (agents/settings_store.py)."""

import agents.settings_store as settings_store


def test_load_settings_empty_when_nothing_saved(monkeypatch):
    monkeypatch.setattr(settings_store, "get_cached", lambda ns, k, ttl: None)
    assert settings_store.load_settings() == {}


def test_save_settings_merges_and_restricts_keys(monkeypatch):
    store = {}
    monkeypatch.setattr(settings_store, "get_cached", lambda ns, k, ttl: store.get((ns, k)))
    monkeypatch.setattr(settings_store, "set_cached", lambda ns, k, v: store.__setitem__((ns, k), v))

    result = settings_store.save_settings(watchlist=["AAPL", "MSFT"], api_key="should-not-persist")
    assert result == {"watchlist": ["AAPL", "MSFT"]}
    assert "api_key" not in result

    result2 = settings_store.save_settings(risk_tolerance=70)
    assert result2["watchlist"] == ["AAPL", "MSFT"]
    assert result2["risk_tolerance"] == 70
