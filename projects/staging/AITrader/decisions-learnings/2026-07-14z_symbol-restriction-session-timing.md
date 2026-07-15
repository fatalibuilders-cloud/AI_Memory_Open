# 2026-07-14z — Narrowed to XAUUSD/GBPUSD, M1 enforced, session-open delay filter added

## Decision

Founder request: **"to perfect and trade only on XAUUSD and GBPUSD"** and **"after one hour opening trading hours in all 3 sessions (London, New York and Asia) the bot should analyse the 1minutes candles to a perfect signal execution even if it's a profit of 0.3$."**

Three concrete changes to `FatalibuildersTraderScalper1.mq5`:

1. **`IsAllowedInstrument()` narrowed from "any forex or metals symbol" to exactly XAUUSD and GBPUSD.** Uses a prefix match (`StringFind(name, "XAUUSD") == 0`, same for GBPUSD) so broker suffixes like `XAUUSDm` or `GBPUSD.a` still qualify, but nothing else does — `EURUSD`, `XAGUSD`, `GBPJPY` etc. all correctly fail. This is a heuristic (broker symbol-naming conventions vary), same caveat as the instrument restriction it replaces.

2. **M1 (1-minute) chart timeframe is now enforced, not just recommended.** `OnInit()` checks `_Period != PERIOD_M1` and refuses to initialize (`INIT_FAILED`) on anything else, closing an item that was previously flagged as an open limitation ("chart timeframe is NOT enforced by the code"). Directly implements "analyse the 1minutes candles."

3. **New session-open delay filter.** `AvoidSessionOpens_Enabled` (default on) blocks new trades for `AvoidSessionOpens_DelayMinutes` (default 60) minutes after each of the 3 major session opens: `AsiaSession_OpenHour_ServerTime` (default 0), `LondonSession_OpenHour_ServerTime` (default 8), `NewYorkSession_OpenHour_ServerTime` (default 13) — all in **server time**, not local time or UTC. New function `IsWithinSessionOpenDelay()`, wired into `OnTick()`'s existing gate sequence right after the weekend-protection check. The bot keeps analyzing every 1-minute candle throughout — it just won't act on a signal until the delay window passes.

## Why the session-open hour defaults are what they are, and the caveat that comes with them

The three default hours (0, 8, 13) approximate widely-cited session opens **in UTC** (Tokyo ~00:00 UTC, London ~08:00 UTC, New York ~13:00 UTC). But MT5's `TimeCurrent()`/`MqlDateTime` reflect the broker's **server time**, which is commonly offset from UTC by a fixed or DST-shifting amount (Exness and many brokers run GMT+2/GMT+3). Without knowing the founder's specific broker/account server-time offset, hardcoding "correct" hours isn't honestly possible — the three hour inputs are left founder-configurable with a clear on-screen warning to check the actual server time (visible on any MT5 chart) and adjust. This mirrors the existing weekend-protection hours, which already carry the same "server time" caveat from earlier sessions.

## What was NOT done: the "$0.30 profit" part

The request's second half — "perfect signal execution even if it's a profit of 0.3$" — was read as "the bot should be willing to take even a small $0.30 win," not as a literal instruction to hardcode $0.30 as a new profit target. This was **not implemented as a code/default change**, for a specific reason:

- Safe Mode's profit-lock targets were deliberately **raised** from an earlier $0.50 default to $1.50/$3.00 in session 13 (`2026-07-14m`) specifically because the smaller target produced a punishing risk:reward ratio — a $0.30 target against the $1 small-account stop-loss is a 1:3.3 ratio, requiring roughly a 77% win rate just to break even (the same category of problem that redesign explicitly fixed).
- Reintroducing a $0.30 target by default would silently undo that fix without being asked to.
- The existing inputs (`SafeMode_ProfitTarget_SmallAccount_Dollars`, etc.) **already support entering $0.30 directly** — no code change is needed if the founder wants to test that value. This is left as a configuration choice, not a hardcoded default, so the tradeoff stays visible rather than baked in silently.

If the founder does want $0.30 to be the actual shipped default for XAUUSD/GBPUSD scalping, that's a real, answerable follow-up — flagged in `NextSteps.md` rather than assumed.

## Open items

- Not compiled/tested (no MT5 environment during staging) — the M1 enforcement, session-open filter, and symbol restriction should all be checked once in MetaEditor/Strategy Tester.
- Session-open default hours (0/8/13, assumed ≈ UTC) need to be verified/adjusted against the founder's actual broker server time before relying on them.
- Whether the $0.30 profit-target question applies to Safe Mode, Aggressive Mode, or a new dedicated micro-scalp tier is still open — see `NextSteps.md`.
