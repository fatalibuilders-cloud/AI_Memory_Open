# FMS Trading Bot — Forex, Metals & Stocks with a Phone Remote

An auto-trading bot for **Forex pairs, gold/silver, and stock CFDs**,
controlled entirely **from your phone** via a private Telegram bot: log in
with a password, then start/stop trading, watch balance and positions, close
trades, and get instant push notifications for every trade the bot opens or
closes.

```
 your phone (Telegram) ⇄ Telegram Bot API ⇄ this bot ⇄ broker (MT5 or OANDA)
```

Six broker backends (`BROKER=` in `.env`):

| Backend | Runs on | Markets |
|---|---|---|
| `mt5` | Windows | forex, metals, stock CFDs — any MT5 broker |
| `exness` | Windows | as above, with Exness traits (`m` suffix, IOC filling) |
| `deriv` | Windows | crypto **and** 24/7 synthetic indices (FOK filling) |
| `vantage` | Windows | as `mt5`, with Vantage traits (`+` suffix) |
| `oanda` | any OS | forex, metals |
| `binance` | any OS | crypto futures, 24/7 |

Exness, Deriv and Vantage all speak MetaTrader 5, so they share one
implementation (`broker/mt5.py`); their modules carry only what genuinely
differs. The most important of those is the **order-filling mode** — Deriv
generally requires FOK where Exness accepts IOC, and a wrong mode is
rejected with "Unsupported filling mode". The bot now detects what each
symbol permits and uses the broker's preference as a tie-breaker.

OANDA and Binance have their own REST APIs and implement the `Broker`
interface directly.

## Why the bot doesn't literally run *on* the phone

Android/iOS suspend background apps aggressively — a bot living on a phone
misses entries, drops connections and dies overnight. The reliable setup is
the one every professional uses: the bot runs 24/7 on a Windows PC or a cheap
Windows VPS (~$10/mo) next to the MT5 terminal, and your phone is the **remote
control** with full authority over it. Same convenience, none of the fragility.

## ⚠️ Risk warning

- Leveraged forex/metals/CFD trading can lose money **fast**. Most retail
  accounts lose money. No strategy — including this one — guarantees profit.
- **Always start on an MT5 demo account** (every broker gives you one free)
  and run it for at least a couple of weeks before going live.
- The bot risks a fixed small % of balance per trade (default 0.5%) with a
  hard daily loss stop (default −3%) and **no martingale** — don't raise
  these limits until you understand exactly what they protect you from.
- Beware of Telegram "signal/profit bots" run by anonymous teams (e.g. paid
  signal bots for binary options). Closed-source bots that want your deposit
  or credentials are frequently scams. This bot is open code that runs on
  your own machine — your credentials never leave it.

---

## Setup (once, ~20 minutes)

Pick your broker backend first:

- **Windows machine available, or you want stocks** → follow the MT5 path below.
- **Linux/Mac (or a free Linux VPS)** → use OANDA: open a free practice
  account at oanda.com, then in the account portal → *Manage API Access* →
  generate a token. Put in `.env`: `BROKER=oanda`, `OANDA_API_TOKEN`,
  `OANDA_ACCOUNT_ID` (looks like `101-001-1234567-001`), `OANDA_ENV=practice`,
  and OANDA-style symbols such as `SYMBOLS=EUR_USD,XAU_USD`. Then skip
  straight to step 2 (Telegram) — no MT5 needed, and on Linux
  `deploy/setup-vps.sh` does the install + systemd service in one command.

### 1. Get an MT5 account (MT5 path)

