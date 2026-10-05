# =============================================================================
# StockSense Agent — Market Data Agent
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Pulls OHLCV history via yfinance, computes SMA/EMA/RSI/MACD/Bollinger Bands,
# and classifies a technical trend signal. Falls back to a deterministic
# synthetic price series (seeded by ticker) if yfinance is unreachable or
# returns no data, so the rest of the pipeline keeps working offline.
# =============================================================================

import hashlib
import time

import numpy as np
import pandas as pd

from agents.cache import get_cached, set_cached

CACHE_TTL_SECONDS = 15 * 60  # price data refreshed at most every 15 minutes


def _mock_history(ticker: str, period_days: int = 180) -> pd.DataFrame:
    """Deterministic synthetic OHLCV series so the app still runs end-to-end
    when yfinance/network is unavailable. Seeded by ticker so repeated calls
    for the same symbol are stable within a session."""
    seed = int(hashlib.sha256(ticker.encode()).hexdigest(), 16) % (2 ** 32)
    rng = np.random.default_rng(seed)

    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=period_days)
    drift = rng.normal(0.0003, 0.015, size=period_days)
    base_price = 50 + (seed % 200)
    close = base_price * np.cumprod(1 + drift)
    high = close * (1 + rng.uniform(0.0, 0.015, size=period_days))
    low = close * (1 - rng.uniform(0.0, 0.015, size=period_days))
    open_ = close * (1 + rng.normal(0, 0.005, size=period_days))
    volume = rng.integers(1_000_000, 20_000_000, size=period_days)

    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


def _fetch_history(ticker: str) -> tuple[pd.DataFrame, bool]:
    """Returns (dataframe, is_mock)."""
    try:
        import yfinance as yf

        df = yf.Ticker(ticker).history(period="6mo", interval="1d")
        if df is None or df.empty or "Close" not in df.columns:
            raise ValueError("empty history")
        return df, False
    except Exception:
        return _mock_history(ticker), True


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["SMA20"] = out["Close"].rolling(20, min_periods=1).mean()
    out["SMA50"] = out["Close"].rolling(50, min_periods=1).mean()
    out["EMA12"] = out["Close"].ewm(span=12, adjust=False).mean()
    out["EMA26"] = out["Close"].ewm(span=26, adjust=False).mean()
    out["MACD"] = out["EMA12"] - out["EMA26"]
    out["MACD_signal"] = out["MACD"].ewm(span=9, adjust=False).mean()
    out["RSI14"] = _rsi(out["Close"], 14)
    bb_mid = out["Close"].rolling(20, min_periods=1).mean()
    bb_std = out["Close"].rolling(20, min_periods=1).std().fillna(0)
    out["BB_mid"] = bb_mid
    out["BB_upper"] = bb_mid + 2 * bb_std
    out["BB_lower"] = bb_mid - 2 * bb_std
    return out


def _classify_trend(df: pd.DataFrame) -> tuple[str, list]:
    latest = df.iloc[-1]
    bullets = []
    score = 0

    if latest["Close"] > latest["SMA50"]:
        bullets.append(f"Price (${latest['Close']:.2f}) is above the 50-day SMA (${latest['SMA50']:.2f}) — uptrend intact.")
        score += 1
    else:
        bullets.append(f"Price (${latest['Close']:.2f}) is below the 50-day SMA (${latest['SMA50']:.2f}) — downtrend pressure.")
        score -= 1

    if latest["SMA20"] > latest["SMA50"]:
        bullets.append("20-day SMA is above the 50-day SMA — short-term momentum is positive (golden-cross bias).")
        score += 1
    else:
        bullets.append("20-day SMA is below the 50-day SMA — short-term momentum is negative (death-cross bias).")
        score -= 1

    rsi = latest["RSI14"]
    if rsi >= 70:
        bullets.append(f"RSI(14) is {rsi:.0f} — overbought, risk of a pullback.")
        score -= 1
    elif rsi <= 30:
        bullets.append(f"RSI(14) is {rsi:.0f} — oversold, potential bounce setup.")
        score += 1
    else:
        bullets.append(f"RSI(14) is {rsi:.0f} — neutral momentum zone.")

    if latest["MACD"] > latest["MACD_signal"]:
        bullets.append("MACD is above its signal line — bullish crossover.")
        score += 1
    else:
        bullets.append("MACD is below its signal line — bearish crossover.")
        score -= 1

    if latest["Close"] >= latest["BB_upper"]:
        bullets.append("Price is at/above the upper Bollinger Band — stretched to the upside.")
        score -= 1
    elif latest["Close"] <= latest["BB_lower"]:
        bullets.append("Price is at/below the lower Bollinger Band — stretched to the downside.")
        score += 1

    if score >= 2:
        signal = "bullish"
    elif score <= -2:
        signal = "bearish"
    else:
        signal = "neutral"

    return signal, bullets


def analyze_market_data(ticker: str) -> dict:
    """Returns technical analysis for `ticker`: indicator-enriched dataframe,
    a bullish/neutral/bearish signal, and plain-English bullets."""
    start = time.time()
    ticker = ticker.upper().strip()

    cache_key = f"history::{ticker}"
    cached = get_cached("market_data", cache_key, CACHE_TTL_SECONDS)

    if cached is not None:
        df = pd.DataFrame(cached["data"])
        df.index = pd.to_datetime(cached["index"])
        is_mock = cached["is_mock"]
    else:
        df, is_mock = _fetch_history(ticker)
        set_cached("market_data", cache_key, {
            "data": df.reset_index(drop=True).to_dict(orient="list"),
            "index": [str(i) for i in df.index],
            "is_mock": is_mock,
        })

    enriched = _compute_indicators(df)
    signal, bullets = _classify_trend(enriched)
    latest = enriched.iloc[-1]

    latency_ms = round((time.time() - start) * 1000, 1)

    return {
        "ticker": ticker,
        "df": enriched,
        "signal": signal,
        "bullets": bullets,
        "is_mock": is_mock,
        "latest_price": float(latest["Close"]),
        "latency_ms": latency_ms,
    }
