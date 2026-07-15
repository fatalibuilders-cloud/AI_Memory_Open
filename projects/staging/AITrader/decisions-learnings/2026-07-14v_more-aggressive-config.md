# Decision: More Aggressive Default Configuration

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Founder asked to make the EA more aggressive, auto-trade as much as possible, and take opportunities the confidence heuristic rates above 50%. Three changes:

1. **Aggressive Mode now applies a confidence gate.** Previously it had *no* filter at all — it took every raw signal regardless of estimated quality. It now requires `GetSignalConfidence() >= 50%` (new input `InpAggressiveModeMinWinProbabilityPct`), matching what the founder described — "take opportunities above 50% winning rate" — rather than literally everything. Safe Mode's filter (65–75%) is unchanged.
2. **Range Filter's ADX ceiling raised from 25 to 30** (`InpAdxMaxForMeanReversion`), letting moderately-trending conditions through, not just calm ranges. More setups qualify to trade.
3. **Default `InpTradingMode` changed from Safe to Aggressive** on a fresh install, so the EA is aggressive out of the box rather than requiring the input to be changed manually.

## What Was Deliberately NOT Changed

Two things directly increase trade frequency but are separate, more consequential risk decisions than "take more opportunities" — left untouched pending explicit confirmation:

- **`InpMaxConcurrentTrades` (2)** — a specific founder decision (2026-07-14h) about total simultaneous exposure. Raising it increases how much can be at risk at once, not just how often trades happen.
- **`InpDailyLossLimitPct` (3%)** — the terminal safety switch. Loosening it means risking more before the EA stops for the day, which is a risk-tolerance decision, not a frequency one.

**Also not changed:** the volume and volatility filters, and the underlying Bollinger/RSI/Stochastic entry logic itself — only the *gating* around it was loosened (who gets to trade, not the definition of a valid setup).

## Rationale

The distinction matters: "more aggressive" was interpreted as "take more of the opportunities the signal already identifies" (loosen the confidence and trend-strength gates), not "increase total risk exposure per trade or per day" (concurrent trades, daily loss limit). The former is what was explicitly asked for; the latter would be a further escalation worth a separate explicit decision.

## Open Items / Follow-ups

- Confirm whether `InpMaxConcurrentTrades` and/or `InpDailyLossLimitPct` should also be raised as part of "more aggressive" — not done here, flagged for founder confirmation.
- All these values are still unvalidated against real backtest data — raising the ADX ceiling and lowering the confidence floor both increase the number of trades taken, which mechanically increases exposure to the "as many trades as possible + transaction costs" risk already flagged in earlier sessions (spread/commission eating into small fixed-dollar profit targets at high frequency).
- The 50% confidence floor is applied to a heuristic score (`GetSignalConfidence()`) that has never been validated against real win-rate outcomes — "above 50% confidence" does not yet mean "actually above 50% real win probability." Still needs real backtest calibration.
