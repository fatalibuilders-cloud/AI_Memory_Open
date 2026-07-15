# FatalibuildersTrader.mq5 — Draft Expert Advisor (v0.40)

**Status:** Draft, uncompiled, unbacktested. This is a structural implementation of the risk-management, dual-mode, daily-control, entry-condition-filter, and (v0.40) short-timeframe scalping signal decisions from `Master-Context.md`, not a finished product.

### v0.40 — v2 scalping signal, forex/metals restricted (2026-07-14u)

Founder asked for a genuine short-timeframe scalper restricted to forex and metals. `GetEntrySignal()` is replaced entirely — no longer the v1 multi-timeframe trend+pullback swing entry, now a **Bollinger Bands + RSI + Stochastic mean-reversion scalp**: price touching/piercing a Bollinger Band, confirmed by RSI oversold/overbought, triggered by a Stochastic turn back from the extreme (not just a static reading, to avoid catching a falling knife mid-move). This is a widely-documented, widely-taught 1-minute scalping methodology (see `decisions-learnings/2026-07-14u_scalping_signal_v2.md` for the research), designed for short timeframes (M1-M5).

**`IsAllowedInstrument()` restricts the EA to forex and metals only** — it checks MT5's forex calc-mode flag plus XAU/XAG/XPT/XPD in the symbol name, and refuses to initialize (`INIT_FAILED`) on anything else. This is a heuristic, not a guaranteed-correct classification across every broker's symbol-naming convention — verify it behaves correctly on your actual broker before relying on it.

**The Range Filter's logic flipped.** v1 was trend-following and wanted strong trends (high ADX); v2 is mean-reversion and wants the opposite — strong trends are dangerous here because price can "walk the band" straight through a Bollinger extreme without reverting. `PassesRangeFilter()` now rejects entries when ADX is *too high*, not too low. `GetSignalConfidence()` was re-derived to match (rewards RSI extremity + low/contained ADX, not trend strength).

**This is a starting hypothesis, not a proven edge.** The methodology is well-established in general; this specific parameter combination on FatalibuildersTrader's target instruments has never been tested. The prior v1 (trend+pullback) work is preserved in `decisions-learnings/2026-07-14q_signal_design_v1.md` for reference, but is no longer what the code runs.

## What's implemented (matches staging decisions)

- Tiered fixed-dollar stop-loss ($1 < $50 equity, $3 ≥ $50 equity) — 2026-07-14f
- Mode-specific profit-lock targets — Safe Mode $1.50/$3.00 by tier, Aggressive Mode $0.50 — 2026-07-14m, 2026-07-14h
- Dynamic risk-based lot sizing (dollar risk ÷ stop distance, not a fixed table) — 2026-07-14e
- Dual exit modes: outright close, or move to breakeven and let the position run — 2026-07-14
- Daily profit target (5% Safe / 20% Aggressive) and 3% daily loss limit, with automatic halt — 2026-07-14h/i/k/l
- Max 2 concurrent open trades — 2026-07-14h
- **Tier-boundary fix** (`RemainingDailyLossBudget()`): a single trade's risk is capped at whatever remains of the day's loss budget, resolving the interaction flagged 2026-07-14i where a $3 stop-loss could exceed a $1.50 daily budget in one trade
- A first-pass news-awareness check using MT5's native economic calendar (skips new entries within a configurable window of high-impact events for the traded symbol's currencies)

### v0.20 additions — entry-condition filters (2026-07-14o)

Founder shared a screenshot of a third-party commercial EA's settings panel ("ForexEA v2.2") and asked to research and add equivalent elements. **Only the input panel was visible — not that product's source code or actual logic.** These filters are honest, independently-researched, well-established retail-EA concepts inspired by the *names* shown, not a reproduction of that product:

- **`PassesVolumeFilter()`** ("Volume Filter") — only trades when current volume is at/above its recent average; avoids illiquid periods with poor execution and wide spreads.
- **`PassesVolatilityFilter()`** ("Volatility Filter") — rejects both dead markets (ATR far below average — poor risk:reward) and abnormal spikes (ATR far above average — often a news/gap event).
- **`PassesRangeFilter()`** ("Range Filter") — implemented as an ADX gate. **Flipped in v0.40**: the current signal is mean-reversion scalping, which wants ranging/choppy conditions and rejects strong trends (opposite of the v1 trend-following pairing).
- **`PassesDataFeedSanityCheck()`** ("Information Feed Filter") — rejects trading on stale quotes or an abnormally wide spread.
- **`IsWeekendEntryBlocked()` / `ApplyWeekendCloseAll()`** ("Weekend Protection") — blocks new entries near Friday close / just after Monday open, and force-closes open positions before the weekend. This is a genuinely valuable addition FatalibuildersTrader didn't have before (avoids weekend gap risk) — added because it's straightforward, well-justified pure risk reduction, not because the reference EA had it.

