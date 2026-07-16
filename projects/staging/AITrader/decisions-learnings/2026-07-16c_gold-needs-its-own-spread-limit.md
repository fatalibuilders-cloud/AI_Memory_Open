# 2026-07-16c — Gold needs its own spread limit; GBPUSD/XAUUSD can't share one

## What happened

Both the spread-filter fix (`2026-07-16`) and the tester-staleness fix (`2026-07-16b`) were confirmed working — a GBPUSD M1 backtest produced real trades. Founder then ran the equivalent backtest on **XAUUSD** and shared the actual `.xlsx` report file. Parsed it directly (via `openpyxl`) rather than reading it from a screenshot, so these numbers are exact:

- Symbol: XAUUSD, M1, 2024.12.31–2026.07.15, Initial Deposit $100
- History Quality: 73% real ticks (good data, not the low-quality OHLC-only mode)
- Bars: 536,861 / Ticks: 125,490,257 — the EA ran through the entire test genuinely
- **Total Trades: 0, Total Deals: 1** (only the opening balance entry — no actual trades)

So `OnInit()` succeeded and the EA processed the whole backtest, but never took a single trade on gold, even with both prior fixes in place.

## Diagnosis

`MaxAllowedSpread_Points` was a single value (60) shared by every allowed symbol. That number was chosen specifically to clear GBPUSD's simulated spread (`2026-07-16`) — it was never evaluated against gold. This project's own code comments already flagged this exact risk before any of this happened: *"metals (like gold) commonly have a much wider normal spread than forex pairs... this setting is the first thing to check and raise"* — written when the instrument restriction was first narrowed to XAUUSD/GBPUSD, and still true. A typical XAUUSD spread, especially with real variable tick data (73% real ticks) instead of a flat simulated one, very plausibly exceeds 60 points depending on the broker's price precision — comfortably explaining zero trades across the entire test.

## Fix

Split the single spread setting into two:
- `MaxAllowedSpread_Points` (60) — GBPUSD/forex, unchanged.
- `MaxAllowedSpread_Points_Gold` (200, new) — XAUUSD only.

New helper `IsGoldSymbol()` (factored out of `IsAllowedInstrument()`) lets `PassesDataFeedSanityCheck()` pick the right threshold per symbol. The diagnostic log message (`LogBlockReason`) now reports whichever limit actually applied, so if gold still gets blocked, the log will show the real spread value against the correct (200) ceiling instead of the old shared (60) one.

**200 is an unvalidated headroom estimate, same caveat as every spread number set so far in this project.** It was not derived from a confirmed real spread value — the founder never checked the Experts/Journal log for the actual rejected spread numbers before this fix was written. If XAUUSD still produces zero trades after this change, the log (searching for "data feed check failed (spread=...)") is the way to get the real number instead of guessing a third time.

## What was NOT done

- Did not touch the GBPUSD/forex spread limit (60) — that's confirmed working.
- Did not add per-symbol limits for any instrument beyond XAUUSD, since only these two symbols are allowed at all.
- Did not attempt to auto-detect a "correct" spread per symbol from broker data — MQL5 doesn't expose a reliable "typical spread" figure distinct from the current live spread, so this remains a manually-set input, same as before.

## Open items

- Founder should recompile and re-run the XAUUSD M1 backtest with this fix and confirm trades now appear, the same way GBPUSD was confirmed.
- If XAUUSD still shows zero trades, check the Experts/Journal log specifically (not just the summary report) for the actual spread values being rejected, and report them back rather than guessing at another default.
- Once both symbols produce trades, the real work starts: comparing actual win rate, profit factor, and drawdown against the documented break-even bars — nothing said so far establishes whether this strategy is profitable, only that it can now mechanically place trades.