Install [MetaTrader 5](https://www.metatrader5.com/) on a Windows PC/VPS and
open a **demo account** with any MT5 broker (or use your existing broker if
they support MT5). Note the **login number, password, and server name**
(shown in MT5 under *File → Login to Trade Account*).

Symbols depend on the broker, e.g. `EURUSD`, `GBPUSD` (forex), `XAUUSD`
(gold), `XAGUSD` (silver), `AAPL`, `TSLA` (stock CFDs). Check the exact names
in MT5's Market Watch and put them in `SYMBOLS`.

### 2. Create your private Telegram bot

1. In Telegram, message **@BotFather** → `/newbot` → pick a name.
2. Copy the token it gives you into `.env` as `TG_BOT_TOKEN`.
3. Choose a strong `TG_PASSWORD` — this is what you'll type on your phone
   to take control. Anyone with this password controls your trading, so
   treat it like a bank PIN.

### 3. Install & run (on the Windows machine with MT5)

```powershell
cd fms-trading-bot
py -m venv .venv ; .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env    # then edit .env
py main.py
```

### 4. Take control from your phone

Open your bot in Telegram and send:

```
/login <your TG_PASSWORD>
/status
/resume        ← the bot starts paused; this arms auto-trading
```

You'll now get a push notification for every position opened/closed.

## Phone commands

| Command | Effect |
|---|---|
| `/login <password>` | Authorize this phone (persists across restarts) |
| `/status` | Mode, balance/equity, open positions, day stats |
| `/balance` | Balance & equity |
| `/positions` | Open positions with live PnL |
| `/close <ticket>` | Close one position |
| `/closeall` | Close everything now |
| `/resume` / `/pause` | Arm / disarm auto-trading (positions stay open on pause) |
| `/risk <pct>` | Change % of balance risked per trade (max 5) |
| `/logout` | De-authorize this phone |

## How it trades

On every closed candle (default M5) per symbol:

1. **Signal** — EMA-20 crossing above EMA-50 with RSI > 45 → **buy**;
   crossing below with RSI < 55 → **sell**.
2. **Exits set at entry** — stop-loss at 1.5×ATR, take-profit at 2×ATR
   (positive reward:risk), executed broker-side so they trigger even if the
   bot goes offline.
3. **Position size** — by default the stop-loss distance is scaled so a loss
   costs `RISK_PCT`% of balance. Setting **`FIXED_LOT=0.01`** overrides that
   and sends exactly 0.01 lots every trade — the broker minimum, and the
   simplest hard cap on exposure while you are testing (1 pip ≈ $0.10 on
   EURUSD instead of $167 at 0.5% risk).
4. **Risk gate** — every entry must pass: daily trade cap, max open
   positions (total and per symbol), per-symbol cooldown, and the daily loss
   limit; position size is computed so the SL loses exactly `RISK_PCT`% of
   balance.

All parameters are in `.env` (see `.env.example`).

### Interval mode (high-frequency) — demo only

`ENTRY_MODE=interval` makes the bot attempt a trade every
`ENTRY_INTERVAL_SECONDS` in the current trend direction instead of waiting
for a crossover. It exists so you can *watch* what high-frequency trading
actually does to an account. Understand the arithmetic first:

Every trade pays the spread (~1 pip on EURUSD). With 0.5% risk and M1-sized
ATR stops (~3 pips) the computed position is ~16 lots, so 1 pip ≈ **$167 per
trade**. At one trade per 30 seconds that is **~$334/minute**, i.e. a
$100,000 account consumed in roughly **5 hours by spread alone**, before the
market moves at all. Frequency multiplies costs; it does not create edge.

To reach the full rate you must also set `TIMEFRAME=M1`,
`COOLDOWN_SECONDS` ≤ the interval, and raise `MAX_TRADES_PER_DAY` /
`MAX_OPEN_POSITIONS` — the risk gates throttle it on purpose, and the bot
logs a warning naming each limit that is holding it back.

## Copying signals from a Telegram group

`signal_copier.py` reads a signal group you belong to, parses the messages
into orders, and — **in paper mode by default** — logs what it would have
done so you can measure the group before trusting it.

```powershell
pip install telethon
.\.venv\Scripts\python.exe signal_copier.py --list-chats   # find the group id
.\.venv\Scripts\python.exe signal_copier.py                # paper mode
.\.venv\Scripts\python.exe signal_copier.py --report       # the group's record
.\.venv\Scripts\python.exe signal_copier.py --live         # place real orders
```

Setup: get `api_id`/`api_hash` from https://my.telegram.org (API development
tools) into `TG_API_ID` / `TG_API_HASH`, then put the group id in
`SIGNAL_CHAT_ID`.

**Why paper mode is the default.** Signal groups publish their winners and
quietly drop their losers, so their advertised record is meaningless. Paper
mode records every signal as it arrives, which after a few weeks gives you
the group's real hit rate — the only basis for deciding whether to follow it.

**Safety rules the copier enforces:**

- a signal is traded only if it has **both** an explicit stop and target
- signals whose levels are on the wrong side of entry are logged, never traded
- symbols the account doesn't offer are skipped with a clear reason
- all normal risk gates apply (`FIXED_LOT`, daily loss stop, position limits)
- a separate cap on signal orders per day (`--max-per-day`, default 5)
- `--live` requires typing `yes` at a confirmation prompt

