# =============================================================================
# StockSense Agent — Webhook Alerts
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Fires a webhook POST when a Market Scan detects a verdict upgrade into
# Buy/Strong Buy territory. Scope note: Streamlit has no background
# scheduler, so this is "alert on verdict change during an on-demand scan",
# not true time-based background monitoring.
# =============================================================================

import requests

_ALERT_WORTHY_VERDICTS = {"Buy", "Strong Buy"}
_TIMEOUT_SECONDS = 5


def should_alert(change: str, verdict: str) -> bool:
    return change == "upgraded" and verdict in _ALERT_WORTHY_VERDICTS


def send_verdict_alert(webhook_url: str, ticker: str, verdict: str, confidence: int, summary: str) -> bool:
    """POSTs a simple JSON payload to `webhook_url` (e.g. a Slack/Discord
    incoming webhook or any generic endpoint). Returns True on a 2xx
    response, False otherwise — never raises, since a flaky webhook should
    never break the scan itself."""
    if not webhook_url:
        return False
    payload = {
        "text": f"📈 StockSense alert: {ticker} upgraded to {verdict} ({confidence}% confidence)\n{summary}",
        "ticker": ticker,
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=_TIMEOUT_SECONDS)
        return 200 <= resp.status_code < 300
    except Exception:
        return False
