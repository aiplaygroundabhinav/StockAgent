"""Unit tests for the accuracy log's judging logic
(agents/accuracy_log.py). Uses an injected in-memory `price_lookup` and
monkeypatches the cache layer so no real SQLite file is touched."""

import time

import agents.accuracy_log as accuracy_log


class _FakeCache:
    def __init__(self):
        self.store = {}

    def get_cached(self, namespace, key, ttl):
        return self.store.get((namespace, key))

    def set_cached(self, namespace, key, value):
        self.store[(namespace, key)] = value


def _patch_cache(monkeypatch):
    fake = _FakeCache()
    monkeypatch.setattr(accuracy_log, "get_cached", fake.get_cached)
    monkeypatch.setattr(accuracy_log, "set_cached", fake.set_cached)
    return fake


def test_log_verdict_appends_entry(monkeypatch):
    _patch_cache(monkeypatch)
    accuracy_log.log_verdict("AAPL", "Buy", 80, 150.0)
    entries = accuracy_log.get_cached(accuracy_log._NAMESPACE, accuracy_log._KEY, 0)
    assert len(entries) == 1
    assert entries[0]["ticker"] == "AAPL"


def test_log_verdict_stores_agent_signals_and_data_flags(monkeypatch):
    _patch_cache(monkeypatch)
    accuracy_log.log_verdict(
        "AAPL", "Buy", 80, 150.0,
        agent_signals={"technical": "bullish", "fundamentals": "neutral"},
        data_flags={"market_data": False, "news": True},
    )
    entries = accuracy_log.get_entries()
    assert entries[0]["agent_signals"]["technical"] == "bullish"
    assert entries[0]["data_flags"]["news"] is True


def test_get_entries_defaults_to_empty_fields(monkeypatch):
    _patch_cache(monkeypatch)
    accuracy_log.log_verdict("AAPL", "Buy", 80, 150.0)
    entries = accuracy_log.get_entries()
    assert entries[0]["agent_signals"] == {}
    assert entries[0]["data_flags"] == {}


def test_judge_buy_correct_on_price_up():
    assert accuracy_log._judge("Buy", 5.0) is True
    assert accuracy_log._judge("Buy", -5.0) is False


def test_judge_sell_correct_on_price_down():
    assert accuracy_log._judge("Sell", -5.0) is True
    assert accuracy_log._judge("Sell", 5.0) is False


def test_judge_hold_correct_within_band():
    assert accuracy_log._judge("Hold", 1.0) is True
    assert accuracy_log._judge("Hold", 10.0) is False


def test_accuracy_summary_pending_when_too_recent(monkeypatch):
    _patch_cache(monkeypatch)
    accuracy_log.log_verdict("AAPL", "Buy", 80, 150.0)
    summary = accuracy_log.get_accuracy_summary(min_age_days=1.0, price_lookup=lambda t: 160.0)
    assert summary["evaluable"] == 0
    assert summary["pending"] == 1


def test_accuracy_summary_evaluates_old_entries(monkeypatch):
    fake = _patch_cache(monkeypatch)
    old_entry = {"ticker": "AAPL", "verdict": "Buy", "confidence": 80, "price_at_call": 100.0,
                 "logged_at": time.time() - 2 * 86400}
    fake.store[(accuracy_log._NAMESPACE, accuracy_log._KEY)] = [old_entry]

    summary = accuracy_log.get_accuracy_summary(min_age_days=1.0, price_lookup=lambda t: 110.0)
    assert summary["evaluable"] == 1
    assert summary["overall_accuracy_pct"] == 100.0
    assert summary["by_verdict"]["Buy"]["count"] == 1
