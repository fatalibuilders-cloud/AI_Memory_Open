# tgscalper — personal Telegram signal copier

Reads trade signals posted by admins in **your own** Telegram groups and places
them on **your own** broker account automatically, so you are not sitting there
waiting to copy a post by hand.

You stay a normal member of the groups. The bot logs in as your Telegram
account, watches up to **5 groups you choose**, parses each admin post, sizes the
trade against your risk rules, and sends the order. It keeps working as long as
the machine it runs on has power, internet and a logged-in session.

---

## The one thing to understand first

**This is not a Telegram "bot" in the bot-token sense, and it cannot be.**

A Bot API bot can only read messages in chats it has been *added to*, and only
when that chat's owner disables privacy mode. You cannot add your bot to someone
else's signal group — so a bot token can never see those posts.

What works instead is an **MTProto user client**: it signs in as *you*, with your
phone number, and therefore sees exactly the messages you see. That is what this
project uses (via [Telethon](https://docs.telethon.dev)).

Consequences worth knowing:

- The `data/tgscalper.session` file it creates is **as sensitive as your
  password**. Anyone holding it can read your Telegram. Keep it on the trading
  machine only, never in git, never in a backup you share.
- Automating a user account is against the spirit of Telegram's ToS if abused.
  Reading your own groups and placing your own trades is normal use; do not use
  this to spam, scrape at scale, or mass-forward. Extreme volume can get an
  account limited.

---

## What it actually does with a signal

```
🔥 GOLD BUY NOW 2350.5          →  symbol   XAUUSD   (your broker's name for it)
SL 2344                            side     BUY
TP1 2355                           entry    market
TP2 2360                           stop     2344
TP3 2370                           target   2355        (tp_mode: first)
                                   size     0.16 lots   (1% of 10k / $6 stop)
```

1. **Parse** — direction, symbol, entry, stop, targets. Handles zones
   (`2350-2352`), pip stops (`SL 30 pips`), decimal commas (`1,0850`), thousands
   separators (`44,250`), `S/L` and `T/P`, and two-digit shorthand
   (`gold buy 2350 sl 44 tp 60` → stop 2344, target 2360).
2. **Refuse nonsense** — a stop on the wrong side of entry, a target 4× the
   price, analysis rather than an order, chit-chat, results announcements. A
   misread digit costs far more than a missed signal, so anything inconsistent is
   logged and dropped.
3. **Check the guards** — trading hours, daily loss halt, max open trades,
   duplicate reposts, spread, symbol allowlist. Details below.
4. **Size** — risk % of balance divided by the stop distance, rounded **down** to
   the broker's lot step so the trade never risks more than intended.
5. **Send** — to the paper broker by default; to MetaTrader 5 when you explicitly
   enable live trading.
6. **Journal** — every message, decision and order into SQLite, so you can always
   trace a position in your account back to the post that caused it.

It also follows the admin's **management posts**, which is where most copy-trading
setups fall down:

| Admin posts | Bot does |
|---|---|
| `SL to BE` | moves the stop to entry (+ your offset) |
| `Close half` / `Close 30%` | part-closes each matching position |
| `Move SL to 2352` | tightens the stop — **refuses to widen it** |
| `Close all trades` | closes them |
| `Signal cancelled` | deletes the pending order |

When the admin *replies* to their original signal, the bot resolves the reply to
the exact tickets that post opened, so "close this one" doesn't touch your other
trades.

---

## Requirements

| | |
|---|---|
| Python | 3.10+ |
| Telegram | API id + hash from <https://my.telegram.org> → *API development tools* |
| Broker | MetaTrader 5 terminal, logged in, "Algo Trading" enabled |
| OS | **Windows** for live MT5 trading (the `MetaTrader5` package is Windows-only). Parser, risk engine, journal and paper mode run anywhere. |
| Hosting | A **Windows VPS** is the normal home for this — a laptop that sleeps or loses wifi stops copying signals. |

> The bot needs your broker's platform running to trade. "As long as it's
> connected to my Telegram and I have data" is true for the *reading* half; the
> *placing* half also needs MT5 up and reachable. A VPS gives you both.

---

## Setup

```bash
cd app-src/telegram-scalper
python -m venv .venv && . .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install MetaTrader5                            # Windows only, for live trading

cp .env.example .env                               # fill in credentials
cp config.example.yaml config.yaml                 # choose your groups and risk
```

**1. Credentials into `.env`** — Telegram api id/hash, phone, MT5 login/password/
server. Nothing secret goes in `config.yaml`.

**2. Check yourself in**

```bash
python -m tgscalper doctor
```

Verifies config, credentials, broker connection and symbol naming, and tells you
what is still missing.

**3. Find your group ids**

```bash
python -m tgscalper chats                 # first run asks for your phone + code
python -m tgscalper chats --search gold
```

```
             id  type       title
-1001234567890  group      Gold Signals VIP
-1009876543210  channel    FX Scalps
```

**4. Choose up to 5 groups** in `config.yaml`:

```yaml
telegram:
  max_groups: 5
  groups:
    - id: -1001234567890
      title: "Gold Signals VIP"
      enabled: true
      senders: []              # empty = any admin of that chat
      risk_multiplier: 1.0

    - id: -1009876543210
      title: "FX Scalps"
      enabled: true
      risk_multiplier: 0.5     # half size while it earns your trust

    - id: -1003333333333
      title: "Crypto Calls"
      enabled: false           # benched — configured, not watched
```

List as many candidates as you like; **at most 5 may be `enabled: true`** at
once. Swapping which five are live is a one-word edit, so you never have to
retype ids. Raise or lower the cap with `max_groups` (1–10) if you change your
mind — 5 is the default because more than that produces contradictory signals on
the same instrument.

To trade only specific admins rather than all of them:

```bash
python -m tgscalper admins -1001234567890
```

and put those ids in that group's `senders:` list.

**5. Watch it on paper for a few days.** `execution.mode` is `paper` out of the
box. Real signals, real parsing, real sizing, simulated fills:

```bash
python -m tgscalper run
python -m tgscalper report --days 3
```

This is the step that tells you whether your groups' formats actually parse and
whether the sizing matches what you'd have done by hand. Do not skip it.

**6. Go live, deliberately.** Two independent switches must agree:

```yaml
# config.yaml
execution:
  mode: live
```
```bash
# .env
TGSCALPER_ALLOW_LIVE=I_UNDERSTAND_THE_RISK
```

Either one alone keeps you on paper. A stale `config.yaml` can never start
sending real orders on its own.

---

## Commands

```
python -m tgscalper doctor                    check config, credentials, broker
python -m tgscalper chats [--search gold]     list chats with their ids
python -m tgscalper admins <chat>             list a chat's admin ids
python -m tgscalper parse <file>              parse messages, no broker involved
python -m tgscalper dryrun <file>             run them through the paper broker
python -m tgscalper run                       start listening
python -m tgscalper report [--days 7]         summarise the journal
```

`parse` and `dryrun` read a file of messages separated by `---` lines. Paste real
posts from your groups into one (`samples/signals.txt` is a starting point) and
you can test the whole pipeline without waiting for the market:

```bash
python -m tgscalper parse samples/signals.txt
```

---

## Risk controls

All in `config.yaml` under `risk:` and `execution:`. These are the only thing
between a bad night in a signal group and your balance.

| Setting | Does |
|---|---|
| `risk_per_trade_pct` | Position size = this % of balance ÷ stop distance |
| `fixed_lot` | Ignore % sizing, always trade this size |
| `max_lot` | Hard ceiling per trade |
| `max_open_trades` / `max_open_per_symbol` | Refuse to pile in |
| `max_daily_loss_pct` | Stop opening new trades once down this much today — survives restarts |
| `max_signals_per_hour` | Cap on a group having a frantic day |
| `allow_symbols` / `block_symbols` | Trade only what you understand |
| `hours` | Session window and weekdays |
| `min_stop_points` | Reject absurdly tight stops (likely a misread) |
| `max_spread_points` | Skip entries during news/rollover spread blowouts |
| `dedupe_window_minutes` | One trade per setup, even if cross-posted to 3 groups |
| `max_entry_slippage_points` | Skip if price already ran past the posted entry |
| `require_stop_loss` | Refuse any signal without a stop (keep this `true`) |
| `risk_multiplier` (per group) | Size down a group you don't fully trust yet |

Sizing example: $10,000 balance, `risk_per_trade_pct: 1.0`, gold signal with a
$6 stop → $100 ÷ ($6 × $100/lot) = 0.1666 → **0.16 lots** (rounded down, risking
$96). A stop too wide to fit the budget at the broker's minimum lot is refused
outright rather than silently over-risked.

---

## Honest limitations

- **The bot cannot make a bad signal group profitable.** It removes your reaction
  delay; it does not add edge. Paper-trade first and read the `report` output.
- **Screenshots are invisible.** Signals posted as images are skipped — there is
  no OCR. Only text and captions are read.
- **Fills differ from the admin's.** You enter seconds later, on your broker's
  spread. `max_entry_slippage_points` bounds this; it cannot eliminate it.
- **Paper P&L is optimistic** — it fills at the signal price and ignores spread,
  swap and slippage. It validates plumbing and sizing, not profitability.
- **Novel formats get skipped, not guessed.** When an admin invents a new layout,
  the parser refuses it and logs why. Check `report` and add an alias or open a
  fix rather than loosening the validation.
- **MT5 only** for live trading today. Other brokers mean writing one adapter
  against `brokers/base.py` — the engine, parser and risk rules are unchanged.

---

## Layout

```
src/tgscalper/
  parser.py      text → Signal, and the refusals
  symbols.py     "GOLD" → whatever your broker calls it (XAUUSD.m, GOLD, …)
  risk.py        sizing + every pre-trade guard (pure functions, no I/O)
  brokers/
    base.py      the interface an adapter implements
    paper.py     default simulated broker
    mt5.py       live MetaTrader 5 execution
  journal.py     SQLite audit trail, dedupe memory, ticket↔message mapping
  engine.py      message → decision → orders
  listener.py    Telethon client for your account
  cli.py         commands
tests/           166 tests, no network or broker required
```

```bash
python -m pytest tests/ -q
```

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `cannot resolve group` | This account isn't a member, or you used a title instead of the numeric id from `chats`. |
| `XAUUSD is not tradable on this account` | Broker names it differently — set `broker.suffix` (`.m`, `m`, `.cash`) or a `symbol_overrides` entry. `doctor` prints what resolves. |
| Signals parse but nothing is placed | Check `report --recent 20`; the skip reason is always recorded. Usually hours, allowlist, or the daily halt. |
| `MT5 initialize failed` | Terminal not running, wrong `MT5_TERMINAL_PATH`, or Algo Trading disabled. |
| Everything says PAPER | Both switches must agree: `execution.mode: live` **and** `TGSCALPER_ALLOW_LIVE`. |
| Nothing at all from a channel | Broadcast channels post as the channel, not a user — that's handled; but check the chat id has the `-100` prefix as `chats` printed it. |

Trading leveraged instruments on someone else's signals can lose money faster
than you can read the messages. Start on paper, start small, and keep
`max_daily_loss_pct` honest.
