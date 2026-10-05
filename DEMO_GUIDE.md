# 📈 StockSense Agent — Live Demo Script

A step-by-step script for presenting StockSense Agent to a training audience. Each
step lists **what to click/type**, **what will happen**, and **what to say** so you can
narrate the multi-agent pipeline in real time using the rationale breakdown and the
Agent Trace tab.

> 💡 Tip: Run `streamlit run app.py` and have this guide open side-by-side.

---

## 0. Setup (before attendees join)

1. `cd StockAgent`
2. Activate your venv and `pip install -r requirements.txt` (one-time).
3. Optional: set your OpenAI key — either `.env` (`OPENAI_API_KEY=sk-...`) or paste it
   into the **Settings** tab at runtime. (The demo works without one too — see Section 5.)
4. `streamlit run app.py` → confirm it opens at `http://localhost:8501`.

> Tabs are: **🔎 Stock Lookup**, **📊 Market Scan**, **🧠 Agent Trace**, **⚙️ Settings**.

**Say:** "This is a multi-agent stock research system — not one model answering a
question, but five specialist agents (technical, fundamentals, sentiment, risk, and a
synthesis agent) each doing one job, with every step of their reasoning visible."

---

## 1. Orient the audience to the UI

**Do:** Point to the three regions without clicking anything yet:
- **Sidebar (left):** Ticker search box, "Analyze ticker" button, "Run market scan"
  button, and a collapsible RSS feed editor.
- **Center:** Four tabs — Stock Lookup, Market Scan, Agent Trace, Settings.
- **Footer:** The "Not financial advice" disclaimer — always visible.

**Say:** "Every output you'll see cites which specialist agent produced it — nothing is
a black-box 'the AI says buy'."

---

## 2. Stock Lookup — single ticker, full pipeline

**Do:** In the sidebar, type `AAPL` into the ticker box and click **Analyze ticker**.

**Watch for:**
- A spinner: "Running multi-agent analysis for AAPL..."
- A toast: "✅ Analysis complete for AAPL — <verdict>"
- A large color-coded verdict badge (dark green = Strong Buy ... red = Strong Sell)
  with a confidence percentage.
- Four signal badges: Technical / Fundamentals / Sentiment / Risk, each
  bullish/neutral/bearish.
- A **Rationale Breakdown** section — one card per agent, in plain English.
- A Plotly price chart with SMA 20/50, EMA 12, and Bollinger Bands overlaid.
- An expandable **🔍 View agent trace** — the exact sequence: Market Data →
  Fundamentals → News/Sentiment → Risk → Recommendation, with latency (and tokens,
  if an LLM ran) per step.

**Say:** "Market Data and Fundamentals and News/Sentiment all ran in parallel — that's
a LangChain `RunnableParallel`, not a sequential agent loop — then Risk and the final
Recommendation synthesis ran after, because they depend on the other three."

---

## 3. Market Scan — the whole watchlist at once

**Do:** Click **Run market scan** in the sidebar.

**Watch for:**
- A spinner scanning all 8 default watchlist tickers (AAPL, MSFT, GOOGL, AMZN, NVDA,
  TSLA, META, JPM).
- A sortable table in the **📊 Market Scan** tab: Ticker, Verdict, Confidence, Price,
  and each specialist's signal.

**Do:** Click a row (e.g. NVDA).

**Watch for:** The same full lookup card — badge, rationale, chart, trace — renders
inline right below the table.

**Say:** "This is how you'd triage a whole portfolio or watchlist for opportunities,
then drill into any one name for the full picture."

---

## 4. Agent Trace tab — the aggregate view

**Do:** Click the **🧠 Agent Trace** tab.

**Watch for:** A dropdown of every query run this session (Stock Lookup and Market
Scan alike); selecting one replays its exact agent sequence with latency/token detail.

**Say:** "Every analysis this session is recorded here — useful for debugging which
agent was slow, or which one fell back to mock data."

---

## 5. No API key — rule-based fallback path

**Do:** Open **⚙️ Settings**, clear the API key field (or just never set one), then
re-run **Analyze ticker**.

**Watch for:**
- The pipeline still completes fully.
- The Recommendation trace step detail reads "... (rule-based synthesis — no API
  key)" instead of "(LLM synthesis)".
- News/Sentiment still produces a bullish/neutral/bearish call via its keyword scorer.

**Say:** "Every specialist agent has a deterministic fallback — so this never breaks a
demo because of a missing key or a flaky network call. It degrades gracefully instead
of crashing."

---

## 6. Settings tab — configuration

**Do:** Click **⚙️ Settings**. Walk through:
- **OpenAI API Key** — stored only in session state, never written to disk.
- **Watchlist** — comma-separated tickers used by Market Scan.
- **News Source URLs** — one RSS feed per line, fed into the News agent.
- **Risk Tolerance slider** (0–100) — shifts how aggressively the Risk agent flags
  volatility.

**Say:** "Turning risk tolerance down makes the Risk agent flag volatility and beta
more aggressively — useful for showing how the same data can produce a different Risk
verdict depending on the user's profile."

---

## 7. Wrap-up talking points

- **Specialist agents, one job each** — technical, fundamentals, sentiment, risk —
  synthesized by a dedicated Recommendation agent, not one model doing everything.
- **LCEL, not LangGraph** — `RunnableParallel` for the independent specialists, plain
  Python for the sequential risk/synthesis steps.
- **Full observability** — every agent call is traced with latency and tokens, both
  inline (per-lookup expander) and in the aggregate Agent Trace tab.
- **Graceful degradation** — mock data and rule-based fallbacks mean the demo never
  breaks because of network/API issues.
- **Not financial advice** — this is a research/education tool, not a trading signal.

**Closing line:** "None of this required an agent framework with its own execution
graph — it's LangChain LCEL chains, Python, and a disciplined tracing convention. The
patterns — parallel specialists, a synthesis step, full observability, graceful
fallback — are what you should take away."
