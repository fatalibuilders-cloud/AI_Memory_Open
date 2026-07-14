# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[Human] Decide whether the $1/$3 stop-loss and $2–$3 profit-lock are fixed figures in all conditions, or a baseline the volatility/news-adaptive module can widen** during high-volatility/news windows (tight fixed-dollar stops are easily triggered by normal noise and don't account for slippage in fast markets).
2. **[Human] Confirm exact SL/TP pairing** — strictly $1 SL/$2 TP and $3 SL/$3 TP, or does each tier get the full $2–$3 TP range as a dual/configurable option?
3. **[Human] Define risk-management gating rules for lot-size changes** — losing-streak cooldown? news-window restriction? max lot size cap? Should size scale back down on drawdown, not just up?
4. **[AI+Human] Design the volatility/news-adaptive rules** — read `Product_Development/agents/Software-Development-advisor.md`; specify exactly which parameters change (stop distance, lot size, profit-lock threshold) and by how much, per volatility/news-impact level.
5. **[Human] Confirm the "text tag / who's the key" fragment** — likely moot now that MQL5 Market handles licensing, but flag if it meant something else.
6. **[Human] Choose economic calendar data source** — MT5's built-in calendar (simplest, no external dependency) vs. a third-party API.
7. **[Human] Lightweight legal review** — IP/commercial counsel review of MQL5 Market listing terms, ToS, and marketing/disclaimer language; confirm no CTA/investment-adviser registration trigger in target (non-US) jurisdictions.
8. **[AI+Human] Backtest + forward-test plan** — cover both exit modes, both volatility regimes, major historical news events, the risk-based sizing logic (including explicit slippage modeling), and net-of-cost profitability at high trade frequency. Validate the ~50% break-even win-rate bar against actual backtest results.
9. **[Human] Confirm MQL5 Market commission structure and review/approval requirements** directly on their site before finalizing the release timeline.
10. **[Human] Evaluate Exness IB/affiliate program** — secondary revenue stream; decide whether to disclose this to customers.

---

## Resolved

- Distribution channel: **MQL5 Market** (not self-hosted).
- Profit-lock exit mechanism: **dual-mode** — outright close OR move stop to breakeven and let the trade run. Both to be built and backtested.
- Trade frequency philosophy: **as many trades as suitable setups appear**, no artificial cap.
- Volatility requirement: must work in **both high- and low-volatility** markets.
- News/analysis integration scope: **economic-calendar-driven adaptation** folded into the volatility-adaptive module. **No external TradingView bridge.**
- Lot-sizing method: **dynamic, risk-based sizing** — the EA analyzes equity and runs risk management before scaling up.
- Stop-loss: **tiered fixed-dollar** — $1 below $50 equity, $3 at/above $50 equity.
- Profit-lock target: **raised to $2–$3** (from the original $0.50–$1) to fix the risk:reward ratio at the ≥$50 tier — worst case is now ~50% win rate to break even instead of ~86%.

## Superseded (no longer critical path)

- ~~Engage a securities attorney for RIA registration~~ — not needed under the EA-license model.
- ~~Evaluate broker-dealer/custodian partners (Alpaca, IBKR, Tradier)~~ — not applicable; broker is customer-selected (Exness named as primary target).
- ~~Design a self-hosted license-key system~~ — not needed; MQL5 Market handles licensing.
- ~~Build a TradingView signal bridge~~ — not needed; news handling stays self-contained within the EA via an economic calendar.
- ~~Fixed equity-threshold lot-scaling table~~ — replaced by dynamic risk-based sizing (now grounded in the tiered stop-loss above).

---

## How to Use This File

Update this file at the end of every staging session. Mark items done, add new ones as they surface. When all three staging documents are complete and the priority queue is clear, promote via `PROJECT_MEMORY_INIT.md`.
