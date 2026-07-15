# FatalibuildersTraderScalper1.mq5 — Draft Expert Advisor (v0.95)

**Status:** Draft, uncompiled, unbacktested. This is a structural implementation of the risk-management, dual-mode, daily-control, entry-condition-filter, short-timeframe scalping signal, more-aggressive-configuration, margin-check, plain-English-input, very-aggressive-equity-risk, symbol/session-restriction, and micro-scalp-target decisions from `Master-Context.md`, not a finished product.

### v0.95 — Safe Mode profit target lowered to $0.30 (2026-07-14zz)

Founder confirmed the $0.30 profit target flagged in `2026-07-14z` should ship as-is ("just make it as instructed"). `SafeMode_ProfitTarget_SmallAccount_Dollars` and `SafeMode_ProfitTarget_LargerAccount_Dollars` both changed from $1.50/$3.00 to **$0.30**. This reintroduces the risk:reward problem session 13 (`2026-07-14m`) originally fixed — break-even win rate is now ~77% (small-account tier) / ~91% (larger-account tier), both above the 65% confidence filter still in place. Implemented directly per instruction; documented in full in `decisions-learnings/2026-07-14zz_safe-mode-profit-target-lowered-to-30-cents.md`, including inline code comments at the input declarations. Aggressive Mode (equity-percentage-based) is untouched.

### v0.90 — narrowed to XAUUSD/GBPUSD, M1 enforced, session-open delay filter (2026-07-14z)

Founder asked to trade only XAUUSD and GBPUSD, and to wait one hour after each of the 3 major session opens (Asia, London, New York) before trading, analyzing 1-minute candles. Three changes: **`IsAllowedInstrument()` narrowed** from "any forex or metals symbol" to exactly XAUUSD/GBPUSD (prefix-matched to tolerate broker suffixes); **M1 chart timeframe is now enforced** in `OnInit()` (previously only recommended); and a **new session-open delay filter** (`AvoidSessionOpens_Enabled`, default 60-minute delay after each of 3 configurable session-open hours, all in server time — see the input comments for the important server-time-vs-UTC caveat). **Did not** hardcode a $0.30 profit target as the request's second half implied — Safe Mode's $1.50/$3.00 targets were deliberately raised from a smaller default in session 13 to fix a risk:reward problem, and silently reverting that wasn't done without being asked; the existing profit-target inputs already support entering $0.30 directly if wanted. See `decisions-learnings/2026-07-14z_symbol-restriction-session-timing.md`.

### v0.80 — "Scalper 1" name + Aggressive Mode redesigned around equity-percentage risk (2026-07-14y)

Founder asked to add "Scalper 1" to the product name (file renamed `FatalibuildersTrader.mq5` → `FatalibuildersTraderScalper1.mq5`) and to make Aggressive Mode "very very aggressive," framed as accepting "20% of blowing a $100 [account] with an 80% equity winning rate." Aggressive Mode now risks/targets a **percentage of current equity per trade** (`AggressiveMode_RiskPerTrade_PercentOfEquity` / `AggressiveMode_RewardPerTrade_PercentOfEquity`, both default 15%, 1:1) instead of the old fixed dollar amounts, with its own much higher daily loss ceiling (`StopForDay_AggressiveMode_IfLossReaches_Percent`, default 50%) so the shared 3% Safe Mode daily limit doesn't silently cap every Aggressive trade back down. **Safe Mode is completely untouched.**

A Monte Carlo simulation (`../simulations/aggressive_mode_ruin_probability_simulation.py`) checked the founder's framing honestly rather than building to match it: at the hoped-for 80% win rate, simulated ruin probability (equity falling to $10 or below) is ~0% at any risk level tested — a genuine 80% edge is safe no matter how aggressively it's sized. The real risk shows up only if the actual win rate turns out closer to 50-55% (plausible for an unbacktested strategy): at the chosen 15%/15% setting, ruin probability ranges from about 2% (55% win rate, 50 trades) to about 32% (50% win rate, 100 trades). See `decisions-learnings/2026-07-14y_scalper1-name-and-aggressive-equity-risk.md` for the full numbers, including a correction of an earlier, less rigorous inline estimate made during the same session.

### v0.70 — plain-English inputs + manual (signals-only) mode (2026-07-14x)

