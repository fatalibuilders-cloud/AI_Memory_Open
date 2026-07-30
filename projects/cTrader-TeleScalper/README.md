# TeleScalper — cTrader cBot

A cTrader Automate cBot that does on cTrader what the TeleScalper_bot spec does on MT5:
it reads trading signals from your Telegram groups, validates them, executes them on the
connected cTrader account and manages them automatically (break even + partial close at
TP1, remainder to TP2), with Telegram notifications for every action.

The ready-to-use file is **[`dist/TeleScalper.algo`](dist/TeleScalper.algo)** — download it
and load it with the **Upload** button in the cTrader mobile app (Algo tab), or drop it into
cTrader Desktop. The source it was built from is in `TeleScalper/`.

There is also an aggressive variant — **[`dist/TeleScalperPro.algo`](dist/TeleScalperPro.algo)**:
risk-% sizing, laddered multi-entry, trailing runner, pyramiding, and a daily loss limit.
See [section 6](#6-telescalper-pro--the-aggressive-variant).

---

## 1. What it does

| Rule | Behaviour |
| --- | --- |
| Signal sources | Up to 5 Telegram chats (groups, channels or DMs), selected by chat ID |
| Valid signals only | A message is traded only if it contains a tradable **symbol**, a **direction**, a **stop loss** and at least **one take profit**. Everything else is ignored. |
| Execution | Market order the moment the signal is validated |
| Position size | Fixed lots (default **0.01**), or optional risk-% sizing off the SL distance |
| Trade cap | Max open trades (default **10**), plus a per-symbol cap (default 3) |
| No duplicates | The same symbol/direction/entry/SL/TP1 combination is never traded twice |
| Break even | SL moves to entry (+ optional buffer) at TP1, and/or after a configurable pip profit |
| Partial profit | Closes **50%** (configurable) at TP1, the remainder runs to TP2 with SL at break even |
| Final target | TP2 is attached to the position as its take profit, so it closes even if the bot restarts |
| Notifications | Telegram messages on start/stop, new trade, break even, TP1 taken, trade closed, and every skip reason |
| Admin commands | `/status`, `/positions`, `/start`, `/stop`, `/trading on\|off`, `/closeall`, `/help` |

Safety checks before every entry: market open, spread limit, max entry deviation from the
signal price, SL/TP verified to be on the correct side of the *live* price, volume within
the symbol's min/max, and levels re-validated after any implausible number is discarded.

### Signal format

The parser is tolerant — all of these are accepted:

```
XAUUSD                          GOLD SELL NOW @ 2354,50        #EURUSD Buy Limit 1.08210
BUY                             SL 2360,50                     Stop Loss 1.07410
Entry: 2354.50                  TP1 2348,50                    Take Profit 1 : 1.08810
SL: 2346.50                     TP2 2340,00                    Take Profit 2 : 1.09410
TP1: 2364.50
TP2: 2374.50
```

Also handled: `US30 BUY 41,250.5 | SL: 41,050.0 | TP: 41,450.0`, `S/L` and `T/P` labels,
`TARGET 2:` as TP2, comma decimals (`2354,50`), thousands separators (`41,250.5`), and
`GOLD`/`NAS100`/`USTEC`/`DOW`-style aliases mapped to your broker's symbol names.

Messages without SL or without any TP are **ignored** — as are messages older than
`Ignore signals older than` minutes (default 10), so a restart never fires off stale trades.

---

## 2. Get the `.algo`

**The built file is in this repo: [`dist/TeleScalper.algo`](dist/TeleScalper.algo)** (35 KB).
Download it and upload it — nothing to build.

- **Mobile:** cTrader app → **Algo** tab → **Upload** → pick `TeleScalper.algo`.
- **Desktop:** Automate → cBots → drop the file in, or copy it to
  `Documents/cAlgo/Robots/`. Signed in with your cTrader ID it then syncs to your other
  devices.

It was built from `TeleScalper/TeleScalper.cs` with the official `cTrader.Automate` 1.0.19
SDK targeting `net6.0`, and the packaged metadata was verified to expose one Robot type
(`cAlgo.Robots.TeleScalper`, FullTrust, TimeZone UTC) with all 23 parameters in their
Telegram / Trading / Management / Diagnostics groups.

`sha256: 713ec9c939f6782abe7e7e05847498b6ca6163abcf39b8a6904d58df7be77119`

### Rebuilding it yourself (optional)

If you change the source, any of these regenerates the `.algo`.

#### Route A — cTrader Desktop (no tooling needed)

1. Open cTrader Desktop → **Automate** → **cBots** → **New cBot**.
2. Delete the template code, paste the whole of
   [`TeleScalper/TeleScalper.cs`](TeleScalper/TeleScalper.cs), save as `TeleScalper`.
3. Press **Build**. On success the `.algo` is written to
   `Documents/cAlgo/Sources/Robots/TeleScalper/bin/…/TeleScalper.algo`.
4. Signed in with your cTrader ID, the cBot syncs to your cTrader account automatically —
   open the mobile app's **Algo** tab and it is already listed. Otherwise copy the `.algo`
   to your phone and use **Upload**.

> The `[Robot(AccessRights = AccessRights.FullAccess)]` attribute is required (the bot calls
> `api.telegram.org`). cTrader asks you to confirm that access on first run.

#### Route B — command line, any OS with the .NET SDK

```bash
cd projects/cTrader-TeleScalper/TeleScalper
dotnet build -c Release
# -> bin/Release/net6.0/TeleScalper.algo
```

Needs .NET SDK 6.0 or newer; the `cTrader.Automate` NuGet package does the `.algo` packaging.

#### Route C — GitHub Actions (no local tooling at all)

Run the **Build cTrader algo** workflow (Actions tab → *Build cTrader algo* → *Run workflow*).
Download the `TeleScalper-algo` artifact from the finished run, unzip it, and upload
`TeleScalper.algo` from the mobile app.

---

## 3. Telegram setup (5 minutes)

1. **Create the bot** — message [@BotFather](https://t.me/BotFather), `/newbot`, follow the
   prompts, copy the token (`123456789:AA…`). Keep it private; it is the password to the bot.
2. **Add the bot to each signal group/channel.** For groups, also send `/setprivacy` →
   *Disable* to BotFather so the bot can see all messages, not just commands.
   (Telegram bots cannot read a chat they are not a member of — there is no way around that.)
3. **Get the chat IDs** — open
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser after a message was
   posted in the group, and read `result[].message.chat.id`. Group IDs are negative
   (`-1001234567890`).
4. **Get your own chat ID** the same way (send the bot a DM first) — that is the
   `Admin / notify chat ID`, where notifications go and the only chat whose commands are obeyed.

---

## 4. Run it

Add an instance (mobile: **Algo** → TeleScalper → *Add instance*; desktop: Automate →
cBots → TeleScalper → *+*), fill in the parameters, then press ▶.

Any symbol/timeframe works for the instance — the bot trades the symbols named in the
signals, not the chart symbol. A 1-minute chart on a liquid pair is a fine host.

| Parameter | Default | Notes |
| --- | --- | --- |
| Bot token | — | From BotFather. Required. |
| Signal chat IDs | — | Comma separated, max 5. Required. |
| Admin / notify chat ID | — | Your own chat ID. Notifications + commands. |
| Poll interval (seconds) | 3 | Telegram long-poll timeout |
| Ignore signals older than | 10 min | 0 disables the age filter |
| Enable trading | true | Off = signals are reported but not traded |
| Lot size | 0.01 | Used unless risk-% sizing is on |
| Size by risk % / Risk % | off / 1.0 | Sizes from balance and SL distance instead |
| Max open trades | 10 | Counts only this bot's positions |
| Max open trades per symbol | 3 | |
| Max spread (pips) | 0 (off) | Skip entries when the spread is wider |
| Max entry deviation (pips) | 0 (off) | Skip when price has already run from the signal entry |
| Symbol whitelist | empty (all) | e.g. `XAUUSD,EURUSD,US30` |
| Broker symbol suffix | empty | e.g. `.r` if your broker names symbols `XAUUSD.r` |
| Extra symbol map | empty | `SIGNAL=BROKER` pairs, e.g. `GOLD=XAUUSD,US30=US30.cash` |
| Trade label | TeleScalper | Positions are found/managed by this label |
| Close % at TP1 | 50 | 0 disables partial closing |
| If partial close impossible | LetRunToTp2 | At 0.01 lots a 50% close is often impossible — either let it run to TP2 with SL at break even, or close fully at TP1 |
| Move SL to break even at TP1 | true | |
| Break even trigger (pips) | 0 (off) | Independent, earlier break-even trigger |
| Break even buffer (pips) | 0.5 | Where "break even" sits relative to entry |
| Verbose logging | true | Every rejected signal is logged with its reason |

### First run checklist

1. Demo account, `Enable trading` **off**, start the instance.
2. Confirm the `✅ TeleScalper started` Telegram message and send `/status`.
3. Post a test signal in the signal group; the log should show it parsed (or the exact
   reason it was rejected).
4. Turn `Enable trading` on, restart the instance, and watch the first live-fire trade on
   demo end to end (entry → TP1 partial → break even → TP2).

---

## 5. Limits worth knowing before you trust it with money

- **Cloud hosting and network access.** Instances marked with the cloud icon run on cTrader
  Cloud rather than your device. If outbound HTTPS is restricted there, the bot logs
  `Telegram poll error` and reads nothing — run it on cTrader Desktop (or a VPS) instead.
  Everything else works identically in both places.
- **Telegram bots only see chats they belong to**, with privacy mode disabled. A copier for
  channels you can't add a bot to would need a user-account client (MTProto), which is a
  different tool and against Telegram's rules for some use cases.
- **The parser is heuristic.** It refuses anything it cannot read cleanly, and it double-checks
  every level against the live price before sending an order — but a badly malformed signal is
  skipped, not guessed at. Read the log after your first day and tune with `Extra symbol map`.
- **Partial closes need volume to split.** At the 0.01-lot minimum there is nothing to halve;
  choose `CloseFullAtTp1` if you would rather bank TP1 than run to TP2 in that case.
- **Restart behaviour.** The bot re-adopts its own open positions (by label, reading TP levels
  back out of the position comment). If the stop is already at or beyond entry it assumes TP1
  was handled. Positions opened by hand or by another bot are never touched.
- **Not backtestable in any meaningful way.** Live Telegram input means the strategy tester
  will show nothing; validate on demo instead.

---

## 6. TeleScalper **PRO** — the aggressive variant

**[`dist/TeleScalperPro.algo`](dist/TeleScalperPro.algo)** — same Telegram signal engine,
tuned to press winners much harder. Upload it exactly like the standard one; the two are
separate cBots and can run side by side (they use different trade labels, so neither
touches the other's positions).

`sha256: b04ef13be48782f827091b410ed0c84bdc55059a21490b13eaa89b2b8aedb6fc`

| | TeleScalper | TeleScalper **PRO** |
| --- | --- | --- |
| Size per signal | 0.01 lots fixed | **2% risk** off the SL distance (or fixed lots) |
| Entries per signal | 1 | **3 laddered entries** (up to 5) |
| Targets | TP1 partial, TP2 final | **one target per entry**; missing targets extrapolated at 1.5R steps |
| Runner | remainder to TP2 | last entry rides the furthest target with a **trailing stop** |
| Stop management | break even at TP1 | break even once *any* entry banks profit, then trail at 0.75R once 1R in profit |
| Adding to winners | never | **pyramids** 1 add at +1R, sized 0.5×, protected at group break even |
| After a stop-out | nothing | optional **recovery re-entry**, 1.5× size, capped (default **off**) |
| Trade caps | 10 total / 3 per symbol | 20 total / 9 per symbol |
| Signals without SL | rejected | optional **fallback SL in pips** (default still rejects) |
| Risk brakes | none | **daily loss limit 10%** + **max 12% total open risk**, both enforced before every entry |

### What "aggressive" costs you

Three entries at 2% risk is roughly **6× the exposure per signal** of the standard bot, and
pyramiding adds more on top. A losing streak draws the account down proportionally faster —
that is the whole point of the setting, so size it deliberately:

- The **daily loss limit** (default 10% of the day's starting balance) locks out new trades
  for the rest of the day once equity drops through it. `/unlock` overrides it, `/status`
  shows the day's P/L. It resets on the next server day.
- **Max total open risk** (default 12%) refuses new signals while the open book already
  risks that much. It is an estimate from stop distance × pip value, not an exact figure.
- **Recovery re-entries are off by default.** Turning them on is martingale behaviour:
  each step multiplies size by 1.5× after a loss, capped at 3 steps. Leave it at 0 unless
  you have specifically decided you want that risk profile.

Start on demo with `Risk %` at 0.5, `Entries per signal` at 2 and pyramiding off, watch a
few signals run end to end, then scale up to taste.

### PRO-only parameters

| Parameter | Default | Notes |
| --- | --- | --- |
| Sizing mode | RiskPercent | Or FixedLots if you prefer a flat size |
| Risk % of balance per signal | 2.0 | Split across the ladder, not per entry |
| Entries per signal (ladder) | 3 | Trimmed automatically if volume can't be split |
| Extra target step (R multiples) | 1.5 | Used when the signal has fewer TPs than entries |
| Trail start / distance (R) | 1.0 / 0.75 | 0 start disables trailing |
| Pyramid adds / trigger / size | 1 / 1.0R / 0.5× | 0 adds disables pyramiding |
| Recovery re-entries / multiplier | 0 / 1.5× | **Off by default** — martingale when enabled |
| Daily loss limit % | 10 | 0 disables the lock |
| Max total risk % open at once | 12 | 0 disables the check |
| Fallback SL (pips) | 0 | 0 = a signal without SL is still rejected |

Extra command: `/unlock` clears the daily loss lock and resets the balance baseline.

---

## 7. Files

```
projects/cTrader-TeleScalper/
├── README.md                      this file
├── dist/
│   ├── TeleScalper.algo           built, ready to upload to cTrader
│   └── TeleScalperPro.algo        aggressive variant, ready to upload
├── TeleScalper/
│   ├── TeleScalper.cs             the cBot (single file, paste-ready)
│   └── TeleScalper.csproj         net6.0 + cTrader.Automate 1.0.19 → TeleScalper.algo
├── TeleScalperPro/
│   ├── TeleScalperPro.cs          the aggressive cBot
│   └── TeleScalperPro.csproj      → TeleScalperPro.algo
└── docs/
    └── SIGNAL-FORMAT.md           parser rules, accepted formats, rejection reasons
```

Both bots compile clean against `cAlgo.API` (net6.0) from `cTrader.Automate` 1.0.19, share
the same signal parser (checked against the sample formats listed above), and their packaged
metadata was verified after bundling — one Robot type each, FullTrust, 23 and 31 parameters
respectively.
