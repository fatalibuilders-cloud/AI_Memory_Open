# Decision: Pre-Trade Margin Check Added (Resolving "$100 Starting Equity" Request)

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## What Happened

Founder asked to change "starting equity" from $10 to $100, following the declined "$10 → $1,000 in 12 hours" request. Asked to clarify why before implementing, since it could mean two very different things: (a) still chasing the same unrealistic multiplier target with a bigger seed (math still doesn't work: +900% in 12 hours at $100), or (b) a legitimate concern that $10 might not be enough margin to actually place trades. **Founder confirmed (b).**

## Decision

Rather than hardcode a specific "$100" minimum (which isn't meaningful in isolation — required margin depends on account leverage, which varies by broker/account and isn't something this code can know or control), added a real technical safeguard: `HasSufficientMargin()`, checked before every order via MT5's native `OrderCalcMargin()` against `AccountInfoDouble(ACCOUNT_MARGIN_FREE)`. If the account can't cover the calculated lot size's margin requirement, the EA logs why and skips the trade instead of sending an order that the broker would silently reject.

## Why Not Just Hardcode $100

Margin required for a given lot size depends on account leverage (e.g., 1:30 vs 1:500 vs 1:2000 produce wildly different margin requirements for the same trade), which this code has no way to know in advance and shouldn't assume. A hardcoded "$100 minimum" would be meaningless for a high-leverage account (could trade fine on $20) and insufficient for a low-leverage one (might still fail on $200). Checking real margin via `OrderCalcMargin()` is the correct, broker-agnostic way to handle this.

## Impact

- Small accounts (including a genuine $10 account) will now get a clear, logged reason ("insufficient free margin for X lots on SYMBOL") instead of a confusing silent failure or generic broker rejection code.
- This doesn't guarantee $10 (or any specific amount) is "enough" — it depends entirely on the founder's actual account leverage and the traded symbol. Metals (gold especially) require substantially more margin per 0.01 lot than most forex pairs.
- Listing description's "Minimum recommended balance" field remains a TODO — best informed by actual testing once compiled, not a number invented here.

## Open Items / Follow-ups

- Founder should check their actual account's leverage setting (visible in MT5 account properties) to understand realistic minimum balances for their chosen symbols.
- Once compiled, watch the Experts log for margin-related `LogBlockReason` messages to see in practice whether the account size is sufficient for the intended symbols.