Founder asked for input names/descriptions anyone can understand (not just traders), plus a choice between full automation and a manual mode where the bot suggests trades instead of placing them. Every input was renamed from technical `Inp*` names to plain-English names (e.g. `InpStopLossDollarsLowTier` → `MaxLossPerTrade_SmallAccount_Dollars`) and grouped into 9 numbered, plain-language `input group` sections. Added `AutoTrade_Or_SignalsOnly` (`AUTO_TRADE` default, or `SIGNALS_ONLY`): in signals-only mode the bot runs its full pipeline and computes the same trade it would have placed, but instead of calling `trade.Buy()/trade.Sell()` it alerts the user (on-chart popup, on-chart note, and phone push if configured) with the suggested direction, lot size, stop-loss, and take-profit, and lets the user place it manually. See `decisions-learnings/2026-07-14x_plain-english-inputs-and-manual-mode.md`.

### v0.60 — pre-trade margin check (2026-07-14w)

Founder asked to raise "starting equity" from $10 to $100, following a declined request to hit an unrealistic profit target ($10→$1,000 in 12 hours) — clarified this was actually about whether $10 is enough margin to place trades at all, not the target. Real concern, real fix: added `HasSufficientMargin()`, checked before every order via MT5's native `OrderCalcMargin()`. If free margin can't cover the calculated lot size, the EA logs why and skips the trade instead of risking a silent broker rejection. **Not a hardcoded "$100 minimum"** — actual margin requirements depend on account leverage, which this code can't know in advance, so it checks the real number via MT5's API instead of guessing. See `decisions-learnings/2026-07-14w_margin-check-added.md`.

### v0.50 — more aggressive configuration (2026-07-14v)

Founder asked to make the EA more aggressive and auto-trade opportunities the confidence heuristic rates above 50%. Three changes: **Aggressive Mode now gates on confidence** (`InpAggressiveModeMinWinProbabilityPct`, default 50%) instead of having no filter at all; **the Range Filter's ADX ceiling raised from 25 to 30** to admit more setups; **default `InpTradingMode` changed to Aggressive**. Deliberately did NOT raise `InpMaxConcurrentTrades` or `InpDailyLossLimitPct` — those are separate, more consequential risk-exposure decisions, not "take more opportunities" decisions. See `decisions-learnings/2026-07-14v_more-aggressive-config.md` for the full reasoning and what's flagged for follow-up.

### v0.40 — v2 scalping signal, forex/metals restricted (2026-07-14u)

Founder asked for a genuine short-timeframe scalper restricted to forex and metals. `GetEntrySignal()` is replaced entirely — no longer the v1 multi-timeframe trend+pullback swing entry, now a **Bollinger Bands + RSI + Stochastic mean-reversion scalp**: price touching/piercing a Bollinger Band, confirmed by RSI oversold/overbought, triggered by a Stochastic turn back from the extreme (not just a static reading, to avoid catching a falling knife mid-move). This is a widely-documented, widely-taught 1-minute scalping methodology (see `decisions-learnings/2026-07-14u_scalping_signal_v2.md` for the research), designed for short timeframes (M1-M5).

**`IsAllowedInstrument()` restricts the EA to forex and metals only** — it checks MT5's forex calc-mode flag plus XAU/XAG/XPT/XPD in the symbol name, and refuses to initialize (`INIT_FAILED`) on anything else. This is a heuristic, not a guaranteed-correct classification across every broker's symbol-naming convention — verify it behaves correctly on your actual broker before relying on it.

**The Range Filter's logic flipped.** v1 was trend-following and wanted strong trends (high ADX); v2 is mean-reversion and wants the opposite — strong trends are dangerous here because price can "walk the band" straight through a Bollinger extreme without reverting. `PassesRangeFilter()` now rejects entries when ADX is *too high*, not too low. `GetSignalConfidence()` was re-derived to match (rewards RSI extremity + low/contained ADX, not trend strength).

**This is a starting hypothesis, not a proven edge.** The methodology is well-established in general; this specific parameter combination on FatalibuildersTrader's target instruments has never been tested. The prior v1 (trend+pullback) work is preserved in `decisions-learnings/2026-07-14q_signal_design_v1.md` for reference, but is no longer what the code runs.

## What's implemented (matches staging decisions)

