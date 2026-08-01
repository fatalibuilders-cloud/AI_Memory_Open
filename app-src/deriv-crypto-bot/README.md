# Deriv Crypto Bot

An automated trading bot for [Deriv](https://deriv.com) that trades **cryptocurrency only** and runs **24/7**.

It watches crypto markets on a schedule, looks for a specific price pattern, and places a trade when it finds one — then keeps doing that indefinitely, reconnecting on its own when the network drops.

---

## Read this first

**This bot can lose money.** It places real trades when pointed at a real account. Automated trading does not make losses less likely — it makes them faster and unattended. Nothing here predicts the market; the strategy is a simple, well-known pattern rule that will have losing days.

Three things follow from that, and they are built into the bot rather than left to you to remember:

1. **It runs on a demo account by default.** If your token belongs to a real-money account, the bot refuses to start unless you explicitly set `DERIV_ALLOW_REAL_MONEY=true`.
2. **It stops itself after a set daily loss.** `DAILY_LOSS_LIMIT` halts trading for the rest of the UTC day. That halt is written to disk, so restarting the bot does **not** clear it.
3. **You can stop it instantly.** Create a file called `KILL_SWITCH` in the bot's folder and it stops opening trades within seconds.

Run it on demo for long enough to see it win *and* lose before you consider anything else. Only risk money you can afford to lose entirely.

---

## What it actually does

Every 30 seconds (configurable), the bot runs one cycle:

1. **Checks on open trades** and records any that have finished, win or lose.
2. **Checks its limits** — daily loss, daily trade count, kill switch. If any is hit, it stops there.
3. **Asks Deriv which crypto markets are open** and picks its universe from that list.
4. **Downloads recent price candles** for each symbol and looks for a signal.
5. **Places a trade** if a signal appears and every risk check passes.

### The strategy

A standard **EMA crossover with two filters**:

- **Signal** — a fast moving average (9 candles) crossing a slow one (21 candles). Crossing up suggests upward momentum → a *Rise* (CALL) contract. Crossing down → a *Fall* (PUT) contract.
- **RSI filter** — skip the trade if the move already looks exhausted (RSI above 70 for a buy, below 30 for a sell). This avoids buying the top of a spike.
- **Volatility filter** — skip the trade if the two averages are too close together relative to recent volatility (ATR). In a flat, choppy market the averages cross constantly and none of it means anything; this filter throws those away.

Every decision the bot makes, including every *refusal* to trade, is logged with its reason.

The strategy lives in one file, `deriv_bot/strategy.py`. Replacing it means writing a function with the same shape — nothing else in the bot needs to change.

### How "crypto only" is enforced

The bot never trades forex, synthetic indices, commodities, or stocks. That is enforced at three independent points:

1. Symbols are **discovered** from Deriv's own market listing and filtered to `market == "cryptocurrency"`. Nothing is hardcoded.
2. If you name symbols in `DERIV_SYMBOLS`, they are still checked against that same filter — putting a forex pair there drops it with an error in the log rather than trading it.
3. A final check immediately before every purchase confirms the symbol is still in the verified crypto set for that cycle.

There are tests for all three. See `tests/test_cycle.py::TestCryptoOnly`.

---

## Setup

You need Python 3.10 or newer.

### 1. Get your Deriv credentials

- **App ID** — register at [developers.deriv.com](https://developers.deriv.com). To start, you can use `1089`, Deriv's public testing app ID.
- **API token** — in your Deriv account, go to **Settings → API token**. Create one with the **Read** and **Trade** scopes.
  - Do **not** tick "Payments" or "Admin". The bot never needs them.
  - Make sure you are on your **virtual (demo)** account when you create it.

### 2. Install

```bash
cd app-src/deriv-crypto-bot
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Open `.env` and set `DERIV_APP_ID` and `DERIV_API_TOKEN`. Everything else has a working default.

> `.env` is git-ignored. Never commit it — the token in it can trade your account.

### 4. Backtest it

See [Backtesting](#backtesting) below. Do this before anything else — it costs nothing and tells you whether the strategy is worth running at all.

### 5. Watch it think before it trades

```bash
DERIV_DRY_RUN=true python -m deriv_bot
```

Dry run does everything except buy: it finds signals and prices real contracts, and logs what it *would* have done. This is the best way to understand its behaviour. Leave it running for a few hours.

### 6. Run it

```bash
python -m deriv_bot
```

Stop with `Ctrl+C` — it finishes the current cycle and shuts down cleanly.

---

## Backtesting

Before running the bot with money, test the strategy on historical prices:

```bash
# Download 30 days of 1-minute candles and replay them
python -m deriv_bot.backtest --symbol cryBTCUSD --days 30 --save-candles btc.json

# Re-run on the saved file (no network, instant)
python -m deriv_bot.backtest --from-file btc.json --symbol cryBTCUSD
```

The backtester drives the **same** strategy and risk code the live bot uses, over a trailing window of exactly `CANDLE_COUNT` candles — which is what the live bot fetches each cycle. So a result reflects the bot's real decision path, not a separate reimplementation of it.

The number to look at is **breakeven win rate**:

```
  Trades               144  (74W / 70L)
  Win rate             51.4%
  Breakeven win rate   54.1%   <-- must beat this
```

With a 0.85 payout, a win gains 0.85 and a loss costs 1.00. That means you need to be right **54.1%** of the time just to break even. A 51% win rate is not "almost profitable" — it is a losing strategy. The report says so plainly.

### What the backtest cannot tell you

**The payout ratio is an assumption, not a measurement.** Deriv prices each contract from live volatility at the moment of purchase, and that price is not recoverable from historical candles. The backtest applies one fixed ratio (`--payout-ratio`, default 0.85) to every trade. This is the single largest source of error in the result.

Three further gaps, all of which flatter the results:

- no spread or slippage is modelled,
- contracts settle from the candle close at expiry, ignoring what happened inside the candle,
- an exact tie is scored as a loss (correct for Deriv's rules) but measured against candle closes rather than ticks.

**Treat a backtest that barely clears breakeven as a losing strategy.** And run several — one period is not evidence.

For reference: replaying the default settings over a synthetic random walk (a market with no exploitable pattern by construction) produces a 51.4% win rate and a net loss. That is the correct and expected answer, and a useful sanity check that the tool is not flattering anything.

---

## Running it 24/7

`python -m deriv_bot` in a terminal stops when you close the terminal. For genuinely continuous operation, use one of these.

### Docker (simplest)

```bash
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml logs -f
```

`restart: unless-stopped` brings it back after a crash or a host reboot.

### systemd (on a Linux server or VPS)

```bash
sudo cp deploy/deriv-crypto-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now deriv-crypto-bot
journalctl -u deriv-crypto-bot -f
```

Edit the paths in the unit file first to match where you installed it.

Either way, **keep the `state/` directory on persistent storage**. That is where the daily loss counter lives. If it is wiped on restart, the daily loss limit resets with it — and a limit that resets is not a limit.

---

## Controlling a running bot

| I want to… | Do this |
|---|---|
| Stop trading right now | `touch KILL_SWITCH` — takes effect within one cycle |
| Resume | `rm KILL_SWITCH` |
| See what it's doing | `docker compose -f deploy/docker-compose.yml logs -f`, or `journalctl -u deriv-crypto-bot -f` |
| See why it *isn't* trading | Set `LOG_LEVEL=DEBUG` — it logs a reason for every symbol it skips |
| Review every trade taken | `cat state/trades.jsonl` — one JSON object per event |
| Check today's P&L | `cat state/bot-state.json` |
| Clear a halt before the day ends | Stop the bot, edit `halted` to `false` in `state/bot-state.json`, restart. Do this deliberately — the halt exists for a reason. |

---

## Settings worth knowing

Full list with comments in `.env.example`. The ones that matter most:

| Setting | Default | What it does |
|---|---|---|
| `DERIV_ALLOW_REAL_MONEY` | `false` | Must be `true` before the bot will touch a real account |
| `DERIV_DRY_RUN` | `false` | Find signals and price contracts, but never buy |
| `STAKE` | `1.0` | Amount per trade, in the account currency |
| `MAX_STAKE_FRACTION` | `0.02` | Hard cap: never stake more than 2% of balance, whatever `STAKE` says |
| `DAILY_LOSS_LIMIT` | `20.0` | Stop trading for the UTC day at this much loss |
| `MAX_OPEN_TRADES` | `2` | How many positions can be open at once |
| `MAX_TRADES_PER_DAY` | `40` | Ceiling on trades opened per UTC day |
| `SYMBOL_COOLDOWN` | `300` | Seconds before the same symbol can be traded again |
| `DERIV_SYMBOLS` | *(blank)* | Blank = all open crypto. Otherwise a comma-separated allowlist |
| `TRADE_DURATION` / `_UNIT` | `5` / `m` | Contract length. Clamped to what Deriv allows for that symbol |

The stake actually used is the **smallest** of: `STAKE`, `MAX_STAKE_FRACTION` × balance, and your remaining daily loss budget. A single trade can never take you past the daily limit in one go.

---

## Tests

```bash
pip install pytest
python -m pytest
```

183 tests covering the indicator maths, the crypto-only filter, every risk limit, state durability across restarts, full trading cycles against a fake Deriv API, and the backtester's accounting. No network access needed.

---

## How the code is organised

```
deriv_bot/
├── __main__.py     Entry point: config, logging, signal handling
├── config.py       Every setting, loaded from the environment
├── api.py          Deriv WebSocket client — requests, reconnection, keepalive
├── market.py       Crypto-only filtering and contract/duration resolution
├── indicators.py   EMA, RSI, ATR in pure Python
├── strategy.py     Signal generation — swap this to change behaviour
├── risk.py         Limits and position sizing
├── state.py        Durable daily counters and the trade journal
├── trader.py       The loop that ties it together
└── backtest.py     Replays history through the same strategy and risk code
```

Two design choices worth explaining:

**Nothing about the Deriv API is hardcoded.** Symbols, contract types, and valid durations are all discovered at runtime and validated against a live proposal before any purchase. If Deriv adds a coin or changes a minimum duration, the bot adapts without a code change.

**The bot polls rather than subscribing to streams.** Polling is slightly less immediate, but after a dropped connection it only has to dial again — there is no subscription state to rebuild. For a process expected to stay up for weeks unattended, that trade is worth making.

---

## Limitations — things it does not do

Being explicit about this matters more than the feature list:

- **The strategy is not proven profitable.** Backtesting exists (above), but it has not been run against enough real history, on enough symbols, over enough periods, to establish an edge — and on random-walk data it correctly shows a loss. Assume no edge until your own testing says otherwise.
- **No stop-loss on an open position.** These contracts settle at a fixed time; the bot cannot exit early. Risk per trade is bounded by the stake, which is the design.
- **No position sizing based on conviction.** Every trade is the same size.
- **Deriv's contract minimums apply.** For some symbols the shortest available contract may be longer than your `TRADE_DURATION`; the bot clamps to what is allowed and logs it.
- **It is not tuned.** The default parameters are conventional starting values, not optimised ones.

---

## License

GPL v3, matching the parent repository.
