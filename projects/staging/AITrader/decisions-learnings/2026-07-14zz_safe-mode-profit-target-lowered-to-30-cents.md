# 2026-07-14zz — Safe Mode profit target lowered to $0.30 per direct instruction

## Decision

Following `2026-07-14z`, which flagged (but did not implement) lowering Safe Mode's profit-lock target toward $0.30, the founder replied **"just make it as instructed."** Implemented directly: `SafeMode_ProfitTarget_SmallAccount_Dollars` and `SafeMode_ProfitTarget_LargerAccount_Dollars` both changed from $1.50 / $3.00 to **$0.30** (both tiers, same value). Aggressive Mode is untouched (already equity-percentage-based since `2026-07-14y`, not part of this request).

## The math this reintroduces (documented, not blocked)

Safe Mode's $1.50/$3.00 targets were originally set in session 13 (`2026-07-14m`) specifically to fix a bad risk:reward ratio — the prior $0.50 target against a $1/$3 tiered stop-loss required an unrealistic 80-100% win rate to break even, which session 13 identified as the actual design flaw, not just a validation gap.

Lowering to $0.30 reproduces (and slightly worsens) that exact problem:

| Tier | Stop-loss | New target | Break-even win rate needed |
|---|---|---|---|
| Small account (<$50 equity) | $1.00 | $0.30 | **~76.9%** |
| Larger account (≥$50 equity) | $3.00 | $0.30 | **~90.9%** |

`SafeMode_MinimumConfidence_Percent` (the win-probability filter) is still set to its prior 65% floor, tuned for the $1.50/$3.00 targets — it was **not** raised to match the new, much higher break-even requirement, since that wasn't part of the instruction. This means Safe Mode can now take trades its own confidence filter rates as good enough (≥65%) that are nonetheless below the win rate actually needed to break even on this new target (77-91%), on an unvalidated, unbacktested signal.

## Why implemented without further pushback

The founder had already been given this exact math in the prior turn (flagged as open item 1d) and explicitly replied to proceed regardless. This is the founder's call to make on their own risk tolerance, not something to relitigate a second time — the responsibility here is documenting it honestly (this file, plus inline code comments at the input declarations), not blocking it.

## What was NOT done

- `SafeMode_MinimumConfidence_Percent` was not auto-raised to compensate — that would be an unrequested additional change layered on top of a direct instruction.
- Aggressive Mode's percentage-based risk/reward (`2026-07-14y`) is untouched.
- No change to stop-loss tiers ($1/$3), daily limits, or any other Safe Mode parameter.

## Open items

- Not compiled/tested (no MT5 environment during staging).
- If real backtesting later shows the v2 signal's actual win rate is well below ~77-91%, Safe Mode will lose money at this target on the small/large tiers respectively — worth revisiting once real data exists, not before.
