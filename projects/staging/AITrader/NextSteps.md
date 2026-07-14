# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[Human] BLOCKING — Define the stop-loss / max-loss-per-trade rule.** Every strategy decision so far (dual-mode exit, dynamic risk-based lot sizing) only covers the winning side. Risk-based position sizing literally cannot be computed without knowing what the losing side of a trade looks like (fixed pips/dollars? ATR-based? something else?). This blocks Epic 1 from really starting.
2. **[Human] Define risk-per-trade percentage** — how much of equity can a single trade risk before the EA sizes up (e.g., 1%, 2%)?
3. **[Human] Define risk-management gating rules for lot-size changes** — losing-streak cooldown? news-window restriction? max lot size cap? Should size scale back down on drawdown, not just up?
4. **[AI+Human] Design the volatility/news-adaptive rules** — read `Product_Development/agents/Software-Development-advisor.md`; specify exactly which parameters change (stop distance, lot size, profit-lock threshold) and by how much, per volatility/news-impact level. Decide whether the highest-impact news tier gets a hard pause instead of just adapted parameters.
5. **[Human] Confirm the "text tag / who's the key" fragment** — likely moot now that MQL5 Market handles licensing, but flag if it meant something else.
6. **[Human] Choose economic calendar data source** — MT5's built-in calendar (simplest, no external dependency) vs. a third-party API.
7. **[Human] Lightweight legal review** — IP/commercial counsel review of MQL5 Market listing terms, ToS, and marketing/disclaimer language; confirm no CTA/investment-adviser registration trigger in target (non-US) jurisdictions.
8. **[AI+Human] Backtest + forward-test plan** — cover both exit modes, both volatility regimes, major historical news events, the risk-based sizing logic, and net-of-cost profitability at high trade frequency.
9. **[Human] Confirm MQL5 Market commission structure and review/approval requirements** directly on their site before finalizing the release timeline.
10. **[Human] Evaluate Exness IB/affiliate program** — secondary revenue stream; decide whether to disclose this to customers.

---

## Resolved

- Distribution channel: **MQL5 Market** (not self-hosted).
- Profit-lock exit mechanism: **dual-mode** — outright close OR move stop to breakeven and let the trade run. Both to be built and backtested.
- Trade frequency philosophy: **as many trades as suitable setups appear**, no artificial cap.
- Volatility requirement: must work in **both high- and low-volatility** markets.
- News/analysis integration scope: **economic-calendar-driven adaptation** folded into the volatility-adaptive module. **No external TradingView bridge.**
- Lot-sizing method: **dynamic, risk-based sizing** — the EA analyzes equity and runs risk management before scaling up, not a fixed manual threshold table. (This resolved the *method*, but surfaced the stop-loss gap — see Priority Queue #1.)

## Superseded (no longer critical path)

- ~~Engage a securities attorney for RIA registration~~ — not needed under the EA-license model.
- ~~Evaluate broker-dealer/custodian partners (Alpaca, IBKR, Tradier)~~ — not applicable; broker is customer-selected (Exness named as primary target).
- ~~Design a self-hosted license-key system~~ — not needed; MQL5 Market handles licensing.
- ~~Build a TradingView signal bridge~~ — not needed; news handling stays self-contained within the EA via an economic calendar.
- ~~Fixed equity-threshold lot-scaling table~~ — replaced by dynamic risk-based sizing.

---

## How to Use This File

Update this file at the end of every staging session. Mark items done, add new ones as they surface. When all three staging documents are complete and the priority queue is clear, promote via `PROJECT_MEMORY_INIT.md`.
