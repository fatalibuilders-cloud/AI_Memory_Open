# Decision: News/Market-Analysis Integration Scope Resolved

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

The EA's news/analysis requirement is confirmed as **Option A — news-aware adaptive trading**, not a live TradingView signal bridge (Option B). The founder's intent: the EA should analyze market conditions and news events that affect trading, and actively **adapt** to fluctuations caused by news (rather than either ignoring news entirely or blindly avoiding all trading around it). "The bot should be on hand and be able to handle any news which affects the market."

## What This Means Concretely

- Use an **economic calendar** as the news-detection source (MT5's built-in calendar data, or a third-party economic calendar API/feed) to identify upcoming/active high-impact news events (e.g., central bank rate decisions, NFP, CPI releases).
- Rather than a simple pause-only filter, the EA should **adapt its behavior** around detected news/volatility events — e.g., widen stop distance, reduce lot size, tighten or loosen the profit-lock threshold, or otherwise adjust parameters so it can keep operating through news-driven volatility instead of just standing aside.
- This folds together with the existing "volatility-adaptive logic" requirement (Document 2) — news events are a primary driver of volatility spikes, so the news-awareness module and the volatility-adaptive module should be designed as one coherent system rather than two separate features.
- **No external TradingView bridge is needed.** This removes the previously flagged complexity/risk around building and hosting an external relay service and the MQL5 Market `WebRequest` review friction that option would have introduced.

## Rationale

Confirmed directly by the founder: the goal is for the bot to actively handle/respond to news-driven fluctuations, not to pull in TradingView's own analysis/signals as a separate data source. An economic-calendar-driven, self-contained adaptation system satisfies this without the added external-dependency risk of a TradingView bridge.

## Open Items / Follow-ups

- Choose the specific economic calendar data source (MT5 built-in calendar vs. a third-party API) — MT5's built-in calendar is the simplest, no external dependency.
- Define the specific adaptation rules: which parameters change (stop distance, lot size, profit-lock threshold, or a temporary pause for the highest-impact events only) and by how much, per volatility/news-impact level.
- This should be designed and backtested together with the volatility-adaptive logic already scoped in Document 2 — not as a separate epic.