**Note on access:** reading a group requires signing in as your own Telegram
account, which creates a `signal_session.session` file granting full access
to your Telegram. It is git-ignored — keep it private, and never share it.

## Multiple brokers — one at a time, or several at once

```powershell
.\.venv\Scripts\python.exe profile.py brokers          # known brokers + naming
.\.venv\Scripts\python.exe profile.py add hfm          # scaffold a profile
notepad .env                                           # fill in its credentials
.\.venv\Scripts\python.exe profile.py use hfm          # switch to one
.\.venv\Scripts\python.exe profile.py use exness,deriv # run BOTH at once
```

Each profile carries its own login, password, server **and symbol list**,
because naming differs per broker — Exness uses `EURUSDm`, most others use
`EURUSD`. Switching never touches your Telegram settings or strategy tuning.

### Running two accounts simultaneously

`ACTIVE_BROKERS=exness,deriv` trades both in one process — for example forex
and gold on Exness during the week, plus crypto or synthetics on Deriv around
the clock. Every account gets:

- its own broker connection, with that broker's traits (Deriv's FOK filling)
- its own symbol list
- **its own risk manager** — daily loss limits and trade caps are per-account,
  so a bad day on one never silences the other
- independent reconnection: one broker going down does not stop the rest

One phone remote covers all of them. `/status` reports each account
separately, `/accounts` lists them, and any command can be scoped by name:

```
/positions deriv      only that account
/closeall exness      close one account's positions
/closeall             close everything, everywhere
```

Note that this multiplies exposure: two accounts at 0.01 lots is 0.02 lots of
real risk, and each account's daily loss limit applies to its own balance.

**Only one MetaTrader 5 account per bot.** The MetaTrader5 python package
drives a single terminal, and logging in with a second account *switches*
that terminal rather than opening a parallel connection — both sessions
would then read and trade the same account while reporting different names.
The bot refuses this combination at startup. Valid combinations:

| Combination | Works |
|---|---|
| one MT5 account (exness *or* deriv *or* vantage) | ✅ |
| MT5 + `binance` | ✅ separate APIs |
| MT5 + `oanda` | ✅ separate APIs |
| `oanda` + `binance` | ✅ |
| exness + deriv (two MT5) | ❌ refused |

To trade two MT5 brokers simultaneously, run a second copy of the bot in its
own folder, with its own **portable** MT5 terminal installation and its own
Telegram bot token.

### Nothing trades? Check Algo Trading first

If orders are rejected with `AutoTrading disabled by client (10027)`, the
**Algo Trading** button in the MT5 toolbar is off. Click it until it is
green. `doctor.py` checks this explicitly, and the bot warns at startup —
this is the most common reason a correctly configured bot never trades.

Brokers that accept Kenyan clients, run MT5, and offer Bitcoin:

| Broker | Crypto | Notes |
|---|---|---|
| HFM | 75+ pairs | CMA-licensed in Kenya, KES accounts |
| Exness | 9 pairs | CMA-licensed, KES accounts, M-Pesa, `m` symbol suffix |
| Pepperstone | BTCUSD ~$15 spread | CMA-licensed, M-Pesa, no KES accounts |
| Deriv | yes + **24/7 synthetic indices** | M-Pesa, very popular in Kenya — see below |
| IC Markets, XM, RoboForex, FBS | yes | see `profile.py brokers` |

### Deriv synthetic indices — the weekend option

Deriv offers **synthetic indices** (Volatility 75, Boom/Crash, Step, Jump)
that trade **24 hours a day, 7 days a week**, including weekends when forex,
metals and stocks are all closed. For a bot that otherwise sits idle from
Friday night to Monday morning, that is a real practical advantage.

```powershell
.\.venv\Scripts\python.exe profile.py add deriv    # pre-fills synthetic symbols
notepad .env                                       # add Deriv MT5 credentials
.\.venv\Scripts\python.exe profile.py use deriv
```

Symbol names contain spaces and are used verbatim, e.g.
`SYMBOLS=Volatility 75 Index,Step Index`. Confirm the exact names your
account offers with `python symbols.py Volatility`.

