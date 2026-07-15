# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[Dev] Recompile `FatalibuildersTraderSuperScalpers.mq5` in MetaEditor** — renamed from `FatalibuildersTrader.mq5` → `FatalibuildersTraderScalper1.mq5` → `FatalibuildersTraderSuperScalpers.mq5`; v1.00 changes added (2026-07-14x: plain-English input rename/groups + AUTO_TRADE/SIGNALS_ONLY manual mode; 2026-07-14y: "Scalper 1" name + Aggressive Mode's equity-percentage risk/reward and its own daily loss ceiling; 2026-07-14z: narrowed to XAUUSD/GBPUSD, M1 enforced, session-open delay filter; 2026-07-14zz: Safe Mode profit target lowered to $0.30; 2026-07-14zzz: renamed "Super Scalpers," MaxTradesOpenAtOnce raised to 20, signal-stacking formalized), needs a fresh compile check.
1g. **[Dev] Assess net-of-cost profitability at 20-concurrent-trade, per-candle-stacking frequency with the $0.30 target** — this combination has never been simulated or backtested and is a materially different cost/risk profile than anything checked so far. See `2026-07-14zzz`.
1h. **[Human] Consider whether lot sizing or the daily-loss-budget logic should account for many simultaneously-open positions drawing down together** now that up to 20 can be open at once — a single adverse move could hit stop-loss on many slots near-simultaneously. Not addressed yet.
1a. **[Human] Check your account's actual leverage setting** (MT5 account properties) to understand realistic minimum balance for your intended symbols — the new margin check will log a clear reason if the account can't cover a trade, watch the Experts log for this once compiled.
1b. **[Human] Decide if Aggressive Mode's 15%/15% equity-percentage risk/reward default is acceptable to ship**, given the Monte Carlo findings in `2026-07-14y` (near-0% ruin at the hoped-for 80% win rate, but roughly 2-32% ruin probability if the real win rate turns out closer to 50-55%) — this is a real risk-exposure decision, not a formality.
1e. **[Dev] Re-run (or explicitly retire) the Safe Mode Monte Carlo expectancy simulation** (`Product_Development/simulations/safe_mode_expectancy_simulation.py`) — it was built and validated against the old $1.50/$3.00 targets and is now stale against the $0.30 target set in `2026-07-14zz`. Its "positive expectancy across realistic win rates" conclusion should not be treated as still true until re-checked against $0.30/$1/$3.
1f. **[Human] Be aware Safe Mode's break-even win rate is now ~77-91%** (per `2026-07-14zz`) with an unbacktested signal and a 65% confidence floor that was tuned for the old, larger targets — real risk of losing money at this setting until backtested, not a formality to skip past.
1c. **[Human] Verify `AsiaSession_OpenHour_ServerTime`/`LondonSession_OpenHour_ServerTime`/`NewYorkSession_OpenHour_ServerTime` (defaults 0/8/13, assumed ≈ UTC) against your actual broker's server time** — shown at the bottom-right of any MT5 chart — before trusting the session-open delay filter to fire at the right moments. See `2026-07-14z`.
2. **[Dev] Run the draft through MT5's Strategy Tester on XAUUSD and GBPUSD at M1** (both now required, not just recommended) — now with the v2 Bollinger/RSI/Stochastic scalping signal, 20-slot concurrency, and signal-stacking, instead of the retired v1 trend+pullback / 2-slot design. Check actual win rate against the documented break-even bars, not just that the plumbing works.
3a. **[Human] Tune `MaxAllowedSpread_Points` per symbol before testing** — the 30-point default is sized for forex majors and is almost certainly too tight for XAUUSD.
4. **[Human] Verify `IsAllowedInstrument()` against your actual broker's exact XAUUSD/GBPUSD symbol names** (e.g., Exness's naming/suffixes) — it's a heuristic, confirm it correctly allows both symbols and blocks everything else.
5. **[Human] Consider walk-forward testing** the v2 signal (validate on a period the parameters weren't tuned on) to guard against curve-fitting before trusting results.
6. **[Human] Validate `GetSignalConfidence()`'s RSI-extremity+low-ADX heuristic against real win-rate outcomes** — it's explainable now (2026-07-14u) but still not a calibrated probability.
7. **[Human] Apply for MQL5 Market Seller registration early** — review takes up to 10 working days, don't let it gate the launch timeline. See `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md` for the full listing/readiness checklist.
8. **[Human] Decide whether the $1/$3 stop-loss and profit-lock targets are fixed in all conditions, or a baseline the volatility/news-adaptive module can widen** during high-volatility/news windows — the draft code only skips new entries near high-impact news, it doesn't widen/adapt parameters yet.
9. **[Human] Reconsider the $50 stop-loss breakpoint** — research confirms a $3 stop-loss at exactly $50 equity is 6% risk, above the professional 1–2% norm, and now also exceeds the 3% daily loss limit in a single trade. Consider raising the breakpoint or smoothing the transition.
10. **[Human] Define risk-management gating rules for lot-size changes** — losing-streak cooldown? news-window restriction? max lot size cap? Should size scale back down on drawdown, not just up? Not implemented in the draft code.
11. **[AI+Human] Design the full volatility/news-adaptive rules** — specify exactly which parameters change and by how much, per volatility/news-impact level (the draft only implements a simple skip-new-entries reaction).
12. **[Human] Confirm the "text tag / who's the key" fragment** — likely moot now that MQL5 Market handles licensing.
13. ~~Choose economic calendar data source~~ — the draft code defaults to **MT5's built-in calendar** (simplest, no external dependency); confirm this is the final choice.
14. **[Human] Lightweight legal review** — use the concrete pre-launch checklist in `2026-07-14j_realistic-targets-launch-readiness.md` (no multiplier claims, no guarantee language, required risk disclosure, accurate mode descriptions).
15. **[AI+Human] Real backtest + forward-test plan (once the code compiles)** — cover both exit modes, both trading modes (Safe/Aggressive) with their now-distinct risk/reward logic, the daily loss limits (3% Safe / 50% Aggressive) and both daily profit targets (5%/20%), major historical news events, the session-open delay filter's actual effect on trade quality, and net-of-cost profitability at high trade frequency, capped at 2 concurrent trades, **on both XAUUSD and GBPUSD**. Compare real results against the Monte Carlo simulations' assumptions.
16. **[Human] Confirm MQL5 Market commission structure** (registration/review process is now researched — commission % specifically still needs confirming).
17. **[Human] Evaluate Exness IB/affiliate program.**
16. **[Human] Validate/tune the new entry-condition filter thresholds** (volume average period, volatility ratio bounds, ADX threshold, spread/staleness limits, weekend hours) once real backtesting is possible — current values are reasonable defaults, not tuned or tested.
17. **[Human] Produce the 3 logo images** (200×200, 140×140, 60×60) — spec in `Product_Development/MQL5_EA/mql5_submission_checklist.md`; needs a designer or design tool, not producible by AI here.
18. **[Human] Fill in the placeholder fields in `mql5_listing_description.md`** (symbol/timeframe, minimum balance, any performance figures) — only once real backtesting exists. Do not publish with invented numbers.

---

## Resolved

- Distribution channel: **MQL5 Market**.
- Profit-lock exit mechanism: **dual-mode** — outright close OR breakeven-and-run.
- Trade frequency: **as many trades as suitable setups appear**, capped at **2 concurrent open trades**.
- Volatility requirement: must work in **both high- and low-volatility** markets.
- News/analysis integration: **economic-calendar-driven adaptation**, no external TradingView bridge.
- Lot-sizing method: **dynamic, risk-based sizing**.
- Stop-loss: **tiered fixed-dollar** — $1 below $50 equity, $3 at/above.
- Profit-lock target: **$0.50** (reverted from a brief $2–$3 change — see decision history for why).
- Trading modes: **Safe Mode** (own $1.50/$3.00 targets, 65–75% win-probability filter, redesigned 2026-07-14m) and **Aggressive Mode** (opportunistic, no filter, shares tiered stop-loss with $0.50 target).
- Daily profit target: **configurable, halts trading for the day once reached.**
- "$50 → $1,000/day": **confirmed internal stretch-goal framing only** — not a build spec, not for marketing.
- Daily loss limit: **fixed at 3%** of the day's starting equity (surfaced a new tier-boundary interaction to fix — see Priority Queue #2).
- "$50→$1,000" and "$10→$100" per day: **both confirmed internal-only narrative framing**, not build specs, not marketing claims. Research-grounded realistic ceiling for an internal aggressive-mode number, if one is ever needed: **5–20%/day**.
- MQL5 Market listing requirements and pre-launch marketing checklist: **researched and documented** (Seller registration timeline, logo sizes, description rules, technical review process, prohibited-claim checklist).
- Aggressive Mode's internal daily target: **set to 20%** (top of the 5-20% research range), now the default for the daily-profit-target setting in that mode.
- Safe Mode's internal daily target: **set to 5%** (top of the 1-5% research range). Both modes now have concrete daily-target defaults.
- Safe Mode redesigned: **own $1.50 (<$50 tier) / $3.00 (≥$50 tier) profit-lock targets, 65-75% win-probability filter** (down from unrealistic 80-100%), validated via Monte Carlo simulation to have positive expectancy at realistic win rates — **simulation only, real backtest still required**.
- **First MQL5 code draft written:** `Product_Development/MQL5_EA/AITrader.mq5` implements every risk-management/mode/daily-control decision above, including the tier-boundary daily-loss-budget fix. Not compiled, not backtested, and uses a placeholder entry signal (see Priority Queue #1-3).
- **Entry-condition filters added (v0.20):** volume, volatility, range/ADX, data-feed sanity, and weekend protection — researched independently and inspired by (not copied from) a third-party reference EA's settings panel. "AI Filter" branding and the reference EA's fixed 3.1 lot size / short-window results were deliberately not adopted — see `2026-07-14o` for why.
- **MQL5 Market submission assets drafted:** listing description text and a full submission checklist (`Product_Development/MQL5_EA/`) — confirmed the EA is not ready to submit (uncompiled, unbacktested, placeholder signal), and that logo images can't be generated in this environment (no image tool available; spec provided instead).
- **Declined to receive MT5/MQL5 login credentials** — no technical capability to run MetaEditor/MT5 or browse to mql5.com here, and sharing live trading/marketplace credentials with an AI agent isn't good security practice regardless. See `2026-07-14p`.
- ~~Real v1 entry signal designed~~ (trend + pullback) — **superseded, see below.**
- **Step-by-step compile guide written:** `Product_Development/MQL5_EA/compile_guide.md` — exact MetaEditor menu paths, folder locations, and what to do with compile errors. Flags that the founder's earlier reference screenshot was from MT4, not MT5 — `.mq5` files require MT5 specifically.
- **First real compile attempt made (milestone):** founder opened the file in actual MetaEditor. First error was a Market version-format rule (`#property version` needed `X.XX` format, not `0.30`) — fixed to `1.00`. Not a logic bug, a submission-format rule.
- **EA attached to a live chart but placed no trades — real bug found and fixed:** `PassesVolumeFilter()` was comparing the still-forming bar's volume to a completed-bar average, which almost always evaluated false. Fixed to compare the last completed bar. Also added verbose diagnostic logging (`InpVerboseLogging`, on by default) so the Experts log now shows exactly which gate blocks each bar's entry. See `2026-07-14s`.
- **Product renamed:** AITrader → **FatalibuildersTrader**. File is now `FatalibuildersTrader.mq5`; code, logs, and MQL5 listing materials updated. Staging folder name (`projects/staging/AITrader/`) intentionally left as internal codename — see `2026-07-14t` if the whole folder should be renamed too.
- **v2 scalping signal built:** Bollinger Bands + RSI + Stochastic mean-reversion scalping replaces the v1 trend+pullback entry, per founder request for a genuine short-timeframe (M1-M5) scalper. Restricted to forex and metals only via `IsAllowedInstrument()`. **Fixed a real logic conflict**: the Range Filter and confidence heuristic were built for a trend-following signal (wanted high ADX) — flipped both to suit mean-reversion (wants low/contained ADX). See `2026-07-14u`. **Still unbacktested — this is a hypothesis, not a proven strategy.**
- **More aggressive default configuration:** Aggressive Mode now gates on >50% confidence (was no filter at all), the Range Filter's ADX ceiling raised from 25 to 30, default trading mode changed to Aggressive. `InpMaxConcurrentTrades` and `InpDailyLossLimitPct` deliberately left unchanged (separate risk-exposure decision, see Priority Queue). See `2026-07-14v`.
- **Declined "$10→$1,000 in 12 hours" (and revised "$100→$1,000") targets** — mathematically requires ~1,800+ winning trades with zero losses in the window; not achievable without martingale/compounding lot-sizing already ruled out. See `2026-07-14v` chat log context (no separate decision file — declined, not built).
- **Pre-trade margin check added:** founder's real concern behind the "$100 starting equity" ask was whether $10 has enough margin to trade at all (confirmed, not the profit target). Added `HasSufficientMargin()` using MT5's `OrderCalcMargin()` — checks real margin via the API rather than hardcoding an arbitrary minimum balance. See `2026-07-14w`.
- **Every input renamed to plain English + grouped**, and a manual `SIGNALS_ONLY` operation mode added alongside `AUTO_TRADE` (alerts the user with a suggested trade instead of placing it automatically). See `2026-07-14x`.
- **Product renamed to FatalibuildersTrader Scalper 1**, and Aggressive Mode redesigned to risk/target a percentage of current equity per trade (15%/15% default, 1:1) instead of small fixed dollars, with its own 50% daily loss ceiling. A Monte Carlo simulation grounds the founder's "20% chance of blowing $100 at an 80% win rate" framing honestly: ~0% ruin at 80% win rate, roughly 2-32% ruin if the real win rate is closer to 50-55%. Safe Mode untouched. See `2026-07-14y`.
- **Narrowed to XAUUSD and GBPUSD only, M1 chart enforced, session-open delay filter added.** `IsAllowedInstrument()` now only accepts gold and GBPUSD; `OnInit()` refuses to run on any timeframe other than M1; a new filter blocks new trades for 60 minutes (configurable) after each of the Asia/London/New York session opens (server time, needs verifying against the actual broker). See `2026-07-14z`.
- **Safe Mode's profit target lowered to $0.30 (both tiers)**, per direct follow-up instruction confirming the change flagged in `2026-07-14z`. Break-even win rate is now ~77%/~91% by tier — documented honestly in code comments and `2026-07-14zz`, implemented as instructed rather than re-blocked a second time. The existing Safe Mode Monte Carlo simulation is now stale against this new target (Priority Queue 1e).
- **Declined to decompile/combine 10 uploaded third-party `.ex5` files.** Compiled bytecode, confirmed via `file`; no decompiler available, and wouldn't have been used regardless since most uploads were named like commercial competitor products — reverse-engineering another vendor's software into ours is an IP problem, not just a technical one (same stance as `2026-07-14o`). See `2026-07-14zzz`.
- **Renamed to FatalibuildersTrader Super Scalpers; `MaxTradesOpenAtOnce` raised from 2 to 20; signal-stacking formalized.** The 20-concurrent-trade cap was the founder's explicit number, given after being asked directly (a decision this project deliberately deferred through several earlier "more aggressive" rounds). Also formalized a real gap found while answering a "max trades in 5 minutes" question: the entry signal was already re-checked every tick with no per-bar guard, letting multiple trades open off one candle's signal — now an explicit, tunable feature (`AllowMultipleTradesPerSignal_Enabled`/`MaxTradesPerSignal_PerBar`) instead of an undocumented side effect. See `2026-07-14zzz`.

## Superseded (no longer critical path)

- ~~Engage a securities attorney for RIA registration~~ — not needed under the EA-license model.
- ~~Evaluate broker-dealer/custodian partners~~ — not applicable.
- ~~Design a self-hosted license-key system~~ — not needed; MQL5 Market handles licensing.
- ~~Build a TradingView signal bridge~~ — not needed.
- ~~Fixed equity-threshold lot-scaling table~~ — replaced by dynamic risk-based sizing.
- ~~$2–$3 profit-lock target~~ — reverted back to $0.50 per founder decision (2026-07-14h).

---

## How to Use This File

Update this file at the end of every staging session. Mark items done, add new ones as they surface. When all three staging documents are complete and the priority queue is clear, promote via `PROJECT_MEMORY_INIT.md`.
