#!/usr/bin/env python3
r"""Decide whether any strategy has a real edge — across symbols, not one.

    .\.venv\Scripts\python.exe find_edge.py --days 60
    .\.venv\Scripts\python.exe find_edge.py --symbols EURUSDm,GBPUSDm,XAUUSDm

`optimize.py` searches one symbol and warns that a survivor could easily
be luck. This applies the only test that separates the two: a real edge
shows up on SEVERAL instruments, a coincidence shows up on exactly one.

For each symbol it fits every strategy on the first two-thirds of the
history and scores the winner on the final third it never saw. Then it
counts, per strategy, how many symbols it survived on — and compares that
against how many would survive by chance alone. Surviving on one symbol
out of nine is the expected amount of luck and means nothing.

The verdict is deliberately hard to pass. "Nothing has an edge" is the
normal answer and the useful one: it costs nothing to hear, where finding
out live costs the account.
"""

from __future__ import annotations

import argparse
import sys
from copy import copy

from fmsbot.config import Settings
from fmsbot.sim import simulate
from fmsbot.vecstrategy import VEC_STRATEGIES

#: Fewer trades than this out of sample and the result is noise. Verified:
#: at 5 the tool passed a strategy on random walks with no edge in them.
MIN_OOS_TRADES = 30
#: A survivor must beat this profit factor, not merely clear 1.0 — costs
#: are already charged, so 1.0 exactly is a coin flip dressed as a result.
MIN_OOS_PF = 1.1
#: Significance required against the tool's own null. 0.05 means: a one-in-
#: twenty chance of calling noise an edge.
ALPHA = 0.05


def shuffled(bars: list, seed: int) -> list:
    """The same bars with their order destroyed.

    Resampling the bar-to-bar returns keeps the volatility, the fat tails
    and the spread-to-movement ratio of the real instrument, while removing
    every trend, level and pattern a strategy could predict. Whatever the
    search finds here, it found in nothing — which is what makes it the
    right yardstick for what it finds in the real series.
    """
    import random
    rnd = random.Random(seed)
    if len(bars) < 3:
        return list(bars)
    steps = [bars[i].close - bars[i - 1].close for i in range(1, len(bars))]
    ups = [b.high - b.close for b in bars]
    downs = [b.close - b.low for b in bars]
    rnd.shuffle(steps)
    rnd.shuffle(ups)
    rnd.shuffle(downs)

    out = [bars[0]]
    price = bars[0].close
    for i, step in enumerate(steps, start=1):
        opened, price = price, price + step
        high = max(opened, price) + abs(ups[i])
        low = min(opened, price) - abs(downs[i])
        out.append(type(bars[0])(bars[i].time, opened, high, low, price))
    return out


