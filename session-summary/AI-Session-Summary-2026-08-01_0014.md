# AI Session Summary — 2026-08-01 00:14 UTC (Root Level)

**Model:** claude-opus-5
**Started:** 2026-08-01 00:14 UTC
**Executor:** Claude Code (remote execution environment, branch `claude/deriv-7h4xbl`)
**Scope:** AI Memory System (root-level) + new application source under `app-src/`

---

## What Was Done

**Intake**

- Executed the root-level session initialization protocol (`agents/open.md`): read `Master-AI-Context.md`, `README.md`, `NextSteps.md`, `Key-Decisions.md`, `Sessions.md`, `Risk-Registry.md`, and the two most recent session summaries.
- Searched the repository for "Deriv". No prior reference existed as a proper noun — every hit was the ordinary word *derive/derived*. Owner then clarified the request: **a bot that trades only crypto, 24/7**, i.e. Deriv.com the trading broker.

**Build — `app-src/deriv-crypto-bot/`**

- Built a complete, runnable trading bot against Deriv's WebSocket v3 API. 9 modules, ~1,400 lines, one runtime dependency (`websockets`).
- **Crypto-only enforcement** at three independent points: symbols discovered from Deriv's `active_symbols` and filtered to `market == "cryptocurrency"`; an operator allowlist that is still subject to that filter; and a final check immediately before every purchase.
- **24/7 operation**: automatic reconnection with exponential backoff and jitter, application-level keepalive ping, graceful SIGTERM/SIGINT shutdown, UTC-midnight counter rollover. Poll-based rather than subscription-based, so recovery after a dropped connection needs no subscription rebuild.
- **Strategy**: EMA(9/21) crossover with an RSI exhaustion filter and an ATR separation filter. Isolated in `strategy.py` so it can be replaced without touching the rest of the bot. Indicators (EMA, RSI, ATR) written in pure Python — no numpy/pandas.
- **Risk controls**: demo account by default (refuses a real-money account unless `DERIV_ALLOW_REAL_MONEY=true`), dry-run mode, kill-switch file, daily loss limit, daily profit target, max concurrent trades, max trades/day, per-symbol cooldown, stake capped at a fraction of balance and at the remaining daily loss budget.
- **Durable state**: daily counters persisted atomically to disk so a restart cannot clear a halt already triggered by the loss limit; every trade appended to a JSON Lines journal.
- **Deployment**: Dockerfile (non-root, volume-mounted state), docker-compose with `restart: unless-stopped`, and a hardened systemd unit.
- **Tests**: 148 tests, all passing, no network required — indicator maths, the crypto-only filter, every risk limit, state durability across restarts, and full trading cycles against a fake Deriv API.
- **Documentation**: README written for a first-time builder per the standing communication decision — plain language, an explicit risk section up front, a control table for a running bot, and a candid limitations section.

**Build — backtesting (follow-up in the same session)**

- Added `deriv_bot/backtest.py`, closing the gap flagged earlier in this session. It replays historical candles through the **same** `strategy.evaluate` and `risk.RiskManager` the live bot uses, over a trailing window of exactly `CANDLE_COUNT` candles — matching what the live bot fetches each cycle.
- Two supporting changes: `StateStore(persist=False)` for in-memory accounting, and an optional `now` argument on `RiskManager.refresh_daily_limits()` so daily limits roll over against historical timestamps.
- Reports trades, win rate, **breakeven win rate**, net P&L, profit factor, max drawdown, longest losing streak, and signals suppressed by risk limits. Text or `--json` output. Loads candles from a file or fetches from Deriv with pagination.
- **Validated in both directions:** on 30,000 synthetic random-walk candles the default settings produce a 51.4% win rate over 144 trades and a **net loss** — correct, since 51.4% is below the 54.1% breakeven implied by a 0.85 payout. On a synthetic trending series it detects the edge (7/7 wins). A backtester that showed profit on random data would be broken.
- Test count rose from 148 to 183.

**Verification**

- `python -m pytest` → 183 passed.
- All modules import and byte-compile cleanly.
- `.env.example` verified to parse into a valid `Config` with demo-safe defaults and token redaction confirmed.
- Entrypoint verified to exit 2 with a readable message (no traceback) when unconfigured.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Built directly in `app-src/`, not via the staging protocol | The request was a concrete build ("create a bot"), not a business-planning exercise. `app-src/` already holds application source. Staging can wrap this later if it becomes a commercial product. |
| Python rather than the repo's existing TypeScript stack | The bot is a headless long-running daemon, unrelated to the Next.js construction app. Python is the conventional choice for this and adds no coupling. |
| Demo account is the default; real money requires an explicit opt-in | A trading bot that defaults to live funds is a foot-gun. The guard fails closed — a payload missing `is_virtual` is treated as real. |
| Nothing about the Deriv API is hardcoded | No outbound access to Deriv's docs from this sandbox. Discovering symbols, contract types, and duration bounds at runtime is both more robust and independent of unverifiable recall. |
| Poll-based rather than streaming subscriptions | Reconnection after a network blip is a redial, with no subscription state to rebuild — the property that matters most for 24/7 unattended operation. |
| Daily halt persisted to disk | Otherwise restarting the process would be a way to trade past the daily loss limit. |

## Projects Affected

- **New:** `app-src/deriv-crypto-bot/` — standalone application source. Not yet a formal `_AI_Training` project workspace.

## Blockers / Pending Human Actions

- **Owner action required before any use:** create a Deriv API token (Read + Trade scopes only — not Payments or Admin) on a **virtual/demo** account, and populate `.env`. The bot cannot run without it, and no key was created or held by the AI, per the standing API-key decision.
- **Recommended before considering real money:** run with `DERIV_DRY_RUN=true` for an extended period, then on demo, to observe both winning and losing days.
- **Backtesting now exists, but has not been run on real data.** The owner should replay real Deriv history across several months and coins (`python -m deriv_bot.backtest --days 30 --save-candles btc.json`) and compare win rate against breakeven win rate. The strategy has demonstrated **no edge** so far, and correctly shows a loss on random-walk data. Treat it as unproven.

## Standards Sync Status

*(no standards modified this session)*

---
*Live file — updated incrementally. Finalized by closure protocol.*
