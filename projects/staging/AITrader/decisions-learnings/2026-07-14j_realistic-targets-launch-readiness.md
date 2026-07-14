# Decision: Realistic Daily Target Guidance + MQL5 Market Launch-Readiness Checklist

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Question Answered: Is $10 → $100 in a Day More Realistic Than $50 → $1,000?

**Directionally yes, but it's still far outside realistic territory.** Both are the same relative claim — $50→$1,000 is +1,900% in a day; $10→$100 is +900% in a day. Neither is achievable safely, and both would read as red flags to anyone with trading experience (including MQL5 Market's own reviewers and buyers).

**Web research grounding (see Sources):**
- Professional day traders typically target **0.03%–0.13% per day**, with **1–2% considered a very good day**.
- **1–10% per month** is a realistic, sustainable range for a skilled trader; **1–3% per month is considered excellent by experienced standards.**
- ~90% of retail traders lose money over time — daily-percentage chasing is specifically called out as the least useful, most misleading metric in trading.

**What this means for AITrader:** even an *aggressive* internal target should stay within a defensible multiple of professional norms, not orders of magnitude beyond them. A internal stretch-goal framing of **turning an account up by roughly 5–20% on an exceptional day** is already far more aggressive than professional practice (5–20% in a day vs. a 1–2% "very good day" for pros) — that's the realistic ceiling for "aggressive but not fraudulent." Anything framed as 10x–20x in a day is not a stretch goal, it's a number that doesn't happen without extreme risk-of-ruin behavior (large martingale-style compounding, no effective stop-loss), which is exactly what the daily loss limit (3%) and stop-loss tiers are designed to prevent.

**Recommendation:** Keep "$50 → $1,000/day" (and similarly "$10 → $100/day") as *internal-only* narrative shorthand for "the aggressive mode, unthrottled" if that's motivating for development purposes, but do not treat either as an engineering target or let it anywhere near a number, projection, or claim visible to a customer or reviewer. If a numeric aggressive-mode target is needed for backtesting/marketing purposes, use something in the 5–20%/day range instead, clearly labeled as a best-case/historical-backtest figure, not a promise.

## MQL5 Market Launch-Readiness Checklist (from official MQL5 documentation)

**Seller registration:** Apply as a Seller before publishing; review typically takes up to 10 working days.

**Product listing requirements:**
- Correct Expert Advisor "Type" field set (buyers filter by this)
- Logo images in three sizes: 200×200, 140×140, 60×60
- Description should cover: trading strategy overview, risk management methods, and system parameters used
- Description formatting rules: **no icons or emojis, keep it clean, don't overuse text styles** — MQL5's own service rules, not just good practice
- Multi-language descriptions recommended (positive effect on sales/visibility)

**Technical review:**
- Product undergoes an **automatic test in the Strategy Tester** on historical price data
- Formally checked for **known programming errors**

**AITrader-specific compliance checklist (from our own decisions, not MQL5's rules — internal bar to hold ourselves to):**
- [ ] No "$50 → $1,000," "$10 → $100," or any multiplier/guarantee framing anywhere in the description, images, or product name
- [ ] No claims of guaranteed profit, "risk-free," or "no losing trades"
- [ ] Performance claims (if any) sourced only from verified backtest/forward-test data, explicitly labeled as historical/hypothetical, not promised
- [ ] Risk disclosure present (trading forex/CFDs carries substantial risk of loss; past performance doesn't guarantee future results)
- [ ] Safe Mode and Aggressive Mode both described accurately — Aggressive Mode's higher risk profile stated plainly, not minimized
- [ ] Description explicitly covers risk management methods (stop-loss tiers, daily loss limit, max concurrent trades) — this doubles as both an MQL5 requirement and a trust signal for buyers
- [ ] No emojis/icons, clean formatting per MQL5 service rules

## Open Items / Follow-ups

- Decide the actual internal Aggressive Mode target number/range once backtesting exists — recommend 5–20%/day as the researched-grounded ceiling for "aggressive but defensible," pending actual results.
- The Legal & Marketing Compliance epic (Document 3, Epic 3) should treat the checklist above as its concrete deliverable, not just a general "review" task.

## Sources

- [How to publish a product on the Market — MQL5 Articles](https://www.mql5.com/en/articles/385)
- [Rules of Using the Market Service — MQL5](https://www.mql5.com/en/market/rules)
- [Forex Trading Profit Per Day Explained](https://www.goatfundedtrader.com/blog/forex-trading-profit-per-day)
- [Realistic Returns for a Forex Trader — Admiral Markets](https://admiralmarkets.com/education/articles/forex-basics/realistic-returns-for-a-forex-trader)
- [How Much % Does a Good Trader Return Per Month?](https://www.a1trading.com/how-much-does-a-good-trader-return-per-month/)
