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


def no_stop_report(args) -> int:
    """What 'never close at a loss' actually costs.

    Removing the stop does not remove the loss — it converts a small
    realised loss into an unbounded floating one that is carried until the
    trade recovers or the account cannot carry it any longer.
    """
    random.seed(5)
    trades = args.trades
    wins = 0
    worst_single = 0.0
    total_realised = 0.0
    open_forever = 0
    # A position cannot be held indefinitely in practice: the account has to
    # carry the floating loss, and margin runs out.
    max_hold = 200_000                      # ticks before we call it stuck

    drawdowns = []
    for _ in range(trades):
        profit = 0.0
        worst = 0.0
        for _ in range(max_hold):
            profit += args.step if random.random() < 0.5 else -args.step
            worst = min(worst, profit)
            if profit >= args.target:
                break
        else:
            open_forever += 1
            drawdowns.append(worst)
            continue
        wins += 1
        total_realised += args.target - args.spread
        worst_single = min(worst_single, worst)
        drawdowns.append(worst)

    print("=" * 66)
    print(f"'NEVER CLOSE AT A LOSS' — {trades:,} trades, target "
          f"${args.target:.2f}, no stop")
    print("=" * 66)
    print(f"\n  closed in profit      : {wins:,} ({100*wins/trades:.1f}%)")
    print(f"  never recovered       : {open_forever:,} "
          f"({100*open_forever/trades:.1f}%)")
    print(f"  realised P&L          : {total_realised:+,.2f}")
    print(f"\n  worst drawdown on ONE trade : ${worst_single:,.2f}")

    drawdowns.sort()
    median = drawdowns[len(drawdowns)//2]
    p95 = drawdowns[int(len(drawdowns)*0.05)]
    print(f"  median trade went      : ${median:,.2f} against you first")
    print(f"  worst 5% went at least : ${p95:,.2f} against you")

    # Concurrent positions all carry their floating loss at once.
    concurrent = 5
    carried = sum(drawdowns[:concurrent])
    print(f"\n  With {concurrent} positions open at once, the account must carry")
    print(f"  about ${abs(carried):,.2f} of floating loss at the bad moments.")
    print(f"  Your balance is ${args.balance:,.2f}.")
    if abs(carried) > args.balance:
        print(f"\n  ** THE ACCOUNT CANNOT CARRY THAT. Margin call closes the")
        print(f"     positions AT THE WORST POINT — the losses you refused to")
        print(f"     take get taken for you, all at once, at the worst price. **")
    print("\n  The win rate looks near-perfect right up until the day it does not.")
    print("  This is how accounts are lost: not through many small losses, but")
    print("  through one refused loss that grows until it cannot be refused.")
    return 0


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
    p.add_argument("--no-stop", action="store_true",
                   help="never close at a loss: hold until the trade recovers")
    p.add_argument("--balance", type=float, default=50.0,
                   help="account balance, for the no-stop margin check")
    args = p.parse_args()

    if args.no_stop:
        return no_stop_report(args)

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
