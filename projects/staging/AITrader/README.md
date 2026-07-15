# AITrader — Staging

**Product name (2026-07-14y):** the actual product is now called **FatalibuildersTrader Scalper 1** (renamed from FatalibuildersTrader, 2026-07-14t → 2026-07-14y) — "AITrader" continues as this staging project's internal folder/codename only. See `decisions-learnings/2026-07-14y_scalper1-name-and-aggressive-equity-risk.md`.

**Status:** Staging (Ideation & Preparation)
**Category:** Software — MetaTrader 5 Expert Advisor (licensed trading bot, ~$300 one-time fee; runs on the customer's own funded Exness account)

This folder is being used to plan FatalibuildersTrader before full project initialization. See `Master-Context.md` for the master reference, `Key-Decisions.md` for the decision index, and `NextSteps.md` for the current priority queue.

## Quick Start (Resuming a Session)

Run `agents/open.md`, then say what you want to work on — e.g. "Continue with Document 2" or "Where are we in staging?"

## Current State

- Document 1 (Project Context): In progress — vision, target market, and institutional dependencies drafted for the EA-license model.
- Document 2 (Architecture/Design): In progress — EA/MQL5 architecture, MQL5 Market distribution, dual-mode exit logic, money-management module, and volatility/news-adaptive module (self-contained, economic-calendar-based) drafted. **First MQL5 code draft written** (`Product_Development/MQL5_EA/FatalibuildersTraderScalper1.mq5`) — see below.
- Document 3 (Release Plan): Drafted — 5 epics, 4 milestones. See `NextSteps.md` for what's blocking finalization.

## Risk Model (current)

**Safe Mode:** tiered fixed-dollar stop-loss ($1 below $50 equity, $3 at/above), own profit-lock targets ($1.50 / $3.00 by tier), 65–75% win-probability filter, **5% daily target**, **3% daily loss limit**. **Aggressive Mode (redesigned 2026-07-14y):** risks/targets a **configurable percentage of current equity per trade** (15%/15% default, 1:1) instead of fixed dollars, >50% confidence filter, **20% daily profit target**, and its own, separate **50% daily loss ceiling** (so it isn't silently capped by Safe Mode's 3% limit). Both modes: max 2 concurrent open trades. A Monte Carlo simulation (`Product_Development/simulations/`) confirms the redesigned Safe Mode has positive expectancy across realistic win rates, and a second simulation grounds Aggressive Mode's risk-of-ruin honestly (near-0% at the hoped-for 80% win rate, roughly 2–32% if the real win rate is closer to 50–55%) — **these are math simulations, not real backtests.**

## MQL5 Code Draft

`Product_Development/MQL5_EA/FatalibuildersTraderScalper1.mq5` (v0.80) implements every risk-management/mode/daily-control decision in this document — tiered stop-loss (Safe Mode) or equity-percentage risk (Aggressive Mode), mode-specific profit-lock targets, dynamic lot sizing, dual exit modes, daily controls with the tier-boundary fix, max concurrent trades, first-pass news awareness, entry-condition filters (volume, volatility, range/ADX, data-feed sanity, weekend protection) — plus a **v2 scalping entry signal**: Bollinger Bands + RSI + Stochastic mean-reversion, restricted to forex and metals only (`IsAllowedInstrument()`), replacing the earlier v1 trend+pullback swing entry per founder request for a genuine short-timeframe (M1-M5) scalper. Grounded in published/widely-taught 1-minute scalping methodology (see `decisions-learnings/2026-07-14u_scalping_signal_v2.md`). All inputs use plain-English names/groups, and a manual `SIGNALS_ONLY` operation mode is available alongside `AUTO_TRADE` (2026-07-14x). **Not compiled, not backtested** (no MT5 environment available during staging) — this is a hypothesis to validate, not a proven edge.

## Biggest Open Item

**Nothing has been backtested against real market data.** The entry-signal design gap is resolved (the code has a real, research-grounded scalping strategy instead of a placeholder), but that strategy's actual win rate, drawdown, and profitability on real forex/metals instruments are completely unknown until it's compiled and run through MT5's Strategy Tester.

## Other Open Items

1. Compile the draft in MetaEditor and run it through MT5's Strategy Tester on a forex or metals symbol at M1/M5 — now with a real strategy to actually evaluate, not just plumbing to check.
1a. Decide whether `MaxTradesOpenAtOnce` (2) should also be raised as part of "more aggressive" (2026-07-14v) — deliberately not changed, since it increases total simultaneous risk exposure rather than just opportunity capture. (Aggressive Mode's daily loss limit *was* deliberately raised separately, to 50%, as part of the 2026-07-14y equity-percentage redesign — see below.)
2. Tune `MaxAllowedSpread_Points` per symbol — the 30-point default is sized for forex majors, almost certainly too tight for metals.
3. Verify `IsAllowedInstrument()` against your actual broker's real symbol names — it's a heuristic, not a guaranteed-correct classification.
4. Consider walk-forward testing to guard against curve-fitting the v2 parameters (Bollinger 20/2.0, RSI 30/70, Stochastic 14,1,3/20/80) before trusting results.
5. Validate `GetSignalConfidence()`'s RSI-extremity+low-ADX heuristic against real win-rate outcomes — explainable now, but still not a calibrated probability.
6. Whether the $1/$3 stop-loss and profit-lock targets are fixed in all conditions or a baseline the volatility/news-adaptive module can widen — the draft only skips new entries near high-impact news, it doesn't adapt parameters yet.
7. Reconsidering the $50 stop-loss breakpoint (research shows $3 at exactly $50 equity is 6% risk, above professional norms, and now also exceeds the 3% daily loss limit in one trade).
8. **Risk-management gating rules** for lot-size changes (losing-streak cooldown, drawdown scale-down, max lot cap) — not implemented in the draft.
9. **Volatility/news-adaptive rules** — the draft implements only a simple skip-entries reaction, not the full parameter-adaptation system described in Document 2.
10. Confirm MT5's built-in calendar (used in the draft) as the final economic calendar data source.
11. Check your account's actual leverage setting to understand realistic minimum balance for your intended symbols — the new margin check (2026-07-14w) will log a clear reason if the account can't cover a trade.

**Confirmed guardrail:** "$50 → $1,000 in a day," "$10 → $100 in a day," and later "$10/$100 → $1,000 in 12 hours" are all internal Aggressive Mode narrative framing at best, and were explicitly declined as build targets (2026-07-14v/w) — none are a build spec or realistic (professional day traders consider 1-2% a very good day; if an internal aggressive-mode number is ever needed, 5-20%/day is the research-backed ceiling). Explicitly barred from marketing copy — flagged to the Legal epic with a concrete pre-launch checklist. A "$10 vs $100 starting equity" follow-up turned out to be a legitimate margin-sufficiency question, not a revival of the profit-multiplier target — addressed with a real `OrderCalcMargin()`-based check (2026-07-14w) rather than a hardcoded balance.

**Aggressive Mode's "very very aggressive" equity-percentage risk (2026-07-14y)** is a genuine, deliberately high-risk setting (15% of equity per trade by default) — grounded in a Monte Carlo simulation rather than an engineered number. It should never be marketed with the founder's original "20% chance of blowing $100 at 80% win rate" framing, since the simulation shows that's not actually how the numbers relate (see `2026-07-14y` for the corrected figures) — same guardrail category as the multiplier claims above.

## MQL5 Market Launch Readiness

**Assessed as NOT ready (2026-07-14p).** Blocking: uncompiled, unbacktested, placeholder entry signal. Two submission assets are drafted and ready for when the EA is: `Product_Development/MQL5_EA/mql5_listing_description.md` (full listing text) and `mql5_submission_checklist.md` (every MQL5 requirement, done/not-done, with clear ownership). Logo images (200×200/140×140/60×60) can't be generated in this environment — a precise spec is in the checklist for a designer instead. Login credentials for MT5/MQL5 were declined — no technical capability to operate those systems here, and sharing live trading/marketplace credentials with an AI agent isn't good practice regardless.

See "Open Questions" in `Master-Context.md` for full detail.

## Business Model History

AITrader started as a discretionary asset-management concept (RIA + custodian) and pivoted to a licensed MT5 Expert Advisor model. See `decisions-learnings/2026-07-14_regulatory-path.md` (superseded) and `decisions-learnings/2026-07-14b_ea-license-business-model.md` (current).
