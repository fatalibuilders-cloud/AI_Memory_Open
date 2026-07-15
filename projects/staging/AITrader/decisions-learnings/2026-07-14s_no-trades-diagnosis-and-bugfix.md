# Fix/Diagnosis: EA Attached But Placing No Trades

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## What Happened

Founder compiled and attached the EA to a live chart with AlgoTrading enabled, but no trades were being placed. Reviewed the code for real bugs rather than only offering generic troubleshooting.

## Real Bug Found and Fixed

**`PassesVolumeFilter()` compared the still-forming (incomplete) current bar's volume against the average of completed bars.** A forming bar has accumulated only a handful of ticks for most of its life, so `vol[0] >= avgVol` evaluated false almost the entire time, only becoming true right before the bar closed. This silently blocked nearly every trade attempt, regardless of market conditions or signal quality. **Fixed** to compare the last *completed* bar's volume (index 1) against the average of the completed bars before it (indices 2 through N+1).

## Diagnostics Added

Added `InpVerboseLogging` (default on) and a `LogBlockReason()` helper that prints the specific reason no trade was taken, once per new bar (not every tick, to avoid flooding the log), covering every gate in `OnTick()`: daily limits, max concurrent trades, weekend protection, spread/data-feed check, news window, each entry filter individually, no-signal, and Safe Mode confidence. Also added success/failure logging when a trade order is actually sent (`trade.Buy`/`trade.Sell` result and retcode on failure).

This directly addresses the "why isn't it trading" question for this and future sessions — instead of guessing remotely, the founder can now open MT5's **Experts** tab (bottom panel) and read exactly which condition is blocking entry on any given bar.

## Other Likely Causes Flagged (not code bugs, but worth checking)

1. **Per-EA "Allow Algo Trading" checkbox** — separate from the global AutoTrading toolbar button. When an EA is first attached, its own Common-tab setting can be unchecked even if the global toggle is green. Common, easy-to-miss cause of "nothing happens."
2. **Spread filter on wide-spread symbols** — `InpMaxSpreadPoints` defaults to 30. Instruments like XAUUSD (gold) commonly have spreads well above that in points, which would make `PassesDataFeedSanityCheck()` block every trade. Worth raising this input if trading gold or other wide-spread instruments.
3. **Weekend protection window** — if testing near Friday close or shortly after Monday open (server time), `IsWeekendEntryBlocked()` will legitimately block all new entries by design.
4. **The strategy is intentionally selective.** Multi-timeframe trend + pullback + momentum-resumption, combined with the ADX/volatility/volume filters, does not fire every bar by design — per the research behind this signal (2026-07-14q), that's expected behavior, not a malfunction. Should not be judged as "broken" from a short observation window alone.

## Open Items / Follow-ups

- Founder should re-compile with these fixes and check the Experts log for the specific `LogBlockReason` messages if trades still don't appear — that will show definitively which gate (if any) is the culprit going forward.
- Once real trades start appearing (even in a demo/backtest context), this is still not validation that the strategy is profitable — same caveat as always, only real backtesting over a meaningful sample answers that.
- Consider turning `InpVerboseLogging` off once behavior is confirmed correct, to reduce log noise in normal operation.
