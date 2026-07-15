# 2026-07-15 — Trailing stop + max trade duration added (independent implementation)

## Context

Following the declined request to decompile/combine 10 uploaded third-party `.ex5` files (`2026-07-14zzz`), the founder asked again, more broadly: "everything caught my eye and wanted you to compile and come up with a super bot." Held the same line — did not read, extract, or reference anything from the uploaded binaries — but treated the underlying goal (a genuinely more capable "super" bot) as legitimate and actionable using independent, well-documented scalping-EA techniques not yet in our own code.

## Decision

Two additions to `FatalibuildersTraderSuperScalpers.mq5`, both standard, widely-documented scalping-EA features, implemented from general trading knowledge rather than any specific product:

1. **True trailing stop.** `ManageOpenPositions()` previously only moved the stop-loss to breakeven once, the first time a `BREAKEVEN_AND_RUN` trade hit its profit target, and then left it there indefinitely. Now, after breakeven is locked, the stop continues trailing behind price as profit grows further — `TrailingStop_Enabled` (default on), `TrailingStop_Distance_Dollars` (default $0.20 behind price), `TrailingStop_StepDollars` (default $0.05 minimum move before re-adjusting, to avoid constant tiny `PositionModify` calls). Only active in `BREAKEVEN_AND_RUN` mode — `OUTRIGHT_CLOSE` already sets a fixed take-profit at trade open, so there's nothing to trail.

2. **Maximum trade duration.** New `ApplyMaxTradeDuration()`, called every tick in `OnTick()` alongside `ManageOpenPositions()`. Force-closes any of this bot's open positions once they've been open longer than `MaxTradeDuration_Minutes` (default 15) without hitting their target or stop-loss. Applies regardless of exit mode. This is a standard scalping safeguard: a strategy built around 1-minute candles and 30-cent targets shouldn't have positions quietly sitting open for hours waiting on an SL/TP that may never come, especially now that up to 20 can be open simultaneously (`2026-07-14zzz`).

## Why this satisfies "come up with a super bot" without touching the uploaded files

Both features are things essentially every commercial scalping/auto-trading EA has (trailing stops and time-based exits are two of the most common scalping techniques in published trading literature) — adding them makes the bot more capable in the way the founder was gesturing at, without needing to know or copy what any specific competitor product does internally.

## What was NOT done

- No content from any of the 10 uploaded `.ex5` files was read, decompiled, or referenced in designing these features.
- No change to entry signal logic, risk sizing, concurrency limits, or daily controls — this is exit-management only.
- Defaults ($0.20 trail distance, $0.05 step, 15-minute max duration) are reasonable starting points for a $0.30-target M1 scalper, not tuned or backtested.

## Open items

- Not compiled/tested (no MT5 environment during staging).
- Trailing-stop and max-duration defaults should be validated against real backtest data once available — a 15-minute cap could cut off a trade that would have hit target at minute 16, and $0.20/$0.05 trail parameters interact with spread the same way the $0.30 target already does (see `2026-07-14zz`/`2026-07-14zzz` cost-of-trading flags).
- `MaxTradeDuration_Minutes` force-closes at market price, which could realize a loss larger than the configured stop-loss if price has moved adversely without yet triggering the SL (e.g., due to slippage or a wide spread at close time) — worth confirming this trade-off is acceptable once real testing is possible.
