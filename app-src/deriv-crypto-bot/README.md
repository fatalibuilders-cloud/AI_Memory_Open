# Deriv Crypto Bot

An automated trading bot for [Deriv](https://deriv.com) that trades **Bitcoin only** and runs **24/7**.

It watches the Bitcoin market on a schedule, looks for a specific price pattern, and places a trade when it finds one — then keeps doing that indefinitely, reconnecting on its own when the network drops.

Bitcoin is the default (`DERIV_SYMBOLS=BTC`). Clearing that one setting widens it to every crypto Deriv offers; it can never widen beyond crypto.

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

### Bitcoin only

`DERIV_SYMBOLS=BTC` in `.env` restricts the bot to Bitcoin. You can write it three ways and all resolve to the same market:

```
DERIV_SYMBOLS=BTC          # simplest
DERIV_SYMBOLS=BTC/USD      # the display name
DERIV_SYMBOLS=cryBTCUSD    # Deriv's exact ticker
```

The bot matches your entry against the symbols Deriv actually reports, so you don't need to know its exact spelling, and a rename upstream won't silently leave the bot with nothing to trade. The preflight check prints exactly which symbol it resolved to, and how many others it is therefore skipping.

To trade all crypto instead, leave `DERIV_SYMBOLS` blank. For a few named coins: `DERIV_SYMBOLS=BTC,ETH`.

> With a single symbol, `MAX_OPEN_TRADES` has no practical effect — the bot holds at most one position per symbol, so only one trade is ever open at a time. The check points this out.

### How "crypto only" is enforced

Underneath the Bitcoin restriction sits a harder guarantee: the bot never trades forex, synthetic indices, commodities, or stocks, whatever `DERIV_SYMBOLS` says. That is enforced at three independent points:

1. Symbols are **discovered** from Deriv's own market listing and filtered to `market == "cryptocurrency"`. Nothing is hardcoded.
2. `DERIV_SYMBOLS` entries are resolved **after** that filter, so an alias can only ever match something already known to be crypto. Putting a forex pair there drops it with an explanation in the log rather than trading it.
3. A final check immediately before every purchase confirms the symbol is still in the verified crypto set for that cycle.

There are tests for all three, plus the alias path. See `tests/test_cycle.py::TestCryptoOnly` and `tests/test_market.py::TestBitcoinOnly`.

---

## Quick start

You need **Python 3.10 or newer** and **git** installed.

### Step 1 — Get the code onto your machine

The bot lives on a branch, so clone that branch directly with `-b`. Cloning into its own folder (`deriv-bot`) keeps this independent of any older copy of the repository you may already have.

**Windows (PowerShell):**

```powershell
cd $HOME
git clone -b claude/deriv-7h4xbl https://github.com/fatalibuilders-cloud/AI_Memory_Open.git deriv-bot
cd deriv-bot\app-src\deriv-crypto-bot
```

**macOS / Linux:**

```bash
cd ~
git clone -b claude/deriv-7h4xbl https://github.com/fatalibuilders-cloud/AI_Memory_Open.git deriv-bot
cd deriv-bot/app-src/deriv-crypto-bot
```

Confirm you are in the right place — this should list `setup.ps1`, `deriv_bot`, and `README.md`:

```powershell
ls          # PowerShell, macOS, and Linux all understand this
```

### Step 2 — Run setup

**Windows (PowerShell):**

```powershell
.\setup.ps1
```

If PowerShell blocks it with *"running scripts is disabled on this system"*, use this instead — it bypasses the policy for this one command only, without changing any system setting:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

**macOS / Linux:**

```bash
./setup.sh
```

Either script creates a virtual environment, installs everything, runs the test suite, and writes a `.env` for you to fill in. Both are safe to re-run and never overwrite an existing `.env`.

### Step 3 — Get a Deriv API token

Go to **[app.deriv.com/account/api-token](https://app.deriv.com/account/api-token)**. Switch to your **Demo / Virtual** account using the switcher at the top right, then create a token with the **Read** and **Trade** scopes ticked — *not* Payments, *not* Admin. The bot never needs those, and withholding them means a leaked token cannot move money out of your account.

Open `.env` and paste the token in after the `=`:

**Windows:** `notepad .env` &nbsp;&nbsp;•&nbsp;&nbsp; **macOS/Linux:** `nano .env`

```
DERIV_API_TOKEN=your_token_here
```

> `.env` is git-ignored. Never commit it — the token in it can trade your account.

> **Copy the right thing.** The token is the short code (about 15 characters) in the **Token** column of the table that appears *after* you click Create — not the Name you typed, and not anything from `developers.deriv.com`. Those are app credentials, a different thing entirely, and they are much longer. The preflight check flags a wrong-length value and tells you so.

### Step 4 — Check it

**Windows (PowerShell):**

```powershell
.venv\Scripts\python.exe -m deriv_bot.check
```

**macOS / Linux:**

```bash
source .venv/bin/activate
python -m deriv_bot.check
```

> **Note for Windows users:** every `python -m ...` command below assumes you have activated the virtual environment. If you'd rather not, just replace `python` with `.venv\Scripts\python.exe` in any command. To activate it in PowerShell: `.\.venv\Scripts\Activate.ps1`

---

## If setup goes wrong

Nearly every setup problem is *being in the wrong folder*. Run `ls` — if you don't see `setup.ps1` and `deriv_bot`, that's the problem, and the errors below follow from it.

| Error | What it means | Fix |
|---|---|---|
| `No module named 'deriv_bot'` | You're not in the bot's folder, or the venv isn't active | `cd` into `deriv-bot\app-src\deriv-crypto-bot`, then use `.venv\Scripts\python.exe -m deriv_bot.check` |
| `DERIV_API_TOKEN is required but not set` | Your `.env` exists but the token line is still blank | Run the check — it prints the exact file, the exact line number, and what to type. Then `notepad .env`, paste after the `=`, **Ctrl+S**, close Notepad |
| Token pasted but still "not set" | Notepad saved it as `.env.txt`, or you didn't save | The check detects the `.txt` case and prints the rename command. Otherwise re-open and confirm Ctrl+S |
| `Token rejected by Deriv` / "The token is invalid" | Deriv received a token it does not recognise | The check prints the token's length and a masked preview, and flags a partial paste, stray spaces, quotes, or leftover placeholder text. If the shape looks fine, the token was likely revoked or you copied its *name* rather than the code |
| `destination path 'AI_Memory_Open' already exists` | You have an older clone from before the bot existed | Clone into a new folder using the `-b ... deriv-bot` form in Step 1 |
| `pathspec 'claude/deriv-7h4xbl' did not match` | Your local copy has never fetched this branch | `git fetch origin` first, then `git checkout claude/deriv-7h4xbl`. Or just re-clone with `-b` |
| `The term '.\setup.ps1' is not recognized` | `setup.ps1` isn't in the current folder | You're in the wrong directory — see above |
| `running scripts is disabled on this system` | PowerShell's execution policy | `powershell -ExecutionPolicy Bypass -File .\setup.ps1` — affects this one command only |
| `cd : Cannot find path ...app-src...` | The clone predates the bot, or the branch isn't checked out | Re-clone with `-b` as in Step 1 |

**Already have an older clone you want to keep?** Update it in place instead of re-cloning:

```powershell
cd $HOME\AI_Memory_Open
git fetch origin
git checkout claude/deriv-7h4xbl
cd app-src\deriv-crypto-bot
```

The `git fetch` is the part that matters — without it, git doesn't know the branch exists.

---

## Checking your setup

`python -m deriv_bot.check` is the first thing to run and the thing to re-run whenever something looks wrong. It connects, authorizes, inspects your account, lists the crypto universe, pulls candles, runs the strategy over them, and prices a real contract — then tells you whether the bot is ready.

**It never buys anything.** It requests a price quote and stops. Running it costs nothing.

```
1. Connection
  [PASS] Connected  wss://ws.derivws.com/websockets/v3
  [PASS] Token accepted  app_id=1089

2. Account
  [PASS] Virtual (demo) account  VRTC1
         No real funds at risk. This is the right place to start.
  [PASS] Balance readable  10,000.00 USD
  [PASS] Stake affordable  1.00 USD per trade

3. Crypto universe
  [PASS] 12 cryptocurrency symbols offered by Deriv
  [PASS] 76 non-crypto symbols excluded  forex, indices, synthetics
  [PASS] 6 symbols selected  cryBTCUSD, cryETHUSD, ...

4. Market data and strategy
  [PASS] Fetched 200 candles for cryBTCUSD  60s each
  [PASS] Data is current  latest candle 12s old
  [PASS] Strategy sees no trade right now  no crossover on the latest candle

5. Contract pricing
  [PASS] Priced a real contract  stake 1.00, payout 1.85 USD
         (This was a price quote only. Nothing was bought.)

  [PASS] Real payout ratio: 0.850  win returns 0.850x your stake
         You must win more than 54.1% of trades to break even.
```

That last block is the reason to run it even when nothing is wrong. **The payout ratio is the biggest assumption in any backtest**, and this measures it instead of guessing. Feed the number straight back in:

```bash
python -m deriv_bot.backtest --days 30 --payout-ratio 0.850
```

If something is broken, the check says what and how to fix it — a rejected token points you at the token page with the right scopes, a missing `Trade` scope is named explicitly, and a real-money account without the opt-in is reported as a failure rather than quietly proceeding.

---

## Running it

In the order that keeps you out of trouble:

```bash
# 1. Backtest first — costs nothing, tells you if the strategy is worth running
python -m deriv_bot.backtest --days 30 --save-candles btc.json

# 2. Dry run — finds signals and prices real contracts, but never buys
DERIV_DRY_RUN=true python -m deriv_bot

# 3. Demo — real mechanics, no real money
python -m deriv_bot
```

Stop with `Ctrl+C` — it finishes the current cycle and shuts down cleanly.

Leave step 3 running long enough to see losing days, not just winning ones. That is the whole point of the exercise.

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

## Comparing strategies

The bot ships nine rules, six real and three controls. Test them all against each other on the same data:

```bash
python -m deriv_bot.backtest --from-file btc.json --compare
python -m deriv_bot.backtest --list-strategies
python -m deriv_bot.backtest --from-file btc.json --strategy donchian
```

Pick one for the live bot with `STRATEGY=` in `.env`.

| Strategy | What it does |
|---|---|
| `ema_cross` | EMA 9/21 crossover with RSI and ATR filters (default) |
| `macd_cross` | MACD line crossing its signal line |
| `donchian` | Breakout beyond the 20-candle range (Turtle-style) |
| `trend_200` | Trade only with the 200-period trend |
| `rsi_reversion` | Buy exits from oversold, sell exits from overbought |
| `bollinger` | Fade closes outside the 2-sigma bands |
| `always_call` | **CONTROL** — always up; the buy-and-hold benchmark |
| `coin_flip` | **CONTROL** — random; the noise floor |
| `never_trade` | **CONTROL** — no trades; cannot lose |

### The controls are the point

A strategy that cannot beat a coin flip is detecting nothing. One that cannot beat `always_call` is worse than just holding Bitcoin. One that cannot beat `never_trade` is worse than leaving your money alone. The comparison report says so in those words rather than crowning a winner.

### What the comparison found here

Run on 60 days of synthetic BTC-like 1-minute candles — in a market that **rose 139%** — with 5-minute contracts:

```
  Strategy         Trades    Win %   Net P&L    vs B/E
  never_trade           0     0.0%     +0.00      --      <- won
  ema_cross           500    49.2%    -44.90     -4.9
  rsi_reversion      1647    49.8%   -130.00     -4.3
  bollinger          3714    50.6%   -239.70     -3.5
  macd_cross         4313    50.6%   -278.15     -3.5
  donchian           5011    50.3%   -345.30     -3.7
  always_call        8636    50.6%   -544.10     -3.4
  coin_flip          8636    49.5%   -732.80     -4.6
```

Every rule lost. Not trading won. Even *always predicting up* lost money in a market that more than doubled, because over five minutes Bitcoin's drift is invisible against the noise — while the payout is charged on every single trade.

That is synthetic data, so treat the exact figures as illustrative. The mechanism it demonstrates is not synthetic.

### Contract length matters more than the indicator

```bash
python -m deriv_bot.backtest --from-file btc.json --strategy always_call --sweep-durations
```

Same data, same rule, only the contract length changing:

| Duration | Win % | Net P&L |
|---|---|---|
| 5m | 50.8% | −974.81 |
| 30m | 51.5% | −138.15 |
| 1h | 51.6% | −66.30 |
| 4h | 58.5% | **+29.50** |
| 12h | 60.5% | **+14.20** |
| 1 day | 64.4% | **+11.30** |

A directional drift accumulates in proportion to time; noise grows only with its square root. So the same edge that is worthless over five minutes clears the payout hurdle comfortably over a day. **Switching from 5-minute to 4-hour contracts changed the result more than switching between any two strategies did.**

The catch: that "edge" is just the market going up. A long contract in the wrong direction loses equally reliably, and fewer, larger bets means much higher variance. If your thesis is "Bitcoin rises", holding Bitcoin expresses it without capping your upside at 0.85x while leaving your downside at 1.0x.

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
| Check my setup is working | `python -m deriv_bot.check` — places no trades |
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
| `STRATEGY` | `ema_cross` | Which rule to trade. See Comparing strategies |
| `DERIV_SYMBOLS` | `BTC` | Bitcoin only. Blank = all open crypto. Accepts `BTC`, `BTC/USD`, or `cryBTCUSD` |
| `TRADE_DURATION` / `_UNIT` | `5` / `m` | Contract length. Clamped to what Deriv allows for that symbol |

The stake actually used is the **smallest** of: `STAKE`, `MAX_STAKE_FRACTION` × balance, and your remaining daily loss budget. A single trade can never take you past the daily limit in one go.

---

## Tests

```bash
pip install pytest
python -m pytest
```

360 tests covering the indicator maths, the crypto-only filter, every risk limit, state durability across restarts, full trading cycles against a fake Deriv API, the backtester's accounting, the preflight check (including a test that it never places a trade), and reconnection after network, proxy, and API failures. No network access or token needed; CI runs them on Python 3.10-3.13, and on Windows and macOS as well as Linux.

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
├── strategies.py   The strategy library, including the honesty controls
├── backtest.py     Replays history; --compare and --sweep-durations
└── check.py        Preflight check — verifies setup, never trades
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
