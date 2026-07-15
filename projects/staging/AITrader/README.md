# AITrader — Staging

**Product name (2026-07-14t):** the actual product is now called **FatalibuildersTrader** — "AITrader" continues as this staging project's internal folder/codename only. See `decisions-learnings/2026-07-14t_product-renamed-fatalibuilderstrader.md`.

**Status:** Staging (Ideation & Preparation)
**Category:** Software — MetaTrader 5 Expert Advisor (licensed trading bot, ~$300 one-time fee; runs on the customer's own funded Exness account)

This folder is being used to plan FatalibuildersTrader before full project initialization. See `Master-Context.md` for the master reference, `Key-Decisions.md` for the decision index, and `NextSteps.md` for the current priority queue.

## Quick Start (Resuming a Session)

Run `agents/open.md`, then say what you want to work on — e.g. "Continue with Document 2" or "Where are we in staging?"

## Current State

- Document 1 (Project Context): In progress — vision, target market, and institutional dependencies drafted for the EA-license model.
- Document 2 (Architecture/Design): In progress — EA/MQL5 architecture, MQL5 Market distribution, dual-mode exit logic, money-management module, and volatility/news-adaptive module (self-contained, economic-calendar-based) drafted. **First MQL5 code draft written** (`Product_Development/MQL5_EA/FatalibuildersTrader.mq5`) — see below.
- Document 3 (Release Plan): Drafted — 5 epics, 4 milestones. See `NextSteps.md` for what's blocking finalization.

## Risk Model (current)

Stop-loss is tiered fixed-dollar: **$1 below $50 equity, $3 at/above.** Two trading modes with **distinct** profit-lock targets: **Safe Mode** ($1.50 / $3.00 by tier, 65–75% win-probability filter, **5% daily target**) and **Aggressive Mode** ($0.50 shared target, no filter, **20% daily target**). Daily risk controls: configurable daily profit target, a **3% daily loss limit**, and max 2 concurrent open trades. A Monte Carlo simulation (`Product_Development/simulations/`) confirms the redesigned Safe Mode has positive expectancy across realistic win rates — **this is a math simulation, not a real backtest.**

## MQL5 Code Draft

`Product_Development/MQL5_EA/FatalibuildersTrader.mq5` (v0.30) implements every risk-management/mode/daily-control decision in this document — tiered stop-loss, mode-specific profit-lock targets, dynamic lot sizing, dual exit modes, daily controls with the tier-boundary fix, max concurrent trades, first-pass news awareness, entry-condition filters (volume, volatility, range/ADX, data-feed sanity, weekend protection) — plus, as of v0.30, a **real v1 entry signal**: multi-timeframe trend + pullback momentum entry, replacing the earlier throwaway EMA-crossover placeholder. Grounded in published/widely-taught methodology (see `decisions-learnings/2026-07-14q_signal_design_v1.md`), chosen as a rule-based v1 with ML treated as a v2 aspiration, not a blocker. **Not compiled, not backtested** (no MT5 environment available during staging) — this is a hypothesis to validate, not a proven edge.

## Biggest Open Item

**Nothing has been backtested against real market data.** The entry-signal design gap is resolved (v0.30 has a real, research-grounded strategy instead of a placeholder), but that strategy's actual win rate, drawdown, and profitability on AITrader's target instruments are completely unknown until it's compiled and run through MT5's Strategy Tester.

## Other Open Items

1. Compile the draft in MetaEditor and run it through MT5's Strategy Tester — now with a real strategy to actually evaluate, not just plumbing to check.
2. Consider walk-forward testing to guard against curve-fitting the v1 parameters (200/20 MA periods, RSI 40/60) before trusting results.
3. Validate `GetSignalConfidence()`'s ADX+RSI heuristic against real win-rate outcomes — explainable now, but still not a calibrated probability.
4. Whether the $1/$3 stop-loss and profit-lock targets are fixed in all conditions or a baseline the volatility/news-adaptive module can widen — the draft only skips new entries near high-impact news, it doesn't adapt parameters yet.
5. Reconsidering the $50 stop-loss breakpoint (research shows $3 at exactly $50 equity is 6% risk, above professional norms, and now also exceeds the 3% daily loss limit in one trade).
6. **Risk-management gating rules** for lot-size changes (losing-streak cooldown, drawdown scale-down, max lot cap) — not implemented in the draft.
7. **Volatility/news-adaptive rules** — the draft implements only a simple skip-entries reaction, not the full parameter-adaptation system described in Document 2.
8. Confirm MT5's built-in calendar (used in the draft) as the final economic calendar data source.

**Confirmed guardrail:** "$50 → $1,000 in a day" and "$10 → $100 in a day" are both internal Aggressive Mode narrative framing only — neither is a build spec or realistic (professional day traders consider 1-2% a very good day; if an internal aggressive-mode number is ever needed, 5-20%/day is the research-backed ceiling). Explicitly barred from marketing copy — flagged to the Legal epic with a concrete pre-launch checklist.

## MQL5 Market Launch Readiness

**Assessed as NOT ready (2026-07-14p).** Blocking: uncompiled, unbacktested, placeholder entry signal. Two submission assets are drafted and ready for when the EA is: `Product_Development/MQL5_EA/mql5_listing_description.md` (full listing text) and `mql5_submission_checklist.md` (every MQL5 requirement, done/not-done, with clear ownership). Logo images (200×200/140×140/60×60) can't be generated in this environment — a precise spec is in the checklist for a designer instead. Login credentials for MT5/MQL5 were declined — no technical capability to operate those systems here, and sharing live trading/marketplace credentials with an AI agent isn't good practice regardless.

See "Open Questions" in `Master-Context.md` for full detail.

## Business Model History

AITrader started as a discretionary asset-management concept (RIA + custodian) and pivoted to a licensed MT5 Expert Advisor model. See `decisions-learnings/2026-07-14_regulatory-path.md` (superseded) and `decisions-learnings/2026-07-14b_ea-license-business-model.md` (current).
