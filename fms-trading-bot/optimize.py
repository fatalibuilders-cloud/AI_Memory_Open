#!/usr/bin/env python3
r"""Search strategies and parameters for a configuration that survives its
own trading costs, then check the winner on unseen data.

    .\.venv\Scripts\python.exe optimize.py --symbol EURUSDm --days 60
    .\.venv\Scripts\python.exe optimize.py --csv data.csv --top 15

How to read the output: the search fits parameters to history, which always
flatters them. Only the OUT-OF-SAMPLE column means anything — it applies
the winning settings to the final third of the data, which the search never
saw. A configuration that is profitable in-sample and negative
out-of-sample is curve-fitted noise, which is the normal result. Finding
nothing is a real answer: it means don't trade this, not "search harder".
"""

from __future__ import annotations

import argparse
import itertools
import sys
from copy import copy

from fmsbot.config import Settings
from fmsbot.sim import simulate
from fmsbot.vecstrategy import VEC_STRATEGIES

# Parameter grids per strategy. Kept modest so a run finishes in seconds
# and so the search space stays small — a huge grid guarantees a
# good-looking fit by chance alone.
GRIDS = {
    "ema_cross": {
        "ema_fast": [9, 12, 20],
        "ema_slow": [21, 50, 100],
        "atr_sl_mult": [1.0, 1.5, 2.0],
        "atr_tp_mult": [1.5, 2.5, 3.5],
        "rsi_floor": [40.0, 45.0],
        "rsi_ceiling": [55.0, 60.0],
    },
    "mean_reversion": {
        "bb_period": [14, 20, 30],
        "bb_std": [2.0, 2.5],
        "rsi_oversold": [20.0, 30.0],
        "rsi_overbought": [70.0, 80.0],
        "atr_sl_mult": [1.0, 1.5, 2.0],
        "atr_tp_mult": [1.0, 1.5, 2.5],
    },
    "breakout": {
        "donchian_period": [10, 20, 40],
        "atr_sl_mult": [1.0, 1.5, 2.0],
        "atr_tp_mult": [1.5, 2.5, 4.0],
    },
    "trend_always": {
        "ema_fast": [9, 20],
        "ema_slow": [21, 50],
        "atr_sl_mult": [1.0, 2.0],
        "atr_tp_mult": [1.5, 3.0],
    },
    # Live results showed the plain crossover losing far more than chance,
    # which makes its inverse a genuine hypothesis rather than a joke.
    "ema_cross_inverted": {
        "ema_fast": [9, 12, 20],
        "ema_slow": [21, 50, 100],
        "atr_sl_mult": [1.0, 1.5, 2.0],
        "atr_tp_mult": [1.5, 2.5, 3.5],
        "rsi_floor": [40.0, 45.0],
        "rsi_ceiling": [55.0, 60.0],
    },
    "rsi_reversion": {
        "rsi_period": [7, 14, 21],
        "rsi_oversold": [20.0, 25.0, 30.0],
        "rsi_overbought": [70.0, 75.0, 80.0],
        "atr_sl_mult": [1.0, 1.5, 2.0],
        "atr_tp_mult": [1.5, 2.0, 3.0],
    },
    "momentum": {
        "ema_slow": [10, 20, 40],
        "atr_sl_mult": [1.0, 1.5, 2.0],
        "atr_tp_mult": [1.5, 2.5, 3.5],
    },
    "bollinger_breakout": {
        "bb_period": [14, 20, 30],
        "bb_std": [1.5, 2.0, 2.5],
        "atr_sl_mult": [1.0, 1.5, 2.0],
        "atr_tp_mult": [1.5, 2.5, 3.5],
    },
}

MIN_TRADES = 20   # fewer than this and the result is noise, not evidence


def combos(grid: dict) -> list[dict]:
    keys = list(grid)
    return [dict(zip(keys, values)) for values in itertools.product(*grid.values())]


def variant(base: Settings, params: dict) -> Settings:
    s = copy(base)
    for key, value in params.items():
        setattr(s, key, value)
    return s


