# 2026-07-16 — Diagnosed: spread filter was blocking every trade in the Strategy Tester

## What happened

Founder ran `FatalibuildersTraderSuperScalpers.mq5` in MT5's Strategy Tester on GBPUSD, M1, across a very long historical range (1993.05.12–2026.07.15), and reported the bot placing zero trades. Shared a screenshot, then a short screen-recording of the Strategy Tester Visualization window scrubbing through different years.

## Diagnosis

Frames extracted from the video (via `ffmpeg`, 1 frame/second) all showed the same thing in MT5's Data Window panel, at multiple different simulated dates (2001, 2002, 2026): **`Spread = 50`**, consistently, never varying.

This is a known MT5 Strategy Tester behavior: unless the test is explicitly configured to replay real historical spread data, the tester applies a single **fixed** spread for the entire backtest, pulled from the symbol's spread at the moment the test was started — not the real spread that existed at each historical bar.

Our EA's data-feed sanity filter, `PassesDataFeedSanityCheck()`, rejects any tick where the current spread exceeds `MaxAllowedSpread_Points` (defaulted to **30**). At a constant 50-point spread, this check fails on **every single tick**, for the entire backtest, unconditionally — before the entry signal, confidence score, or any other filter is ever evaluated. This alone is sufficient to explain zero trades over the full test range regardless of market conditions, and is very likely the actual root cause here (as opposed to the earlier hypothesis from the still screenshot, that a calm/ranging market simply hadn't produced a qualifying mean-reversion signal yet — that may also be true some of the time, but couldn't have mattered if this filter was already rejecting everything first).

## Fix

`MaxAllowedSpread_Points` raised from 30 to **60**, giving headroom above the 50-point spread observed in this specific tester run.

**Important caveat, documented rather than glossed over:** 60 is a number chosen to unblock *this specific backtest run*, not a validated real-account setting. Two open questions this doesn't resolve:

1. **Is 50 points a realistic GBPUSD spread for the founder's actual account?** 50 points (5 pips on a 5-digit quote) is plausible for a standard (non-ECN/raw) retail account, especially outside peak liquidity hours, but could also just be an artifact of the tester's fixed-spread simplification not reflecting real market conditions. This should be checked against the founder's actual broker/account type once live or demo trading, not assumed from one backtest.
2. **60 as a filter ceiling is a "let the test proceed" number, not a "trade at that spread level" endorsement.** A 60-point (6 pip) spread is wide for GBPUSD by normal standards — if real live spreads are typically much tighter (e.g., 5-15 points on many ECN accounts), the founder may want to lower this back down for live trading once the actual typical spread is known, so the filter still does its intended job of rejecting genuinely bad moments rather than passing everything through.

## What was NOT done

- Did not change `PassesDataFeedSanityCheck()`'s logic itself, or `MaxAllowedPriceDelay_Seconds` — only the spread threshold.
- Did not attempt to configure MT5's Strategy Tester settings (e.g., switching to "Every tick based on real ticks" mode, which would use variable historical spread instead of a fixed value) — that's a founder-side Strategy Tester configuration choice, not something in the `.mq5` file.
- Did not touch entry signal logic, confidence scoring, or any other filter — this was isolated to the one confirmed blocker.

## Open items

- Founder should re-run the backtest with the updated file and confirm trades now appear.
- Once trades appear, check whether the "calm market" hypothesis from the earlier screenshot (RSI/Stochastic sitting mid-range, no signal) also reduces trade frequency in ranging periods — that's a separate, legitimate reason for fewer trades, not a bug.
- Consider re-running the Strategy Tester with real historical spread data (if the broker/data source supports it) for a more realistic test than the fixed-spread default.
- `MaxAllowedSpread_Points` should be revisited once real live/demo spread data is available for the founder's actual account.
