"""Unit tests for the data provider abstraction (agents/data_providers.py).
Finnhub is monkeypatched/disabled so no network calls happen."""

from agents import data_providers


def test_finnhub_disabled_without_api_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    provider = data_providers.FinnhubProvider()
    assert provider.enabled is False
    assert provider.get_quote("AAPL") is None


def test_cross_check_returns_none_without_fallback(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    monkeypatch.setattr(data_providers, "get_cached", lambda *a, **k: None)
    monkeypatch.setattr(data_providers, "set_cached", lambda *a, **k: None)
    assert data_providers.cross_check_price("AAPL", 150.0) is None


def test_cross_check_flags_material_disagreement(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "fake-key")
    monkeypatch.setattr(data_providers, "get_cached", lambda *a, **k: 100.0)  # cached Finnhub quote
    monkeypatch.setattr(data_providers, "set_cached", lambda *a, **k: None)

    result = data_providers.cross_check_price("AAPL", 150.0)  # 50% off cached $100
    assert result is not None
    assert result["flag"] is True
    assert result["fallback_source"] == "Finnhub"


def test_cross_check_no_flag_when_prices_agree(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "fake-key")
    monkeypatch.setattr(data_providers, "get_cached", lambda *a, **k: 150.5)
    monkeypatch.setattr(data_providers, "set_cached", lambda *a, **k: None)

    result = data_providers.cross_check_price("AAPL", 150.0)
    assert result is not None
    assert result["flag"] is False
