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

## Risk Model (resolved)

Stop-loss is tiered fixed-dollar: **$1 below $50 equity, $3 at/above.** Profit-lock target is **$2–$3** (raised from an original $0.50–$1 after the founder confirmed keeping the stop-loss and raising the reward instead). Worst-case break-even win rate is now ~50%, down from the earlier ~86%. See `decisions-learnings/2026-07-14f_tiered-stop-loss.md` and `2026-07-14g_profit-target-raised.md`.

## Open Items

1. Whether the $1/$3 stop-loss and $2–$3 profit-lock are fixed in all conditions or a baseline the volatility/news-adaptive module can widen.
2. Exact SL/TP pairing — strict per-tier pairing vs. a dual/configurable $2–$3 range for both tiers.
3. **Risk-management gating rules** for lot-size changes (losing-streak cooldown, drawdown scale-down, max lot cap).
4. **Volatility/news-adaptive rules** — the requirement and overall approach (economic calendar, no TradingView bridge) are set; the specific parameter-adaptation rules are not yet designed.
5. **Economic calendar data source** — MT5 built-in vs. third-party API.

See "Open Questions" in `Master-Context.md` for full detail.

## Business Model History

AITrader started as a discretionary asset-management concept (RIA + custodian) and pivoted to a licensed MT5 Expert Advisor model. See `decisions-learnings/2026-07-14_regulatory-path.md` (superseded) and `decisions-learnings/2026-07-14b_ea-license-business-model.md` (current).