**Understand what these are before trading them.** Synthetic indices are not
real markets — the prices are generated by Deriv's own random number engine,
audited but wholly internal. There is no external price discovery, no news,
no other participants: Deriv is simultaneously the venue, the price source
and your counterparty. That is not automatically bad (the volatility is
genuinely random rather than manipulated, which arguably makes technical
strategies *more* honest to test), but it is a fundamentally different
proposition from trading EURUSD, and worth knowing before you commit money.
Volatility 75 in particular moves violently — treat `FIXED_LOT=0.01` as a
hard floor there, not a starting point.

Symbol suffixes vary by **account type** as well as broker — confirm with
`python symbols.py BTC` once connected rather than guessing.

## Updating

```powershell
.\update.ps1
```

Does the whole sequence in the right order: stops the bot, kills any
leftover process from this folder, pulls, validates `.env`, restarts, and
prints what changed plus the last few log lines.

Do not just run `git pull` — that only changes files on disk. The running
bot keeps executing the code it loaded at startup, so an update without a
restart looks like nothing happened (new phone commands come back as
"Unknown command"). Running git while the bot holds files open can also
leave git stuck on a `y/n` unlink prompt.

## Does it actually work? — measuring real results

```powershell
.\.venv\Scripts\python.exe report.py --days 7
```

Reads the broker's own deal history, so this is what actually happened
rather than an estimate: win rate, profit factor, average win and loss,
best and worst trade, and a per-symbol and per-day breakdown. It counts
only trades this bot placed (magic 984512) unless you pass `--all`.

**Read the profit factor.** Above 1.0 the configuration makes money;
below 1.0 it loses, and trading more often or bigger only loses faster.

**Sample size matters more than the number.** Under ~30 trades the result
is meaningless; under ~100 treat it as noise in either direction. A run of
luck looks exactly like an edge until it stops.

## Backtesting — measure before you trust

`backtest.py` replays the strategy over real history from your own MT5
terminal and reports what it would actually have returned:

```powershell
.\.venv\Scripts\python.exe backtest.py --symbol EURUSDm --days 30 --balance 50
.\.venv\Scripts\python.exe backtest.py --symbol BTCUSDm --days 30 --preset aggressive
```

It reports trades, win rate, profit factor, max drawdown, end balance and the
average daily return — then projects how long 20x would take at that rate.
The simulation is deliberately pessimistic: entries fill at the next bar's
open (no lookahead), the spread is charged on every entry, and when a bar's
range covers both stop and target it assumes the **stop** was hit.

Read `profit factor` first: below 1.0 the configuration loses money, and no
amount of leverage or frequency fixes a losing edge — it only loses faster.

### Searching for an edge

`optimize.py` grid-searches eight strategies (EMA crossover and its inverse,
Bollinger mean reversion, Bollinger breakout, Donchian breakout, RSI
reversion, momentum, always-with-trend) over parameter ranges,
fits on the first two-thirds of the data and reports each candidate's
performance on the **final third it never saw**:

```powershell
.\.venv\Scripts\python.exe optimize.py --symbol EURUSDm --days 60
```

Two rules for reading it honestly:

1. **In-sample numbers mean nothing.** Fitting parameters to history always
   produces something that looks good.
2. **One out-of-sample survivor out of hundreds also means nothing.** The
   tool prints how many combinations it tried and how many would pass by
   pure luck. A real edge appears across several symbols and periods; a
   coincidence appears in exactly one. Verified: on a synthetic random walk
   with no edge by construction, the search still found a config returning
   +4.3% out-of-sample.

The genuinely useful outcome is often "nothing survived" — that saves you
the money you would have lost finding out live.

### The decisive test — `find_edge.py`

`optimize.py` searches one symbol and *warns* you the survivor may be luck.
`find_edge.py` settles it, and is the tool to run before risking anything:

```powershell
.\.venv\Scripts\python.exe find_edge.py --days 60
```

It applies two tests a single-symbol search cannot:

1. **Across instruments.** A real edge shows up on several symbols; a
   coincidence shows up on exactly one.
2. **Against its own null.** For every symbol it re-runs the identical
   search on *shuffled copies of the same bars* — same volatility, same
   fat tails, every predictable pattern destroyed. Whatever the search
   finds there, it found in nothing. A strategy only counts if it beats
   that, at p < 0.05 on a binomial test.

The second test is the one that matters, and it was not optional. An
earlier version of this tool used a hand-picked bar (profit factor 1.1
over 5 trades) and confidently recommended `ema_cross` on **pure random
walks with no edge in them by construction**. Both tests are verified in
both directions: silent on random walks, and on synthetic series with a
real trend built in it flags breakout, trend-following and momentum on
6 of 6 symbols at p < 0.001.

