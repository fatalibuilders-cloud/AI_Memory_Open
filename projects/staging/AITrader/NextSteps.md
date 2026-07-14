# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[Human] Quantify the lot-scaling schedule** — "scale lot size once equity reaches target" needs actual numbers: at what equity thresholds does lot size increase, and by how much each step?
2. **[AI+Human] Design the volatility/news-adaptive rules** — read `Product_Development/agents/Software-Development-advisor.md`; specify exactly which parameters change (stop distance, lot size, profit-lock threshold) and by how much, per volatility/news-impact level. Decide whether the very highest-impact news tier gets a hard pause instead of just adapted parameters.
3. **[Human] Confirm the "text tag / who's the key" fragment** — likely moot now that MQL5 Market handles licensing, but flag if it meant something else.
4. **[Human] Choose economic calendar data source** — MT5's built-in calendar (simplest, no external dependency) vs. a third-party API.
5. **[Human] Lightweight legal review** — IP/commercial counsel review of MQL5 Market listing terms, ToS, and marketing/disclaimer language; confirm no CTA/investment-adviser registration trigger in target (non-US) jurisdictions.
6. **[AI+Human] Backtest + forward-test plan** — cover both exit modes (outright close vs. breakeven-and-run), both volatility regimes, major historical news events, and net-of-cost profitability at 0.01 lot / high trade frequency.
7. **[Human] Confirm MQL5 Market commission structure and review/approval requirements** directly on their site before finalizing the release timeline.
8. **[Human] Evaluate Exness IB/affiliate program** — secondary revenue stream (commission per lot traded by referred users); decide whether to disclose this to customers.

---

## Resolved

- Distribution channel: **MQL5 Market** (not self-hosted).
- Profit-lock exit mechanism: **dual-mode** — outright close OR move stop to breakeven and let the trade run. Both to be built and backtested.
- Trade frequency philosophy: **as many trades as suitable setups appear**, no artificial cap.
- Volatility requirement: must work in **both high- and low-volatility** markets.
- News/analysis integration scope: **economic-calendar-driven adaptation** (widen stops, reduce lot size, adjust profit-lock threshold around news events) folded into the volatility-adaptive module. **No external TradingView bridge.**

## Superseded (no longer critical path)

- ~~Engage a securities attorney for RIA registration~~ — not needed under the EA-license model.
- ~~Evaluate broker-dealer/custodian partners (Alpaca, IBKR, Tradier)~~ — not applicable; broker is customer-selected (Exness named as primary target).
- ~~Design a self-hosted license-key system~~ — not needed; MQL5 Market handles licensing.
- ~~Build a TradingView signal bridge~~ — not needed; news handling stays self-contained within the EA via an economic calendar.

---

## How to Use This File

Update this file at the end of every staging session. Mark items done, add new ones as they surface. When all three staging documents are complete and the priority queue is clear, promote via `PROJECT_MEMORY_INIT.md`.
