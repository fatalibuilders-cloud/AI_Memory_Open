# Decision: Safe Mode Redesigned for Realistic, Positive Expectancy

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Safe Mode is redesigned around a more realistic premise. The previous design (an 80–100% win-probability filter sharing Aggressive Mode's $0.50 profit-lock target) had two problems: (1) requiring an 80–100% win rate is itself an unrealistic bar that very few real trading systems sustain, and (2) even if hit, the shared $0.50 target against the $3 stop-loss tier meant it still lost money at realistic win rates below ~86%.

**Safe Mode now has its own risk:reward, separate from Aggressive Mode:**

| Tier | Stop-Loss | Profit-Lock (NEW, Safe Mode only) | Break-even win rate |
|---|---|---|---|
| < $50 equity | $1 | **$1.50** | 40% |
| ≥ $50 equity | $3 | **$3.00** | 50% |

**Win-probability filter lowered from 80–100% to a realistic 65–75%** — still meaningfully more selective than Aggressive Mode (which has no filter), but grounded in what well-designed trading systems actually achieve, rather than a near-mythical win rate.

Aggressive Mode is unchanged ($0.50 target, shared tiered stop-loss, no filter, 20% daily target) — it's allowed to carry more risk by design; Safe Mode is the one that needed to actually deliver on its name.

## Why the Old 80-100% Premise Was the Real Problem

Requiring 80-100% win rate to be "safe" isn't how safety works in trading — it's how you paint yourself into a corner. Real conservative strategies get their safety from favorable risk:reward at *moderate*, achievable win rates (55-65%), not from a near-perfect win rate that's extremely hard to find, sustain, or honestly claim in marketing. Fixing the risk:reward instead of the win-rate assumption is the standard, defensible way to build a genuinely conservative system.

## Mathematical Simulation (NOT a real backtest — see caveat below)

Ran a Monte Carlo expectancy simulation (`Product_Development/simulations/safe_mode_expectancy_simulation.py`, full output in the adjacent `.txt` file) comparing old vs. new Safe Mode design across a range of *assumed* win rates (50-75%), with an illustrative $0.05/trade cost estimate, 20 trades/day cap, 5% daily target, 3% daily loss limit.

**Results, revised design:**

| Win Rate | <$50 tier avg daily P&L | ≥$50 tier avg daily P&L |
|---|---|---|
| 50% | +1.79%/day | -0.08%/day (roughly breakeven) |
| 55% | +2.83%/day | +0.46%/day |
| 60% | +3.81%/day | +1.21%/day |
| 65% | +4.70%/day | +1.85%/day |
| 70% | +5.48%/day | +2.47%/day |
| 75% | +6.09%/day | +3.11%/day |

**Results, old design (for comparison):** at the ≥$50 tier, even a 75% win rate produced **-3.30%/day** and hit the 3% daily loss limit on **87% of simulated days.** The old design was not marginal — it was structurally losing money across the entire realistic win-rate range.

**⚠️ Critical caveat — read before treating this as validation:** This is a pure mathematical simulation of the stated dollar parameters under assumed win rates. It uses **no real market data, no MQL5 code, and no MT5 Strategy Tester** — none of those exist yet (Epic 1 hasn't started). It only proves the *design's arithmetic* is sound; it says nothing about whether the actual signal logic can achieve a 55-75% real-world win rate. That can only be answered by building the EA and backtesting it against real historical data, which is still the next real milestone, not something completed by this simulation.

## Impact

- Safe Mode's <$50 tier is robust even at a 50% win rate (breakeven is only 40%).
- Safe Mode's ≥$50 tier needs at least ~55% real win rate to be reliably profitable — a realistic, achievable bar, unlike the old design's 85.7% requirement.
- The 5% daily target (2026-07-14l) is achievable under this design at win rates ≥60% per the simulation, without needing the implausible win rates the old design required.

## Open Items / Follow-ups

- **Real backtesting is still required** — this simulation is not a substitute. Once Epic 1 produces actual MQL5 code, run it through MT5's Strategy Tester against real historical data and compare actual results to this simulation's assumptions.
- The $0.05/trade cost assumption is illustrative — replace with real Exness spread/commission data once available.
- Confirm whether Safe Mode's new $1.50/$3.00 targets interact cleanly with the volatility/news-adaptive module and the daily-loss-limit tier-boundary issue (2026-07-14i) — those open items still apply.
