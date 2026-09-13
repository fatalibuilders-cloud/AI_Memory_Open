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
#: Significance required against the tool's own null, AFTER correcting for
#: how many strategies were tried. 0.05 means: a one-in-twenty chance that
#: anything in the whole run is called an edge when nothing has one.
ALPHA = 0.05
#: Confidence used for the upper bound on the null rate. The null rate is
#: itself estimated from a handful of shuffled runs, so its point estimate
#: is worth little; the p-values use this bound instead, which is the
#: pessimistic reading those runs still permit.
NULL_CONFIDENCE = 0.90


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


def binomial_at_most(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    from math import comb
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def null_rate_upper(hits: int, trials: int, confidence: float) -> float:
    """The largest null rate the shuffled runs could plausibly be hiding.

    One hit in twelve shuffled runs is not proof that the rate is 8%; with
    that little data it could easily be a quarter. Using the point estimate
    makes every p-value look better than the evidence supports, so take the
    upper end of the interval instead (Clopper-Pearson, by bisection) and
    let the p-values be conservative until more null runs narrow it.
    """
    if trials <= 0:
        return 1.0
    if hits >= trials:
        return 1.0
    lo, hi = hits / trials, 1.0
    for _ in range(60):                      # plenty for double precision
        mid = (lo + hi) / 2
        # P(seeing this few hits or fewer) at rate `mid`. The upper bound is
        # the rate at which that probability falls to (1 - confidence).
        if binomial_at_most(hits, trials, mid) > 1.0 - confidence:
            lo = mid
        else:
            hi = mid
    return hi


def null_runs_needed(k: int, n: int, tried: int, hits: int = 0,
                     trials: int = 0, max_runs: int = 60) -> int:
    """Shuffled runs per symbol that could settle a k-of-n result.

    The hits already seen are what decide this, and an earlier version
    ignored them: it assumed every further run would come back clean and
    so advised 7 runs to a user who had just finished 7 runs that found
    the strategy in noise 4 times out of 42. More runs sharpen a rate;
    they do not lower one. So project the observed rate forward, and
    return 0 when no amount of computation can bring the bound low
    enough — which is the honest answer whenever the measured noise rate
    is already near the level the result would have to beat.
    """
    rate = hits / trials if trials else 0.0
    for runs in range(1, max_runs + 1):
        total = runs * n
        if total <= trials:
            continue                       # already done, nothing to learn
        bound = null_rate_upper(round(rate * total), total, NULL_CONFIDENCE)
        if family_wise(binomial_at_least(k, n, bound), tried) < ALPHA:
            return runs
    return 0


def symbols_needed(k: int, n: int, tried: int, rate: float,
                   max_symbols: int = 40) -> int:
    """Symbols needed for the same survival fraction to mean something.

    Three of six against a 10% noise rate is not significant once the
    search is counted, and it never will be — the fraction has to hold up
    over more instruments. This says how many, at the rate already
    measured, which is the difference between a test worth running and
    another re-run of the one that already failed to settle it.
    """
    if not k:
        return 0
    share = k / n
    for count in range(n + 1, max_symbols + 1):
        need = round(share * count)
        if family_wise(binomial_at_least(need, count, rate), tried) < ALPHA:
            return count
    return 0


def family_wise(pval: float, tried: int) -> float:
    """P(at least one of `tried` strategies scores this well by luck).

    Testing thirteen strategies and reporting the best one's p-value is the
    oldest way to manufacture a discovery: at p = 0.05 apiece, roughly one
    in two such runs produces a "winner" with nothing in it. This is the
    number that belongs in the verdict.
    """
    tried = max(tried, 1)
    return 1.0 - (1.0 - pval) ** tried


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


def report(per_strategy: dict, null_hits: dict, tested_symbols: list,
           tried: int, null_per_symbol: int, days: int) -> int:
    """Print the verdict. Separated so it can be tested.

    Everything above it takes minutes of simulation to produce. A
    formatting mistake here throws all of that away at the last step,
    which is exactly when there is no patience left to re-run it.
    """
    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    n = len(tested_symbols)
    null_trials = n * null_per_symbol
    print(f"\n  Tested {n} symbol(s), and ran the identical search on "
          f"{null_trials} shuffled")
    print( "  copies of the same bars — same volatility, no predictable structure.")
    print( "  A strategy only counts if it beats what the search finds in noise.\n")

    print(f"  Judged {tried} strategies, so a p-value below is the chance that "
          f"ANY of\n  the {tried} would score this well with no edge in any of "
          f"them — not the\n  chance for one named in advance. The noise column "
          f"shows the measured\n  rate and the pessimistic bound the null runs "
          f"still allow.\n")

    print(f"  {'strategy':20} {'real':>6} {'noise':>11} {'p':>9}   verdict")
    print("  " + "-" * 65)
    winners = []
    close = []
    names = sorted(set(per_strategy) | set(null_hits),
                   key=lambda k: -len(per_strategy.get(k, [])))
    for name in names:
        k = len(per_strategy.get(name, []))
        hits = null_hits.get(name, 0)
        p0 = hits / null_trials if null_trials else 0.5
        # A rate estimated from a dozen runs is barely estimated at all, and
        # a rate of zero is never established by not seeing something. Judge
        # against the top of the interval those runs leave open.
        p0_hi = (null_rate_upper(hits, null_trials, NULL_CONFIDENCE)
                 if null_trials else 1.0)
        raw = binomial_at_least(k, n, p0)
        pval = family_wise(binomial_at_least(k, n, p0_hi), tried)
        if k >= 2 and pval < ALPHA:
            verdict = "beats noise"
            winners.append((name, k, pval))
        elif k >= 2 and raw < ALPHA:
            verdict = "not proven"
            close.append((name, k, raw, family_wise(raw, tried), pval,
                          hits, p0_hi))
        elif k:
            verdict = "within noise"
        else:
            verdict = "-"
        noise = f"{p0*100:.0f}-{p0_hi*100:.0f}%"
        print(f"  {name:20} {k:3}/{n:<2} {noise:>11} {pval:9.3f}   {verdict}")

    print()
    if winners:
        for name, k, pval in winners:
            print(f"  {name} survived on {k} of {n} symbols, and chance across "
                  f"all\n  {tried} strategies explains that only "
                  f"{pval*100:.1f}% of the time. That is the")
            print( "  weakest evidence worth acting on — and acting on it means")
            print( "  DEMO, for weeks, at the size you would really trade.")
            print( "  Backtests carry no slippage, no requotes, no weekend gaps")
            print( "  and no nerves.")
        print( "\n  Confirm before believing it: re-run with --null-runs 5 and")
        print( "  again over a different window (--days 120). An edge that is")
        print( "  real survives both; a coincidence survives exactly the run")
        print( "  that discovered it.")
    elif close:
        print("  NOTHING PROVEN — but one candidate is worth another look.")
        for name, k, raw, fam, pval, _, _ in close:
            print(f"\n  {name} survived on {k} of {n} symbols. On its own that "
                  f"reads as\n  p = {raw:.3f}, which looks like a finding. Two "
                  f"things stand between\n  that number and a real one:")
            print(f"    - {tried} strategies were tried, and the best of "
                  f"{tried} is not the same\n      as one named in advance. "
                  f"Counting the search: p = {fam:.3f}.")
            print(f"    - the noise rate came from {null_trials} shuffled runs, "
                  f"which pins it down\n      only loosely. At the pessimistic "
                  f"end those runs allow: p = {pval:.3f}.")
        name, k, _, _, _, hits, p0_hi = max(close, key=lambda c: c[1])
        # By symbol count, not by the prettiest p-value: the strongest
        # real result is the one worth spending more computation on.
        runs = null_runs_needed(k, n, tried, hits, null_trials)
        print( "\n  Neither objection says the candidate is worthless — both say "
               "this run\n  cannot tell. What would tell:\n")

        if runs:
            print(f"  1. More shuffled runs. {runs} per symbol would pin the "
                  f"noise rate down\n     tightly enough for {k} of {n} to "
                  f"count, if the rate holds.\n")
            print(f"       .\\.venv\\Scripts\\python.exe find_edge.py "
                  f"--days {days} --null-runs {runs}\n")
        else:
            print(f"  1. NOT more shuffled runs. {hits} of the {null_trials} "
                  f"shuffled runs found\n     {name} in noise, so the noise "
                  f"rate really is around "
                  f"{hits / max(null_trials, 1) * 100:.0f}%, and\n     {k} of "
                  f"{n} does not beat that once the search is counted. More "
                  f"runs\n     measure that rate more precisely; they do not "
                  f"lower it.\n")

        wider = symbols_needed(k, n, tried, p0_hi)
        if wider:
            print(f"  2. More symbols. At the noise rate measured here, the "
                  f"same share\n     surviving over {wider} symbols would "
                  f"clear the bar. Add the ones you\n     actually want to "
                  f"trade:\n")
            print(f"       .\\.venv\\Scripts\\python.exe find_edge.py "
                  f"--days {days} --null-runs {null_per_symbol} \\\n"
                  f"           --symbols <your {wider} symbols>\n")
        else:
            print(f"  2. More symbols would help, but this share surviving "
                  f"cannot reach\n     significance at the noise rate "
                  f"measured, at any number of symbols.\n")

        print(f"  3. One strategy, named in advance, on data it has not seen. "
              f"The\n     {tried}-strategy penalty exists because {name} was "
              f"PICKED from\n     this run. Test only it, on a window this run "
              f"did not use, and\n     the penalty is gone — the hypothesis "
              f"was fixed before the data:\n")
        print(f"       .\\.venv\\Scripts\\python.exe find_edge.py "
              f"--days {days * 2} --null-runs {null_per_symbol} \\\n"
              f"           --strategy {name}\n")
        print( "     This is the cheapest of the three and the only one that "
               "answers\n     the question asked. It is also the one that can "
               "come back negative,\n     which is what makes it worth "
               "anything.\n")
        print( "  An edge that is real survives a window it was not chosen on.")
        print( "  A coincidence survives exactly the run that discovered it.")
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
        # The span is worth printing because it is not the number asked
        # for: --days on M1 requests days x 1440 bars, and weekends have
        # none, so 60 "days" of M1 reaches back about 84 calendar days.
        # Confirming on "a different window" means checking these dates.
        from datetime import datetime, timezone
        span = " to ".join(
            datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")
            for t in (bars[0].time, bars[-1].time))
        print(f"\n{symbol}  ({len(bars)} bars, {span}, spread {spread:g})")
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

    if report(per_strategy, null_hits, tested_symbols,
              len(grids), args.null_runs, args.days):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
