# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[Human] Quantify the lot-scaling schedule** — "scale lot size once equity reaches target" needs actual numbers: at what equity thresholds does lot size increase, and by how much each step?
2. **[Human] Decide news/analysis integration scope** — (a) simple economic-calendar news filter (standard, low-complexity) vs. (b) full TradingView signal bridge (requires building/hosting an external relay service, plus MQL5 Market `WebRequest` policy considerations). See `decisions-learnings/2026-07-14c_strategy-and-distribution-details.md` for the tradeoff.
3. **[Human] Confirm the "text tag / who's the key" fragment** — likely moot now that MQL5 Market handles licensing, but flag if it meant something else.
4. **[Human] Lightweight legal review** — IP/commercial counsel review of MQL5 Market listing terms, ToS, and marketing/disclaimer language; confirm no CTA/investment-adviser registration trigger in target (non-US) jurisdictions.
5. **[AI+Human] Design volatility-adaptive logic** — read `Product_Development/agents/Software-Development-advisor.md`; specify how entry/stop/target sizing adapts between high- and low-volatility conditions (ATR-based is the standard approach).
6. **[AI+Human] Backtest + forward-test plan** — cover both exit modes (outright close vs. breakeven-and-run), both volatility regimes, and net-of-cost profitability at 0.01 lot / high trade frequency.
7. **[Human] Confirm MQL5 Market commission structure and review/approval requirements** directly on their site before finalizing the release timeline.
8. **[Human] Evaluate Exness IB/affiliate program** — secondary revenue stream (commission per lot traded by referred users); decide whether to disclose this to customers.

---

## Resolved This Session (2026-07-14, follow-up)

- Distribution channel: **MQL5 Market** (not self-hosted).
- Profit-lock exit mechanism: **dual-mode** — outright close OR move stop to breakeven and let the trade run. Both to be built and backtested.
- Trade frequency philosophy: **as many trades as suitable setups appear**, no artificial cap.
- Volatility requirement: must work in **both high- and low-volatility** markets (design still open, see Priority Queue #5).

## Superseded (no longer critical path)

- ~~Engage a securities attorney for RIA registration~~ — not needed under the EA-license model.
- ~~Evaluate broker-dealer/custodian partners (Alpaca, IBKR, Tradier)~~ — not applicable; broker is customer-selected (Exness named as primary target).
- ~~Design a self-hosted license-key system~~ — not needed; MQL5 Market handles licensing.

---

## How to Use This File

Update this file at the end of every staging session. Mark items done, add new ones as they surface. When all three staging documents are complete and the priority queue is clear, promote via `PROJECT_MEMORY_INIT.md`.
