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
| Broker | MetaTrader 5 terminal, logged in, "Algo Trading" enabled. **Exness and Deriv both work with this** — see below. |
| OS | **Windows** for live MT5 trading (the `MetaTrader5` package is Windows-only). Parser, risk engine, journal and paper mode run anywhere. |
| Hosting | A **Windows VPS** is the normal home for this — a laptop that sleeps or loses wifi stops copying signals. |

> The bot needs your broker's platform running to trade. "As long as it's
> connected to my Telegram and I have data" is true for the *reading* half; the
> *placing* half also needs MT5 up and reachable. A VPS gives you both.

---

## Windows quick start

Open **PowerShell** and paste this. It installs Python and Git if they are
missing, fetches the project, builds the environment, asks for your credentials,
and runs a self-check:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
$d="$env:USERPROFILE\tgscalper"
if (!(Test-Path $d)) { git clone --depth 1 https://github.com/fatalibuilders-cloud/AI_Memory_Open.git $d }
Set-Location "$d\app-src\telegram-scalper"
.\windows\setup.ps1 -Broker deriv
```

Use `-Broker exness` for an Exness account, or `-Broker default` for a plain
forex profile. Re-running the script updates an existing install and leaves your
`.env` alone unless you say otherwise.

If `git` is not installed yet, the first line fails — run this instead, which
installs Git first:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
winget install --id Git.Git --exact --silent --accept-package-agreements --accept-source-agreements
$env:Path="$env:Path;$env:ProgramFiles\Git\cmd"
$d="$env:USERPROFILE\tgscalper"
git clone --depth 1 https://github.com/fatalibuilders-cloud/AI_Memory_Open.git $d
Set-Location "$d\app-src\telegram-scalper"
.\windows\setup.ps1 -Broker deriv
```

Then, in order:

```powershell
.\windows\run.ps1 chats            # 1. list your groups and their ids
notepad config.yaml                # 2. put up to 5 ids under telegram.groups
.\windows\run.ps1 symbols          # 3. check your broker's symbol names
.\windows\run.ps1 run              # 4. watch it on PAPER for a few days
.\windows\run.ps1 report --days 3  #    then read what it would have done
```

To keep it running on a VPS across reboots:

```powershell
.\windows\autostart.ps1            # register a scheduled task (logon + auto-restart)
Get-Content .\logs\tgscalper.log -Wait -Tail 40
```

MetaTrader 5 must also be running and logged in with **Algo Trading** enabled —
set MT5 to start with Windows too, or the bot will read Telegram and have nowhere
to send orders.

| Script | Does |
|---|---|
| `windows\setup.ps1` | Full install: prerequisites, venv, dependencies, config, `.env`, self-check |
| `windows\run.ps1` | Runs any command through the venv — `run.ps1 doctor`, `run.ps1 run`, … |
| `windows\autostart.ps1` | Registers/removes the scheduled task (`-Remove` to undo) |

---

## Your broker: Exness and Deriv

**Both are MetaTrader 5 brokers, so neither needs a new adapter.** `provider: mt5`
covers both. What differs is only the login details and the symbol naming.

### Exness

```yaml
broker:
  provider: mt5
  suffix: ""      # Standard accounts: XAUUSD, EURUSD
  # suffix: "m"   # Cent/Mini accounts often list XAUUSDm, EURUSDm
```
```bash
# .env
MT5_LOGIN=12345678
MT5_PASSWORD=your-mt5-password
MT5_SERVER=Exness-MT5Real5        # demo servers are Exness-MT5Trial<N>
```

Use the **MT5 account** credentials from your Exness personal area, not your
website login. If you are unsure about the suffix, leave it blank — an
unmatched suffix falls back to the bare name, and `doctor` prints what actually
resolved.

### Deriv

```yaml
broker:
  provider: mt5
  suffix: ""      # Deriv symbols carry no suffix
```
```bash
# .env
MT5_LOGIN=987654321
MT5_PASSWORD=your-mt5-password
MT5_SERVER=DerivSVG-Server-02     # whatever your MT5 account shows
```

Same trap, and it catches people constantly: create an **MT5 account** inside the
Deriv dashboard and use *its* credentials. Your deriv.com website login will not
work here.

**Synthetic indices are supported.** Deriv lists them with spaces —
`Volatility 75 Index`, `Boom 500 Index`, `Step Index` — while signal groups write
`V75`, `vix75`, `boom500`. The resolver maps between the two:

| Group writes | Trades |
|---|---|
| `V75`, `vix75`, `vol 75`, `R_75` | Volatility 75 Index |
| `V10` `V25` `V50` `V100` | the matching Volatility Index |
| `BOOM 500`, `boom500`, `B1000` | Boom 500 / Boom 1000 Index |
| `CRASH 1000`, `C500` | Crash 1000 / Crash 500 Index |
| `Step Index` | Step Index |
| `J75`, `Jump 75` | Jump 75 Index |

A bare `crash`, `boom` or `step` is deliberately **not** an alias — "market crash
incoming" and "step by step guide" are ordinary chat, and matching them would
invent trades out of conversation.

```bash
python -m tgscalper parse samples/deriv-signals.txt
```

Two Deriv-specific settings worth changing:

- **Synthetics trade 24/7, weekends included.** The default `risk.hours` is
  Mon–Fri, so weekend signals get skipped. Widen `days` to all seven if you trade
  them.
- **Minimum lots differ from forex.** Boom/Crash start around 0.2 lots, Volatility
  indices around 0.001. With a small balance the smallest tradable lot can risk
  more than your `risk_per_trade_pct` allows — the bot refuses that trade rather
  than silently over-risking, and tells you so in the journal. Paper-trade first
  and read the skip reasons.

> Deriv also has a native WebSocket API that needs no MT5 terminal and would run
> on Linux instead of a Windows VPS. It trades multiplier contracts rather than
> classic MT5 positions, so it is a genuinely different adapter — not built here.
> Say the word if you want it.

---

## Setup

> **On Windows, skip this section** — `windows\setup.ps1` does all of it for you.
> See [Windows quick start](#windows-quick-start) below.

```bash
cd app-src/telegram-scalper
python -m venv .venv && . .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                                   # required: the package lives in src/
pip install MetaTrader5                            # Windows only, for live trading

cp .env.example .env                               # fill in credentials
cp config.example.yaml config.yaml                 # or config.deriv.yaml for Deriv
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
python -m tgscalper symbols [--search vol]    inspect the broker's symbol names
python -m tgscalper chats [--search gold]     list chats with their ids
python -m tgscalper admins <chat>             list a chat's admin ids
python -m tgscalper parse <file>              parse messages, no broker involved
python -m tgscalper dryrun <file>             run them through the paper broker
python -m tgscalper run                       start listening
python -m tgscalper report [--days 7]         summarise the journal
```

On Windows use `.\windows\run.ps1 <command>`, which picks up the venv for you.

`symbols` is the one to reach for whenever an instrument will not trade — it
prints your terminal's own symbol strings rather than what anyone assumes they
are:

```
  V75          -> Volatility 75 Index
  BOOM500      -> Boom 500 Index
  NAS100       -> NOT TRADABLE on this account
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
- **MT5 only** for live trading today — which covers Exness and Deriv, but a
  broker without an MT5 bridge means writing one adapter against
  `brokers/base.py`. The engine, parser and risk rules stay unchanged.
- **Paper specs for synthetics are approximations.** The dry-run contract sizes
  for Volatility/Boom/Crash indices are plausible defaults; the live path reads
  the real specification from your terminal, which is authoritative.

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
