# 2026-07-16b — Second zero-trades cause: stale-quote check unreliable in Strategy Tester

## What happened

After raising `MaxAllowedSpread_Points` from 30 to 60 (`2026-07-16`), founder re-ran the GBPUSD M1 Strategy Tester backtest and still got **zero trades**.

## Diagnosis

`PassesDataFeedSanityCheck()` does two checks, not one: spread (just fixed) and quote staleness. The staleness half:

```
datetime lastTick = (datetime)SymbolInfoInteger(_Symbol, SYMBOL_TIME);
if(TimeCurrent() - lastTick > MaxAllowedPriceDelay_Seconds)
   return false;
```

This is meant to catch a frozen/dead live price feed. But `SymbolInfoInteger(_Symbol, SYMBOL_TIME)` is a known MT5 quirk inside the Strategy Tester: depending on the test mode (especially anything other than "every tick based on real ticks"), it does not reliably track simulated time the way `TimeCurrent()` does — it can return `0` or a stale value unrelated to the backtest's simulated clock. If that happens, `TimeCurrent() - lastTick` becomes an enormous number (potentially the entire Unix timestamp), which will always exceed `MaxAllowedPriceDelay_Seconds` (60) — failing this check on literally every tick, for the whole backtest. Structurally identical in effect to the spread bug, just a different half of the same function.

This wasn't confirmed via a log (the founder hasn't shared Journal/Experts output yet — still the most reliable way to know for certain), but it's a well-documented category of MT5 tester behavior and a clean mechanical explanation for "still 0 trades right after fixing the only other thing in the same function."

## Fix

The staleness check is now skipped entirely when running inside the Strategy Tester, detected via `MQLInfoInteger(MQL_TESTER)`:

```
if(!MQLInfoInteger(MQL_TESTER))
{
   datetime lastTick = (datetime)SymbolInfoInteger(_Symbol, SYMBOL_TIME);
   if(TimeCurrent() - lastTick > MaxAllowedPriceDelay_Seconds)
      return false;
}
```

This isn't a hack to force trades through — it's the conceptually correct fix. "Is my broker's live feed frozen?" is not a meaningful question during a backtest: the Strategy Tester deterministically replays historical data, there is no live feed to freeze. The spread check remains active in both modes (a spread threshold is still meaningful to test against). The check will resume applying automatically once the EA runs live or on a demo account, since `MQL_TESTER` is only true inside the Strategy Tester.

## What was NOT done

- Did not disable or weaken the spread check in tester mode — only staleness.
- Did not confirm this via the Experts/Journal log — this is a well-reasoned fix based on known MT5 tester behavior, not a confirmed diagnosis. If trades still don't appear after this fix, the log becomes the mandatory next step rather than another guess.

## Open items

- Founder should recompile and re-run the same backtest. If trades appear now, this (combined with the spread fix) was the full explanation.
- If trades still don't appear, the Journal/Experts log tab (bottom panel of the Strategy Tester, not the Visualization window) must be checked — `ShowDetailedLog_Enabled` is on by default and prints the exact block reason for every skipped bar via `LogBlockReason()`. That is the only way to move from reasoned hypotheses to a confirmed answer at this point.
