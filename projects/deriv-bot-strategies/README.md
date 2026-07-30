# Deriv Bot strategies (XML)

Two strategy files for **Deriv Bot** — [bot.deriv.com](https://bot.deriv.com) — the Blockly
bot builder that shows *"Importing XML files from Binary Bot and other third-party platforms
may take longer"* on its import dialog.

| File | What it is |
| --- | --- |
| [`TeleScalper-Deriv-Safe.xml`](TeleScalper-Deriv-Safe.xml) | Flat stake, session take-profit / stop-loss, stops after 3 losses in a row |
| [`TeleScalper-Deriv-Aggressive.xml`](TeleScalper-Deriv-Aggressive.xml) | Martingale after a loss (2.1×, capped at 4 steps), wider session limits |

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

What that does **not** cover: neither strategy has been run on a Deriv account, so the
behaviour on live ticks — fill quality, how the momentum rule performs, whether the limits
trigger where you expect — is unverified. Run the safe one on demo first.
