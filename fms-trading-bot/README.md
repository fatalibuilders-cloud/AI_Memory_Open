# FMS Trading Bot — Forex, Metals & Stocks with a Phone Remote

An auto-trading bot for **Forex pairs, gold/silver, and stock CFDs** through
**MetaTrader 5**, controlled entirely **from your phone** via a private
Telegram bot: log in with a password, then start/stop trading, watch balance
and positions, close trades, and get instant push notifications for every
trade the bot opens or closes.

```
 your phone (Telegram) ⇄ Telegram Bot API ⇄ this bot ⇄ MetaTrader 5 ⇄ your broker
```

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

### 1. Get an MT5 account

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
3. **Risk gate** — every entry must pass: daily trade cap, max open
   positions (total and per symbol), per-symbol cooldown, and the daily loss
   limit; position size is computed so the SL loses exactly `RISK_PCT`% of
   balance.

All parameters are in `.env` (see `.env.example`).

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
        ├── base.py        # Broker interface (add OANDA/Alpaca here later)
        └── mt5.py         # MetaTrader 5 adapter
```

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
