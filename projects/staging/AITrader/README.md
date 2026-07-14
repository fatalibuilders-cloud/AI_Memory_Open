# AITrader — Staging

**Status:** Staging (Ideation & Preparation)
**Category:** Software — MetaTrader 5 Expert Advisor (licensed trading bot, ~$300 one-time fee; runs on the customer's own funded Exness account)

This folder is being used to plan AITrader before full project initialization. See `Master-Context.md` for the master reference, `Key-Decisions.md` for the decision index, and `NextSteps.md` for the current priority queue.

## Quick Start (Resuming a Session)

Run `agents/open.md`, then say what you want to work on — e.g. "Continue with Document 2" or "Where are we in staging?"

## Current State

- Document 1 (Project Context): In progress — vision, target market, and institutional dependencies drafted for the EA-license model.
- Document 2 (Architecture/Design): In progress — EA/MQL5 architecture, MQL5 Market distribution, dual-mode exit logic, money-management module, and volatility/news-adaptive module (self-contained, economic-calendar-based) drafted.
- Document 3 (Release Plan): Drafted — 5 epics, 4 milestones. See `NextSteps.md` for what's blocking finalization.

## Biggest Open Item (blocking, high severity)

**Stop-loss is now defined ($1 below $50 equity, $3 at/above), but it creates a risk:reward problem that needs founder sign-off before build.** The ≥$50 tier risks $3 to make only $0.50–$1 — a 3:1 to 6:1 ratio against the trade, needing a 75–86% win rate just to break even before spread/commission. Either this is intentional (and there's a reason it's expected to work), or the profit-lock target needs to scale up with the stop-loss tier too. See `decisions-learnings/2026-07-14f_tiered-stop-loss.md`.

## Other Open Items

1. Whether the $1/$3 stop-loss is fixed in all conditions or a baseline the volatility/news-adaptive module can widen.
2. **Risk-management gating rules** for lot-size changes (losing-streak cooldown, drawdown scale-down, max lot cap).
3. **Volatility/news-adaptive rules** — the requirement and overall approach (economic calendar, no TradingView bridge) are set; the specific parameter-adaptation rules are not yet designed.
4. **Economic calendar data source** — MT5 built-in vs. third-party API.

See "Open Questions" in `Master-Context.md` for full detail.

## Business Model History

AITrader started as a discretionary asset-management concept (RIA + custodian) and pivoted to a licensed MT5 Expert Advisor model. See `decisions-learnings/2026-07-14_regulatory-path.md` (superseded) and `decisions-learnings/2026-07-14b_ea-license-business-model.md` (current).
