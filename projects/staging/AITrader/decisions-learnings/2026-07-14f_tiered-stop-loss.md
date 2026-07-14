# Decision: Tiered Fixed-Dollar Stop-Loss by Account Equity

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Stop-loss (max loss per trade) is a **tiered fixed-dollar amount** based on current account equity:
- **Equity below $50:** stop-loss = **$1** per trade
- **Equity at/above $50:** stop-loss = **$3** per trade

This unblocks the dynamic risk-based lot-sizing module (2026-07-14e): lot size can now be computed so that if the stop-loss is hit, the realized loss equals the tier's designated amount.

## Math This Surfaces — Needs Founder Confirmation

Combining this with the existing $0.50–$1 profit-lock target produces a **risk:reward ratio that gets worse, not better, for larger accounts**:

| Equity Tier | Stop-Loss (risk) | Profit-Lock (reward) | Risk:Reward | Win rate needed just to break even (before spread/commission) |
|---|---|---|---|---|
| < $50 | $1 | $0.50 | 1 : 0.5 | ~66.7% |
| < $50 | $1 | $1 | 1 : 1 | ~50% |
| ≥ $50 | $3 | $0.50 | 1 : 0.17 (6:1 against) | ~85.7% |
| ≥ $50 | $3 | $1 | 1 : 0.33 (3:1 against) | ~75% |

The ≥$50 tier requires a very high win rate (75–86%) just to break even, before accounting for spread/commission at all — and at high trade frequency (already a stated requirement), transaction costs compound this further. **This needs explicit founder confirmation that it's intentional**, or the profit-lock target should scale with the stop-loss tier too (e.g., ≥$50 tier uses a larger profit-lock target, not just a larger stop-loss).

## Additional Feasibility Flags

1. **Tight-stop feasibility at minimum lot size:** At the 0.01 minimum lot size, a $1–$3 stop-loss corresponds to a very small price-movement distance for most instruments (the exact pip distance depends on the pair and current price, but it's tight). A tight stop is easily triggered by normal spread/noise, and the EA is separately required to work in high-volatility conditions — those two requirements are in tension. Worth deciding whether stop-loss distance should be a **fixed dollar figure regardless of volatility** (as stated) or should widen during high-volatility/news windows via the already-scoped volatility-adaptive module, using $1/$3 as a baseline rather than a hard universal value.
2. **Discontinuity at the $50 boundary:** Stop-loss jumps from $1 to $3 (a 3x step) at exactly $50 equity, rather than scaling smoothly. This means an account at $49 risks 2%+ of equity while an account at $51 risks ~5.9% of equity — worth confirming this step-function behavior is intended rather than a smoother scaling curve.
3. **Slippage in volatile/news conditions:** Fixed-dollar stops don't guarantee the exact loss amount during fast market moves (especially around news, which this EA is designed to trade through) — actual losses can exceed the stated $1/$3 due to slippage. This should be modeled explicitly in backtesting, not assumed away.

## Open Items / Follow-ups

- **Confirm intent on the risk:reward asymmetry** — is the ≥$50 tier's low reward-to-risk ratio intentional (relying on a very high win rate), or should profit-lock targets scale with the stop-loss tier?
- **Decide whether stop-loss should be volatility-adjusted** (tying into the existing volatility/news-adaptive module) rather than a flat dollar figure in all conditions.
- **Model slippage explicitly** in the backtest/forward-test plan (Epic 1), not just theoretical stop-loss distance.