Judge on profit factor. A win rate is chosen by where you put the stop —
`winrate.py` will engineer any figure you name and show you what it costs.

## Trailing stops (chandelier exit)

The cash ladder (`PROFIT_STAGES`) locks a fixed amount and then stops
helping: a move that runs far gives back everything above the last rung.
A trailing stop keeps following.

```env
TRAIL_ATR_MULT=1.5        # trail 1.5 ATR behind the best price reached
TRAIL_START_MONEY=0.10    # but only once the trade is $0.10 ahead
```

Off by default (`0`). Turn it on without hand-editing the file:

```powershell
.\Set-BotSetting.ps1 TRAIL_ATR_MULT=1.5 TRAIL_START_MONEY=0.10
```

That stops the bot, backs `.env` up, validates the result, restores the
previous file if the new one is unusable, and restarts. Hand-editing
`.env` has caused two outages here — an inline comment that crashed
startup, and Notepad's byte-order mark blanking the first setting — so
the setter quotes `#` values and writes without a mark.

Both settings can be overridden per symbol
(`SYM_XAUUSDM_TRAIL_ATR_MULT=...`), since 1.5 ATR is a different amount of
money on gold than on EURUSD.

Two properties it must have, and both are easy to get wrong:

* **It measures from the peak, not the current price.** Trailing off the
  current price makes the stop follow the trade back down, which is not a
  trailing stop at all.
* **It only ever tightens.** A stop is never moved further from price, so
  it can never give a losing trade more room.

Two things the textbook version leaves out, which the live account would
have hit immediately:

* **The broker's minimum stop distance.** A trailing stop computed close
  to price is rejected with retcode 10011 ("bad stops") and the update is
  simply lost. It is pulled back to the closest legal place instead.
* **The exit side.** A long closes at the bid, not the ask. Tracking the
  peak on the entry side flatters every trade by one spread.

It also refuses to send an update smaller than 10% of the trail distance,
or the stop gets nudged a fraction of a tick every loop and the trade
server throttles you.

Turning trailing on changes what a trade *is*, so it changes the evidence
fingerprint and the record starts scoring again from zero. That is
deliberate — results from the old exits are not evidence about the new
ones.

### Trailing stops from PowerShell

The bot trails continuously once `TRAIL_ATR_MULT` is set. `Trail-Stops.ps1`
does the same job as a standalone tool — for positions opened by hand or
by another EA, or just to watch the arithmetic on real numbers:

```powershell
.\Trail-Stops.ps1                                  # preview, sends nothing
.\Trail-Stops.ps1 -Apply -Multiplier 1.5
.\Trail-Stops.ps1 -Apply -Watch -IntervalSeconds 30
```

PowerShell cannot talk to MetaTrader 5 — its API is a Python package that
speaks to the terminal over local IPC — so the script calls `bridge.py`,
which exposes the bot's own broker layer as JSON (`positions`, `bars`,
`info`, `modify`). Because it is the same layer, the script works against
Exness, Deriv, Vantage, OANDA and Binance unchanged.

`Get-ATR` there is Wilder's ATR and is checked against the Python the bot
actually trades on: on the same 120 bars both return 2.7356467117,
identical to the last digit. Peaks are persisted to `trail_peaks.json`
between passes — a trailing stop that forgets the peak follows the trade
back down.

Stop the bot before running it. Two processes cannot share one MT5
terminal, and both would be moving the same stops.

## Trading more often

Trade count is not a setting. It falls out of four things, three of which
fight each other: how many symbols, how long a position stays open (a
symbol already positioned cannot open another), the entry interval and
cooldown, and the caps. `throughput.py` solves the system:

```powershell
.\.venv\Scripts\python.exe throughput.py --target 2000
.\.venv\Scripts\python.exe throughput.py --target 2000 --apply
```

Hold time is the binding constraint and it is estimated, not guessed: for
a driftless walk absorbed at -a or +b the expected time is a*b over the
per-bar variance, so with the stop at 1.5 ATR and the target at 2.0 ATR a
position lasts about 3 bars. That is 15 minutes on M5 and 3 minutes on
M1 — which is why 2,000/day needs M1 and cannot be reached on M5 with six
symbols, whatever the interval is set to.

