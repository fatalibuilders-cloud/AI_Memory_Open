# Deriv Bot strategies (XML)

Strategy files for **Deriv Bot** — [bot.deriv.com](https://bot.deriv.com) — the Blockly
bot builder that shows *"Importing XML files from Binary Bot and other third-party platforms
may take longer"* on its import dialog.

| File | What it is |
| --- | --- |
| [`TeleScalper-Deriv-Safe.xml`](TeleScalper-Deriv-Safe.xml) | Flat stake, session take-profit / stop-loss, stops after 3 losses in a row |
| [`TeleScalper-Deriv-Aggressive.xml`](TeleScalper-Deriv-Aggressive.xml) | Martingale after a loss (2.1×, capped at 4 steps), wider session limits |
| [`TeleScalper-Deriv-DataRun.xml`](TeleScalper-Deriv-DataRun.xml) | Measurement build — same logic, limits widened so it collects hours of data without halting |
| [`analyse-results.py`](analyse-results.py) | Turns a Deriv transactions CSV into win rate vs break-even, noise band, streaks, halts, and an equity-curve chart |

> **These are for Deriv Bot, not cTrader.** The two platforms share nothing: cTrader runs
> compiled `.algo` cBots (see [`../cTrader-TeleScalper`](../cTrader-TeleScalper)), Deriv Bot
> runs Blockly XML on Deriv's digital-options products. A strategy cannot be moved between
> them, and Deriv Bot cannot read Telegram signals the way the cTrader bots do.

---

## Import them

1. Open [bot.deriv.com](https://bot.deriv.com) and sign in (pick the **demo** account first).
2. **Bot Builder** → **Import** → **Local** → choose the `.xml` file → **Open**.
3. The workspace loads with the blocks laid out. Press **Run** to start, **Stop** to halt.

The strategies replace whatever is currently on the canvas (they are saved as full
strategies, `collection="false"`), so save your existing work first if you have any.

## What they trade

Both are set up the same way out of the box:

- **Market:** Volatility 100 Index (`R_100`), synthetic indices
- **Trade type:** Up/Down → Rise/Fall, contract type **Both**
- **Duration:** 5 ticks
- **Direction:** buys **Rise** when the last tick moved up, **Fall** when it moved down
  (a momentum-follow rule — the *Purchase conditions* block)
- **Restart on error:** on

## Editing the settings

Everything you would want to tune is a variable in the **Initialization** section of the
trade-definition block — click the number and type a new one.

### Safe

| Variable | Default | Meaning |
| --- | --- | --- |
| `initial stake` | 1 | Stake per trade, in your account currency |
| `take profit` | 10 | Session profit at which the bot stops |
| `stop loss` | 10 | Session loss at which the bot stops |
| `max losses in a row` | 3 | Stops after this many consecutive losses |

Stake never changes: a loss costs one stake, nothing more.

### Aggressive

| Variable | Default | Meaning |
| --- | --- | --- |
| `initial stake` | 1 | Starting stake |
| `martingale multiplier` | 2.1 | Stake is multiplied by this after every loss |
| `max martingale steps` | 4 | After this many consecutive losses the stake **resets** to the initial stake |
| `take profit` | 25 | Session profit at which the bot stops |
| `stop loss` | 30 | Session loss at which the bot stops |

**Read this before running the aggressive one.** Martingale means a losing streak grows the
stake geometrically: at 2.1× from a stake of 1, the fourth trade in a streak stakes 9.26 and
the streak has cost 13.5 by then. The step cap and the session stop-loss are what stop that
from running away — do not raise the cap without lowering the stake, and do not set the
stop loss to 0. Nothing about martingale changes the edge of the underlying trades; it only
changes how the losses are distributed.

Both files stop the bot cleanly when a limit is hit (a notification fires and the bot simply
does not trade again) rather than closing anything mid-contract.

## Changing the market or duration

- **Market/symbol:** the *Market* block at the top — pick market, submarket and symbol from
  the dropdowns (e.g. Volatility 75, Crash 500, Step Index).
- **Duration:** the *Trade options* block — `5` ticks by default; switch the unit dropdown to
  seconds/minutes if you prefer.
- **Direction rule:** the *Purchase conditions* block — swap `check_direction` for an
  indicator block (SMA/RSI/Bollinger are in the toolbox under **Analysis → Indicators**) if
  you want a filter instead of raw momentum.

## Telegram alerts (optional)

Deriv Bot has a **Notify Telegram** block (toolbox → **Utility → Misc**) that takes an access
token, a chat ID and a message. Drop one into the *After purchase* stack with a message built
from the *Last trade result* / *Contract details* blocks if you want the same running
commentary the cTrader bots send. It is left out of these files because an empty token would
throw at runtime.

---

## Running a measurement session

`TeleScalper-Deriv-DataRun.xml` exists because the Safe file is built to protect an account,
not to collect data: its 3-losses-in-a-row rule halts the bot every few minutes, so a long
run turns into constant restarting. The data build changes four numbers and nothing else:

| Variable | Safe | DataRun | Why |
| --- | --- | --- | --- |
| `max losses in a row` | 3 | 15 | 15 straight losses is a 1-in-33,000 event — effectively never halts |
| `take profit` | 10 | 100 | Room to run for hours |
| `stop loss` | 10 | 100 | Still bounded — the run ends rather than bleeding indefinitely |
| duration | 5 ticks | 1 tick | Matches the first run, and gives the most independent samples per hour |

Stake stays flat at 1.00. **Demo account only** — this is a measurement, not a trading setup.

At roughly one trade every 8–11 seconds you get about **400 trades an hour**. Three hours is
~1,200 trades, where the −4%-per-trade expectation predicts about **−48**, with a 1σ spread of
±33. So a typical honest outcome lands somewhere between −114 and +18. If the curve finishes
well above that band, that is the interesting result worth chasing.

Then export and analyse:

1. Deriv → **Reports** → **Statement** → download CSV (or use the bot's own export).
2. `python3 analyse-results.py Transactions_*.csv --chart equity.png --martingale`

It prints the win rate against the break-even rate implied by your payout, how many sigma the
result sits from expectation, streaks, every point where the bot halted itself, and — with
`--martingale` — what the same sequence of wins and losses would have done with the
aggressive file's stake escalation. The chart plots your equity against the expectation line
inside a ±2σ cone, which is the quickest way to see whether a run is edge or luck.

## How these were validated

Both files were checked against Deriv Bot's own source (`deriv-com/deriv-app`,
`packages/bot-skeleton`):

- structure mirrors the canonical workspace `scratch/xml/main.xml` — the same
  `trade_definition` block with its `TRADE_OPTIONS`, `INITIALIZATION` and `SUBMARKET`
  statements, plus `before_purchase` and `after_purchase` stacks
- all 26 block types used in each file exist in the block registry harvested from the 129
  block definition files in that package
- every dropdown value (`CHECK_RESULT`, `CHECK_DIRECTION`, `PURCHASE_LIST`, `TYPE_LIST`,
  `DURATIONTYPE_LIST`, `NOTIFICATION_TYPE`, …) matches `src/constants/config.ts`
- variable references resolve to declared variables, no duplicate block ids, XML well-formed
- `is_dbot="true"` / `collection="false"` match what Deriv's own `save()` writes, which is
  what its importer expects for a full strategy

What that does **not** cover: how the momentum rule performs. The Safe file has now been
run on demo (see the run log below) — it imported, traded, and halted on its loss guard
exactly as designed, but 26 trades say nothing about profitability, and on a random-number
synthetic index there is no edge for a tick-direction rule to find.

---

## Run log

| Date | File | Trades | Win rate | Net | Verdict |
| --- | --- | --- | --- | --- | --- |
| 2026-07-30 19:06–19:11 | Safe (duration edited to 1 tick) | 26 | 53.85% | +0.88 | +0.39σ from expectation — noise. Loss guard fired correctly at 3 consecutive losses, twice. |

Raw data and charts live in [`results/`](results/).
