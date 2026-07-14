# AITrader — Staging

**Status:** Staging (Ideation & Preparation)
**Category:** Software — MetaTrader 5 Expert Advisor (licensed trading bot, ~$300 one-time fee; runs on the customer's own funded Exness account)

This folder is being used to plan AITrader before full project initialization. See `Master-Context.md` for the master reference, `Key-Decisions.md` for the decision index, and `NextSteps.md` for the current priority queue.

## Quick Start (Resuming a Session)

Run `agents/open.md`, then say what you want to work on — e.g. "Continue with Document 2" or "Where are we in staging?"

## Current State

- Document 1 (Project Context): In progress — vision, target market, and institutional dependencies drafted for the EA-license model.
- Document 2 (Architecture/Design): In progress — EA/MQL5 architecture, MQL5 Market distribution, dual-mode exit logic, and money-management module drafted; volatility-adaptive design and news/TradingView integration scope still open.
- Document 3 (Release Plan): Drafted — 6 epics, 5 milestones. See `NextSteps.md` for what's blocking finalization.

## Biggest Open Items

1. **Lot-scaling schedule** — not yet quantified (equity thresholds + increment size).
2. **News/analysis integration scope** — a simple news filter vs. a full TradingView bridge are very different builds; needs a founder decision.
3. **Volatility-adaptive design** — the requirement is set (must work in high and low volatility), the design (e.g. ATR-based) is not yet specified.

See "Open Questions" in `Master-Context.md` for full detail.

## Business Model History

AITrader started as a discretionary asset-management concept (RIA + custodian) and pivoted to a licensed MT5 Expert Advisor model. See `decisions-learnings/2026-07-14_regulatory-path.md` (superseded) and `decisions-learnings/2026-07-14b_ea-license-business-model.md` (current).