Then it prices it, because the spread is charged on every trade whether
it wins or loses, and trading more often multiplies it exactly. On six
symbols at real Exness spreads, 2,000 trades a day costs **$231 a day in
spread alone** — $4,856 a month. Volume cannot create an edge. It
multiplies whatever edge exists, including a negative one.

### Enforcing the rate

`MIN_TRADES_PER_HOUR` holds the pace rather than hoping for it. When the
trailing-hour count falls behind, the entry interval shortens in
proportion to the shortfall, down to `ENTRY_INTERVAL_FLOOR_SECONDS`. It
never lengthens past `ENTRY_INTERVAL_SECONDS` and never drops below the
floor.

But an interval only controls how often the bot *tries*. Whether a try
becomes a trade depends on gates that have nothing to do with the clock —
a symbol already holding a position, a cooldown, the open-position limit,
the daily loss cap. So the more important half is the diagnosis: every
refusal is counted and grouped by the setting you would actually change,
and once an hour the shortfall is reported with the binding one named:

```
0 trades in the last hour, target 100.
What refused the rest:
  60 x one position per symbol
  12 x cooldown
Mostly one position per symbol — raise MAX_POSITIONS_PER_SYMBOL, or add
symbols — the interval cannot help while every symbol is occupied.
```

`/pace` shows the same thing on demand. A bot quietly missing its target
while you adjust the wrong setting is worse than one that tells you which
gate is closed.

## Tests

```powershell
.\.venv\Scripts\python.exe run_tests.py          # all of them
.\.venv\Scripts\python.exe run_tests.py ladder   # one file
```

No pytest, no dependencies. **Every test here is a bug that reached a
live account** — the ladder capping winners at $0.10, a stop that moved
backwards, a safety gate that failed open, an entry path that raised on
every trade. None of them are hypothetical; each one already cost money
once. Run this before pushing and after changing anything in `fmsbot/`.

## A rule-based setup: sweep, structure break, retest

`liquidity_sweep` implements a discretionary-style plan as testable code:

1. **Trend** from a higher timeframe, built by aggregating the entry bars
   (`HTF_RATIO=12` makes 1H from M5, `48` makes 4H). Counter-trend setups
   are discarded, never reversed.
2. **Liquidity**: the previous session's high and low (`SESSION_BARS`),
   where resting stops sit.
3. **The sweep**: price trades through that level and closes back inside,
   leaving a rejection wick worth at least `SWEEP_REJECT` of the bar's
   range. A close *beyond* the level is a breakout, not a sweep, and is
   refused — that single test is what separates the two, and it is
   covered by its own regression test.
4. **The structure break**: within `STRUCTURE_WINDOW` bars, a close past
   the swing the sweep created.
5. **The stop** goes beyond the sweep's extreme — the price that
   invalidates the idea — not at a fixed distance. Target is `RR_TARGET`
   times that risk, default 2.0.

Everything is measured on closed bars, and the sweep extreme is known
before the entry bar, so there is no lookahead.

It is searchable like any other strategy, which is the point — measure it
before it sees money:

```powershell
.\.venv\Scripts\python.exe find_edge.py --days 60 --strategy liquidity_sweep
```

## Rungs in dollars cap your winners

A live account produced this, over and over:

```
XAUUSDm #3159433562 at +2.20 — stage 2/2: stop raised to lock in +0.10
position 3159433562 closed +0.10
```

Every winner closed at exactly `+0.10`. That is the ladder working as
configured, and it is a losing structure. Once the last rung is applied
the stop stops moving, so the trade can never make more than that rung's
lock — while the losses stay full size. With a $9.28 gold stop, capping
winners at $0.10 raises the break-even win rate from **76% to 98.9%**.

Fixed-dollar rungs cannot avoid this, because the right number depends on
the instrument, the volatility and the lot size all at once. So set them
as a share of what the trade is actually aiming at:

```env
PROFIT_STAGES_PCT=50:0,75:50
```

At half the target the stop goes to break-even; at three-quarters it
locks half. That is correct on EURUSD and on gold and on Bitcoin without
being tuned, because it is measured against each trade's own take-profit.
It overrides `PROFIT_STAGES` when set.

The bot also now notices the failure directly: if the last rung's lock is
under 20% of the target, it says so once and shows the fix.

## A hard cap on what one trade may lose

A stop loss is the broker's promise, and promises fail: placed at the
wrong distance, rejected and silently lost, or gapped straight through.

```env
MAX_LOSS_PER_TRADE=1.0
```

