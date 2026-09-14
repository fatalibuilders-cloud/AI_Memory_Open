#!/usr/bin/env python3
r"""Test the edge test, on data whose answer is already known.

    .\.venv\Scripts\python.exe calibrate.py
    .\.venv\Scripts\python.exe calibrate.py --walk-forward 4

`find_edge.py` decides whether real money gets risked. Nothing checks it
except this, and the need is not hypothetical: an early version passed
`ema_cross` on pure random walks with no edge in them by construction.
That was caught by hand, once, and the check was then thrown away.

So it runs twice, on synthetic instruments:

  * **Noise** -- random walks. Every pattern in them is an accident. The
    tool must find NOTHING. A tool that flags something here will flag
    something on your account, and you will believe it.
  * **Edge** -- the same walks with a real, mechanical regularity built
    in. The tool must find it. A test that never says yes is not safe,
    it is useless, and its silence about your strategies would mean
    nothing at all.

Both answers matter. Passing one and failing the other is worse than
failing both, because it looks like it works.
"""

from __future__ import annotations

import argparse
import random
import sys

from fmsbot.broker.base import Bar
from fmsbot.config import Settings

import find_edge as fe

#: Enough bars for a walk-forward to have folds worth fitting.
BARS = 9000
#: Bars per synthetic "day" — only used to give the bars plausible times.
STEP = 300


def _walk(rnd: random.Random, drift: float = 0.0,
          momentum: float = 0.0) -> list[Bar]:
    """A price series. `momentum` makes each step lean the way the last
    one went, which is the regularity a trend strategy exists to find."""
    bars, price, step = [], 1.1000, 0.0
    for i in range(BARS):
        step = rnd.gauss(0, 0.0004) + drift + step * momentum
        opened, price = price, price + step
        high = max(opened, price) + abs(rnd.gauss(0, 0.0002))
        low = min(opened, price) - abs(rnd.gauss(0, 0.0002))
        bars.append(Bar(i * STEP, opened, high, low, price))
    return bars


def series(kind: str, count: int, seed: int) -> dict:
    """`count` synthetic instruments of one kind."""
    out = {}
    for k in range(count):
        rnd = random.Random(seed * 1000 + k)
        bars = (_walk(rnd) if kind == "noise"
                else _walk(rnd, drift=0.000015, momentum=0.25))
        out[f"{kind.upper()}{k}"] = (bars, 1000.0, 0.00008)
    return out


def verdict(base, data, grids, null_runs, folds, tried) -> list:
    """The strategies find_edge would call an edge, with their p-values."""
    survivors, nulls, tested = fe.assess(
        base, data, grids, null_runs, folds, 100.0, quiet=True)
    n, trials = len(tested), len(tested) * null_runs
    out = []
    for name, syms in survivors.items():
        k = len(syms)
        hits = nulls.get(name, 0)
        bound = (fe.null_rate_upper(hits, trials, fe.NULL_CONFIDENCE)
                 if trials else 1.0)
        p = fe.family_wise(fe.binomial_at_least(k, n, bound), tried)
        if k >= 2 and p < fe.ALPHA:
            out.append((name, k, n, p))
    return sorted(out, key=lambda r: r[3])


def main() -> int:
    p = argparse.ArgumentParser(description="Check find_edge against known data")
    p.add_argument("--symbols", type=int, default=6)
    p.add_argument("--null-runs", type=int, default=3)
    p.add_argument("--walk-forward", type=int, default=1)
    p.add_argument("--strategy", help="check only this one")
    p.add_argument("--seed", type=int, default=11)
    args = p.parse_args()

    import optimize as opt
    grids = ({args.strategy: opt.GRIDS[args.strategy]} if args.strategy
             else opt.GRIDS)
    base = Settings.load(dotenv_path=None)
    base.fixed_lot = 0.01

    print("=" * 74)
    print(f"CALIBRATION — {args.symbols} synthetic symbols, "
          f"{len(grids)} strategies, {args.null_runs} null runs")
    if args.walk_forward > 1:
        print(f"  walk-forward: {args.walk_forward} folds")
    print("=" * 74)

    print("\n1. NOISE — random walks. Nothing in them to find.")
    found = verdict(base, series("noise", args.symbols, args.seed), grids,
                    args.null_runs, args.walk_forward, len(grids))
    if found:
        print("   FAIL — it called noise an edge:")
        for name, k, n, pval in found:
            print(f"     {name}: {k}/{n} symbols, p = {pval:.4f}")
    else:
        print("   pass — silent, as it must be.")

    print("\n2. EDGE — the same walks with a real trend built in.")
    got = verdict(base, series("edge", args.symbols, args.seed + 1), grids,
                  args.null_runs, args.walk_forward, len(grids))
    if got:
        print("   pass — it found what was planted:")
        for name, k, n, pval in got:
            print(f"     {name}: {k}/{n} symbols, p = {pval:.4f}")
    else:
        print("   FAIL — it missed an edge that is there by construction.")

    ok = (not found) and bool(got)
    print("\n" + "=" * 74)
    if ok:
        print("CALIBRATED. It says no to noise and yes to a real edge, so a")
        print("verdict from it on your own data is worth reading.")
    else:
        print("NOT CALIBRATED. Fix this before believing any verdict it gives")
        print("about a real account — including a negative one.")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
