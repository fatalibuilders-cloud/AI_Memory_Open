# Decision/Milestone: v2 Scalping Signal (Bollinger + RSI + Stochastic), Forex/Metals Restricted

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

Founder asked to build a genuine short-timeframe scalping bot, restricted to forex and metals only, "closer to a perfect scalper's bot." This is a strategy swap, not a tweak — `GetEntrySignal()` is replaced entirely.

**New v2 signal: Bollinger Bands + RSI + Stochastic mean-reversion scalping**, grounded in widely-documented, widely-taught 1-minute scalping methodology (see Sources below), not invented for this project:

1. Price touches/pierces a Bollinger Band (default 20-period, 2.0 std-dev) on the last completed bar — a statistical extreme.
2. RSI confirms oversold (≤30) / overbought (≥70) at that same bar.
3. **Stochastic turn-confirmation trigger** (default 14,1,3 settings, 20/80 levels): price was in extreme territory and is now turning back — not just a static extreme reading, which avoids entering while price is still falling/rising ("catching a falling knife").

The prior v1 (multi-timeframe trend + pullback, 2026-07-14q) is retired from the running code but preserved in its own decision file for reference.

## Instrument Restriction

Added `IsAllowedInstrument()`, checked in `OnInit()` — the EA refuses to initialize (`INIT_FAILED`) on anything that isn't recognized as forex or metals. Checks MT5's `SYMBOL_TRADE_CALC_MODE` for forex pairs, plus XAU/XAG/XPT/XPD in the symbol name for metals (since metals are commonly classified as CFD calc-mode on brokers, not forex calc-mode). This is a heuristic — broker symbol-naming conventions vary — and fails closed (blocks) rather than guessing on anything unrecognized.

## Critical Logic Fix This Forced

**The existing Range Filter (ADX-based) was built for the v1 trend-following signal and wanted strong trends (high ADX).** Bolting the new mean-reversion signal onto that filter unchanged would have silently worked against it: mean-reversion strategies specifically fear strong trends, because price can "walk the band" straight through a Bollinger extreme without ever reverting. **`PassesRangeFilter()` is flipped** — it now rejects entries when ADX is too high (default max 25), favoring ranging/choppy conditions instead. `GetSignalConfidence()` was re-derived to match: it now rewards RSI extremity and low/contained ADX, the opposite of the v1 version's "reward high ADX" logic.

This is exactly the kind of bug that happens when a new strategy is added without re-checking every filter's assumptions — caught and fixed before shipping, not left for the founder to discover as another "why isn't it trading right" mystery.

## What Was NOT Changed

- Risk management framework (tiered stop-loss, mode-specific profit-lock targets, dynamic lot sizing, daily loss limit, daily profit targets, max concurrent trades) — unchanged, already well-suited to scalping's small fixed-dollar targets.
- Volume filter, volatility filter, data-feed sanity check, weekend protection, news-window check — unchanged, still applicable.
- Diagnostic logging (`InpVerboseLogging`) — unchanged, updated only where its messages referenced old filter semantics.

## Sources

- [Master 1 Minute Scalping Strategy: Indicators & Charts — XS](https://www.xs.com/en/blog/1-minute-scalping-strategy/)
- [Bollinger Bands Scalping Strategy with RSI & Stochastic — ForexTester](https://forextester.com/blog/bollinger-bands-rsi-stochastic-scalping-strategy/)
- [1 Minute Scalping Strategy: Rules, Setups and Trading — StockGro](https://www.stockgro.club/blogs/trading/1-minute-scalping-strategy/)
- [Four Popular 1-Minute Scalping Strategies in 2026 — FXOpen](https://fxopen.com/blog/en/1-minute-scalping-trading-strategies-with-examples/)

## Open Items / Follow-ups

- Still not compiled or backtested against real data — this is a hypothesis grounded in general published methodology, not validated for this specific parameter set on these specific instruments.
- `InpMaxSpreadPoints` (default 30) needs manual tuning per symbol, especially metals — no auto-detection built in.
- Verify `IsAllowedInstrument()` behaves correctly against the founder's actual broker's real symbol names (e.g., Exness's exact XAUUSD/forex symbol naming, which sometimes includes suffixes like "!" seen in the earlier reference screenshot).
- Chart timeframe (M1/M5 recommended) is not enforced by the code — purely a recommendation in documentation.
- Once real backtest data exists, tune Bollinger/RSI/Stochastic parameters and the ADX ranging threshold per instrument rather than assuming one setting fits both forex and metals.
