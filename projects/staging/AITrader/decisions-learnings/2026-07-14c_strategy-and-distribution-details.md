# Decision: Distribution Channel, Exit Logic, Lot Sizing, and Trading Scope

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decisions

1. **Distribution channel:** List AITrader on the official **MQL5 Market** rather than self-hosting a license-key system. MQL5 Market provides its own licensing/delivery infrastructure.
2. **Profit-lock exit logic:** Once a trade hits the $0.50–$1 profit target, the EA should support **two configurable exit modes**: (a) close the position outright and bank the profit, or (b) move the stop-loss to breakeven and let the position continue running (protecting against the trade turning into a loss while leaving upside open). Both modes should be built and selectable/testable rather than picking one permanently at this stage.
3. **Lot sizing:** Default/starting lot size is **0.01** (micro-lot). The EA should also support **equity-based scaling** — increasing lot size as account equity grows past defined thresholds (a money-management / position-sizing schedule, exact thresholds TBD).
4. **Trade frequency:** No artificial cap — the EA should take **as many trades as the market presents suitable setups for**. This reinforces the scalping/frequent-small-wins design already established.
5. **Volatility adaptability:** The EA must function across **both high- and low-volatility market conditions**, implying volatility-adaptive logic (e.g., ATR-based filters or dynamic parameter adjustment) rather than a single fixed-parameter strategy tuned to one regime.
6. **News/analysis integration:** The EA should incorporate **news and analysis, referencing TradingView** as a source. Exact scope not yet finalized — see Open Items below, this has real architectural and MQL5-Market-policy implications.

## Context

This resolves several items flagged as unclear from the prior voice-transcription session, most notably the profit-lock exit mechanics (previously garbled as "piece of tape" / "starfish"). It also adds meaningful new scope: dynamic lot sizing, volatility adaptability, and news/TradingView integration — all of which affect the Document 2 architecture and the Epic 1 (Core EA Strategy) backlog.

## Open Items / Follow-ups

- **Lot-scaling schedule:** Define the exact equity thresholds and lot-size increments (e.g., "+0.01 lot per $X equity gained") — currently just "should scale," not yet quantified.
- **News/TradingView integration scope — needs a decision between two very different builds:**
  - **Option A — News-event filter only (simpler, standard):** Use an economic calendar (MT5 has built-in calendar data, or a third-party economic calendar API) to pause/adjust trading around high-impact news releases. This is a common, well-precedented EA feature.
  - **Option B — Live TradingView signal/analysis integration (complex):** MQL5 (MT5's language) cannot natively consume TradingView Pine Script or receive TradingView webhooks. This would require building an external bridge/relay service (TradingView alert → webhook → bridge server → EA via MT5's `WebRequest` function) and hosting/maintaining that bridge.
  - **MQL5 Market policy constraint:** Products listed on MQL5 Market can use `WebRequest` for external calls, but end users must explicitly whitelist the target URL in their MT5 terminal settings, and MQL5's review process scrutinizes external network calls. This affects feasibility/friction for Option B specifically and should be confirmed against MQL5 Market's current submission rules before committing to that scope.
- **Exit-mode default:** Once both exit modes (outright close vs. breakeven-and-run) are built and backtested, decide which is the default vs. which is a user-configurable option in the MQL5 Market listing.
- **MQL5 Market commission/review process:** Confirm current commission structure and the product review/approval requirements directly on MQL5's site before finalizing the release timeline (Epic 3/4 in Document 3).
