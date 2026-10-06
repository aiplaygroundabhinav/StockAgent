"""Unit tests for scan change-detection (agents/scan_history.py)."""

import agents.scan_history as scan_history


def test_classify_change_new_when_no_previous():
    assert scan_history.classify_change(None, "Buy") == "new"


def test_classify_change_upgraded():
    previous = {"verdict": "Hold"}
    assert scan_history.classify_change(previous, "Buy") == "upgraded"


def test_classify_change_downgraded():
    previous = {"verdict": "Buy"}
    assert scan_history.classify_change(previous, "Sell") == "downgraded"


def test_classify_change_unchanged():
    previous = {"verdict": "Buy"}
    assert scan_history.classify_change(previous, "Buy") == "unchanged"


def test_record_and_get_previous_verdict(monkeypatch):
    store = {}
    monkeypatch.setattr(scan_history, "set_cached", lambda ns, k, v: store.__setitem__((ns, k), v))
    monkeypatch.setattr(scan_history, "get_cached", lambda ns, k, ttl: store.get((ns, k)))

    assert scan_history.get_previous_verdict("AAPL") is None
    scan_history.record_scan("AAPL", "Buy", 80, 12345.0)
    prev = scan_history.get_previous_verdict("AAPL")
    assert prev["verdict"] == "Buy"
    assert prev["confidence"] == 80
