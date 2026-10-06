"""Unit tests for agents/alerts.py — webhook-on-verdict-change logic.
No real network calls: send_verdict_alert's requests.post is monkeypatched."""

from agents import alerts


def test_should_alert_only_on_upgrade_into_buy():
    assert alerts.should_alert("upgraded", "Buy") is True
    assert alerts.should_alert("upgraded", "Strong Buy") is True
    assert alerts.should_alert("upgraded", "Hold") is False
    assert alerts.should_alert("downgraded", "Buy") is False
    assert alerts.should_alert("unchanged", "Buy") is False
    assert alerts.should_alert("new", "Buy") is False


def test_send_verdict_alert_no_url_returns_false():
    assert alerts.send_verdict_alert("", "AAPL", "Buy", 80, "test") is False


def test_send_verdict_alert_success(monkeypatch):
    class FakeResponse:
        status_code = 200

    def fake_post(url, json, timeout):
        assert url == "https://example.com/hook"
        assert json["ticker"] == "AAPL"
        return FakeResponse()

    monkeypatch.setattr(alerts.requests, "post", fake_post)
    assert alerts.send_verdict_alert("https://example.com/hook", "AAPL", "Buy", 80, "test") is True


def test_send_verdict_alert_handles_failure(monkeypatch):
    def fake_post(url, json, timeout):
        raise ConnectionError("network down")

    monkeypatch.setattr(alerts.requests, "post", fake_post)
    assert alerts.send_verdict_alert("https://example.com/hook", "AAPL", "Buy", 80, "test") is False


def test_send_verdict_alert_non_2xx(monkeypatch):
    class FakeResponse:
        status_code = 500

    monkeypatch.setattr(alerts.requests, "post", lambda url, json, timeout: FakeResponse())
    assert alerts.send_verdict_alert("https://example.com/hook", "AAPL", "Buy", 80, "test") is False
