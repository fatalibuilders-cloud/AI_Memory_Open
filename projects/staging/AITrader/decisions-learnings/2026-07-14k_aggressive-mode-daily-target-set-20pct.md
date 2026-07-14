# Decision: Aggressive Mode Internal Daily Target Set to 20%

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Founder adopted the research-backed recommendation from 2026-07-14j: Aggressive Mode's internal daily profit target is set to **20%** — the top of the recommended 5–20%/day range. This is the number to use for the EA's configurable daily-profit-target feature default in Aggressive Mode, for internal backtesting goals, and as the number to validate (or invalidate) against real backtest/forward-test data. **It remains internal-only** — not a marketing claim, per the 2026-07-14h and 2026-07-14j guardrails, which still apply unchanged.

## What This Means Concretely

- The EA's configurable daily profit target (2026-07-14h) can default to **20%** in Aggressive Mode (user can still override it — it's a user-facing setting, just with a sensible aggressive-mode default now).
- Safe Mode should get its own, more conservative default given its lower trade frequency and win-rate-filtered approach — **not yet set, still an open item** (see NextSteps). Recommend something meaningfully lower than 20%, consistent with Safe Mode's "safe" branding — e.g., in the 1-5%/day range, matching what research shows as realistic for a genuinely conservative approach, though this is a recommendation, not yet a founder decision.
- 20%/day is still roughly **10-20x** the "very good day" benchmark (1-2%) established in prior research — it is achievable only as a best-case/backtested outcome, not an expectation for every trading day, and must be validated against real data before being trusted. Some days will fall short, some may hit the 3% daily loss limit instead.
- Reaching 20% with a flat $0.50 profit-lock per trade requires either a high volume of winning trades or the position size growing meaningfully within the day as equity compounds (the existing dynamic risk-based lot-sizing module, 2026-07-14e, is what makes this mathematically plausible at all — without it, a flat $0.50 per trade would need an impractically large trade count to reach 20% on any but the smallest accounts).

## Open Items / Follow-ups

- **Set Safe Mode's own daily target default** (lower than Aggressive Mode's 20%, not yet decided).
- **Validate 20%/day against real backtest data** once Epic 1 backtesting exists — if actual results fall well short, revisit the default rather than leaving an unvalidated number in the product.
- This default is still bound by the existing 3% daily loss limit on the downside — the risk profile stays asymmetric (capped downside at -3%, aspirational upside target at +20%) by design, consistent with "cut losses early, let strategy compound on good days."
