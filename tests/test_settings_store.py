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


def test_save_settings_persists_portfolios(monkeypatch):
    store = {}
    monkeypatch.setattr(settings_store, "get_cached", lambda ns, k, ttl: store.get((ns, k)))
    monkeypatch.setattr(settings_store, "set_cached", lambda ns, k, v: store.__setitem__((ns, k), v))

    portfolios = {"My Watchlist": ["AAPL"], "Growth": ["NVDA", "AMD"]}
    result = settings_store.save_settings(portfolios=portfolios)
    assert result["portfolios"] == portfolios


def test_save_settings_persists_theme(monkeypatch):
    store = {}
    monkeypatch.setattr(settings_store, "get_cached", lambda ns, k, ttl: store.get((ns, k)))
    monkeypatch.setattr(settings_store, "set_cached", lambda ns, k, v: store.__setitem__((ns, k), v))

    result = settings_store.save_settings(theme="light")
    assert result["theme"] == "light"


def test_combine_portfolios_merges_and_dedupes():
    portfolios = {
        "My Watchlist": ["AAPL", "MSFT"],
        "Growth": ["MSFT", "NVDA"],
        "Dividend Income": ["JNJ"],
    }
    tickers, ticker_portfolios = settings_store.combine_portfolios(
        portfolios, ["My Watchlist", "Growth"]
    )
    assert tickers == ["AAPL", "MSFT", "NVDA"]  # order preserved, no duplicate MSFT
    assert ticker_portfolios["MSFT"] == ["My Watchlist", "Growth"]
    assert ticker_portfolios["AAPL"] == ["My Watchlist"]
    assert "JNJ" not in ticker_portfolios  # Dividend Income wasn't selected


def test_combine_portfolios_empty_selection():
    portfolios = {"My Watchlist": ["AAPL"]}
    tickers, ticker_portfolios = settings_store.combine_portfolios(portfolios, [])
    assert tickers == []
    assert ticker_portfolios == {}


def test_combine_portfolios_uppercases_and_strips_tickers():
    portfolios = {"Messy": [" aapl ", "msft"]}
    tickers, ticker_portfolios = settings_store.combine_portfolios(portfolios, ["Messy"])
    assert tickers == ["AAPL", "MSFT"]
