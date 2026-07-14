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

## Risk Model (current)

Stop-loss is tiered fixed-dollar: **$1 below $50 equity, $3 at/above.** Profit-lock target is **$0.50** (briefly raised to $2–$3, then reverted per founder decision). Two trading modes: **Safe Mode** (only trades 80–100% win-probability setups) and **Aggressive Mode** (opportunistic, no filter). Daily risk controls: configurable daily profit target (halts trading once hit), a **3% daily loss limit**, and max 2 concurrent open trades.

## Biggest Open Items

1. **Daily-loss-limit / stop-loss tier boundary interaction:** at exactly $50 equity, 3% ($1.50) is smaller than the ≥$50 tier's $3 stop-loss — a single losing trade can exceed the whole day's budget. Needs explicit handling before build.
2. **Safe Mode's 80% win-probability floor may not clear the ≥$50 tier's 85.7% break-even requirement.** Needs backtest validation before that tier ships in Safe Mode — otherwise a strategy marketed as "safe" could structurally lose money at that tier even with an 80-85% win rate.

## Other Open Items

1. Whether the $1/$3 stop-loss and $0.50 profit-lock are fixed in all conditions or a baseline the volatility/news-adaptive module can widen.
2. Whether Safe Mode needs its own risk parameters distinct from Aggressive Mode.
3. Reconsidering the $50 stop-loss breakpoint (research shows $3 at exactly $50 equity is 6% risk, above professional norms, and now also exceeds the 3% daily loss limit in one trade).
4. **Risk-management gating rules** for lot-size changes (losing-streak cooldown, drawdown scale-down, max lot cap).
5. **Volatility/news-adaptive rules** — approach is set (economic calendar, no TradingView bridge); specific parameter-adaptation rules are not yet designed.
6. **Economic calendar data source** — MT5 built-in vs. third-party API.

**Confirmed guardrail:** "$50 → $1,000 in a day" and "$10 → $100 in a day" are both internal Aggressive Mode narrative framing only — neither is a build spec or realistic (professional day traders consider 1-2% a very good day; if an internal aggressive-mode number is ever needed, 5-20%/day is the research-backed ceiling). Explicitly barred from marketing copy — flagged to the Legal epic with a concrete pre-launch checklist.

## MQL5 Market Launch Readiness

Researched and documented (`decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md`): Seller registration process (~10 business days, apply early), logo size requirements, listing description content/formatting rules, and MQL5's technical review (automated Strategy Tester + manual programming-error check). Paired with an AITrader-specific compliance checklist covering marketing red flags. See Document 3, Epics 2-3 in `Master-Context.md`.

See "Open Questions" in `Master-Context.md` for full detail.

## Business Model History

AITrader started as a discretionary asset-management concept (RIA + custodian) and pivoted to a licensed MT5 Expert Advisor model. See `decisions-learnings/2026-07-14_regulatory-path.md` (superseded) and `decisions-learnings/2026-07-14b_ea-license-business-model.md` (current).
