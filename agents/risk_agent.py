# =============================================================================
# StockSense Agent — Risk Agent
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Flags volatility, beta exposure, sector concentration, and earnings-date
# proximity. Consumes the Market Data and Fundamentals agents' outputs
# rather than re-fetching data, so it's cheap to run after them.
# =============================================================================

import time

import numpy as np


def _annualized_volatility(df) -> float:
    returns = df["Close"].pct_change().dropna()
    if returns.empty:
        return 0.0
    return float(returns.std() * np.sqrt(252) * 100)


def _earnings_proximity_days(ticker: str) -> int:
    """Returns days until the next known earnings date, or -1 if unknown."""
    try:
        import yfinance as yf
        import pandas as pd

        cal = yf.Ticker(ticker).get_earnings_dates(limit=4)
        if cal is None or cal.empty:
            return -1
        future = [idx for idx in cal.index if idx.tz_localize(None) >= pd.Timestamp.today()]
        if not future:
            return -1
        days = (min(future).tz_localize(None) - pd.Timestamp.today()).days
        return max(days, 0)
    except Exception:
        return -1


def analyze_risk(ticker: str, market_data: dict, fundamentals: dict,
                  watchlist_sectors: list = None, risk_tolerance: int = 50) -> dict:
    """`risk_tolerance` is 0 (very conservative) - 100 (very aggressive), from
    the Settings tab slider; it shifts how harshly volatility/beta are flagged."""
    start = time.time()
    bullets = []
    score = 0  # positive score => lower risk

    vol = _annualized_volatility(market_data["df"])
    vol_threshold_high = 45 - (risk_tolerance - 50) * 0.2  # more tolerant users get a higher bar
    if vol >= vol_threshold_high:
        bullets.append(f"Annualized volatility is {vol:.0f}% — materially elevated.")
        score -= 1
    elif vol <= 20:
        bullets.append(f"Annualized volatility is {vol:.0f}% — relatively calm.")
        score += 1
    else:
        bullets.append(f"Annualized volatility is {vol:.0f}% — moderate.")

    beta = fundamentals.get("metrics", {}).get("beta")
    if beta is not None:
        if beta > 1.5:
            bullets.append(f"Beta of {beta:.2f} means the stock swings more than the broad market.")
            score -= 1
        elif beta < 0.8:
            bullets.append(f"Beta of {beta:.2f} suggests below-market volatility.")
            score += 1
        else:
            bullets.append(f"Beta of {beta:.2f} tracks close to the broad market.")
    else:
        bullets.append("Beta not available for this ticker.")

    sector = fundamentals.get("metrics", {}).get("sector", "Unknown")
    if watchlist_sectors:
        same_sector = sum(1 for s in watchlist_sectors if s == sector)
        concentration_pct = (same_sector / len(watchlist_sectors)) * 100 if watchlist_sectors else 0
        if concentration_pct >= 40:
            bullets.append(f"{concentration_pct:.0f}% of your watchlist is in {sector} — concentration risk if the sector turns.")
            score -= 1
        else:
            bullets.append(f"Sector exposure ({sector}) is {concentration_pct:.0f}% of the watchlist — reasonably diversified.")

    days_to_earnings = _earnings_proximity_days(ticker)
    if 0 <= days_to_earnings <= 7:
        bullets.append(f"Earnings are in {days_to_earnings} day(s) — expect elevated volatility into the print.")
        score -= 1
    elif days_to_earnings > 7:
        bullets.append(f"Next earnings report is ~{days_to_earnings} days out — no immediate event risk.")
        score += 1
    else:
        bullets.append("Next earnings date is unavailable.")

    if score >= 1:
        level = "Low"
    elif score <= -2:
        level = "High"
    else:
        level = "Medium"

    latency_ms = round((time.time() - start) * 1000, 1)

    return {
        "ticker": ticker,
        "level": level,
        "signal": {"Low": "bullish", "Medium": "neutral", "High": "bearish"}[level],
        "bullets": bullets,
        "volatility_pct": round(vol, 1),
        "days_to_earnings": days_to_earnings,
        "latency_ms": latency_ms,
    }
