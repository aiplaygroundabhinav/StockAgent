# =============================================================================
# StockSense Agent — SQLite TTL Cache
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# A tiny on-disk cache so repeated lookups (same ticker, same minute) don't
# re-hit yfinance / RSS feeds and blow through rate limits. Keyed by
# (namespace, key) with a per-namespace TTL. Values are stored as JSON.
# =============================================================================

import json
import os
import sqlite3
import threading
import time

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache.db")
_lock = threading.Lock()


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            namespace TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            stored_at REAL NOT NULL,
            PRIMARY KEY (namespace, key)
        )
        """
    )
    return conn


def get_cached(namespace: str, key: str, ttl_seconds: int):
    """Returns the cached value for (namespace, key) if present and still
    within ttl_seconds, else None."""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT value, stored_at FROM cache WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
        finally:
            conn.close()

    if not row:
        return None
    value_json, stored_at = row
    if time.time() - stored_at > ttl_seconds:
        return None
    try:
        return json.loads(value_json)
    except (TypeError, json.JSONDecodeError):
        return None


def set_cached(namespace: str, key: str, value):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO cache (namespace, key, value, stored_at) VALUES (?, ?, ?, ?)",
                (namespace, key, json.dumps(value, default=str), time.time()),
            )
            conn.commit()
        finally:
            conn.close()


def cached_call(namespace: str, key: str, ttl_seconds: int, fn):
    """Runs fn() and caches the result, or returns the cached result if
    still fresh. fn() must return a JSON-serializable value."""
    cached = get_cached(namespace, key, ttl_seconds)
    if cached is not None:
        return cached, True
    value = fn()
    set_cached(namespace, key, value)
    return value, False