The bot then closes any position past that itself, without waiting for
the stop, and says so. It is a backstop, not a replacement — between two
polls the price can still move, so this is a ceiling on what the bot will
tolerate, not a guarantee of the exact loss. It is per-symbol overridable
and off by default.

### Money settings are in the broker's units, not dollars

This bit costs people real money. On an Exness **cent** account, balance,
equity and every position's profit are reported in **cents**. A `0.10`
break-even rung is then a tenth of a cent — cleared by every trade
instantly, so the stop snaps to break-even the moment a position opens
and the protection does nothing at all.

The symptom is unmistakable once you know it: a position showing `+2000`
triggering a stage meant for `+0.10`. The bot now watches for exactly
that — a position two orders of magnitude past the top rung — and says so
once, naming the account currency.

If you are on a cent account, multiply every money setting by 100 or move
to a standard account, then re-run `tune_symbols.py` to derive them from
the account you are actually on.

## The bot keeps score on itself, and stops when it is losing

This is the most important safety feature in the project, and it exists
because of what the live account did: over **139 real trades it won 21.6%
against a 42.9% chance rate — z = -5.07, a one-in-two-million result — and
lost $46.28.** The evidence that it was losing was conclusive by trade 30.
Nothing was watching, so it kept going for another 109.

`fmsbot/evidence.py` now watches. It records every closed trade and asks
one question of the running total: *could a strategy with no edge at all
have produced this?*

- **Losing beyond chance** → trading halts, and Telegram says why.
  Replayed against that real 139-trade record, the halt fires at trade 30
  and the loss stops at **-$10.55 instead of -$48.66**.
- **Never proved anything** → real-money accounts are refused entirely.
  Demo is where a configuration earns the right to trade money.
  (`LIVE_REQUIRES_EVIDENCE=false` overrides this, deliberately.)
- **Winning beyond chance** → it says so, and calls it permission to keep
  testing rather than permission to add money.

Check it any time from your phone with `/evidence`, and `/evidence reset`
after you change something real. The record is keyed to a fingerprint of
the settings that produced it, so changing the strategy, timeframe or
exits starts the scoring again by itself — results from a different
configuration are not evidence about this one.

The threshold is p < 0.01, not the usual 0.05, because the test runs after
every single trade and repeated looks at growing data find "significance"
by chance far more often than one look does. Verified against 300
simulated zero-edge records: 1.7% were misjudged, inside the 1% alpha plus
sampling error, and a genuine edge is still recognised.

## One size does not fit gold, Bitcoin and EURUSD

The live account's own record made this unavoidable: metals were 8% of the
trades and 77% of the losses. Not because gold is unpredictable, but because
a single set of settings was applied to instruments whose spreads differ by
two orders of magnitude. A $0.50 target is four times the spread on EURUSD,
about *equal* to the spread on gold, and rounding error on Bitcoin. On gold
that trade could not pay even when the direction was right.

`tune_symbols.py` measures each instrument in your own terminal — real
spread, real ATR, the broker's minimum stop distance, the cash value of a
price move at your lot size — and solves for settings that pass the bot's
own filters **by construction**:

```powershell
.\.venv\Scripts\python.exe tune_symbols.py           # measure and show
.\.venv\Scripts\python.exe tune_symbols.py --apply   # write them to .env
```

Stop the bot first — two processes sharing one MT5 terminal interfere. The
`--apply` run keeps a backup in `.env.bak`.

`retune.ps1` does that whole sequence for you — stops the bot, edits `.env`,
measures, validates and restarts — and refuses to write anything that would
leave an account with no symbols:

```powershell
.\retune.ps1                                    # preview, changes nothing
.\retune.ps1 -Apply                             # commit the tuned values
.\retune.ps1 -Apply -Drop USDCHFm,NZDUSDm -Stages "0.10:0,0.25:0.10"
```

It writes `SYM_<SYMBOL>_<SETTING>` lines, which override the shared value
for that instrument only:

```env
SYM_EURUSDM_SL_MONEY=0.80
SYM_EURUSDM_TP_MONEY=1.07
SYM_EURUSDM_PROFIT_STAGES=0.213:0,0.533:0.213
SYM_XAUUSDM_SL_MONEY=2.25
SYM_XAUUSDM_TP_MONEY=3.00
SYM_XAUUSDM_PROFIT_STAGES=0.6:0,1.5:0.6
```

