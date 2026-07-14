# Decision: Profit-Lock Target Raised to $2–$3 (Risk:Reward Fix)

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

In response to the risk:reward concern flagged in `2026-07-14f_tiered-stop-loss.md`, the founder chose to **keep the tiered stop-loss as-is** ($1 below $50 equity, $3 at/above) and **raise the profit-lock target from $0.50–$1 to $2–$3**. This replaces the profit-lock target everywhere it was previously specified as $0.50–$1.

## Resulting Risk:Reward

| Equity Tier | Stop-Loss (risk) | Profit-Lock (reward) | Risk:Reward | Win rate needed to break even (before costs) |
|---|---|---|---|---|
| < $50 | $1 | $2 | 1 : 2 | ~33% |
| < $50 | $1 | $3 | 1 : 3 | ~25% |
| ≥ $50 | $3 | $2 | 1 : 0.67 (3:2 against) | ~60% |
| ≥ $50 | $3 | $3 | 1 : 1 | ~50% |

This resolves the earlier high-severity concern: the ≥$50 tier now needs a 50–60% win rate to break even rather than 75–86%, which is a realistic bar for a well-tuned strategy. The <$50 tier is now favorably skewed (only needs 25–33% win rate before costs), which is not a problem in itself but is worth knowing since it changes the trade-frequency/win-rate tradeoff for that tier.

## Impact

This changes the profit-lock target everywhere referenced in Documents 1–3 (vision statement, success metrics, exit logic, dual-mode exit description, risk tables). All prior references to "$0.50–$1" profit-lock are superseded by "$2–$3."

## Open Items Carried Forward (unchanged by this decision)

- Whether $2–$3 (like the stop-loss) is a fixed dollar figure in all conditions, or should be adjusted by the volatility/news-adaptive module.
- Exact pairing: is it $1 SL / $2 TP and $3 SL / $3 TP specifically, or should both tiers have access to the full $2–$3 TP range (dual-mode choice, matching how the original $0.50/$1 target was described as a dual option)? Assumed to still be a dual/configurable target ($2 or $3) unless the founder specifies exact tier pairing.
