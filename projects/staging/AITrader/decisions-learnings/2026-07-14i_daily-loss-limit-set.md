# Decision: Daily Loss Limit Set to 3%

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Daily loss limit is **3% of the day's starting equity**. Once realized + floating losses for the day reach 3%, the EA stops trading until the next day — the symmetric counterpart to the configurable daily profit target already decided (2026-07-14h).

## Rationale

Matches the founder's earlier "if I lose 3% in a day, I'm done" instinct and sits within the research-backed 3–5% range (FTMO's daily loss limit is 5%; many individual professional traders use a stricter personal 3% rule). This closes the last flagged gap in the daily risk-control framework — the profit target and loss limit are now symmetric.

## Impact

Both daily controls are now fully specified:
- **Daily profit target:** user-configurable, halts trading for the day once reached.
- **Daily loss limit:** fixed at **3%** of the day's starting equity, halts trading for the day once reached.

This applies to both Safe Mode and Aggressive Mode. It's a meaningful backstop for Aggressive Mode specifically, since that mode has no win-rate filter and was flagged as having "no safety margin" in the prior session's risk register.