Two things worth understanding before you use the numbers:

* **The break-even ladder is scaled too, and it has to be.** A rung at
  $0.25 is half a EURUSD target and rounding error on gold — the same
  figure protects one instrument and never fires on another. Each rung
  keeps the *fraction* of the target it had, so the protection behaves
  identically everywhere.
* **It also checks whether you can afford the instrument.** Tuning a
  symbol to its own spread says nothing about whether the account can
  carry it. Lot sizes have a floor, so on gold the *smallest position the
  broker accepts* can still risk more in one trade than your daily loss
  cap allows. The tool prints each stop as a share of your balance and the
  balance the instrument would need to obey your own risk rule. When a
  symbol is over that line, no setting fixes it — fund the account or drop
  the symbol.
* **The tuned targets will be larger than what you asked for.** That is the
  measurement talking, not a preference. A target that does not clear the
  round trip by a real multiple is a losing trade with extra steps, and
  raising it is the only honest way to fix that. If the required target
  looks too big to hit, the instrument is telling you it is not worth
  trading at this timeframe — which is why the tool marks symbols whose
  spread exceeds half their ATR as too wide, and says to drop them.

Setting names are matched on letters and digits only, so broker suffixes and
spaces do not matter: `EURUSDm` → `SYM_EURUSDM_`, `Volatility 75 Index` →
`SYM_VOLATILITY75INDEX_`. `check_config.py` prints which overrides loaded and
flags any that name a symbol you are not trading.

## Project layout

```
fms-trading-bot/
├── main.py                # entry point
├── .env.example           # copy to .env and fill in
├── doctor.py              # why is it not trading?
├── report.py              # what your real trades actually did
├── backtest.py            # replay the strategy over history
├── optimize.py            # search strategies, judge out-of-sample
├── find_edge.py           # is it an edge, or noise? the decisive test
├── winrate.py             # engineer any win rate, and see its cost
├── tune_symbols.py        # per-instrument settings from real spreads
├── check_config.py        # validate .env before restarting
├── throughput.py          # solve for a trades-per-day target, and price it
├── Set-BotSetting.ps1     # change a setting safely, then restart
├── bridge.py              # the broker as JSON, for other languages
├── Trail-Stops.ps1        # ATR trailing stops from PowerShell
└── fmsbot/
    ├── config.py          # settings
    ├── indicators.py      # EMA / RSI / ATR (pure python)
    ├── strategy.py        # EMA-cross + RSI filter, ATR exits
    ├── risk.py            # daily limits + risk-based sizing
    ├── telegram.py        # phone remote (stdlib, long-polling)
    ├── bot.py             # orchestrator
    └── broker/
        ├── __init__.py    # build_broker() factory
        ├── base.py        # Broker interface
        ├── mt5.py         # MetaTrader 5 engine (Windows)
        ├── exness.py      # Exness traits   (MT5 subclass)
        ├── deriv.py       # Deriv traits    (MT5 subclass, synthetics)
        ├── vantage.py     # Vantage traits  (MT5 subclass)
        ├── oanda.py       # OANDA v20 REST adapter (any OS)
        └── binance.py     # Binance USD-M Futures REST adapter (any OS)
```

## Running it 24/7 for free

See [deploy/DEPLOY.md](deploy/DEPLOY.md):

- **MT5 mode** — AWS free-tier Windows (12 months) or your broker's free VPS;
  `deploy/setup-windows.ps1` handles install, auto-start and crash-restart.
- **OANDA mode** — Oracle Cloud Always-Free Linux VM (free forever);
  `deploy/setup-vps.sh` does the same via systemd.

## Troubleshooting

- **`MetaTrader5 package not available`** — you're not on Windows, or
  `pip install MetaTrader5` failed. The bot must run where the MT5 terminal is.
- **`MT5 initialize failed`** — check MT5_LOGIN/PASSWORD/SERVER; set `MT5_PATH`
  to the full path of `terminal64.exe`; make sure *Algo Trading* is enabled in
  the MT5 terminal (button in the toolbar).
- **`No bars for SYMBOL`** — wrong symbol name for your broker; check Market
  Watch in MT5 (right-click → Show All).
- **Order rejected `Invalid volume`/`Market closed`** — stock CFDs trade only
  during exchange hours; forex/metals close on weekends.
- **No Telegram replies** — wrong `TG_BOT_TOKEN`, or the server has no
  outbound internet access to api.telegram.org.
