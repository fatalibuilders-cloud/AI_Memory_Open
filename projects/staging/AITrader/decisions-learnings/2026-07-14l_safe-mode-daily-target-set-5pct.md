# Decision: Safe Mode Internal Daily Target Set to 5%

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Safe Mode's daily profit-target default is set to **5%** — the top of the 1–5%/day recommendation from 2026-07-14k, and the founder's chosen value. Both trading modes now have concrete daily-target defaults:

- **Safe Mode:** 5%/day default
- **Aggressive Mode:** 20%/day default

Both remain user-configurable settings (the customer can override them); these are just the shipped defaults.

## Rationale

5% still comfortably exceeds the "very good day" benchmark from research (1–2%/day for professional traders), so Safe Mode is still branded honestly as more conservative than Aggressive Mode's 20% default, while being ambitious enough to be a meaningful product differentiator from ultra-conservative approaches. It sits at the top of the previously recommended 1–5% range rather than the middle or bottom — founder's call, not a research-mandated exact figure.

## Impact

This closes the last open item from the trading-modes/daily-controls design. The full risk framework is now:

| Parameter | Value |
|---|---|
| Stop-loss (< $50 equity) | $1 |
| Stop-loss (≥ $50 equity) | $3 |
| Profit-lock target | $0.50 |
| Daily loss limit | 3% of day's starting equity |
| Safe Mode daily target | 5% (default, configurable) |
| Aggressive Mode daily target | 20% (default, configurable) |
| Max concurrent trades | 2 |

## Open Items Carried Forward (unchanged)

- Both 5% and 20% are targets to validate against real backtest/forward-test data, not guarantees — still needs Epic 1 backtesting to confirm plausibility.
- The daily-loss-limit / stop-loss tier-boundary interaction (2026-07-14i) is still unresolved.
- Safe Mode's win-rate floor (80%) vs. the ≥$50 tier's 85.7% break-even requirement is still unresolved.
