# Decision/Milestone: First MQL5 EA Draft Written

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## What Happened

Founder asked to draft the actual MQL5 entry/exit logic. Wrote a first structural implementation: `Product_Development/MQL5_EA/AITrader.mq5`, implementing every risk-management, mode, and daily-control decision made during staging (tiered stop-loss, mode-specific profit-lock targets, dynamic lot sizing, dual exit modes, daily profit target/loss limit with the tier-boundary fix, max 2 concurrent trades, first-pass news awareness via MT5's native calendar).

## Important Gap This Surfaced

**No part of the staging process ever specified the actual entry signal** — what technical/market condition triggers a buy or sell. Every decision from session 1 through 13 was about risk management, exits, sizing, and daily controls — the "AI"/strategy core of "AI Trader" has not been designed. The draft file uses a clearly-labeled placeholder (EMA crossover + RSI filter) purely so the EA is structurally complete and testable — this carries no claimed edge and should not be treated as the product's real strategy.

## What Was NOT Done (and could not be done in this environment)

- **Not compiled.** No MetaEditor/MT5 installation available here — needs to be opened and compiled (F7) in the real MetaEditor.
- **Not backtested.** No MT5 Strategy Tester or historical tick data available here. The only validation is the pre-existing Monte Carlo expectancy simulation (`../simulations/`), which checks dollar-amount arithmetic, not real signal/market behavior.

This is explicitly a code *draft*, not a validated or even compiled product. See `Product_Development/MQL5_EA/README.md` for the full placeholder list and suggested next steps.

## Open Items / Follow-ups

- **Design the real entry-signal logic** — this is now the single largest remaining gap, likely deserving its own dedicated design session (indicator-based? price action? ML-based signal generation? — not yet decided).
- **Design a real signal-confidence model** for Safe Mode's win-probability filter (currently stubbed).
- Compile and run the draft through MT5's Strategy Tester (even with the placeholder signal) to validate the risk-management plumbing works mechanically, separate from validating any real edge.
- Implement the full volatility/news-adaptive parameter system (Document 2) — the draft only has a simple "skip entries near high-impact news" reaction, not the full stop/lot/target adaptation described in the docs.
