# FMS Trading Bot — Forex, Metals & Stocks with a Phone Remote

An auto-trading bot for **Forex pairs, gold/silver, and stock CFDs**,
controlled entirely **from your phone** via a private Telegram bot: log in
with a password, then start/stop trading, watch balance and positions, close
trades, and get instant push notifications for every trade the bot opens or
closes.

```
 your phone (Telegram) ⇄ Telegram Bot API ⇄ this bot ⇄ broker (MT5 or OANDA)
```

Two interchangeable broker backends (`BROKER=` in `.env`):

| Backend | Runs on | Markets |
|---|---|---|
| `mt5` (MetaTrader 5) | Windows only | forex, metals, stock CFDs |
| `oanda` (REST API) | Linux / Mac / Windows | forex, metals |

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

`optimize.py` grid-searches four strategies (EMA crossover, Bollinger mean
reversion, Donchian breakout, always-with-trend) over parameter ranges,
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

## Project layout

```
fms-trading-bot/
├── main.py                # entry point
├── .env.example           # copy to .env and fill in
└── fmsbot/
    ├── config.py          # settings
    ├── indicators.py      # EMA / RSI / ATR (pure python)
    ├── strategy.py        # EMA-cross + RSI filter, ATR exits
    ├── risk.py            # daily limits + risk-based sizing
    ├── telegram.py        # phone remote (stdlib, long-polling)
    ├── bot.py             # orchestrator
    └── broker/
        ├── base.py        # Broker interface
        ├── mt5.py         # MetaTrader 5 adapter (Windows)
        └── oanda.py       # OANDA v20 REST adapter (any OS)
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