**Deliberately NOT added:**
- The reference EA's **"AI Filter"** toggle. Labeling `GetSignalConfidence()` (already a placeholder stub) as "AI" without a real trained model would repeat the exact kind of unsubstantiated marketing claim already flagged as a legal risk in `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md`. If genuine AI/ML signal scoring is wanted later, that's a real, separate model-training project.
- The reference EA's **3.1 fixed lot size** and any lot-sizing approach resembling "Deposit Acceleration." FatalibuildersTrader's dynamic risk-based sizing (starting at 0.01) was decided carefully over multiple sessions — a large fixed lot contradicts it and was not adopted.
- **The reference account's result is not a target.** The screenshot showed a ~$5,000 account reaching ~$31,600 in roughly 2 days (+533%) — the same order of magnitude as the "$50→$1,000/day" claim already ruled out earlier in this project as unrealistic and a marketing red flag (see `2026-07-14j`). It most likely reflects the oversized 3.1-lot position sizing catching a favorable run, not a repeatable edge, and should not be used as a benchmark.

## What's still a placeholder / unvalidated — do not treat these as final

1. **`GetEntrySignal()` — real methodology, unvalidated parameters.** Bollinger Bands (20, 2.0) + RSI (14, 30/70) + Stochastic (14,1,3, 20/80) is a real, documented approach, but this specific parameter combination has never been backtested on real data for these instruments. Treat it as a serious hypothesis to test, not a finished strategy.
2. **`GetSignalConfidence()` — Safe Mode's 65-75% win-probability filter.** A rule-based heuristic (RSI extremity + low ADX), not a hardcoded number, but still not a calibrated probability — needs validation against real win-rate outcomes.
3. **`IsAllowedInstrument()` — heuristic symbol classification.** Checks forex calc-mode + XAU/XAG/XPT/XPD in the name; verify against your actual broker's symbol names, don't assume it's perfect across every broker.
4. **`InpMaxSpreadPoints` (default 30)** is tuned for major forex pairs and is almost certainly too tight for metals — raise it manually for XAUUSD/XAGUSD, there's no auto-detection.
5. **Chart timeframe is not enforced.** M1-M5 is recommended for this scalping signal, but the code will run on whatever timeframe you attach it to.
6. **`GetStopDistancePoints()` — stop distance in price terms.** Uses a basic ATR multiple as a placeholder. The full volatility/news-adaptive parameter system described in Document 2 (widening stops, adjusting lot size, etc. around news/volatility) is not implemented — this file only has a simple "skip new entries near high-impact news" reaction, not the full adaptive design.
7. **Equity-based lot-size scaling on winning streaks** is not implemented — only the downside protections (tiered stop-loss, daily loss limit) are here. Gating rules for scaling up were flagged as open in `NextSteps.md`.

## What I have not done (and can't do in this environment)

- **Not compiled.** This needs the MetaEditor that ships with MetaTrader 5 — I don't have that here. Open it in MetaEditor and hit Compile (F7) to check for syntax errors before anything else.
- **Not backtested.** Real backtesting requires MT5's Strategy Tester with real historical tick data for your target symbol(s) via Exness or another broker — also not available in this environment. The only validation this design has had is (a) the Monte Carlo *expectancy* simulation in `../simulations/` (checks the dollar-amount arithmetic, not real market behavior), and (b) general published research on the *class* of strategy (Bollinger/RSI/Stochastic mean-reversion scalping), not this specific parameter set.

## Suggested next steps

1. Open in MetaEditor, compile, fix any syntax errors.
2. On a forex or metals symbol, at M1 or M5, run it in MT5's Strategy Tester on historical data — with a real strategy hypothesis behind it now — to see actual win rate, drawdown, and profitability, not just plumbing.
3. Compare actual win rate against the break-even bars already documented (Safe Mode: 40%/50%; Aggressive Mode: 66.7%/85.7%) and against the Monte Carlo simulation's assumptions.
4. Tune `InpMaxSpreadPoints` per symbol, especially for metals.
5. Consider walk-forward testing (validate on a period the parameters weren't tuned on) to guard against curve-fitting before trusting results.
6. If results are weak, iterate on this rule-based hypothesis (different band/RSI/Stochastic settings, different instruments) before considering ML-based signal generation — the agreed plan treats ML as a later path, not an immediate fallback.
