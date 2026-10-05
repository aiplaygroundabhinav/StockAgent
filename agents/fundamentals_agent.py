# =============================================================================
# StockSense Agent — Fundamentals Agent
# Author : Abhinav Rawat · AI Architect · AI Playground
#
# Pulls valuation/growth/leverage metrics from yfinance's `.info` payload.
# yfinance's `info` dict is notoriously inconsistent across tickers/versions,
# so every field is read defensively and the whole thing falls back to a
# deterministic mock profile if the ticker can't be resolved at all.
# =============================================================================

import hashlib
import time

from agents.cache import get_cached, set_cached

CACHE_TTL_SECONDS = 60 * 60  # fundamentals move slowly — cache for an hour


def _mock_fundamentals(ticker: str) -> dict:
    seed = int(hashlib.sha256(ticker.encode()).hexdigest(), 16)
    return {
        "sector": "Technology",
        "industry": "Software — Infrastructure",
        "trailing_pe": 18 + (seed % 25),
        "forward_pe": 16 + (seed % 20),
        "eps_growth": round(((seed % 40) - 15) / 100, 3),
        "revenue_growth": round(((seed % 30) - 5) / 100, 3),
        "debt_to_equity": round((seed % 150) / 100, 2),
        "beta": round(0.6 + (seed % 140) / 100, 2),
        "profit_margin": round(((seed % 35) + 2) / 100, 3),
        "is_mock": True,
    }


def _fetch_fundamentals(ticker: str) -> dict:
    try:
        import yfinance as yf

        info = yf.Ticker(ticker).get_info()
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            # Some tickers resolve with a near-empty info dict — treat as a miss.
            if len(info or {}) < 5:
                raise ValueError("empty info payload")

        data = {
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps_growth": info.get("earningsGrowth"),
            "revenue_growth": info.get("revenueGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
            "beta": info.get("beta"),
            "profit_margin": info.get("profitMargins"),
            "is_mock": False,
        }
        # If literally everything is None, treat this as unusable and fall back.
        if all(v is None for k, v in data.items() if k not in ("sector", "industry", "is_mock")):
            raise ValueError("no usable fundamentals fields")
        return data
    except Exception:
        return _mock_fundamentals(ticker)


def _classify_fundamentals(data: dict) -> tuple[str, list]:
    bullets = []
    score = 0

    pe = data.get("trailing_pe")
    if pe is not None:
        if pe < 20:
            bullets.append(f"Trailing P/E of {pe:.1f} is reasonable/undemanding for the sector.")
            score += 1
        elif pe > 40:
            bullets.append(f"Trailing P/E of {pe:.1f} is rich — priced for strong continued growth.")
            score -= 1
        else:
            bullets.append(f"Trailing P/E of {pe:.1f} is in a moderate, market-average range.")
    else:
        bullets.append("Trailing P/E not available for this ticker.")

    eps_growth = data.get("eps_growth")
    if eps_growth is not None:
        pct = eps_growth * 100
        if pct > 10:
            bullets.append(f"EPS growth of {pct:.1f}% is strong.")
            score += 1
        elif pct < 0:
            bullets.append(f"EPS growth of {pct:.1f}% is negative — earnings are contracting.")
            score -= 1
        else:
            bullets.append(f"EPS growth of {pct:.1f}% is modest.")

    rev_growth = data.get("revenue_growth")
    if rev_growth is not None:
        pct = rev_growth * 100
        if pct > 10:
            bullets.append(f"Revenue growth of {pct:.1f}% shows healthy top-line expansion.")
            score += 1
        elif pct < 0:
            bullets.append(f"Revenue growth of {pct:.1f}% — revenue is shrinking year over year.")
            score -= 1
        else:
            bullets.append(f"Revenue growth of {pct:.1f}% is steady but unspectacular.")

    dte = data.get("debt_to_equity")
    if dte is not None:
        if dte > 150:
            bullets.append(f"Debt-to-equity of {dte:.0f}% is elevated — balance-sheet leverage risk.")
            score -= 1
        elif dte < 50:
            bullets.append(f"Debt-to-equity of {dte:.0f}% is conservative.")
            score += 1
        else:
            bullets.append(f"Debt-to-equity of {dte:.0f}% is within a normal range.")

    margin = data.get("profit_margin")
    if margin is not None:
        pct = margin * 100
        if pct > 15:
            bullets.append(f"Profit margin of {pct:.1f}% reflects healthy pricing power.")
            score += 1
        elif pct < 0:
            bullets.append(f"Profit margin of {pct:.1f}% — the company is currently unprofitable.")
            score -= 1

    if score >= 2:
        signal = "bullish"
    elif score <= -2:
        signal = "bearish"
    else:
        signal = "neutral"

    bullets.append(f"Sector: {data.get('sector', 'Unknown')} · Industry: {data.get('industry', 'Unknown')}")
    return signal, bullets


def analyze_fundamentals(ticker: str) -> dict:
    start = time.time()
    ticker = ticker.upper().strip()

    cache_key = f"fundamentals::{ticker}"
    data = get_cached("fundamentals", cache_key, CACHE_TTL_SECONDS)
    if data is None:
        data = _fetch_fundamentals(ticker)
        set_cached("fundamentals", cache_key, data)

    signal, bullets = _classify_fundamentals(data)
    latency_ms = round((time.time() - start) * 1000, 1)

    return {
        "ticker": ticker,
        "metrics": data,
        "signal": signal,
        "bullets": bullets,
        "is_mock": data.get("is_mock", False),
        "latency_ms": latency_ms,
    }
