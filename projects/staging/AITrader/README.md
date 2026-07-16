# AITrader — Staging

**Product name (2026-07-14zzz):** the actual product is now called **FatalibuildersTrader Super Scalpers** (renamed FatalibuildersTrader → Scalper 1 → Super Scalpers, 2026-07-14t → 2026-07-14y → 2026-07-14zzz) — "AITrader" continues as this staging project's internal folder/codename only. See `decisions-learnings/2026-07-14zzz_super-scalpers-rename-and-max-concurrency-raised.md`.

**Status:** Staging (Ideation & Preparation)
**Category:** Software — MetaTrader 5 Expert Advisor (licensed trading bot, ~$300 one-time fee; runs on the customer's own funded Exness account)

This folder is being used to plan FatalibuildersTrader before full project initialization. See `Master-Context.md` for the master reference, `Key-Decisions.md` for the decision index, and `NextSteps.md` for the current priority queue.

## Quick Start (Resuming a Session)

Run `agents/open.md`, then say what you want to work on — e.g. "Continue with Document 2" or "Where are we in staging?"

## Current State

- Document 1 (Project Context): In progress — vision, target market, and institutional dependencies drafted for the EA-license model.
- Document 2 (Architecture/Design): In progress — EA/MQL5 architecture, MQL5 Market distribution, dual-mode exit logic, money-management module, and volatility/news-adaptive module (self-contained, economic-calendar-based) drafted. **First MQL5 code draft written** (`Product_Development/MQL5_EA/FatalibuildersTraderSuperScalpers.mq5`) — see below.
- Document 3 (Release Plan): Drafted — 5 epics, 4 milestones. See `NextSteps.md` for what's blocking finalization.

## Risk Model (current)

**Safe Mode:** tiered fixed-dollar stop-loss ($1 below $50 equity, $3 at/above), a **$0.30 profit-lock target on both tiers** (lowered from $1.50/$3.00, 2026-07-14zz, per direct founder instruction — reintroduces a ~77%/~91% break-even win-rate requirement the earlier targets were specifically raised to avoid), 65–75% win-probability filter, **5% daily target**, **3% daily loss limit**. **Aggressive Mode (redesigned 2026-07-14y):** risks/targets a **configurable percentage of current equity per trade** (15%/15% default, 1:1) instead of fixed dollars, >50% confidence filter, **20% daily profit target**, and its own, separate **50% daily loss ceiling** (so it isn't silently capped by Safe Mode's 3% limit). **Both modes: max 20 concurrent open trades** (raised from 2, 2026-07-14zzz — a direct multiplier on simultaneous risk exposure, done only after being asked for explicitly), plus a formal per-candle signal-stacking cap (`AllowMultipleTradesPerSignal_Enabled`/`MaxTradesPerSignal_PerBar`) that makes a previously-accidental "multiple trades off one bar's signal" behavior explicit and tunable. A Monte Carlo simulation (`Product_Development/simulations/`) confirms the redesigned Safe Mode has positive expectancy across realistic win rates **at the old $1.50/$3.00 targets — stale against the current $0.30 target, not yet re-run**, and a second simulation grounds Aggressive Mode's risk-of-ruin honestly (near-0% at the hoped-for 80% win rate, roughly 2–32% if the real win rate is closer to 50–55%) — **these are math simulations, not real backtests.**

## MQL5 Code Draft

`Product_Development/MQL5_EA/FatalibuildersTraderSuperScalpers.mq5` (v1.11) implements every risk-management/mode/daily-control decision in this document — tiered stop-loss (Safe Mode) or equity-percentage risk (Aggressive Mode), mode-specific profit-lock targets, dynamic lot sizing, dual exit modes (breakeven-and-run now includes a true trailing stop, 2026-07-15), a maximum trade duration force-close (2026-07-15), daily controls with the tier-boundary fix, high-concurrency trade limits (up to 20 open, with formal per-candle stacking controls), first-pass news awareness, entry-condition filters (volume, volatility, range/ADX, data-feed sanity, weekend protection, session-open delay) — plus a **v2 scalping entry signal**: Bollinger Bands + RSI + Stochastic mean-reversion, now restricted to **XAUUSD and GBPUSD only** (`IsAllowedInstrument()`, narrowed 2026-07-14z from the earlier broader forex/metals heuristic) and **M1 chart enforced** (2026-07-14z). Grounded in published/widely-taught 1-minute scalping methodology (see `decisions-learnings/2026-07-14u_scalping_signal_v2.md`). All inputs use plain-English names/groups, and a manual `SIGNALS_ONLY` operation mode is available alongside `AUTO_TRADE` (2026-07-14x). **Founder ran a real Strategy Tester backtest (2026-07-16) — produced 0 trades, root cause diagnosed as a spread-filter bug (see below), now fixed but not yet re-tested.**

## Biggest Open Item

**A real Strategy Tester backtest has now been run — it produced zero trades, and the cause has been found and fixed, but not yet re-confirmed.** Founder backtested GBPUSD M1 in MT5's Strategy Tester; a shared screenshot/video showed a flat 50-point simulated spread the whole test, which the EA's old 30-point spread filter rejected on every tick before the entry signal was ever evaluated. `MaxAllowedSpread_Points` raised to 60 (2026-07-16) — but the backtest has not been re-run since, so the underlying signal's actual trade count, win rate, and profitability on real XAUUSD/GBPUSD data are still unknown. See `decisions-learnings/2026-07-16_spread-filter-blocking-all-trades.md`.

## Other Open Items

1. **Re-run the GBPUSD M1 Strategy Tester backtest with the updated spread filter (60 points)** and confirm trades now appear — this is the immediate next step, more urgent than anything below. See `2026-07-16`.
1a. **Re-run the Safe Mode Monte Carlo simulation against the $0.30 target** (it's stale against the old $1.50/$3.00 figures) — see `2026-07-14zz`.
1b. **Verify the session-open hours** (`AsiaSession_OpenHour_ServerTime`/`LondonSession_OpenHour_ServerTime`/`NewYorkSession_OpenHour_ServerTime`, defaults 0/8/13 assuming server time ≈ UTC) against your actual broker's server clock — see `2026-07-14z`.
1c. **Assess net-of-cost profitability at 20-concurrent-trade, per-candle-stacking frequency with a $0.30 target** — spread/commission cost per round-trip could dominate the small target at this trade volume; this combination has not been simulated or backtested. See `2026-07-14zzz`.
1d. Consider whether lot sizing or the daily-loss-budget logic needs to account for many simultaneously-open positions drawing down together in one adverse move, now that up to 20 can be open at once — not addressed yet.
2. **Tune `MaxAllowedSpread_Points` against real account data** — raised to 60 (2026-07-16) only to unblock a backtest that showed a flat 50-point tester-simulated spread; confirm this against your actual broker's real GBPUSD/XAUUSD spread once on live/demo quotes, don't treat 60 as validated.
3. Verify `IsAllowedInstrument()` against your actual broker's real XAUUSD/GBPUSD symbol names (e.g. suffixes like `m` or `.a`) — it's a heuristic, not a guaranteed-correct classification.
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

**Declined to decompile/combine 10 uploaded third-party `.ex5` files into this EA — asked twice, declined both times (2026-07-14zzz, 2026-07-15).** `.ex5` is compiled bytecode, not source — confirmed via `file`, no decompiler available, and wouldn't have been used even if one were: most of the uploads were named like commercial competitor products, and reverse-engineering another vendor's compiled software into ours is an IP problem, not just a technical one, consistent with the "AI Filter" precedent from `2026-07-14o`. The founder's actual goal (a more capable/aggressive bot) was pursued both times using only our own source: first via `MaxTradesOpenAtOnce`/signal-stacking (`2026-07-14zzz`), then via a trailing stop and max trade duration (`2026-07-15`) — both independent, widely-documented techniques, not derived from the uploads.

## MQL5 Market Launch Readiness

**Assessed as NOT ready (2026-07-14p).** Blocking: uncompiled, unbacktested, placeholder entry signal. Two submission assets are drafted and ready for when the EA is: `Product_Development/MQL5_EA/mql5_listing_description.md` (full listing text) and `mql5_submission_checklist.md` (every MQL5 requirement, done/not-done, with clear ownership). Logo images (200×200/140×140/60×60) can't be generated in this environment — a precise spec is in the checklist for a designer instead. Login credentials for MT5/MQL5 were declined — no technical capability to operate those systems here, and sharing live trading/marketplace credentials with an AI agent isn't good practice regardless.

See "Open Questions" in `Master-Context.md` for full detail.

## Business Model History

AITrader started as a discretionary asset-management concept (RIA + custodian) and pivoted to a licensed MT5 Expert Advisor model. See `decisions-learnings/2026-07-14_regulatory-path.md` (superseded) and `decisions-learnings/2026-07-14b_ea-license-business-model.md` (current).
