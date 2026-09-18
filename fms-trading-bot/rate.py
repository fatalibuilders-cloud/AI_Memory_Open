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
        slots = max(1, s.max_positions_per_symbol) * len(symbols)
        slots = min(slots, max(1, s.max_open_positions))
        hold = hold_minutes(args.target, slots, args.hours)
        per_bar = {"M1": 1, "M5": 5, "M15": 15, "M30": 30,
                   "H1": 60, "H4": 240, "D1": 1440}[s.timeframe]
        hold_bars = hold / per_bar

        print("=" * 78)
        print(f"RATE — {args.target:g} trades/day, {len(symbols)} symbols, "
              f"{s.timeframe}, {rr:g}R")
        print(f"  {s.max_open_positions} positions may be open at once and "
              f"{s.max_positions_per_symbol} per symbol,")
        print(f"  so {slots} slots. Over {args.hours:g}h that is one trade per "
              f"slot every {hold:.1f} min")
        print(f"  = {hold_bars:.1f} {s.timeframe} bars per trade.")
        print("=" * 78)
        if hold_bars < 2:
            print(f"\n  A trade cannot open and close in {hold_bars:.1f} bars. "
                  f"Raise\n  MAX_OPEN_POSITIONS / MAX_POSITIONS_PER_SYMBOL, add "
                  f"symbols, or lower\n  the target. Nothing below this line "
                  f"can fix it.")

        settings_out, refused = {}, []
        for symbol in symbols:
            per = s.for_symbol(symbol)
            try:
                bars = broker.bars(symbol, s.timeframe, args.bars)
                spread = broker.spread(symbol)
                lot = broker.volume_from_lots(symbol, 0.01)
                value = broker.value_per_price(symbol, lot)
                floor = broker.min_stop_distance(symbol)
            except Exception as exc:
                print(f"\n{symbol}: cannot measure ({str(exc)[:60]})")
                continue
            sigma = per_bar_move(bars)
            stop, target = exits_for_hold(hold_bars, sigma, rr)
            if stop <= 0 or value <= 0:
                print(f"\n{symbol}: no movement measured")
                continue
            cost = (spread / stop) if stop > 0 else 9.9
            need = required_win_rate(rr, cost)
            print(f"\n{symbol}")
            print(f"  moves {sigma:.5f} per bar, spread {spread:.5f}")
            print(f"  exits for a {hold:.0f}-min hold: stop {stop:.5f}, "
                  f"target {target:.5f}")
            print(f"  at {lot:g} lot that is SL_MONEY={stop * value:.2f}, "
                  f"TP_MONEY={target * value:.2f}")
            print(f"  spread is {cost * 100:.0f}% of the risk, so it needs a "
                  f"{need:.1f}% win rate")
            if floor and stop < floor:
                refused.append((symbol, f"stop {stop:.5f} is inside the "
                                        f"broker's {floor:.5f} minimum"))
            elif cost > args.max_cost:
                refused.append((symbol, f"spread is {cost * 100:.0f}% of the "
                                        f"risk"))
            else:
                key = "".join(c for c in symbol.upper() if c.isalnum())
                settings_out[f"SYM_{key}_SL_MONEY"] = f"{stop * value:.2f}"
                settings_out[f"SYM_{key}_TP_MONEY"] = f"{target * value:.2f}"

        print("\n" + "=" * 78)
        print("VERDICT")
        print("=" * 78)
        usable = len(settings_out) // 2
        if usable:
            share = args.target / usable
            print(f"\n  {usable} of {len(symbols)} symbols can carry this rate, "
                  f"at {share:.0f} trades each.")
        for symbol, why in refused:
            print(f"    {symbol:12} cannot: {why}")
        if refused:
            print(f"\n  A symbol that cannot is not a setting to force. Its "
                  f"spread is a real\n  cost paid on every one of those "
                  f"{args.target:g} trades.")
        if settings_out and args.apply:
            from fmsbot import envfile
            changes = envfile.save(settings_out)
            print(f"\n  Wrote {len(changes)} setting(s) to .env (backup in "
                  f".env.bak):")
            for c in changes:
                print(f"    {c}")
            print( "\n  Also needed, and NOT written here because they are "
                   "account-wide:")
            print(f"    FIXED_LOT=0.01           the cash exits need a fixed "
                  f"size")
            print(f"    MAX_TRADES_PER_DAY={int(args.target * 1.2)}")
            print(f"    MIN_TRADES_PER_HOUR={args.target / args.hours:.0f}")
        elif settings_out:
            print( "\n  Re-run with --apply to write these per-symbol exits "
                   "to .env.")
        print( "\n  These exits deliver the RATE. They do not create an edge: "
               "the win\n  rate above is what they need merely to break even, "
               "and find_edge.py\n  is what says whether anything here reaches "
               "it.")
        return 0
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
