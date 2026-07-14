# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[AI+Human] Resolve the daily-loss-limit / stop-loss tier boundary interaction** — at exactly $50 equity, the 3% daily loss limit ($1.50) is *smaller* than the ≥$50 tier's single-trade stop-loss ($3). A single loss can blow past the whole day's budget. Needs explicit logic (e.g., cap a trade's max loss at the remaining daily budget) rather than assuming the two limits compose cleanly.
2. **[AI+Human] Backtest-validate Safe Mode's win rate at the ≥$50 stop-loss tier specifically** — the stated 80% floor may not clear the 85.7% break-even bar for that tier. If it doesn't hold up, raise the floor for that tier or give it its own target.
3. **[Human] Decide whether Safe Mode needs its own risk parameters** (separate target/stop) distinct from Aggressive Mode, or whether both share the $0.50 target / tiered stop-loss and differ only in trade selectivity.
4. **[Human] Decide whether the $1/$3 stop-loss and $0.50 profit-lock are fixed in all conditions, or a baseline the volatility/news-adaptive module can widen** during high-volatility/news windows.
5. **[Human] Reconsider the $50 stop-loss breakpoint** — research confirms a $3 stop-loss at exactly $50 equity is 6% risk, above the professional 1–2% norm, and now also exceeds the 3% daily loss limit in a single trade. Consider raising the breakpoint or smoothing the transition.
6. **[Human] Define risk-management gating rules for lot-size changes** — losing-streak cooldown? news-window restriction? max lot size cap? Should size scale back down on drawdown, not just up?
7. **[AI+Human] Design the volatility/news-adaptive rules** — specify exactly which parameters change and by how much, per volatility/news-impact level.
8. **[Human] Confirm the "text tag / who's the key" fragment** — likely moot now that MQL5 Market handles licensing.
9. **[Human] Choose economic calendar data source** — MT5's built-in calendar vs. a third-party API.
10. **[Human] Lightweight legal review** — now includes an explicit check that no "$50 to $1,000/day" or similar multiplier claims appear anywhere in public-facing copy (Aggressive Mode's stretch-goal framing is internal only).
11. **[AI+Human] Backtest + forward-test plan** — cover both exit modes, both trading modes (Safe/Aggressive), both stop-loss tiers, the 3% daily loss limit and daily profit target, major historical news events, and net-of-cost profitability at high trade frequency, capped at 2 concurrent trades.
12. **[Human] Confirm MQL5 Market commission structure and review/approval requirements.**
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
- Trading modes: **Safe Mode** (80–100% win-probability filter) and **Aggressive Mode** (opportunistic, no filter).
- Daily profit target: **configurable, halts trading for the day once reached.**
- "$50 → $1,000/day": **confirmed internal stretch-goal framing only** — not a build spec, not for marketing.
- Daily loss limit: **fixed at 3%** of the day's starting equity (surfaced a new tier-boundary interaction to fix — see Priority Queue #1).

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
