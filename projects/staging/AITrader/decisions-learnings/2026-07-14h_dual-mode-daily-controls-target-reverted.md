# Decision: Profit Target Reverted to $0.50, Dual Trading Modes, Daily Controls Added

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decisions

1. **Profit-lock target reverted to $0.50** (supersedes 2026-07-14g's $2–$3 change) — applies across the EA, paired with the existing tiered stop-loss ($1 below $50 equity, $3 at/above).
2. **Max 2 concurrent open trades.** The EA can open and close as many trades sequentially as it wants ("as many as possible"), but never more than 2 positions open at the same time.
3. **Daily profit target (configurable).** The EA supports a user-set daily profit target; once equity gains reach that target for the day, the EA stops trading until the next day. This is a "daily injection"/instruction the user sets, not a fixed hardcoded number.
4. **Two trading modes:**
   - **Safe Mode:** Only takes trades the EA's internal signal filter rates at 80–100% historical win probability. Trades less often, prioritizes high-confidence setups.
   - **Aggressive Mode:** Trades opportunistically whenever conditions look suitable, no win-probability filter gate. Internal stretch-goal framing: "turn $50 into $1,000 in a day" — **see Open Items, this is explicitly an internal aspiration, not a product spec or marketing claim (founder-confirmed).**
5. **Web research incorporated** (see Sources below) — professional risk-per-trade guidance and daily-loss-limit best practice, used to sanity-check the above rather than override founder decisions.

## Math This Reintroduces — Flagged, Founder Aware

Reverting to $0.50 profit-lock against the tiered stop-loss brings back the risk:reward math flagged in 2026-07-14f:

| Equity Tier | Stop-Loss | Target | Ratio | Win rate needed to break even (before costs) |
|---|---|---|---|---|
| < $50 | $1 | $0.50 | 1:0.5 | ~66.7% |
| ≥ $50 | $3 | $0.50 | 1:0.17 (6:1 against) | ~85.7% |

**This is where the two-mode design matters:** Safe Mode's 80–100% win-probability filter is *supposed* to cover this gap. It comfortably clears the <$50 tier's 66.7% requirement, but **80% alone does not clear the ≥$50 tier's 85.7% requirement** — only the very top of the claimed 80–100% range does. This needs explicit backtest validation before the ≥$50 tier goes live in Safe Mode; if actual win rate lands at, say, 82%, that tier still loses money by design at that stop/target ratio. Aggressive Mode has no win-rate filter at all, so it inherits the full 66.7%/85.7% requirement with no built-in safety margin — this is a known, accepted tradeoff for that mode per the founder's "internal stretch goal" framing, not an oversight.

## Web Research Findings (used to inform, not override, founder decisions)

- **Risk per trade:** professional/institutional standard is 1–2% of equity per trade; some 2026 backtesting data suggests under 0.5–1% performs even better. [Sources below]
- **Daily loss limits:** prop firms (e.g., FTMO) commonly cap daily loss at 5% of equity and total drawdown at 10%; a common individual-trader rule is "stop for the day after a 3% loss." Most serious risk frameworks pair a daily loss limit with a daily profit target — the founder's daily-profit-target feature (decision 3 above) covers one side; **a daily loss limit is recommended as the symmetric control** (see Open Items).
- **Relevant finding on the $50 stop-loss breakpoint:** at exactly $50 equity, the $3 stop-loss is 6% of equity — well above the 1–2% professional guideline, and above even the more permissive prop-firm daily limits on a single trade. This was already flagged as a discontinuity concern in 2026-07-14f; the research confirms it's outside typical professional risk norms, not just a stylistic concern.

## Open Items / Follow-ups

- **Add a daily loss limit** (symmetric to the daily profit target) — recommended default to discuss: 3–5% of starting daily equity, matching common professional practice, but this is the founder's call.
- **Backtest-validate Safe Mode's ≥$50 tier specifically** — confirm actual win rate clears 85.7%, not just 80%, before relying on it. Consider raising Safe Mode's win-probability floor above 80% specifically for that tier, or giving Safe Mode its own more favorable target instead of sharing $0.50 with Aggressive Mode.
- **Reconsider the $50 stop-loss breakpoint** — a $3 stop-loss right at $50 equity (6% risk) exceeds professional norms; consider raising the breakpoint (e.g., to $150–$300 equity, where $3 is closer to 1–2%) or smoothing the transition instead of a hard 3x jump at $50.
- **Aggressive Mode guardrail (from founder decision):** do not build compounding/martingale-style lot-size logic aimed at hitting the $50→$1,000/day figure, and do not use that figure (or similar multiplier claims) in any marketing copy — flagged for the Legal & Marketing Compliance epic (Document 3, Epic 3) as a specific prohibited-claim example, since "turn $X into $Y in a day" is a recognized pattern in fraudulent trading-bot marketing.

## Sources

- [How Much Should I Risk Per Trade? (The 1% vs 2%)](https://arongroups.co/forex-articles/optimal-risk-per-trade/)
- [% Risk per Trade (1–2% Rule) — FX Foundations](https://fxfoundations.com/learn/risk-management/percent-risk-per-trade)
- [Risk Per Trade: 1% vs 2% Rule — Math, Data & Scenarios](https://traderssecondbrain.com/guides/risk-per-trade-guide)
- [The 1% Risk Rule for Day Trading and Swing Trading](https://tradethatswing.com/the-1-risk-rule-for-day-trading-and-swing-trading/)
- [How Much to Risk Per Trade? Under 0.5% Wins Most](https://hoc-trade.com/blogs/trading-psychology/how-much-to-risk-per-trade)
- [The 1% Risk Rule: Essential Risk Management in Trading](https://takeprofittrader.com/blog/one-percent-risk-rule)
- [Trading Objectives — FTMO.com](https://ftmo.com/en/trading-objectives/)
- [Maximum Daily Loss — FTMO Academy](https://academy.ftmo.com/lesson/maximum-daily-loss/)
- [FTMO Rules & Drawdown Limits (2026) — PropJournal](https://propjournal.net/prop-firms/ftmo/rules)
