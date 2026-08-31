#!/usr/bin/env python3
r"""Solve for a target number of trades a day — and price it.

    .\.venv\Scripts\python.exe throughput.py --target 2000
    .\.venv\Scripts\python.exe throughput.py --target 2000 --apply

Trade count is not a setting; it is an outcome of four things, and three
of them fight each other:

  * how many symbols are traded
  * how long a position stays open (a symbol with a position open cannot
    take another, so hold time sets the ceiling per symbol)
  * the entry interval and the per-symbol cooldown
  * the caps: MAX_TRADES_PER_DAY, MAX_OPEN_POSITIONS

This measures the real ATR and spread, estimates hold time from them,
works out whether the target is reachable at all, and says what would
have to change. Then it prices the whole thing, because the one number
that does not care about any of the above is the spread: it is charged
on every trade, win or lose.

Stop the bot before running this: two processes sharing one MT5 terminal
interfere.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from fmsbot.config import Settings

SECONDS_PER_DAY = 86400
TF_SECONDS = {"M1": 60, "M2": 120, "M3": 180, "M4": 240, "M5": 300,
              "M6": 360, "M10": 600, "M12": 720, "M15": 900, "M20": 1200,
              "M30": 1800, "H1": 3600, "H4": 14400, "D1": 86400}


def hold_bars(sl_mult: float, tp_mult: float) -> float:
    """Expected bars a position stays open, before drift.

    For a driftless random walk absorbed at -a or +b, the expected time is
    a*b divided by the per-bar variance. With the stop at sl_mult ATR, the
    target at tp_mult ATR and a per-bar move of about one ATR, the ATRs
    cancel and the answer is simply the product of the two multiples.

    This is an estimate, not a measurement: a trending market resolves
    faster and a quiet one slower. It is the right order of magnitude,
    which is all that is needed to know whether a target is reachable.
    """
    return max(sl_mult * tp_mult, 0.5)


def main() -> int:
    p = argparse.ArgumentParser(description="Solve for a trades-per-day target")
    p.add_argument("--target", type=int, default=2000, help="trades per day")
    p.add_argument("--account")
    p.add_argument("--hours", type=float, default=24.0,
                   help="trading hours per day (forex ~24, metals ~23)")
    p.add_argument("--apply", action="store_true", help="write settings to .env")
    p.add_argument("--bars", type=int, default=300)
    args = p.parse_args()

    settings = Settings.load()
    configs = settings.broker_configs()
    cfg = configs[0]
    if args.account:
        matches = [c for c in configs if c.name.lower() == args.account.lower()]
        if not matches:
            print(f"No account '{args.account}'.", file=sys.stderr)
            return 1
        cfg = matches[0]

    from fmsbot.broker import build_broker_from_config
    broker = build_broker_from_config(cfg)
    broker.connect()
    try:
        lot = settings.fixed_lot or 0.01
        window = args.hours * 3600

        print("=" * 78)
        print(f"THROUGHPUT — target {args.target:,} trades/day on {cfg.name}")
        print("=" * 78)

        costs = {}
        for symbol in cfg.symbols:
            try:
                spread = broker.spread(symbol)
                per_price = broker.value_per_price(symbol, lot)
            except Exception as exc:
                print(f"  {symbol}: unavailable ({str(exc)[:40]})")
                continue
            if spread <= 0 or per_price <= 0:
                print(f"  {symbol}: could not price it")
                continue
            costs[symbol] = spread * per_price
        if not costs:
            print("\nNothing measurable — is the market open and MT5 logged in?")
            return 1

        n = len(costs)
        per_symbol_needed = args.target / n

        # --- what the timeframe allows ---------------------------------
        print(f"\n{'timeframe':>10} {'hold est':>10} {'per symbol':>12} "
              f"{'x' + str(n) + ' symbols':>14}  verdict")
        print("-" * 78)
        workable = []
        for tf in ("M1", "M5", "M15", "H1"):
            bar = TF_SECONDS[tf]
            hold = hold_bars(settings.atr_sl_mult, settings.atr_tp_mult) * bar
            per_symbol = window / hold
            total = per_symbol * n
            ok = total >= args.target
            if ok:
                workable.append((tf, hold, total))
            print(f"{tf:>10} {hold/60:9.1f}m {per_symbol:12.0f} {total:14,.0f}  "
                  f"{'reaches it' if ok else 'cannot reach it'}")

        print("\n  A symbol holding one position cannot open another, so hold time")
        print(f"  sets the ceiling: {args.hours:g}h / hold, times {n} symbols.")
        print("  Hold is estimated from your own exits "
              f"({settings.atr_sl_mult} x {settings.atr_tp_mult} ATR "
              f"= {hold_bars(settings.atr_sl_mult, settings.atr_tp_mult):.1f} bars).")

        if not workable:
            print(f"\n  NOT REACHABLE at any timeframe with {n} symbols.")
            print(f"  {args.target:,}/day needs {per_symbol_needed:,.0f} per symbol, "
                  "which is one every")
            print(f"  {window/per_symbol_needed:.0f}s — shorter than a position "
                  "survives. Add symbols,")
            print( "  raise MAX_POSITIONS_PER_SYMBOL, or tighten the exits so trades")
            print( "  resolve faster.")
            best_tf = "M1"
        else:
            best_tf, best_hold, best_total = workable[0]
            print(f"\n  Reachable on {best_tf}: about {best_total:,.0f}/day "
                  f"available against a {args.target:,} target.")

        bar = TF_SECONDS[best_tf]
        hold = hold_bars(settings.atr_sl_mult, settings.atr_tp_mult) * bar
        interval = max(5, int(window * n / args.target))
        concurrent = args.target / window * hold

        print(f"\n{'':2}Settings that produce it:")
        print(f"    TIMEFRAME={best_tf}")
        print("    ENTRY_MODE=interval")
        print(f"    ENTRY_INTERVAL_SECONDS={interval}   "
              f"(one attempt per symbol every {interval}s)")
        print(f"    COOLDOWN_SECONDS={interval}")
        print(f"    MAX_TRADES_PER_DAY={int(args.target * 1.2)}   "
              "(headroom, or the cap itself becomes the limit)")
        print(f"    MAX_OPEN_POSITIONS={max(1, int(concurrent * 1.5) + 1)}   "
              f"(about {concurrent:.0f} will be open at once)")

        # --- the bill --------------------------------------------------
        mean_cost = sum(costs.values()) / len(costs)
        daily = mean_cost * args.target
        print("\n" + "=" * 78)
        print("WHAT IT COSTS")
        print("=" * 78)
        print(f"\n  {'symbol':16} {'spread cost per trade':>24}")
        for symbol, cost in sorted(costs.items(), key=lambda kv: -kv[1]):
            print(f"  {symbol:16} {cost:24.3f}")
        print(f"\n  average {mean_cost:.3f} x {args.target:,} trades = "
              f"${daily:,.2f} PER DAY in spread alone.")
        print(f"  ${daily * 5:,.2f} a week. ${daily * 21:,.2f} a month.")

        try:
            balance = broker.balance()
        except Exception:
            balance = 0.0
        if balance > 0:
            print(f"\n  Your balance is ${balance:,.2f}. To break even the strategy")
            print(f"  must earn ${daily:,.2f}/day — {daily/balance*100:.0f}% of the "
                  "account every day —")
            print( "  before it makes you a cent. This is arithmetic, not pessimism:")
            print( "  the spread is charged on every trade whether it wins or loses,")
            print( "  and trading more often multiplies it exactly.")
        print("\n  Volume cannot create an edge. It multiplies whatever edge")
        print("  exists — and yours is currently unmeasured. find_edge.py")
        print("  settles that; this tool only makes the meter run faster.")

        if not args.apply:
            print("\nRe-run with --apply to write these settings into .env.")
            return 0

        env_path = Path(".env")
        if not env_path.exists():
            print("\nNo .env here — run this from the bot folder.", file=sys.stderr)
            return 1
        wanted = {
            "TIMEFRAME": best_tf,
            "ENTRY_MODE": "interval",
            "ENTRY_INTERVAL_SECONDS": str(interval),
            "COOLDOWN_SECONDS": str(interval),
            "MAX_TRADES_PER_DAY": str(int(args.target * 1.2)),
            "MAX_OPEN_POSITIONS": str(max(1, int(concurrent * 1.5) + 1)),
        }
        lines = env_path.read_text(encoding="utf-8-sig").splitlines()
        out, seen = [], set()
        for line in lines:
            key = line.split("=", 1)[0].strip().upper() if "=" in line else ""
            if key in wanted:
                out.append(f"{key}={wanted[key]}")
                seen.add(key)
            else:
                out.append(line)
        for key, value in wanted.items():
            if key not in seen:
                out.append(f"{key}={value}")
        shutil.copyfile(env_path, Path(".env.bak"))
        env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"\nWrote {len(wanted)} settings to .env (backup in .env.bak).")
        print("Restart:  .\\update.ps1")
        print("\nThe record starts again: TIMEFRAME is part of what defines a")
        print("configuration, so /evidence will score this one from zero.")
        return 0
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
