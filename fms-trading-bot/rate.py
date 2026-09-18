#!/usr/bin/env python3
r"""Solve a trades-per-day target into settings, per symbol.

    .\.venv\Scripts\python.exe rate.py --target 1000
    .\.venv\Scripts\python.exe rate.py --target 1000 --rr 3 --apply

"1000 trades a day" is not a setting, it is a consequence of four things:
how many positions may be open at once, how long each one lasts, how many
symbols there are, and how many hours the market is open. Only the second
is negotiable, and it is set by where the stop and target sit.

    trades/day = positions x minutes-per-day / minutes-held

A position lasts, for a price that drifts nowhere, about

    E[hold] = stop x target / (per-bar movement)^2   bars

so demanding more trades forces the exits closer together, and the spread
does not move with them. That is the whole tension: past a point the
target is smaller than the cost of opening the trade, and the arithmetic
says so rather than the account discovering it.

This measures each symbol's real per-bar movement and spread, solves the
exits that deliver the target rate, and prints what win rate those exits
would then need. Symbols that cannot do it are named, with the reason.
"""

from __future__ import annotations

import argparse
import sys

from fmsbot.config import Settings


def hold_minutes(target_per_day: float, positions: int,
                 hours_open: float = 24.0) -> float:
    """Minutes one position may last, for the target rate to be reached."""
    if target_per_day <= 0 or positions <= 0:
        return 0.0
    return positions * hours_open * 60.0 / target_per_day


def exits_for_hold(hold_bars: float, sigma: float, rr: float) -> tuple:
    """(stop, target) in price that last about `hold_bars` bars.

    From the barrier-crossing time of a driftless walk, E[T] = a*b/sigma^2
    with a the stop distance and b the target. Fixing b = rr*a gives
    a = sigma * sqrt(hold / rr).
    """
    if hold_bars <= 0 or sigma <= 0 or rr <= 0:
        return 0.0, 0.0
    stop = sigma * (hold_bars / rr) ** 0.5
    return stop, stop * rr


def required_win_rate(rr: float, cost_ratio: float) -> float:
    """Break-even win rate at this reward:risk, costs included (%)."""
    if rr <= 0:
        return 100.0
    return 100.0 * (1.0 + cost_ratio) / (rr + 1.0)


