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

## UI layout

| Tab | Purpose |
|---|---|
| 🔎 **Stock Lookup** | Ticker search → verdict badge → rationale breakdown → Plotly chart (SMA/EMA/Bollinger) → agent trace |
| 📊 **Market Scan** | Runs the pipeline across your watchlist; sortable table of verdicts; click a row to drill into its full card |
| 🧠 **Agent Trace** | Per-query timeline across this session: agent sequence, inputs/outputs, latency, tokens |
| ⚙️ **Settings** | API key, watchlist editor, RSS source editor, risk tolerance slider |

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
  market_data_agent.py        # Technical indicators
  fundamentals_agent.py         # Valuation/growth/leverage metrics
  news_agent.py                  # RSS ingestion + sentiment scoring
  risk_agent.py                    # Volatility/beta/concentration/earnings risk
  recommendation_agent.py           # Synthesis -> verdict + confidence + rationale
  callbacks.py                       # Trace capture helpers
  cache.py                             # SQLite TTL cache for external API calls
ui/
  theme.py               # Shared CSS, hero banner, badges, footer disclaimer
  lookup_panel.py          # Stock Lookup tab
  scan_panel.py              # Market Scan tab
  trace_panel.py                # Agent Trace tab
  settings_panel.py               # Settings tab
data/                              # cache.db created here at runtime (gitignored)
requirements.txt
DEMO_GUIDE.md
```

## Caching & rate limits

External API calls (yfinance price/fundamentals, RSS feeds) are cached in a SQLite
database (`data/cache.db`) with per-source TTLs (prices: 15 min, fundamentals: 1 hour,
news: 30 min) to avoid hammering upstream services on repeated lookups.

---

Built by **Abhinav Rawat** · AI Playground
