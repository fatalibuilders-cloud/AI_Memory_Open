# Decision/Milestone: Real v1 Entry Signal Designed (Multi-Timeframe Trend + Pullback)

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Founder agreed to the recommended approach for resolving the entry-signal gap: start with a rule-based v1 strategy (fast to build, transparent, testable now), treating ML-based signal generation as a v2 aspiration rather than blocking on it.

**Chosen v1 strategy: multi-timeframe trend + pullback momentum entry.**

1. **Higher-timeframe trend filter** — determine trend direction using price vs. a slow moving average (default: 200 SMA on H1) on a timeframe higher than the trading timeframe.
2. **Trading-timeframe pullback** — require price to have pulled back to/through a shorter moving average (default: 20 EMA) in the direction against the higher-timeframe trend — i.e., a genuine dip, not chasing an already-extended move.
3. **Momentum-resumption trigger** — RSI crossing back through a level (default 40 up / 60 down) confirms the pullback is over and the higher-timeframe trend is reasserting.

This replaces the throwaway single-timeframe EMA-crossover placeholder from v0.10-v0.20.

## Why This Approach, Not Something Invented

Web research confirmed multi-timeframe trend + pullback entry is a widely-documented, widely-taught methodology in both retail and more rigorous trading education — not something invented for this project. Key points from research:
- Using a longer-period MA (commonly 200-period) for trend direction and a shorter MA for pullback/entry timing is a standard combination.
- Combining multiple confirming conditions (trend filter + pullback + momentum trigger) is specifically called out as reducing false signals compared to a single crossover.
- Dynamic, volatility-based stop-loss (already implemented via ATR in this project) is noted as adapting better than fixed distances — consistent with the existing design.
- Backtesting research also honestly notes these strategies "often come with significant drawdowns" and require "psychological resilience... during periods of low win ratios" — i.e., this is not a guaranteed-win system, consistent with everything already established about realistic expectations in this project.

## What Else Changed

**`GetSignalConfidence()` upgraded from a flat placeholder (70.0) to a rule-based heuristic** combining ADX (trend strength) and RSI distance from neutral (momentum conviction), scaled to 0-100. This is still explicitly NOT a calibrated probability — it hasn't been checked against real win-rate outcomes — but it's a real, explainable scoring rule instead of a hardcoded number, and gives Safe Mode's filter something meaningful to threshold against once backtesting can validate whether it actually correlates with win rate.

## What This Does NOT Resolve

- **Still not backtested against real data.** Everything here is grounded in *general* published research about the *class* of strategy, not a backtest of *this specific parameter set* on real AITrader instruments/timeframes. That validation still requires Epic 1's real MT5 Strategy Tester work.
- **Still not compiled.**
- The confidence-score heuristic still needs real validation — it's a reasonable, explainable rule, not a proven predictor.
- Parameter defaults (200/20 MA periods, RSI 40/60 levels, H1 higher timeframe) are standard starting values from research, not yet tuned or optimized for AITrader's specific target instruments (Exness pairs) or timeframe.

## Open Items / Follow-ups

- Backtest this specific parameter combination once the code compiles, across multiple instruments/timeframes and both volatility regimes (per the existing backtest plan in NextSteps.md).
- Consider walk-forward testing (train/validate on separate historical periods) to guard against curve-fitting the parameters to one dataset — standard practice flagged by the research, not yet built into the process.
- Revisit whether the higher timeframe (H1) and periods (200/20) are appropriate once real symbol/timeframe choices are finalized for the MQL5 listing.
- If backtest results are weak, iterate on this rule-based hypothesis before jumping to ML — per the agreed approach, ML is a v2 path, not a fallback for a disappointing v1 without first trying reasonable iteration.