def per_bar_move(bars) -> float:
    """Typical bar-to-bar movement: the sigma the hold time depends on."""
    steps = sorted(abs(bars[i].close - bars[i - 1].close)
                   for i in range(1, len(bars)))
    if not steps:
        return 0.0
    # The median, scaled to a standard deviation for a normal walk. The
    # mean would be dragged around by news spikes, and those are not what
    # most trades wait through.
    return steps[len(steps) // 2] * 1.4826


def slots_for(symbols: int, per_symbol: int, ceiling: int) -> int:
    """Positions that can actually be open at once."""
    return max(1, min(symbols * max(1, per_symbol), max(1, ceiling)))


def solve(measured: dict, target: float, per_symbol: int, ceiling: int,
          minutes_per_bar: float, rr: float, max_cost: float,
          hours: float) -> dict:
    """Which symbols can carry the rate, re-solved as others drop out.

    Refusing a symbol takes its slots with it, which shortens every
    remaining trade and widens the spread's share of the risk — so a
    refusal can cause another. The first version of this tool solved the
    exits once for all six symbols, refused five, and reported the sixth
    as fine at settings that assumed the other five were still there.
    """
    keep = list(measured)
    # Accumulated across passes: a symbol dropped in the first round is
    # still dropped, and the reason it was dropped is the finding.
    gone: list = []
    while keep:
        slots = slots_for(len(keep), per_symbol, ceiling)
        hold = hold_minutes(target, slots, hours)
        bars = hold / minutes_per_bar if minutes_per_bar else 0.0
        rows, refused = {}, []
        for symbol in keep:
            m = measured[symbol]
            stop, tp = exits_for_hold(bars, m["sigma"], rr)
            if stop <= 0 or m["value"] <= 0:
                refused.append((symbol, "no movement measured"))
                continue
            cost = m["spread"] / stop
            if m["floor"] and stop < m["floor"]:
                refused.append((symbol, f"stop {stop:.5f} is inside the "
                                        f"broker's {m['floor']:.5f} minimum"))
            elif cost > max_cost:
                refused.append((symbol, f"spread is {cost * 100:.0f}% of the "
                                        f"risk"))
            else:
                rows[symbol] = {
                    "stop": stop, "target": tp, "cost": cost,
                    "sl_money": stop * m["value"],
                    "tp_money": tp * m["value"],
                    "win_rate": required_win_rate(rr, cost),
                }
        if not refused:
            return {"keep": keep, "rows": rows, "slots": slots,
                    "hold": hold, "bars": bars, "dropped": gone}
        gone.extend(refused)
        keep = [s for s in keep if s not in dict(refused)]
    return {"keep": [], "rows": {}, "slots": 0, "hold": 0.0, "bars": 0.0,
            "dropped": gone}


def main() -> int:
    p = argparse.ArgumentParser(description="Solve a trades/day target")
    p.add_argument("--target", type=float, default=1000.0)
    p.add_argument("--rr", type=float, help="reward:risk (default: RR_TARGET)")
    p.add_argument("--hours", type=float, default=24.0,
                   help="hours a day the market is open to you")
    p.add_argument("--bars", type=int, default=2000)
    p.add_argument("--max-cost", type=float, default=0.25,
                   help="refuse a symbol whose spread exceeds this share "
                        "of the risk (default 0.25)")
    p.add_argument("--apply", action="store_true",
                   help="write the per-symbol settings to .env")
    args = p.parse_args()

    s = Settings.load()
    rr = args.rr if args.rr else s.rr_target
    from fmsbot.broker import build_broker_from_config
    cfg = s.broker_configs()[0]
    broker = build_broker_from_config(cfg)
    broker.connect()
    try:
        symbols = list(cfg.symbols)
        per_bar = {"M1": 1, "M5": 5, "M15": 15, "M30": 30,
                   "H1": 60, "H4": 240, "D1": 1440}[s.timeframe]

        measured = {}
        for symbol in symbols:
            try:
                bars = broker.bars(symbol, s.timeframe, args.bars)
                measured[symbol] = {
                    "sigma": per_bar_move(bars),
                    "spread": broker.spread(symbol),
                    "lot": broker.volume_from_lots(symbol, 0.01),
                    "value": broker.value_per_price(
                        symbol, broker.volume_from_lots(symbol, 0.01)),
                    "floor": broker.min_stop_distance(symbol),
                }
            except Exception as exc:
                print(f"{symbol}: cannot measure ({str(exc)[:60]})")

        got = solve(measured, args.target, s.max_positions_per_symbol,
                    s.max_open_positions, per_bar, rr, args.max_cost,
                    args.hours)

        print("=" * 78)
        print(f"RATE — {args.target:g} trades/day, {len(measured)} symbols, "
              f"{s.timeframe}, {rr:g}R")
        print(f"  {s.max_open_positions} may be open at once and "
              f"{s.max_positions_per_symbol} per symbol.")
        print("=" * 78)

        for symbol, why in got["dropped"]:
            m = measured[symbol]
            print(f"\n{symbol}  DROPPED — {why}")
            print(f"  moves {m['sigma']:.5f} per bar against a "
                  f"{m['spread']:.5f} spread")

        if not got["keep"]:
            print(f"\n  No symbol can carry {args.target:g} trades a day at "
                  f"a spread cost under\n  {args.max_cost * 100:.0f}%. Lower "
                  f"--target, raise MAX_POSITIONS_PER_SYMBOL, or add symbols\n"
                  f"  that move more per unit of spread.")
            return 1

        print(f"\n  With {len(got['keep'])} symbol(s) left there are "
              f"{got['slots']} slots, so each trade gets")
        print(f"  {got['hold']:.1f} min ({got['bars']:.1f} "
              f"{s.timeframe} bars). Re-solved at that hold:")

        settings_out = {}
        for symbol in got["keep"]:
            r, m = got["rows"][symbol], measured[symbol]
            print(f"\n{symbol}")
            print(f"  moves {m['sigma']:.5f} per bar, spread {m['spread']:.5f}")
            print(f"  stop {r['stop']:.5f}, target {r['target']:.5f}")
            print(f"  at {m['lot']:g} lot: SL_MONEY={r['sl_money']:.2f}, "
                  f"TP_MONEY={r['tp_money']:.2f}")
            print(f"  spread is {r['cost'] * 100:.0f}% of the risk, so it "
                  f"needs a {r['win_rate']:.1f}% win rate")
            key = "".join(c for c in symbol.upper() if c.isalnum())
            settings_out[f"SYM_{key}_SL_MONEY"] = f"{r['sl_money']:.2f}"
            settings_out[f"SYM_{key}_TP_MONEY"] = f"{r['tp_money']:.2f}"

        print("\n" + "=" * 78)
        print("VERDICT")
        print("=" * 78)
        share = args.target / len(got["keep"])
        print(f"\n  {', '.join(got['keep'])} — {share:.0f} trades a day each.")
        if got["dropped"]:
            print(f"\n  The {len(got['dropped'])} dropped symbol(s) must leave "
                  f"SYMBOLS. Left in, they keep\n  trading on ATR stops and "
                  f"pay that spread on every one of their trades —\n  a "
                  f"refusal here is not a warning, it is a cost.")
            settings_out["SYMBOLS"] = ",".join(got["keep"])

        if args.apply:
            from fmsbot import envfile
            changes = envfile.save(settings_out)
            print(f"\n  Wrote {len(changes)} setting(s) to .env "
                  f"(backup in .env.bak):")
            for c in changes:
                print(f"    {c}")
            print( "\n  Account-wide, and not written here:")
            print( "    FIXED_LOT=0.01           the cash exits need a fixed size")
            print(f"    MAX_TRADES_PER_DAY={int(args.target * 1.2)}")
            print(f"    MIN_TRADES_PER_HOUR={args.target / args.hours:.0f}")
        else:
            print( "\n  Re-run with --apply to write these.")

        worst = max(r["win_rate"] for r in got["rows"].values())
        print(f"\n  These exits deliver the RATE. They do not create an edge: "
              f"{worst:.0f}% is\n  what the hardest of them needs merely to "
              f"break even, and find_edge.py\n  is what says whether anything "
              f"reaches it.")
        return 0
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
