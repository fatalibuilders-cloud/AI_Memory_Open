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

## Confirmed (2026-07-16, same day)

Founder re-ran a backtest on GBPUSD M1 for 2026.01.01–2026.07.15 and shared the History tab: real trades now appear, with entries, stop-loss/take-profit fills, and both winning and losing outcomes visible. **Both fixes (spread filter + tester staleness skip) together resolved the zero-trades issue.** Never confirmed via the Experts/Journal log directly (the trade history itself was sufficient confirmation) — noting this in case the log is still worth checking later for filter-tuning purposes, not because the diagnosis is in doubt.

## Open items

- Get the full backtest Report (net profit, win rate, profit factor, max drawdown, total trade count) once this run completes — a handful of visible trades in the History tab is not enough to say anything about whether the strategy has a real edge.
- Re-run across a longer/different date range and on XAUUSD once GBPUSD looks reasonable, to avoid over-reading one short window.
