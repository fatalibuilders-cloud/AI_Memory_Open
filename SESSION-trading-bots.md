# Session Log — Building Automated Trading Bots

**Date:** 25 July 2026
**Branch:** `claude/pocket-option-trading-bot-g8dnqk`
**Operator:** Eng Ali (Kenya) · **Broker:** Exness (CMA-licensed) · **Machine:** Windows

---

## What Was Built

Two independent trading bots plus a full analysis toolkit, in 18 commits.

| Project | Purpose | Status |
|---|---|---|
| `pocket-option-bot/` | Binary options on Pocket Option via its WebSocket feed | Built, untested live |
| `fms-trading-bot/` | Forex / Metals / Stocks / Crypto via MetaTrader 5, phone-controlled | **Running live on demo** |

The second one is the working system. It connects to an Exness MT5 demo
account, streams prices, evaluates a strategy on closed candles, and places
orders with stop-loss and take-profit set broker-side — all controlled from a
phone through a private Telegram bot.

---

## Final Working Setup

```
phone (Telegram) ⇄ Telegram Bot API ⇄ bot (Windows PC) ⇄ MetaTrader 5 ⇄ Exness
```

**Live configuration:**

| Setting | Value |
|---|---|
| Account | Exness demo `436966088` (`ExnessKE-MT5Trial9`), $100,009 |
| Symbols | `EURUSDm`, `XAUUSDm` (+ `BTCUSDm` pending confirmation) |
| Timeframe | M5 |
| Strategy | EMA 20/50 crossover, RSI filter, ATR stops |
| Position size | `FIXED_LOT=0.01` |
| Daily loss stop | 3% (15% on aggressive preset) |
| Auto-arm | `START_PAUSED=0` |

**Phone commands:** `/login` `/status` `/balance` `/positions` `/close` `/closeall`
`/resume` `/pause` `/risk` `/logout`

**Keep running:** `Start-ScheduledTask -TaskName FMSTradingBot` — auto-starts at
boot, restarts on crash. MT5 must stay open; the PC must not sleep.

---

## The Debugging Trail

Every failure encountered, and what actually fixed it. Most were my bugs.

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | `..venvScriptspython.exe` not found | Commands written for PowerShell, pasted into Git Bash | Use PowerShell, or forward slashes |
| 2 | `python--version` not recognised | Missing space in the typed command | `python --version` |
| 3 | Multi-line pastes fused into one line | PowerShell strips newlines on paste | Paste one line at a time; use `;` separators |
| 4 | `Cannot find path` / `not a git repository` | Running from `C:\Users\Eng Ali` instead of the bot folder | Always `cd` first |
| 5 | `fms-trading-bot` folder missing | Clone had only `main`; work lives on a feature branch | `git checkout claude/pocket-option-...` |
| 6 | `ValueError: could not convert '0.5   # % of balance...'` | **My bug** — dotenv loader kept inline comments | Strip ` #` comments from unquoted values |
| 7 | `MT5 initialize failed: Process create failed` | `MT5_PATH` pointed at the folder, not the `.exe` | Point at `terminal64.exe`, or leave blank |
| 8 | Endless connect → `No bars for EURUSD` → reconnect | Exness names symbols with an `m` suffix | `SYMBOLS=EURUSDm,XAUUSDm` |
| 9 | `Symbol EURUSDM does not exist` | **My bug** — config force-uppercased symbol names | Preserve case; added case-insensitive resolution |
| 10 | One bad symbol killed the whole session | **My bug** — per-symbol error escaped the trading loop | Isolate per symbol; only escalate if *all* fail |
| 11 | "It's still not trading" (×4) | Two causes stacked: wrong symbol names, and `START_PAUSED=1` re-pausing after every restart | `doctor.py` + `START_PAUSED=0` |
| 12 | `SyntaxWarning: "\." invalid escape` | **My bug** — non-raw docstring | Raw string |

**The breakthrough:** rather than keep guessing at #11, I wrote `doctor.py` — a
read-only diagnostic that walks the entire path from config to order and names
the blocker. It found the wrong symbol names in one run, after several rounds
of failed guesses.

---

## Tools Built

| Tool | What it answers |
|---|---|
| `doctor.py` | "Why isn't it trading?" — config, connection, per-symbol data, signal history, risk gates, verdict |
| `symbols.py` | "What instruments does my account actually have?" — grouped, filterable, flags disabled ones |
| `backtest.py` | "What would this configuration have returned?" — win rate, profit factor, drawdown, projection |
| `optimize.py` | "Does *any* strategy here have an edge?" — grid search with out-of-sample validation |
| `preset.py` | Switch between conservative / balanced / aggressive tuning safely |

---

## The Evidence

