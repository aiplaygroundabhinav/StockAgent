"""Shared pytest fixtures for StockSense Agent unit tests.

These tests target the pure/deterministic logic inside each specialist
agent (indicator math, signal classification, weighted scoring) without
hitting the network — no yfinance/feedparser/OpenAI calls are made.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make the repo root importable (tests/ sits one level below it) so
# `import agents...` works regardless of the invoking cwd.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def uptrend_df():
    """A clearly bullish, steadily rising synthetic price series, long
    enough (120 bars) for all rolling windows (SMA50, BB20) to be fully
    populated."""
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=120)
    rng = np.random.default_rng(42)
    drift = rng.normal(0.004, 0.004, size=120)  # strong, low-noise uptrend
    close = 100 * np.cumprod(1 + drift)
    high = close * 1.01
    low = close * 0.99
    open_ = close * 0.999
    volume = rng.integers(1_000_000, 5_000_000, size=120)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


@pytest.fixture
def downtrend_df():
    """A clearly bearish, falling synthetic price series. Drift/seed tuned
    to land in a death-cross / below-SMA50 / bearish-MACD state WITHOUT
    hitting extreme RSI oversold territory (which `_classify_trend` treats
    as a bullish "bounce setup" nuance, not a pure downtrend signal)."""
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=120)
    rng = np.random.default_rng(6)
    drift = rng.normal(-0.0015, 0.006, size=120)  # moderate, noisier downtrend
    close = 100 * np.cumprod(1 + drift)
    high = close * 1.01
    low = close * 0.99
    open_ = close * 1.001
    volume = rng.integers(1_000_000, 5_000_000, size=120)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )
