# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[Human] Clarify garbled items from voice session** — several points didn't transcribe clearly: (a) "text tag / who's the key", (b) "piece of tape onto the...", (c) "what happens if you put a starfish? / the AI trade is successful", (d) exact profit-lock mechanism (fixed take-profit order vs. trailing/breakeven-lock once $0.50-$1 floating profit is reached, and whether that's flat-dollar or scales with lot size). Nothing in Document 1/2's strategy section should be treated as final until these are resolved.
2. **[Human] Lightweight legal review** (replaces the old RIA-registration item, now superseded) — IP/commercial counsel review of licensing terms, ToS, and marketing/disclaimer language; confirm no CTA/investment-adviser registration trigger in target (non-US) jurisdictions.
3. **[AI+Human] Decide distribution channel** — self-hosted site with own license-key system vs. listing on the official MQL5 Market (which has built-in licensing/delivery) vs. both.
4. **[AI+Human] Decide multi-broker scope for v1** — Exness-only, or broader MT5-compatible broker support from the start?
5. **[Human] Evaluate Exness IB/affiliate program** — secondary revenue stream (commission per lot traded by referred users); decide whether to disclose this to customers.
6. **[AI+Human] Backtest + forward-test plan** — read `Product_Development/agents/Software-Development-advisor.md`; needs a live/demo forward-test track record before launch marketing, since spread/slippage can undermine small fixed-dollar profit targets in ways backtests may not capture.
7. **[Human] Confirm payment processor** — must accept trading-software/EA merchants (some standard processors restrict this category).

---

## Superseded (no longer critical path)

- ~~Engage a securities attorney for RIA registration~~ — not needed under the EA-license model (AITrader never holds customer funds). Replaced by item 2 above.
- ~~Evaluate broker-dealer/custodian partners (Alpaca, IBKR, Tradier)~~ — not applicable; broker is customer-selected (Exness named as primary target).

---

## How to Use This File

Update this file at the end of every staging session. Mark items done, add new ones as they surface. When all three staging documents are complete and the priority queue is clear, promote via `PROJECT_MEMORY_INIT.md`.
