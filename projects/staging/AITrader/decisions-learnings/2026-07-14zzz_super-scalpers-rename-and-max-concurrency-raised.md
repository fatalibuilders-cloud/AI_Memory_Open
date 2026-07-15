# 2026-07-14zzz — "Super Scalpers" rename, MaxTradesOpenAtOnce raised to 20, signal-stacking formalized

## Context: declined to decompile/combine uploaded competitor EAs

The founder uploaded ten `.ex5` files (SafeScalperPro, Scalping Robot Pro MT5, Smart Trading Copilot MT5, SuperScalp Pro Auto Trader ×2, Gold Scalper for MT5 EA, RangeBreakout EA MT5, XAUUSD_5_minute ×3, and AITrader_5 — likely the founder's own earlier compiled build of this project) and asked to "combine the files come up with a super aggressive bot."

**Declined, and explained why rather than silently ignoring the request:** `.ex5` is MetaTrader's compiled bytecode output, confirmed via `file` (reports as opaque `data`) — there is no decompiler available in this environment, and MQL5 bytecode does not reverse cleanly into readable source with standard tools. Independent of that technical limit, most of the filenames indicate third-party commercial products; reverse-engineering another vendor's compiled software to fold its logic into our own product would be a real IP problem, not just a technical one, and directly contradicts the precedent already set in this project (`2026-07-14o`, where a reference EA's screenshot was used only for publicly-visible filter *names*, never its actual logic). No file content was extracted or used from any of the ten uploads.

## What was actually done instead

The founder's underlying goal — a genuinely more aggressive bot — was pursued using only our own source, via two `AskUserQuestion` rounds (since both changes below are the kind of risk-multiplying decision this project has repeatedly deferred to the founder rather than assumed):

1. **Renamed the product** from "FatalibuildersTrader Scalper 1" to **"FatalibuildersTrader Super Scalpers"** per direct instruction ("super scalpers on the name"). File renamed `FatalibuildersTraderScalper1.mq5` → `FatalibuildersTraderSuperScalpers.mq5`; all internal copyright/log/trade-comment strings updated.

2. **`MaxTradesOpenAtOnce` raised from 2 to 20** — the founder's explicit number, given after being asked directly (this cap was deliberately left unchanged through several earlier "more aggressive" rounds — `2026-07-14v`, `2026-07-14y` — specifically because it multiplies simultaneous risk exposure in a way that's a separate decision from opportunity capture, not a byproduct of it). This is now done because it was asked for directly with the tradeoff made explicit in the question itself (2.5x/5x/10x framing), not assumed as a default of "more aggressive."

3. **Formalized the "multiple trades per candle" behavior** that a review of the code (prompted by the founder's "max trades in 5 minutes" question) revealed was already happening accidentally: `OnTick()` re-evaluates the entry signal on every price tick, not once per bar, and had no guard against opening a second (third, ...) trade off the same completed candle's signal as long as a concurrency slot was free. This was surfaced proactively, not something the founder asked to find. Per the founder's choice ("Formalize it"), added:
   - `AllowMultipleTradesPerSignal_Enabled` (default `true`) — explicit on/off switch for the behavior.
   - `MaxTradesPerSignal_PerBar` (default 20) — caps how many trades one candle's signal can contribute, independent of `MaxTradesOpenAtOnce` (which caps total open positions from all signals combined).
   - New globals `g_signalStackBarTime` / `g_tradesThisBarSignal` track and reset the per-candle count; the counter increments only on a successful trade open (or a signals-only alert), not on failed order attempts, so a transient broker rejection doesn't eat into the same-bar quota.

## What this means combined with the earlier $0.30 target and 20-slot cap

With `MaxTradesOpenAtOnce = 20`, `MaxTradesPerSignal_PerBar = 20`, and a $0.30 Safe Mode profit target, the bot can now — in principle — open up to 20 positions off a single 1-minute candle's signal within moments of each other (network/broker latency permitting), and as those tiny-target positions close and free slots, cycle through many more within the same 5-minute window. There is no code-level ceiling on total trades over any time window; the real-world limit is broker execution speed and, more importantly, **spread and commission cost eating into a 30-cent target at high frequency** — a concern already flagged in `NextSteps.md` and now substantially more urgent given the scale of concurrent exposure involved.

## What was NOT done

- No file content from any uploaded `.ex5` was read, decompiled, or incorporated.
- Confidence filters, stop-loss tiers, daily loss limits, and the session-open delay filter are all unchanged — this only touches concurrency and per-bar stacking.
- No automatic adjustment of position sizing to compensate for 10x more concurrent slots — `CalculateLotSize()` still sizes each trade independently off the existing per-trade risk-dollar inputs, so 20 concurrent trades means roughly 20x the dollar risk on the table at once versus the original 2-slot design, not a risk-neutral change.

## Open items

- Not compiled/tested (no MT5 environment during staging).
- **Real backtest is now more urgent than before** — 20 concurrent positions plus unlimited same-bar stacking plus a $0.30 target is a materially different risk/cost profile than anything tested so far, even in simulation.
- Consider whether `CalculateLotSize()` or the daily-loss-budget logic needs to account for many simultaneously-open positions drawing down together (a fast adverse move could hit stop-loss on many of the 20 slots near-simultaneously) — not addressed here, flagged for follow-up.
