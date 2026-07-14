# Decision: Lot Sizing Uses Dynamic Risk-Based Scaling, Not Fixed Thresholds

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Lot sizing is **not** a fixed manual schedule ("+0.01 lot every $X of equity"). Instead, the EA should continuously analyze current account equity and run its own risk-management assessment before increasing lot size — a **dynamic, risk-based position-sizing model** rather than static thresholds. Starting lot size remains 0.01.

## What This Means Concretely

This is the standard approach professional/algorithmic trading systems use, generally called **fixed-fractional risk-based position sizing**:

1. Define a **risk-per-trade percentage** of current equity (e.g., risk 1% of equity per trade — exact percentage is an open item, see below).
2. Before each trade (or periodically), the EA calculates: `lot size = (equity × risk% ) / (stop-loss distance in account currency per lot)`.
3. As equity grows, the same risk% naturally produces a larger lot size — this is what "automatically adjust and upgrade" means in practice, rather than a hand-picked equity-threshold table.
4. The EA should also incorporate a "run risk management" check before scaling up — e.g., don't increase size after a losing streak, don't increase size during detected high-volatility/news windows (ties into the volatility/news-adaptive module already scoped), and respect a maximum lot size / maximum equity-at-risk cap.

## Critical Gap This Surfaces

Risk-based position sizing **requires a defined stop-loss (max loss per trade)** to compute lot size from — this hasn't been defined yet. So far, the strategy design only covers the *winning* exit (profit-lock: outright close or breakeven-and-run at $0.50–$1). There is no documented answer yet to "what happens if the trade moves against the position — is there a stop-loss, and if so, how far?" This is now a blocking open item: risk-based lot sizing can't actually be built or backtested without it.

## Rationale

Confirmed by founder: lot size should scale automatically based on the EA's own equity analysis and risk management, not a fixed manual table. This is well-precedented in algorithmic trading (fixed-fractional / risk-based sizing) and fits naturally with the EA's other adaptive components (volatility/news module).

## Open Items / Follow-ups

- **Define the stop-loss / max-loss-per-trade rule** — this blocks risk-based lot sizing from being designed at all. Needs founder input: is there a stop-loss, and how is it set (fixed pips/dollars, ATR-based, or something else)?
- **Define the risk-per-trade percentage** (e.g., 1%, 2%) — how much of equity is the EA allowed to risk on a single trade before sizing up?
- **Define "run risk management before increasing"** more precisely — what specific checks gate a size increase (e.g., minimum number of trades since last increase, no increase after N consecutive losses, no increase during high-impact news windows, a maximum lot size cap)?
- **Reduction rules:** should lot size also scale *down* if equity drops (drawdown protection), not just up? Not yet specified — worth confirming since most robust risk-based systems do both directions.