def binomial_at_least(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p) — how easily chance explains this."""
    from math import comb
    if p <= 0:
        return 0.0 if k > 0 else 1.0
    if p >= 1:
        return 1.0
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def search(base: Settings, bars, point_value: float, spread: float,
           balance: float, grids: dict, label: str = "") -> dict:
    """Best in-sample config per strategy, scored out of sample."""
    import optimize as opt

    split = int(len(bars) * 2 / 3)
    train, test = bars[:split], bars[split:]
    out = {}
    for name, grid in grids.items():
        if label:
            # This runs for minutes with nothing to show. Silence looks
            # identical to a hang, and a hang is what people assume.
            print(f"\r    {label}: {name:<20}", end="", flush=True)
        cls = VEC_STRATEGIES[name]
        best = None
        for params in opt.combos(grid):
            if params.get("ema_fast", 0) >= params.get("ema_slow", 10 ** 9):
                continue
            s = copy(base)
            for key, value in params.items():
                setattr(s, key, value)
            r = simulate(train, cls(s), s, balance, point_value, spread)
            if len(r.trades) < opt.MIN_TRADES:
                continue
            if best is None or r.profit_factor > best[1].profit_factor:
                best = (params, r, s)
        if best is None:
            continue
        params, in_sample, s = best
        oos = simulate(test, cls(s), s, balance, point_value, spread)
        out[name] = (params, in_sample, oos)
    return out


def survived(oos) -> bool:
    return len(oos.trades) >= MIN_OOS_TRADES and oos.profit_factor >= MIN_OOS_PF


def main() -> int:
    p = argparse.ArgumentParser(description="Test for an edge across symbols")
    p.add_argument("--symbols", help="comma-separated; default: the account's")
    p.add_argument("--account", help="which account, when several are configured")
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--balance", type=float, default=100.0)
    p.add_argument("--timeframe")
    p.add_argument("--strategy", help="test only this one")
    p.add_argument("--null-runs", type=int, default=2,
                   help="shuffled copies per symbol to calibrate against "
                        "(default 2; higher is stricter and slower)")
    args = p.parse_args()

    base = Settings.load()
    if args.timeframe:
        base.timeframe = args.timeframe
    if base.fixed_lot <= 0:
        base.fixed_lot = 0.01        # keep sizing constant across the test

    configs = base.broker_configs()
    cfg = configs[0]
    if args.account:
        matches = [c for c in configs if c.name.lower() == args.account.lower()]
        if not matches:
            print(f"No account '{args.account}'.", file=sys.stderr)
            return 1
        cfg = matches[0]
    symbols = ([s.strip() for s in args.symbols.split(",") if s.strip()]
               if args.symbols else list(cfg.symbols))
    if not symbols:
        print("No symbols to test.", file=sys.stderr)
        return 1

    import optimize as opt
    import backtest as bt
    grids = ({args.strategy: opt.GRIDS[args.strategy]} if args.strategy
             else opt.GRIDS)
    combos_total = sum(len(opt.combos(g)) for g in grids.values())

    print("=" * 78)
    print(f"EDGE TEST — {len(symbols)} symbol(s), {base.timeframe}, "
          f"{args.days} days, {len(grids)} strategies")
    print(f"  {combos_total} parameter combinations per symbol, fitted on the "
          f"first two-thirds")
    print(f"  and scored on the final third. A survivor needs profit factor "
          f">= {MIN_OOS_PF}")
    print(f"  and at least {MIN_OOS_TRADES} out-of-sample trades, and must then")
    print( "  beat what the same search finds in shuffled copies of the same bars.")
    runs = combos_total * len(symbols) * (1 + args.null_runs)
    print(f"  About {runs:,} simulations — a few minutes. Leave it running.")
    print("=" * 78)

    per_strategy: dict[str, list[str]] = {}
    null_hits: dict[str, int] = {}
    tested_symbols = []
    for symbol in symbols:
        try:
            bars, point_value, spread = bt.load_mt5(
                base, symbol, base.timeframe, args.days)
        except Exception as exc:
            print(f"\n{symbol}: no data ({str(exc)[:50]})")
            continue
        if len(bars) < 500:
            print(f"\n{symbol}: only {len(bars)} bars, need 500+")
            continue
        tested_symbols.append(symbol)
        print(f"\n{symbol}  ({len(bars)} bars, spread {spread:g})")
        results = search(base, bars, point_value, spread, args.balance, grids,
                         label="searching")

        # The same search on the same bars with their order destroyed. This
        # is the yardstick: anything the search can find in noise, it will
        # also find in the real series, and that part is not an edge.
        for seed in range(args.null_runs):
            fake = search(base, shuffled(bars, hash(symbol) % 10_000 + seed),
                          point_value, spread, args.balance, grids,
                          label=f"calibrating {seed + 1}/{args.null_runs}")
            for name, (_, _, oos) in fake.items():
                if survived(oos):
                    null_hits[name] = null_hits.get(name, 0) + 1

        print("\r" + " " * 46 + "\r", end="")
        if not results:
            print("    no strategy produced enough trades to judge")
            continue
        for name, (params, ins, oos) in sorted(
                results.items(), key=lambda kv: -kv[1][2].profit_factor):
            ok = survived(oos)
            if ok:
                per_strategy.setdefault(name, []).append(symbol)
            print(f"    {name:20} in-sample PF {ins.profit_factor:5.2f}  |  "
                  f"out-of-sample PF {oos.profit_factor:5.2f} "
                  f"({len(oos.trades):3} trades) {'survived' if ok else ''}")

    n = len(tested_symbols)
    if n == 0:
        print("\nNo symbol had usable data. Open MT5, log in, and re-run.")
        return 1

    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    null_trials = n * args.null_runs
    print(f"\n  Tested {n} symbol(s), and ran the identical search on "
          f"{null_trials} shuffled")
    print( "  copies of the same bars — same volatility, no predictable structure.")
    print( "  A strategy only counts if it beats what the search finds in noise.\n")

    print(f"  {'strategy':20} {'real':>6} {'noise':>8} {'p':>9}   verdict")
    print("  " + "-" * 62)
    winners = []
    names = sorted(set(per_strategy) | set(null_hits),
                   key=lambda k: -len(per_strategy.get(k, [])))
    for name in names:
        k = len(per_strategy.get(name, []))
        # Never claim the null rate is zero: an event unseen in a few dozen
        # trials is not an impossible one, so use the smallest rate those
        # trials could have hidden.
        p0 = max(null_hits.get(name, 0) / null_trials, 1.0 / (2 * null_trials)) \
            if null_trials else 0.5
        pval = binomial_at_least(k, n, p0)
        if k >= 2 and pval < ALPHA:
            verdict = "beats noise"
            winners.append((name, k, pval))
        elif k:
            verdict = "within noise"
        else:
            verdict = "-"
        print(f"  {name:20} {k:3}/{n:<2} {p0*100:7.0f}% {pval:9.3f}   {verdict}")

    print()
    if winners:
        for name, k, pval in winners:
            print(f"  {name} survived on {k} of {n} symbols, which chance alone")
            print(f"  explains only {pval*100:.1f}% of the time. That is the "
                  f"weakest evidence")
            print( "  worth acting on — and acting on it means DEMO, for weeks, at the")
            print( "  size you would really trade. Backtests carry no slippage, no")
            print( "  requotes, no weekend gaps and no nerves.")
    else:
        print("  NO EDGE FOUND.")
        print("  Every apparent winner appeared no more often than the same")
        print("  search finds in shuffled noise. This is the normal result, and")
        print("  it is worth more than it feels: it is the money you did not lose")
        print("  finding out live. Options — try another timeframe, add history")
        print("  with --days, or accept that these strategies do not beat their")
        print("  own costs on this market and do not risk money on them.")
    print("\n  Judge on profit factor, never on win rate. A win rate is chosen")
    print("  by where the stop sits (see winrate.py); profit factor is earned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
