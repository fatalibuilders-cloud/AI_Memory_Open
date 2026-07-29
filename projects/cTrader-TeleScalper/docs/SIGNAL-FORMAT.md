# Signal format reference

How TeleScalper reads a Telegram message. Nothing here needs to be configured — it is what
the parser accepts, so you can tell at a glance whether a provider's format will work.

## Minimum for a trade

A message is traded only when **all four** of these are found:

1. a **direction** — `BUY`, `SELL`, `LONG` or `SHORT` (any case, anywhere in the message)
2. a **stop loss** — `SL`, `S/L`, `S.L`, `STOP LOSS`, `STOPLOSS`, followed by a price
3. at least one **take profit** — `TP`, `TP1`, `T/P`, `TAKE PROFIT`, `TARGET`, followed by a price
4. a **symbol** that exists on your trading account

Anything else — commentary, "closed +40 pips", "be patient", screenshots without a caption —
is ignored silently (and logged when *Verbose logging* is on).

## Accepted shapes

```
XAUUSD                              GOLD SELL NOW @ 2354,50
BUY                                 SL 2360,50
Entry: 2354.50                      TP1 2348,50
SL: 2346.50                         TP2 2340,00
TP1: 2364.50 (50%)
TP2: 2374.50 (final)                #EURUSD Buy Limit 1.08210
Risk: 1%                            Stop Loss 1.07410
Time: Now                           Take Profit 1 : 1.08810
                                    Take Profit 2 : 1.09410

US30 BUY 41,250.5 | SL: 41,050.0 | TP: 41,450.0
NAS100 sell @ 20150.5 S/L 20250.5 T/P 19950.5 TARGET 2: 19850.5
SELL BTCUSD entry 64500 sl 65200 tp1 63800
```

Details:

- **Separators** — `:`, `=`, `-`, `@` or nothing at all between a label and its price.
- **Decimals** — `2354.50` and `2354,50` both work. `41,250.5` is read as forty-one thousand
  (comma = thousands separator when a dot is also present, or when 3 digits follow it).
- **Entry is optional.** With no entry, or with an entry the bot decides is implausible (more
  than 20% away from the live price — usually a lot size or a risk number caught by mistake),
  the trade simply executes at market.
- **Pending-order wording is not honoured.** `Buy Limit 1.08210` executes at market like any
  other signal. Set *Max entry deviation (pips)* if you want signals skipped once price has
  moved away from the quoted entry.
- **Third and later targets are ignored.** TP1 drives the partial close, TP2 becomes the
  position's take profit.
- **Numbered targets win over position.** `TP1`/`Target 2` are ordered by their number;
  unnumbered targets are ordered by where they appear in the message.

## Symbol matching

The symbol token is matched against your account in this order:

1. **Extra symbol map** parameter — `SIGNAL=BROKER` pairs, e.g. `GOLD=XAUUSD,US30=US30.cash`.
   This always wins, so it is the fix for any symbol the bot cannot find.
2. The token itself, with your **Broker symbol suffix** appended.
3. The token with common broker suffixes: `.r .a .p .pro .ecn .raw .cash .spot .std m c z # _ -ECN .m`.
4. Built-in aliases: `GOLD/XAU → XAUUSD`, `SILVER/XAG → XAGUSD`, `DOW/DJ30 → US30`,
   `NASDAQ/NAS/USTEC → NAS100`, `SPX/SPX500/SP500 → US500`, `DAX/DAX40 → GER40`,
   `FTSE/FTSE100 → UK100`, `NIKKEI/JP225 → JPN225`, `WTI/CRUDE → USOIL`, `BRENT → UKOIL`,
   `BTC/BITCOIN → BTCUSD`, `ETH/ETHEREUM → ETHUSD` — each also tried with the suffixes above.
5. `EURUSD` is also tried as `EUR/USD`.

Words like `BUY`, `TP1`, `ENTRY`, `RISK`, `LIMIT`, `TARGET` (and those words with digits
attached, e.g. `PROFIT1`) are never treated as symbols. The first token that resolves to a
real symbol on your account wins, so put the symbol at the top of the signal if you control
the format.

## Rejection reasons you will see in the log

| Log message | Meaning |
| --- | --- |
| `no BUY/SELL direction` | No direction word found |
| `no stop loss` | No SL label + price |
| `no take profit` | No TP label + price |
| `symbol not found on this account` | Add an `Extra symbol map` entry |
| `<SYMBOL> not in whitelist` | Blocked by the *Symbol whitelist* parameter |
| `BUY levels inconsistent` / `SELL levels inconsistent` | SL/TP on the wrong side of entry — the message was probably a mid-trade update, not a new signal |
| `Signal ignored (older than N minutes)` | Stale message, e.g. picked up right after a restart |
| `Duplicate signal … ignored` | Same symbol/direction/entry/SL/TP1 already traded |

And the notifications you get on Telegram when a valid signal is *not* traded: auto trading
off, max open trades reached, max trades per symbol reached, market closed, spread too wide,
price already past SL or TP1, volume below the symbol minimum, or the order being rejected
by the broker (with the broker's own error text).
