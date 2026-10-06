# 📈 StockSense Agent

A multi-agent stock research & recommendation system built with **Streamlit** and
**LangChain**. Give it a ticker (or a whole watchlist) and it orchestrates five
specialist agents — Market Data, Fundamentals, News & Sentiment, Risk, and a final
Recommendation synthesizer — into one clear verdict with a transparent, inspectable
reasoning trail.

> ⚠️ **Not financial advice — for research/education only.** StockSense Agent
> synthesizes public data and LLM reasoning; it can be wrong, stale, or biased.
> Always do your own due diligence before making investment decisions.

A companion app to the [RAGDEMO](https://github.com/aiplaygroundabhinav) and
[PharmacyAgent](https://github.com/aiplaygroundabhinav/PharmacyAgent) training series —
same visual theme (dark navy / teal / purple, Space Mono + DM Sans), same
"show the agent's work" philosophy.

## Multi-agent architecture

Built with LangChain **LCEL** (`RunnableParallel` + chains) — **no LangGraph**.

```
                         ┌─────────────────┐
                 ┌──────▶│ Market Data      │──┐
                 │       └─────────────────┘  │
   Ticker ───▶ Orchestrator (RunnableParallel) │   ┌───────────┐    ┌──────────────────┐
                 │       ┌─────────────────┐  ├──▶│ Risk Agent │──▶│ Recommendation    │──▶ Verdict
                 ├──────▶│ Fundamentals     │──┤   └───────────┘    │ Agent (synthesis) │    + confidence
                 │       └─────────────────┘  │                    └──────────────────┘    + rationale
                 └──────▶│ News & Sentiment │──┘
                         └─────────────────┘
```

- **Orchestrator** (`agents/orchestrator.py`) — routes a ticker to specialists via
  `RunnableParallel`, then runs Risk and Recommendation sequentially, capturing a full
  trace (agent, status, latency, tokens) at every step.
- **Market Data Agent** — yfinance price history; computes SMA(20/50), EMA(12/26),
  RSI(14), MACD, Bollinger Bands; classifies bullish/neutral/bearish trend.
- **Fundamentals Agent** — P/E, EPS growth, revenue growth, debt-to-equity, profit
  margin, sector/industry from yfinance `.info`.
- **News & Sentiment Agent** — ingests a configurable list of RSS feeds (`feedparser`),
  filters for ticker-relevant headlines, and scores sentiment — via an LLM when an
  OpenAI key is configured, or a deterministic keyword scorer otherwise.
- **Risk Agent** — flags volatility, beta, sector concentration (vs. your watchlist),
  and earnings-date proximity.
- **Recommendation Agent** — synthesizes all four signals into **Strong Buy / Buy /
  Hold / Sell / Strong Sell**, a 0–100% confidence score, and a rationale broken down
  per signal source.

Every data agent has a deterministic **mock-data fallback** (clearly labeled 🧪 in the
UI) so the app keeps working end-to-end even without network access or an API key.

## What's new (Phase 1 — Trust & Validation)

- **📒 Track Record tab** — every verdict is persisted to SQLite with full per-agent
  signals and data-source flags; a backtest engine computes forward returns at 1/3/6
  months vs. SPY and buckets hit rate + average excess return by verdict type and
  confidence band. Buckets under 20 samples are shown as "insufficient data" rather
  than a misleadingly precise percentage.
- **🛡️ Mock-data guard** — if any specialist fell back to mock/stale data, the
  Recommendation agent now caps confidence at 40%, forces the verdict to
  "Hold / Unreliable Data", and the UI shows a per-source "data as of" timestamp.
  Mock-data results are automatically excluded from Top Picks.
- **📈 Relative Performance signal** — a new 5th signal compares the stock's own
  1/3/6/12-month return to SPY and to its GICS sector SPDR ETF, feeding directly into
  the Recommendation agent's weighted score.
- **🔀 Optional Finnhub fallback** — set `FINNHUB_API_KEY` in `.env` to cross-check the
  latest price against a second data provider; material disagreement (>5%) is flagged
  as a data-quality signal. Disabled (no-op) until a key is configured.

## What's new (earlier)

- **🏆 Top Picks to Buy** — Market Scan ranks today's Buy/Strong Buy calls by verdict
  strength + confidence and surfaces the top 3 as standout cards.
- **Sector-relative fundamentals** — P/E is judged against a reference sector average
  (Technology vs. Financial Services vs. Energy, etc.), not one fixed number for every
  ticker, with a fallback to absolute thresholds for sectors outside the reference list.
- **Analyst consensus** — pulls Wall Street's `recommendationKey` / mean target price /
  analyst count from yfinance and flags whether it agrees or differs from our
  Fundamentals signal.
- **SPY benchmark overlay + lookback selector** — Stock Lookup lets you pick 1mo–2y
  and shows a normalized "you vs. the market" chart alongside the indicator chart.
- **Accuracy track record** — every verdict is logged with its price-at-call; the
  Settings tab shows directional accuracy once calls are ≥1 day old, overall and
  per-verdict-bucket, so the tool's calibration is visible and honest.
- **Settings persistence** — watchlist, RSS sources, risk tolerance, and webhook URL
  survive app restarts (SQLite-backed). The API key is never persisted to disk.
- **Scan change detection + alerts** — Market Scan flags each ticker as
  new/upgraded/downgraded/unchanged vs. its last scan, and can fire a webhook
  (Slack/Discord-style JSON POST) when a ticker is upgraded into Buy/Strong Buy.
  ⚠️ Scope note: this fires only during a scan you actually run — Streamlit has no
  background scheduler, so this is "alert on change during an on-demand scan," not
  unattended time-based monitoring.

## UI layout

| Tab | Purpose |
|---|---|
| 🔎 **Stock Lookup** | Ticker search + lookback period → verdict badge → rationale breakdown (incl. analyst consensus) → Plotly chart (SMA/EMA/Bollinger) + SPY benchmark overlay → agent trace |
| 📊 **Market Scan** | Runs the pipeline across your watchlist; Top Picks cards; sortable table with per-ticker verdicts + change-vs-last-scan badge; click a row to drill into its full card |
| 🧠 **Agent Trace** | Per-query timeline across this session: agent sequence, inputs/outputs, latency, tokens |
| 📒 **Track Record** | Backtested hit rate & avg excess return vs. SPY at 1/3/6mo horizons, by verdict type and confidence band |
| ⚙️ **Settings** | API key, watchlist editor, RSS source editor, risk tolerance slider, alert webhook URL, accuracy track record dashboard |

## Setup

```bash
git clone https://github.com/aiplaygroundabhinav/StockAgent.git
cd StockAgent
pip install -r requirements.txt
cp .env.example .env   # then add your OPENAI_API_KEY (optional — see below)
streamlit run app.py
```

Open http://localhost:8501.

### Running without an OpenAI key

The app runs fully without `OPENAI_API_KEY` set — the News/Sentiment and
Recommendation agents use deterministic rule-based logic instead of LLM reasoning.
Add a key (via `.env` or the Settings tab) to unlock LLM-powered sentiment summaries
and recommendation rationale.

## Repo structure

```
app.py                      # Streamlit entrypoint — sidebar, tabs, trigger wiring
agents/
  orchestrator.py            # LCEL RunnableParallel pipeline + trace capture
  market_data_agent.py        # Technical indicators + SPY benchmark fetch
  fundamentals_agent.py         # Valuation/growth/leverage + analyst consensus
  news_agent.py                  # RSS ingestion + sentiment scoring
  risk_agent.py                    # Volatility/beta/concentration/earnings risk
  recommendation_agent.py           # Synthesis -> verdict + confidence + rationale
  relative_performance_agent.py      # Stock vs. SPY / sector ETF return comparison
  backtest_engine.py                   # Forward-return backtest for the Track Record tab
  data_providers.py                      # yfinance + optional Finnhub fallback/cross-check
  callbacks.py                       # Trace capture helpers
  cache.py                             # SQLite TTL cache for external API calls
  settings_store.py                      # Persists non-secret settings to disk
  scan_history.py                          # "changed since last scan" detection
  accuracy_log.py                            # Verdict logging + accuracy dashboard
  alerts.py                                    # Webhook POST on verdict upgrade
ui/
  theme.py               # Shared CSS, hero banner, badges, footer disclaimer
  lookup_panel.py          # Stock Lookup tab
  scan_panel.py              # Market Scan tab (incl. Top Picks)
  trace_panel.py                # Agent Trace tab
  track_record_panel.py           # Track Record tab (backtest breakdown)
  settings_panel.py               # Settings tab (incl. accuracy dashboard)
data/                              # cache.db created here at runtime (gitignored)
tests/                              # pytest suite for agent logic (no network)
requirements.txt
requirements-dev.txt
DEMO_GUIDE.md
```

## Caching & rate limits

External API calls (yfinance price/fundamentals, RSS feeds) are cached in a SQLite
database (`data/cache.db`) with per-source TTLs (prices: 15 min, fundamentals: 1 hour,
news: 30 min) to avoid hammering upstream services on repeated lookups.

---

Built by **Abhinav Rawat** · AI Playground
