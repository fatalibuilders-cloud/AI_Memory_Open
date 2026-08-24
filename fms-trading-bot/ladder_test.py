#!/usr/bin/env python3
r"""Simulate a staged protective stop and show the real outcome distribution.

    .\.venv\Scripts\python.exe ladder_test.py
    .\.venv\Scripts\python.exe ladder_test.py --trades 2000 --stop 0.40 --target 0.50

A break-even ladder is often pictured as "trades either break even or win".
It has three outcomes, not two:

  1. never reaches the first trigger  -> the FULL stop loss
  2. reaches it, then pulls back      -> break-even (or the locked amount)
  3. keeps going                      -> the target

Outcome 1 is the one that decides whether the ladder pays, and it is the
one most easily left out of a mental model. This runs the mechanics tick
by tick so the split is measured rather than assumed.
"""

from __future__ import annotations

import argparse
import random
from collections import Counter


def parse_stages(text: str) -> list[tuple[float, float]]:
    out = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        trigger, _, lock = part.partition(":")
        out.append((float(trigger), float(lock or 0)))
    return sorted(out)


def simulate(trades: int, stop: float, target: float,
             stages: list[tuple[float, float]], spread: float,
             step: float, seed: int = 11) -> tuple[Counter, float]:
    """Random walk from entry until the stop or target is touched.

    Money units throughout: the walk is in profit, not price.
    """
    random.seed(seed)
    outcomes: Counter = Counter()
    total = 0.0
    for _ in range(trades):
        profit = 0.0
        floor = -stop                      # current stop, in profit terms
        stage_reached = -1
        while True:
            profit += step if random.random() < 0.5 else -step
            # tighten as stages are earned
            for i, (trigger, lock) in enumerate(stages):
                if i > stage_reached and profit >= trigger:
                    stage_reached = i
                    floor = max(floor, lock)
            if profit <= floor:
                result = round(floor, 2)
                break
            if profit >= target:
                result = round(target, 2)
                break
        total += result - spread
        if result <= -stop:
            outcomes["full stop"] += 1
        elif result < 0:
            outcomes[f"partial {result:+.2f}"] += 1
        elif result == 0:
            outcomes["break-even 0.00"] += 1
        elif result >= target:
            outcomes[f"target {result:+.2f}"] += 1
        else:
            outcomes[f"locked {result:+.2f}"] += 1
    return outcomes, total


def main() -> int:
    p = argparse.ArgumentParser(description="Measure a protective-stop ladder")
    p.add_argument("--trades", type=int, default=2000)
    p.add_argument("--stop", type=float, default=0.40, help="full stop loss ($)")
    p.add_argument("--target", type=float, default=0.50, help="take profit ($)")
    p.add_argument("--stages", default="0.10:0,0.25:0.10",
                   help="trigger:lock pairs (default 0.10:0,0.25:0.10)")
    p.add_argument("--spread", type=float, default=0.12, help="cost per trade ($)")
    p.add_argument("--step", type=float, default=0.01,
                   help="price granularity in $ of profit (default 0.01)")
    args = p.parse_args()

    stages = parse_stages(args.stages)
    outcomes, total = simulate(args.trades, args.stop, args.target, stages,
                               args.spread, args.step)

    print("=" * 66)
    print(f"{args.trades:,} TRADES — stop ${args.stop:.2f}, target "
          f"${args.target:.2f}, spread ${args.spread:.2f}")
    print(f"ladder: " + ", ".join(f"at +${t:.2f} lock +${l:.2f}" for t, l in stages))
    print("=" * 66)

    print(f"\n{'outcome':22} {'count':>7} {'share':>8} {'money':>12}")
    print("-" * 52)
    gross = 0.0
    for name, count in sorted(outcomes.items(),
                              key=lambda kv: -kv[1]):
        value = 0.0
        if name == "full stop":
            value = -args.stop
        elif name != "break-even 0.00":
            value = float(name.split()[-1])
        money = value * count
        gross += money
        print(f"{name:22} {count:7,} {100*count/args.trades:7.1f}% {money:+12,.2f}")

    costs = args.spread * args.trades
    print("-" * 52)
    print(f"{'gross':22} {'':>7} {'':>8} {gross:+12,.2f}")
    print(f"{'spread':22} {'':>7} {'':>8} {-costs:+12,.2f}")
    print(f"{'NET':22} {'':>7} {'':>8} {total:+12,.2f}")
    print(f"\nper trade: {total/args.trades:+.4f}")

    stopped = outcomes["full stop"]
    print(f"\n{100*stopped/args.trades:.1f}% of trades never reached the first "
          f"trigger (+${stages[0][0]:.2f})")
    print(f"and took the full ${args.stop:.2f} stop. That is "
          f"${stopped*args.stop:,.2f} of losses,")
    print(f"which is what the winners have to cover.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
