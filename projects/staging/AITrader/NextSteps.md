# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[Human/Dev] Write the actual MQL5 EA code (Epic 1) — nothing has been built yet.** Every "backtest" so far is a mathematical simulation of the design's arithmetic (`Product_Development/simulations/`), not a real test against market data. Real validation requires actual code run through MT5's Strategy Tester.
2. **[AI+Human] Resolve the daily-loss-limit / stop-loss tier boundary interaction** — at exactly $50 equity, the 3% daily loss limit ($1.50) is *smaller* than the ≥$50 tier's single-trade stop-loss ($3). A single loss can blow past the whole day's budget. Needs explicit logic (e.g., cap a trade's max loss at the remaining daily budget) rather than assuming the two limits compose cleanly.
3. **[Human] Apply for MQL5 Market Seller registration early** — review takes up to 10 working days, don't let it gate the launch timeline. See `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md` for the full listing/readiness checklist.
4. **[Human] Decide whether the $1/$3 stop-loss and profit-lock targets are fixed in all conditions, or a baseline the volatility/news-adaptive module can widen** during high-volatility/news windows.
5. **[Human] Reconsider the $50 stop-loss breakpoint** — research confirms a $3 stop-loss at exactly $50 equity is 6% risk, above the professional 1–2% norm, and now also exceeds the 3% daily loss limit in a single trade. Consider raising the breakpoint or smoothing the transition.
6. **[Human] Define risk-management gating rules for lot-size changes** — losing-streak cooldown? news-window restriction? max lot size cap? Should size scale back down on drawdown, not just up?
7. **[AI+Human] Design the volatility/news-adaptive rules** — specify exactly which parameters change and by how much, per volatility/news-impact level.
8. **[Human] Confirm the "text tag / who's the key" fragment** — likely moot now that MQL5 Market handles licensing.
9. **[Human] Choose economic calendar data source** — MT5's built-in calendar vs. a third-party API.
10. **[Human] Lightweight legal review** — use the concrete pre-launch checklist in `2026-07-14j_realistic-targets-launch-readiness.md` (no multiplier claims, no guarantee language, required risk disclosure, accurate mode descriptions).
11. **[AI+Human] Real backtest + forward-test plan (once Epic 1 code exists)** — cover both exit modes, both trading modes (Safe/Aggressive) with their now-distinct targets, both stop-loss tiers, the 3% daily loss limit and both daily targets (5%/20%), major historical news events, and net-of-cost profitability at high trade frequency, capped at 2 concurrent trades. Compare real results against the Monte Carlo simulation's assumptions.
12. **[Human] Confirm MQL5 Market commission structure** (registration/review process is now researched — commission % specifically still needs confirming).
13. **[Human] Evaluate Exness IB/affiliate program.**

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
- Safe Mode redesigned: **own $1.50 (<$50 tier) / $3.00 (≥$50 tier) profit-lock targets, 65-75% win-probability filter** (down from unrealistic 80-100%), validated via Monte Carlo simulation to have positive expectancy at realistic win rates — **simulation only, real backtest still required (Priority Queue #1)**.

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
