#!/usr/bin/env python3
r"""Diagnose why the bot is not trading.

    .\.venv\Scripts\python.exe doctor.py

Checks, in order, everything that stands between "bot running" and "order
placed", and prints a verdict naming the actual blocker. Read-only: it
never sends an order.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone

from fmsbot.config import Settings
from fmsbot.strategy import EmaCrossStrategy
from fmsbot.risk import RiskManager

OK = "[ OK ]"
BAD = "[FAIL]"
WARN = "[WARN]"


def scan_history(strategy: EmaCrossStrategy, bars: list) -> list[tuple[int, str, str]]:
    """Replay closed bars and collect every signal the strategy would emit."""
    hits = []
    start = strategy.min_bars()
    for i in range(start, len(bars) + 1):
        window = bars[:i]
        sig = strategy.signal(window)
        if sig:
            hits.append((window[-1].time, sig.side, sig.reason))
    return hits


def fmt_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def main() -> int:
    print("=" * 68)
    print("FMS BOT DOCTOR")
    print("=" * 68)

    settings = Settings.load()
    problems = settings.validate()
    print(f"\n-- CONFIG --")
    print(f"  broker      : {settings.broker}")
    print(f"  symbols     : {settings.symbols}")
    print(f"  timeframe   : {settings.timeframe}")
    print(f"  start_paused: {settings.start_paused}")
    print(f"  risk/trade  : {settings.risk_pct}%")
    print(f"  strategy    : EMA{settings.ema_fast}/{settings.ema_slow}, "
          f"RSI{settings.rsi_period} floor {settings.rsi_floor}/ceil {settings.rsi_ceiling}")
    if problems:
        for p in problems:
            print(f"  {BAD} {p}")
        return 1
    print(f"  {OK} config valid")

    # -- broker ------------------------------------------------------
    print(f"\n-- BROKER CONNECTION --")
    from main import build_broker
    broker = build_broker(settings)
    try:
        broker.connect()
    except Exception as exc:
        print(f"  {BAD} connect failed: {exc}")
        return 1
    balance = broker.balance()
    equity = broker.equity()
    print(f"  {OK} connected — balance {balance:.2f}, equity {equity:.2f}")

    open_positions = broker.positions()
    print(f"  open positions: {len(open_positions)}")
    for p in open_positions:
        print(f"     #{p.ticket} {p.side.upper()} {p.symbol} {p.volume} PnL {p.profit:+.2f}")

    # -- symbols + data ------------------------------------------------
    strategy = EmaCrossStrategy(settings)
    need = max(settings.history_bars, strategy.min_bars() + 2)
    all_hits: dict[str, list] = {}
    data_ok = False

    for symbol in settings.symbols:
        print(f"\n-- SYMBOL {symbol} --")
        try:
            bars = broker.bars(symbol, settings.timeframe, need)
        except Exception as exc:
            print(f"  {BAD} no data: {exc}")
            continue
        closed = bars[:-1]
        age_min = (time.time() - closed[-1].time) / 60.0
        print(f"  {OK} {len(bars)} bars, last closed {fmt_ts(closed[-1].time)} "
              f"({age_min:.0f} min ago), close {closed[-1].close}")
        if age_min > 60:
            print(f"  {WARN} data looks stale — market closed (weekend/holiday) "
                  f"or symbol not streaming")
        else:
            data_ok = True

        if len(closed) < strategy.min_bars():
            print(f"  {BAD} only {len(closed)} closed bars, strategy needs "
                  f"{strategy.min_bars()}")
            continue

        sig_now = strategy.signal(closed)
        print(f"  signal on latest closed bar: {sig_now.side.upper() if sig_now else 'none'}")

        hits = scan_history(strategy, closed)
        all_hits[symbol] = hits
        span_h = (closed[-1].time - closed[0].time) / 3600.0
        print(f"  signals in last {span_h:.1f}h of history: {len(hits)}")
        for ts, side, reason in hits[-5:]:
            print(f"     {fmt_ts(ts)}  {side.upper():4}  {reason}")

    # -- risk gates ------------------------------------------------------
    print(f"\n-- RISK GATES (simulated for first symbol) --")
    risk = RiskManager(settings)
    sym = settings.symbols[0]
    sym_open = len([p for p in open_positions if p.symbol == sym])
    allowed, reason = risk.can_enter(sym, balance, equity, len(open_positions), sym_open)
    if allowed:
        print(f"  {OK} a signal right now would be allowed through")
        print(f"     risk amount/trade: {risk.risk_amount(balance):.2f}")
    else:
        print(f"  {WARN} entry would be BLOCKED: {reason}")

    # -- verdict -----------------------------------------------------------
    print("\n" + "=" * 68)
    print("VERDICT")
    print("=" * 68)
    total = sum(len(h) for h in all_hits.values())
    if not data_ok:
        print("  Market data is not arriving (or the market is closed).")
        print("  -> If it's the weekend, forex/metals are shut until Monday.")
        print("  -> Otherwise fix the symbol names shown above in .env SYMBOLS.")
    elif settings.start_paused:
        print("  Data and strategy are fine.")
        print("  START_PAUSED=1, so after EVERY restart the bot waits for /resume.")
        print("  -> Send /status on your phone; if it says PAUSED, send /resume.")
        print("  -> Set START_PAUSED=0 in .env to arm automatically on start.")
    elif total == 0:
        print(f"  Everything works, but the strategy produced ZERO signals across")
        print(f"  the whole history window — it is simply being very selective.")
        print("  -> Loosen it (see suggestions below) or wait for a crossover.")
    else:
        print(f"  Everything works. {total} signal(s) occurred in the scanned history;")
        print("  the bot trades only signals that fire while it is running and armed.")
        print("  -> If it was paused/restarting at those moments, it missed them.")

    if total == 0 and data_ok:
        print("\n  To trade more often, edit .env:")
        print("     TIMEFRAME=M1          (5x more candles)")
        print("     EMA_FAST=9")
        print("     EMA_SLOW=21           (crosses far more often)")
        print("     RSI_FLOOR=40")
        print("     RSI_CEILING=60        (filter rejects less)")
        print("     COOLDOWN_SECONDS=60")
        print("  More trades is NOT more profit — it also means more losses.")

    broker.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
