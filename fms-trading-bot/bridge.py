#!/usr/bin/env python3
r"""Expose the broker to other languages as JSON on stdout.

    python bridge.py positions
    python bridge.py bars XAUUSDm M5 60
    python bridge.py info XAUUSDm
    python bridge.py modify 123456 2380.10 2400.00

PowerShell, batch files and anything else cannot talk to MetaTrader 5:
its API is a Python package that speaks to the terminal over local IPC.
This is the thin seam — it reuses the bot's own broker layer, so an
adapter written for Exness, Deriv, OANDA or Binance works here unchanged.

Every command prints one JSON object. On failure it prints
{"ok": false, "error": "..."} and exits 1, so a caller can branch on the
exit code without parsing.

Stop the bot before using this: two processes sharing one MT5 terminal
interfere.
"""

from __future__ import annotations

import json
import sys

from fmsbot.config import Settings


def fail(message: str) -> int:
    print(json.dumps({"ok": False, "error": str(message)}))
    return 1


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return fail("usage: bridge.py positions|bars|info|modify [args]")
    command = argv[1]

    settings = Settings.load()
    configs = settings.broker_configs()
    account = None
    if "--account" in argv:
        i = argv.index("--account")
        if i + 1 >= len(argv):
            return fail("--account needs a name")
        account = argv[i + 1]
        del argv[i:i + 2]
    cfg = configs[0]
    if account:
        matches = [c for c in configs if c.name.lower() == account.lower()]
        if not matches:
            return fail(f"no account '{account}'")
        cfg = matches[0]

    from fmsbot.broker import build_broker_from_config
    broker = build_broker_from_config(cfg)
    try:
        broker.connect()
    except Exception as exc:
        return fail(f"connect failed: {exc}")

    try:
        if command == "positions":
            out = [{"ticket": p.ticket, "symbol": p.symbol, "side": p.side,
                    "volume": p.volume, "entry": p.entry_price, "sl": p.sl,
                    "tp": p.tp, "profit": p.profit}
                   for p in broker.positions()]
            print(json.dumps({"ok": True, "account": cfg.name, "positions": out}))
            return 0

        if command == "bars":
            if len(argv) < 5:
                return fail("usage: bridge.py bars SYMBOL TIMEFRAME COUNT")
            symbol, timeframe, count = argv[2], argv[3], int(argv[4])
            bars = broker.bars(symbol, timeframe, count)
            print(json.dumps({
                "ok": True, "symbol": symbol,
                "high": [b.high for b in bars],
                "low": [b.low for b in bars],
                "close": [b.close for b in bars],
            }))
            return 0

        if command == "info":
            if len(argv) < 3:
                return fail("usage: bridge.py info SYMBOL")
            symbol = argv[2]
            print(json.dumps({
                "ok": True, "symbol": symbol,
                "spread": broker.spread(symbol),
                "min_stop": broker.min_stop_distance(symbol),
                # the side a position is CLOSED at: a long exits at the bid
                "bid": broker.current_price(symbol, "sell"),
                "ask": broker.current_price(symbol, "buy"),
                "value_per_price": broker.value_per_price(
                    symbol, settings.fixed_lot or 0.01),
            }))
            return 0

        if command == "modify":
            if len(argv) < 5:
                return fail("usage: bridge.py modify TICKET SL TP")
            ticket, sl, tp = int(argv[2]), float(argv[3]), float(argv[4])
            broker.modify_position(ticket, sl, tp)
            print(json.dumps({"ok": True, "ticket": ticket, "sl": sl, "tp": tp}))
            return 0

        return fail(f"unknown command '{command}'")
    except Exception as exc:
        return fail(exc)
    finally:
        try:
            broker.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
