# 2026-07-14x — Plain-English input names + manual (signals-only) operation mode

## Decision

Two changes to `FatalibuildersTraderScalper1.mq5` (at the time still named `FatalibuildersTrader.mq5`), both requested directly by the founder:

1. **Renamed every input variable from technical `Inp*` names to plain-English, self-explanatory names**, and organized all inputs into 9 numbered `input group` sections with plain-language section titles (e.g. "HOW MUCH CAN BE LOST ON ONE TRADE?" instead of a bare risk-parameter list). Every input now has a comment explaining what it does in non-jargon terms. Full old-name → new-name mapping is in the code diff / session log; example: `InpTradingMode` → `TradingStyle_SafeOrAggressive`, `InpStopLossDollarsLowTier` → `MaxLossPerTrade_SmallAccount_Dollars`.

2. **Added a manual operation mode.** New `enum ENUM_OPERATION_MODE { AUTO_TRADE, SIGNALS_ONLY }` and input `AutoTrade_Or_SignalsOnly` (default `AUTO_TRADE`, preserving existing behavior). In `SIGNALS_ONLY` mode the EA runs its full signal/filter pipeline exactly as before, computes the same suggested lot size/stop-loss/take-profit it would have used, but never calls `trade.Buy()`/`trade.Sell()`. Instead it calls a new `SendSignalAlert()` function which fires `Alert()` (on-chart popup), `Comment()` (persistent on-chart text), and `SendNotification()` (phone push, if the user has configured a MetaQuotes ID under MT5 Options → Notifications — silently does nothing if not configured, does not error). Throttled to once per new bar via `g_lastSignalAlertBarTime` so it doesn't repeat every tick.

## Why

Founder's request: "once created on the inputs please [use] terms which anyone can understand especially people who don't know much about trading... also put and option of manual operation and auto trading operation so that someone can decide to use the auto trade which finds signals and place a trade on your behalf full automated and manual the bot give signals sell or buy to you."

This is aimed at buyers who are not MQL5/trading-jargon-literate — the EA is sold on the MQL5 Market to retail customers, most of whom will never open the code and only interact with the input panel MT5 shows when attaching the EA to a chart.

## Implementation notes

- The rename was mechanical (`sed` with `\b` word-boundary regex across the whole file, verified via grep that zero old `Inp*` references remained) — no logic changed by the rename itself.
- `SIGNALS_ONLY` reuses every existing filter/signal/sizing computation unchanged; the only new code is the branch at the end of `OnTick()` that decides whether to call `trade.Buy()/trade.Sell()` or `SendSignalAlert()`.
- This does not change any risk-management math — it is purely about who (bot or human) pulls the trigger once a valid setup is found.

## Open items

- `SendNotification()` requires the user to have configured MT5's push-notification settings themselves — not something this code can do or verify. The listing description / README should mention this as an optional setup step for anyone who wants phone alerts in manual mode.
- Not compiled/tested since this change (no MT5 environment available during staging) — should be verified in MetaEditor before this ships, same caveat as every other change made during staging.