def main() -> int:
    p = argparse.ArgumentParser(description="Search for a configuration with real edge")
    p.add_argument("--symbol", default=None)
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--csv")
    p.add_argument("--balance", type=float, default=50.0)
    p.add_argument("--timeframe", help="override timeframe (M1/M5/M15/H1...)")
    p.add_argument("--top", type=int, default=10, help="how many results to show")
    p.add_argument("--strategy", choices=list(GRIDS), help="search only this one")
    p.add_argument("--point-value", type=float)
    p.add_argument("--spread", type=float)
    args = p.parse_args()

    base = Settings.load()
    if args.timeframe:
        base.timeframe = args.timeframe
    if base.fixed_lot <= 0:
        base.fixed_lot = 0.01          # keep sizing constant across the search
    symbol = args.symbol or (base.symbols[0] if base.symbols else "EURUSD")

    # --- data ---------------------------------------------------------
    import backtest as bt
    if args.csv:
        bars = bt.load_csv(args.csv)
        point_value = args.point_value or bt.point_value_for(symbol)
        spread = args.spread if args.spread is not None else bt.spread_for(symbol)
    else:
        try:
            bars, point_value, spread = bt.load_mt5(base, symbol, base.timeframe, args.days)
        except Exception as exc:
            print(f"Could not load MT5 data: {exc}", file=sys.stderr)
            return 1
        if args.point_value:
            point_value = args.point_value
        if args.spread is not None:
            spread = args.spread

    if len(bars) < 500:
        print(f"Only {len(bars)} bars — need at least 500 to search.", file=sys.stderr)
        return 1

    split = int(len(bars) * 2 / 3)
    train, test = bars[:split], bars[split:]
    print("=" * 76)
    print(f"OPTIMIZE  {symbol} {base.timeframe}  {len(bars)} bars "
          f"({(bars[-1].time - bars[0].time) / 86400:.0f} days)")
    print(f"  in-sample: {len(train)} bars   out-of-sample: {len(test)} bars")
    print(f"  spread {spread:g}, size {base.fixed_lot} lot, balance {args.balance:.0f}")
    print("=" * 76)

    names = [args.strategy] if args.strategy else list(GRIDS)
    results = []
    tested = 0
    for name in names:
        cls = VEC_STRATEGIES[name]
        grid = combos(GRIDS[name])
        print(f"  searching {name}: {len(grid)} combinations...")
        for params in grid:
            tested += 1
            if params.get("ema_fast", 0) >= params.get("ema_slow", 10 ** 9):
                continue
            s = variant(base, params)
            r = simulate(train, cls(s), s, args.balance, point_value, spread)
            if len(r.trades) < MIN_TRADES:
                continue
            results.append((name, params, r))

    if not results:
        print("\nNo configuration produced enough trades to judge. Try more days, "
              "a faster timeframe, or lower MIN_TRADES.")
        return 0

    results.sort(key=lambda x: x[2].profit_factor, reverse=True)

    print(f"\n{'strategy':15} {'PF':>6} {'win%':>6} {'trades':>7} {'return%':>9} "
          f"{'maxDD%':>7}  | {'OUT-OF-SAMPLE':>22}")
    print("-" * 76)
    profitable_oos = []
    for name, params, r in results[: args.top]:
        cls = VEC_STRATEGIES[name]
        s = variant(base, params)
        oos = simulate(test, cls(s), s, args.balance, point_value, spread)
        pf = r.profit_factor
        opf = oos.profit_factor
        flag = "OK" if opf > 1.0 and len(oos.trades) >= 5 else ""
        if flag:
            profitable_oos.append((name, params, r, oos))
        print(f"{name:15} {pf:6.2f} {r.win_rate:6.1f} {len(r.trades):7} "
              f"{r.return_pct:+9.1f} {r.max_drawdown_pct:7.1f}  | "
              f"PF {opf:5.2f} ret {oos.return_pct:+7.1f}% {flag:>3}")
        print(f"{'':15}   {params}")

    print("\n" + "=" * 76)
    if profitable_oos:
        name, params, r, oos = profitable_oos[0]
        print(f"BEST SURVIVOR: {name} {params}")
        print(f"  in-sample  PF {r.profit_factor:.2f}, return {r.return_pct:+.1f}%")
        print(f"  out-of-sample PF {oos.profit_factor:.2f}, return {oos.return_pct:+.1f}% "
              f"over {oos.span_days:.0f} days ({len(oos.trades)} trades)")
        if oos.per_day_pct > 0:
            bal, days = args.balance, 0
            while bal < args.balance * 20 and days < 3650:
                bal *= 1 + oos.per_day_pct / 100
                days += 1
            print(f"  at {oos.per_day_pct:+.2f}%/day, 20x would take "
                  f"{'>10 years' if days >= 3650 else f'~{days} days'}")
        print(f"\n  ! MULTIPLE-TESTING WARNING: {tested} combinations were tried.")
        print(f"    Even on data with NO real edge, roughly {max(1, tested // 20)} of them")
        print( "    would clear out-of-sample by chance. One survivor out of hundreds is")
        print( "    NOT evidence of edge — it is the expected amount of luck.")
        print( "    Before believing it: re-run on a DIFFERENT symbol and a different")
        print( "    period. An edge that is real shows up in several; a coincidence")
        print( "    shows up in exactly one. Then demo it for weeks — never live money")
        print( "    straight from a backtest.")
    else:
        print("NOTHING SURVIVED OUT-OF-SAMPLE.")
        print("  Every configuration that looked good on the first two-thirds of the")
        print("  data failed on the last third. That is the normal outcome, and it is")
        print("  useful information: these strategies have no edge on this instrument")
        print("  after costs. Options: try another symbol or timeframe, or accept that")
        print("  this approach does not work and do not risk money on it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
