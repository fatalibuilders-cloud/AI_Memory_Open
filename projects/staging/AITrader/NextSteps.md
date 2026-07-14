# Next Steps — AITrader (Staging)

**Last Updated:** 2026-07-14

---

## Priority Queue

1. **[Human] Engage a securities attorney** — confirm state vs. SEC RIA registration threshold, jurisdiction plan, and Form ADV requirements before further build investment. This is the critical-path gating item for the whole project.
2. **[Human] Evaluate broker-dealer/custodian partners** — Alpaca Securities, Interactive Brokers, Tradier (or others). Compare API capabilities, fee splits, supported asset classes, and RIA-friendliness.
3. **[AI+Human] Decide technology stack** — read `Product_Development/agents/Software-Development-advisor.md` and work through frontend/backend/data/ML infrastructure choices.
4. **[AI+Human] Draft the fee model** — read `Finance/agents/Finance-advisor.md`; note performance-fee restrictions for retail/non-qualified clients under the Investment Advisers Act.
5. **[AI+Human] Draft Document 3 (Release Plan)** — deferred until items 1-2 are resolved enough to know whether Phase 1 is "paper trading only" or can include live trading.
6. **[Human] Consider a Phase 0 fallback** — signal/recommendation-only launch (no discretionary authority) if RIA registration timeline threatens the desired launch date.

---

## How to Use This File

Update this file at the end of every staging session. Mark items done, add new ones as they surface. When all three staging documents are complete and the priority queue is clear, promote via `PROJECT_MEMORY_INIT.md`.