### Backtest — three presets, 30 days of M5 data, $50 start, 0.01 lot

| Preset | Trades | Win rate | Profit factor | $50 became | Max drawdown |
|---|---|---|---|---|---|
| Conservative | 43 | 34.9% | 0.92 | $48.93 (−2%) | 6% |
| Balanced | 43 | 34.9% | 0.74 | $46.40 (−7%) | 8% |
| Aggressive | 198 | 16.2% | 0.49 | $21.67 (−57%) | 58% |

**Aggression made it dramatically worse.** 4.6× the trades produced 4.6× the
costs and under half the win rate.

### The spread test — same strategy, same period, only costs varied

| Spread | Return |
|---|---|
| Zero | **+9.6%** |
| Realistic (1.2 pip) | **−7.2%** |
| Wide (5 pip) | **−39.8%** |

The strategy has a slight edge *before* costs. Trading costs consume it
entirely. This single comparison explains why high-frequency trading destroys
small accounts.

### The random-walk test — why "profitable backtests" are usually noise

The optimizer was run on a **pure random walk** — data with mathematically zero
edge by construction. Out of 583 combinations tried, it still produced a
"winner" showing **+4.3% out-of-sample**.

That is how every Telegram "profit bot" screenshot is manufactured: try
hundreds of settings, publish the one that looked good, never mention the rest.
`optimize.py` now prints this warning itself.

**Standard for believing any result:** it must survive on *more than one
symbol* and *more than one period*. Real edge repeats; luck appears once.

---

## Targets Discussed

Three targets were requested. Each was assessed honestly:

**"A trade every 30 seconds"** — Built as opt-in `ENTRY_MODE=interval`. At 0.5%
risk sizing this costs ~$167/trade in spread (~$334/minute), draining $100k in
about 5 hours *before the market moves*. With `FIXED_LOT=0.01` it drops to
~$0.10/trade, making it survivable enough to observe. The mode exists so the
effect can be watched, not because it is advisable.

**"$50 → $1,000 in 8 hours"** — Not reachable. $50 at 1:400 leverage controls
~0.2 lots; $950 profit requires ~475 pips on EURUSD (daily range: 60–100) or a
$47 move in gold (daily range: $20–40). This is the market's speed limit, not a
configuration problem.

**"$50 → $1,000 every month"** — Mathematically self-refuting. 20×/month
compounded for a year turns $50 into **$2×10¹⁷** — roughly 2,000× all the money
on Earth. It also equals 10%/day sustained, against the best fund in history
(Renaissance Medallion) at ~66%/**year**. If such a configuration existed, its
owner would own the world economy within a year.

**What is real:** the only honest route is a strategy with profit factor above
1.0 *after costs*, verified across multiple symbols and periods, then compounded
patiently. The current EMA crossover does not clear that bar (PF 0.49–0.92). The
toolkit exists to find one that does — or to prove none of these do, which saves
the money that would have been lost discovering it live.

---

## Safety Decisions Kept Throughout

Two things were deliberately never added, despite aggressive targets:

1. **No martingale.** Doubling down after losses is the fastest route to zero.
2. **Fixed 0.01 lots.** On a $50 account this is the difference between a bad
   run costing 15% and costing everything.

Also enforced: demo-first everywhere, live mode requiring explicit confirmation,
credentials only in git-ignored `.env` files, password-gated phone access with
brute-force throttling, and hard daily loss stops that pause the bot for the day
rather than "recovering".

---

## Where Things Stand

**Working:** MT5 connection, live price data on EURUSDm, strategy producing
signals (5 in 25 hours), risk gates, phone control, auto-restart, full analysis
toolkit.

**Open:** BTC symbol name unconfirmed (`symbols.py BTC` will settle it); the
optimizer has not yet been run on real Exness data.

**Next:**

1. `symbols.py BTC` → finalise symbol list
2. `optimize.py --symbol EURUSDm --days 60` → real-data edge test
3. Same on `XAUUSDm` → does anything survive on *both*?
4. Let the demo run the week; review trade count, win rate, daily PnL on Friday

**Market hours reminder:** forex and metals closed from Friday ~midnight to
Monday ~1am Kenyan time. Crypto trades 24/7 — the only thing that can trade over
a weekend.

---

## Honest Summary

A complete, working, well-instrumented trading system was built and is running.
What has *not* been established is that it makes money — and the evidence
gathered so far says this particular strategy does not, once trading costs are
counted.

That is a genuinely valuable outcome. The measurement tools now exist to test
any future strategy in seconds rather than losing weeks of demo time, or worse,
real money. The bot is the easy part; finding a real edge is the hard part, and
it has not been found yet.

**Do not fund a live account until something clears profit factor 1.0
out-of-sample on multiple symbols and survives weeks of demo trading.**
