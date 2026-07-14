# AITrader.mq5 — Draft Expert Advisor (v0.20)

**Status:** Draft, uncompiled, unbacktested. This is a structural implementation of the risk-management, dual-mode, daily-control, and (v0.20) entry-condition-filter decisions from `Master-Context.md`, not a finished product.

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
- **`PassesRangeFilter()`** ("Range Filter") — implemented as an ADX trend-strength gate. The placeholder signal (EMA crossover) is trend-following, so the useful pairing is skipping choppy/ranging conditions where crossovers whipsaw — the opposite use-case from a range-scalping strategy, chosen to match our actual signal type.
- **`PassesDataFeedSanityCheck()`** ("Information Feed Filter") — rejects trading on stale quotes or an abnormally wide spread.
- **`IsWeekendEntryBlocked()` / `ApplyWeekendCloseAll()`** ("Weekend Protection") — blocks new entries near Friday close / just after Monday open, and force-closes open positions before the weekend. This is a genuinely valuable addition AITrader didn't have before (avoids weekend gap risk) — added because it's straightforward, well-justified pure risk reduction, not because the reference EA had it.

**Deliberately NOT added:**
- The reference EA's **"AI Filter"** toggle. Labeling `GetSignalConfidence()` (already a placeholder stub) as "AI" without a real trained model would repeat the exact kind of unsubstantiated marketing claim already flagged as a legal risk in `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md`. If genuine AI/ML signal scoring is wanted later, that's a real, separate model-training project.
- The reference EA's **3.1 fixed lot size** and any lot-sizing approach resembling "Deposit Acceleration." AITrader's dynamic risk-based sizing (starting at 0.01) was decided carefully over multiple sessions — a large fixed lot contradicts it and was not adopted.
- **The reference account's result is not a target.** The screenshot showed a ~$5,000 account reaching ~$31,600 in roughly 2 days (+533%) — the same order of magnitude as the "$50→$1,000/day" claim already ruled out earlier in this project as unrealistic and a marketing red flag (see `2026-07-14j`). It most likely reflects the oversized 3.1-lot position sizing catching a favorable run, not a repeatable edge, and should not be used as a benchmark.

## What's still a placeholder — do not treat these as final

1. **`GetEntrySignal()` — the actual trading strategy.** This was never specified anywhere in the staging process; every decision so far covered risk management, not what triggers a trade. Currently a simple EMA-crossover + RSI filter, purely so the EA has *something* to backtest structurally. **This is the single biggest remaining gap and probably deserves its own dedicated design session** before this EA is worth taking seriously.
2. **`GetSignalConfidence()` — Safe Mode's 65-75% win-probability filter.** Stubbed to return a fixed value. Needs a real model once real signal logic and backtesting exist (e.g., historical win rate by setup type).
3. **`GetStopDistancePoints()` — stop distance in price terms.** Uses a basic ATR multiple as a placeholder. The full volatility/news-adaptive parameter system described in Document 2 (widening stops, adjusting lot size, etc. around news/volatility) is not implemented — this file only has a simple "skip new entries near high-impact news" reaction, not the full adaptive design.
4. **Equity-based lot-size scaling on winning streaks** is not implemented — only the downside protections (tiered stop-loss, daily loss limit) are here. Gating rules for scaling up were flagged as open in `NextSteps.md`.

## What I have not done (and can't do in this environment)

- **Not compiled.** This needs the MetaEditor that ships with MetaTrader 5 — I don't have that here. Open it in MetaEditor and hit Compile (F7) to check for syntax errors before anything else.
- **Not backtested.** Real backtesting requires MT5's Strategy Tester with real historical tick data for your target symbol(s) via Exness or another broker — also not available in this environment. The only validation this design has had is the Monte Carlo *expectancy* simulation in `../simulations/` (checks the dollar-amount arithmetic, not real market behavior).

## Suggested next steps

1. Open in MetaEditor, compile, fix any syntax errors.
2. Run it in MT5's Strategy Tester on a demo/historical dataset — even with the placeholder signal — to confirm the risk-management plumbing behaves as intended (daily halt triggers correctly, lot sizing produces sane values, tier boundaries work).
3. Treat step 2's results as "does the machinery work," not "is this profitable" — the placeholder signal has no claimed edge.
4. Design the real entry-signal logic (this is genuinely a separate, substantial task) before trusting any backtest numbers.