- Safe Mode: tiered fixed-dollar stop-loss ($1 < $50 equity, $3 ≥ $50 equity) — 2026-07-14f; flat $0.30 profit-lock target on both tiers (lowered from $1.50/$3.00) — 2026-07-14zz
- Aggressive Mode: equity-percentage risk/reward per trade (15%/15% by default, 1:1), not fixed dollars — 2026-07-14y
- Dynamic risk-based lot sizing (dollar risk ÷ stop distance, not a fixed table) — 2026-07-14e
- Dual exit modes: outright close, or move to breakeven and let the position run — 2026-07-14
- Daily profit target (5% Safe / 20% Aggressive) and mode-specific daily loss limit (3% Safe / 50% Aggressive), with automatic halt — 2026-07-14h/i/k/l/y
- Max 2 concurrent open trades — 2026-07-14h
- **Tier-boundary fix** (`RemainingDailyLossBudget()`): a single trade's risk is capped at whatever remains of the day's loss budget, resolving the interaction flagged 2026-07-14i where a $3 stop-loss could exceed a $1.50 daily budget in one trade
- A first-pass news-awareness check using MT5's native economic calendar (skips new entries within a configurable window of high-impact events for the traded symbol's currencies)
- Restricted to XAUUSD and GBPUSD only, M1 chart enforced, and a session-open delay filter (waits a configurable number of minutes after each of the Asia/London/New York session opens before trading) — 2026-07-14z

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
3. **`IsAllowedInstrument()` — heuristic symbol classification (narrowed 2026-07-14z).** Checks for an XAUUSD or GBPUSD prefix in the symbol name; verify against your actual broker's exact symbol names (e.g. `XAUUSDm`, `GBPUSD.a`), don't assume it's perfect across every broker.
4. **`MaxAllowedSpread_Points` (default 30)** is tuned for major forex pairs and is almost certainly too tight for XAUUSD — raise it manually, there's no auto-detection.
5. **Chart timeframe is now enforced as M1 (2026-07-14z)** — `OnInit()` refuses to run on anything else.
6. **Session-open delay filter (2026-07-14z) default hours are UTC approximations, not your broker's actual server time** — `AsiaSession_OpenHour_ServerTime`/`LondonSession_OpenHour_ServerTime`/`NewYorkSession_OpenHour_ServerTime` need verifying against your broker's real server clock before the "wait 1 hour after session open" behavior fires at the right time.
7. **`GetStopDistancePoints()` — stop distance in price terms.** Uses a basic ATR multiple as a placeholder. The full volatility/news-adaptive parameter system described in Document 2 (widening stops, adjusting lot size, etc. around news/volatility) is not implemented — this file only has a simple "skip new entries near high-impact news" reaction, not the full adaptive design.
8. **Equity-based lot-size scaling on winning streaks** is not implemented — only the downside protections (tiered stop-loss, daily loss limit) are here. Gating rules for scaling up were flagged as open in `NextSteps.md`.

## What I have not done (and can't do in this environment)

- **Not compiled.** This needs the MetaEditor that ships with MetaTrader 5 — I don't have that here. Open it in MetaEditor and hit Compile (F7) to check for syntax errors before anything else.
- **Not backtested.** Real backtesting requires MT5's Strategy Tester with real historical tick data for your target symbol(s) via Exness or another broker — also not available in this environment. The only validation this design has had is (a) the Monte Carlo *expectancy* simulation in `../simulations/` (checks the dollar-amount arithmetic, not real market behavior), and (b) general published research on the *class* of strategy (Bollinger/RSI/Stochastic mean-reversion scalping), not this specific parameter set.

## Suggested next steps

1. Open in MetaEditor, compile, fix any syntax errors.
2. On XAUUSD or GBPUSD, on the M1 chart (both now required), run it in MT5's Strategy Tester on historical data — with a real strategy hypothesis behind it now — to see actual win rate, drawdown, and profitability, not just plumbing.
3. Compare actual win rate against the break-even bars already documented (Safe Mode: 40%/50%; Aggressive Mode: 66.7%/85.7%) and against the Monte Carlo simulation's assumptions.
4. Tune `MaxAllowedSpread_Points` per symbol, especially for XAUUSD. Verify the session-open hours against the actual broker's server time.
5. Consider walk-forward testing (validate on a period the parameters weren't tuned on) to guard against curve-fitting before trusting results.
6. If results are weak, iterate on this rule-based hypothesis (different band/RSI/Stochastic settings, different instruments) before considering ML-based signal generation — the agreed plan treats ML as a later path, not an immediate fallback.
