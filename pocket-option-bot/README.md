# Pocket Option Auto-Trading Bot

A Python bot that connects to your Pocket Option account over the platform's
live WebSocket feed, streams prices, builds candles, runs a technical strategy
(RSI + EMA filter, or Bollinger reversal) and places binary-option trades
automatically — with strict, non-negotiable risk limits.

---

## ⚠️ Read this first

1. **Pocket Option has no official public API.** This bot speaks the same
   WebSocket protocol the Pocket Option web app uses and signs in with your
   browser session (SSID). Pocket Option can change the protocol at any time,
   which would break the bot until it's updated. Automated trading may also
   violate Pocket Option's Terms of Service — accounts have been suspended for
   it. You use this at your own risk.
2. **Binary options are extremely high risk.** A losing trade loses 100% of the
   stake, while a winning trade pays out ~70–92%. That asymmetry means even a
   50%-accurate strategy loses money over time. No strategy in this repo (or
   anywhere) guarantees profit. **Never trade money you can't afford to lose.**
3. **Beware of third-party "signal bots"** (Telegram bots, paid signal groups,
   "AI profit bots"). Anything that asks for your deposit, your password, or a
   fee to "guarantee profits" is almost certainly a scam. This bot is
   open-source, runs only on your machine, and your credentials never leave it.
4. **Always start on the demo account** (`PO_DEMO=1`, the default) and run it
   for days, not minutes, before even considering live mode.

---

## Setup

### 1. Install

```bash
cd pocket-option-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Requires Python 3.10+.

### 2. Get your SSID (session credential)

The bot authenticates the same way your browser does, using the session frame
the web app sends when it connects:

1. Open https://pocketoption.com in Chrome/Edge/Firefox and **log in**.
   Switch to the **demo** account first (top-right balance switcher).
2. Open DevTools (`F12`) → **Network** tab → filter by **WS** (WebSocket).
3. Reload the page. Click the WebSocket connection to `po.market` and open the
   **Messages / Frames** panel.
4. Find the outgoing (client → server) frame that starts with `42["auth",` —
   it looks like:
   ```
   42["auth",{"session":"a1b2c3...","isDemo":1,"uid":12345678,"platform":2}]
   ```
5. Copy the **entire** frame and paste it into `.env` as `PO_SSID=...`.

Notes:
- A demo-session frame has `"isDemo":1`; a live-session frame has `"isDemo":0`.
  To trade live later you must capture the SSID **while the live account is
  selected** in the browser.
- The session expires when you log out (and periodically). If the bot reports
  auth timeouts, re-capture a fresh SSID.
- **Treat the SSID like a password.** Anyone who has it can operate your
  account. `.env` is git-ignored — keep it that way.

### 3. Run

```bash
# Demo account (default) — do this first
python main.py

# Watch signals without placing any orders at all
python main.py --dry-run

# Override settings ad hoc
python main.py --asset EURUSD_otc --stake 1 --expiry 60 --strategy bollinger

# LIVE account — asks for confirmation, real money at risk
python main.py --live
```

The bot warms up first (default: 60 closed candles ≈ 1 hour on the 1-minute
timeframe) so its indicators have real data, then trades signals as they occur.
Stop it any time with `Ctrl+C`.

---

## How it decides to trade

```
tick stream ─→ 1-min candles ─→ strategy signal ─→ risk manager ─→ order
```

**Strategies** (`PO_STRATEGY`):

- `rsi_ema` (default): CALL when RSI ≤ 30 **and** price is above the EMA-50
  (dip in an uptrend); PUT when RSI ≥ 70 **and** price is below the EMA-50.
  The EMA filter stops it from fighting the trend.
- `bollinger`: classic band-reversal — CALL on a close below the lower band,
  PUT on a close above the upper band.

**Risk manager** — every trade must pass all of these, and when a stop trips
the bot stops for the day (it deliberately has **no martingale/recovery**
mode, because doubling-down after losses is the fastest way to zero):

| Limit | Default | Env var |
|---|---|---|
| Stake per trade | $1 (capped at $50) | `PO_STAKE`, `PO_MAX_STAKE` |
| Stake as % of balance | off | `PO_STAKE_PCT` |
| Max trades per day | 20 | `PO_MAX_TRADES_PER_DAY` |
| Max consecutive losses | 3 | `PO_MAX_CONSECUTIVE_LOSSES` |
| Daily loss limit | $20 | `PO_DAILY_LOSS_LIMIT` |
| Daily profit target (stop when reached) | off | `PO_DAILY_PROFIT_TARGET` |
| Cooldown between trades | 120 s | `PO_COOLDOWN_SECONDS` |
| Open positions at once | 1 (hardcoded) | — |

---

## Project layout

```
pocket-option-bot/
├── main.py                 # CLI entry point
├── requirements.txt
├── .env.example            # copy to .env and fill in
└── pocket_bot/
    ├── config.py           # settings from .env
    ├── client.py           # Pocket Option WebSocket client (auth, stream, orders)
    ├── candles.py          # tick → OHLC candle aggregation
    ├── indicators.py       # RSI, EMA, SMA, Bollinger (pure python)
    ├── strategy.py         # signal strategies
    ├── risk.py             # money management / daily stops
    └── bot.py              # orchestration + reconnect loop
```

## Troubleshooting

- **"Auth timed out"** — SSID expired or malformed. Re-capture it (step 2).
  Also check `PO_DEMO` matches the account the SSID came from.
- **"Could not authenticate on any region"** — usually an expired SSID; can
  also be a protocol change on Pocket Option's side.
- **Connected but no ticks** — the asset may be closed; try an `_otc` asset
  (e.g. `EURUSD_otc`), OTC markets run 24/7.
- **Orders rejected** — stake below the platform minimum ($1), asset closed,
  or expiry not supported for that asset.

## Running it 24/7 for free

See [deploy/DEPLOY.md](deploy/DEPLOY.md) — step-by-step guide for an Oracle
Cloud Always-Free VM, with `deploy/setup-vps.sh` doing the install,
auto-start-on-boot and auto-restart-on-crash in one command.

## Extending

Add a strategy by subclassing `Strategy` in `pocket_bot/strategy.py` and
registering it in the `STRATEGIES` dict — it gets the full candle history and
returns `"call"`, `"put"`, or `None` on each closed candle.
