#!/usr/bin/env python3
"""Analyse a Deriv Bot transaction export.

Usage:
    python3 analyse-results.py Transactions_*.csv [--chart equity.png]

Reads one or more Deriv "Transactions" CSV exports (statement download from
Deriv → Reports → Statement, or the bot's own export), and reports what the
run actually says: win rate against the break-even rate implied by the payout,
where the result sits inside the noise band, streaks, and the points where the
bot halted itself.

With --chart it draws the equity curve against the expectation line and a
±2 sigma cone, so luck and edge are visually separable.
"""

import argparse
import csv
import datetime as dt
import math
import os
import sys


def read_trades(paths):
    trades = []
    for path in paths:
        with open(path, newline="") as handle:
            for row in csv.DictReader(handle):
                row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
                if not row.get("Start Time") or not row.get("Profit/Loss"):
                    continue
                try:
                    trades.append(
                        {
                            "market": row.get("Market", ""),
                            "start": dt.datetime.strptime(
                                row["Start Time"].replace(" GMT", ""), "%Y-%m-%d %H:%M:%S.%f"
                            ),
                            "entry": float(row["Entry Spot"]),
                            "exit": float(row["Exit Spot"]),
                            "entry_time": row.get("Entry Spot Time", ""),
                            "exit_time": row.get("Exit Spot Time", ""),
                            "stake": float(row["Buy Price"]),
                            "pl": float(row["Profit/Loss"]),
                        }
                    )
                except (KeyError, ValueError):
                    continue

    # Deriv exports newest first; work forwards in time and drop duplicates.
    unique = {(t["start"], t["stake"], t["pl"], t["entry"]): t for t in trades}
    return sorted(unique.values(), key=lambda t: t["start"])


def summarise(trades):
    wins = [t for t in trades if t["pl"] > 0]
    losses = [t for t in trades if t["pl"] <= 0]
    n = len(trades)
    net = sum(t["pl"] for t in trades)
    staked = sum(t["stake"] for t in trades)
    payout = (sum(t["pl"] for t in wins) / sum(t["stake"] for t in wins)) if wins else 0.0

    flat = len({round(t["stake"], 2) for t in trades}) == 1
    break_even = 1 / (1 + payout) if payout else float("nan")
    # Per-trade P/L in stake units: +payout or -1, assuming a coin-flip outcome.
    ev_unit = 0.5 * payout - 0.5
    sd_unit = math.sqrt(0.5 * payout ** 2 + 0.5 - ev_unit ** 2)
    avg_stake = staked / n
    expected = n * ev_unit * avg_stake
    sigma = math.sqrt(n) * sd_unit * avg_stake

    print("=" * 64)
    print("trades            : %d   (%s)" % (n, trades[0]["market"] or "unknown market"))
    print(
        "window            : %s -> %s  (%.0f min)"
        % (
            trades[0]["start"].strftime("%Y-%m-%d %H:%M:%S"),
            trades[-1]["start"].strftime("%H:%M:%S"),
            (trades[-1]["start"] - trades[0]["start"]).total_seconds() / 60,
        )
    )
    print(
        "wins / losses     : %d / %d   (%.2f%% win rate)"
        % (len(wins), len(losses), 100 * len(wins) / n)
    )
    print(
        "stake             : %s   payout on win %.0f%%"
        % (
            "flat %.2f" % trades[0]["stake"] if flat else "variable %.2f - %.2f"
            % (min(t["stake"] for t in trades), max(t["stake"] for t in trades)),
            100 * payout,
        )
    )
    print("net P/L           : %+.2f on %.2f staked  (%+.2f%% of turnover)" % (net, staked, 100 * net / staked))
    print()
    print("break-even win rate: %.2f%%   (needed %.1f wins, got %d)" % (100 * break_even, n * break_even, len(wins)))
    print("expected P/L if the market is a coin flip: %+.2f" % expected)
    print("1 sigma over %d trades: %.2f  ->  this run is %+.2f sigma from expectation"
          % (n, sigma, (net - expected) / sigma if sigma else 0))
    if abs((net - expected) / sigma if sigma else 0) < 2:
        print("                      -> inside the noise band: no edge demonstrated either way")
    else:
        print("                      -> outside 2 sigma: worth a longer run to confirm")

    if ev_unit < 0:
        need = round((2 * sd_unit / (0.54 * payout - 0.46)) ** 2) if (0.54 * payout - 0.46) > 0 else None
        if need:
            print("trades needed to prove a 54%% win rate at 2 sigma: ~%d" % need)

    ties = [t for t in trades if t["entry"] == t["exit"]]
    if ties:
        print("\nexact ties (entry == exit, a loss on Rise/Fall): %d (%.1f%% of trades)"
              % (len(ties), 100 * len(ties) / n))

    return {"net": net, "expected_unit": ev_unit, "sd_unit": sd_unit, "avg_stake": avg_stake}


def streaks(trades):
    marks = ["W" if t["pl"] > 0 else "L" for t in trades]
    longest = {"W": 0, "L": 0}
    run, prev = 0, None
    for m in marks:
        run = run + 1 if m == prev else 1
        prev = m
        longest[m] = max(longest[m], run)

    print("\nsequence:")
    for i in range(0, len(marks), 50):
        print("  " + " ".join(marks[i:i + 50]))
    print("  longest losing streak %d, longest winning streak %d" % (longest["L"], longest["W"]))


def halts(trades, threshold=45):
    gaps = [
        (a, b, (b["start"] - a["start"]).total_seconds())
        for a, b in zip(trades, trades[1:])
        if (b["start"] - a["start"]).total_seconds() > threshold
    ]
    print("\nhalts / idle gaps over %ds: %d" % (threshold, len(gaps)))
    for a, b, gap in gaps[:20]:
        print("  %s -> %s  (%.0fs idle)" % (a["start"].strftime("%H:%M:%S"), b["start"].strftime("%H:%M:%S"), gap))
    if len(gaps) > 20:
        print("  ... and %d more" % (len(gaps) - 20))


def martingale_what_if(trades, multiplier=2.1, cap=4):
    wins = [t for t in trades if t["pl"] > 0]
    if not wins:
        return
    payout = sum(t["pl"] for t in wins) / sum(t["stake"] for t in wins)
    base = min(t["stake"] for t in trades)
    stake, step, bal, peak, dd, worst = base, 0, 0.0, 0.0, 0.0, base
    for t in trades:
        worst = max(worst, stake)
        if t["pl"] > 0:
            bal += stake * payout
            stake, step = base, 0
        else:
            bal -= stake
            step += 1
            if step >= cap:
                step, stake = 0, base
            else:
                stake *= multiplier
        peak = max(peak, bal)
        dd = min(dd, bal - peak)

    print("\nsame outcomes with martingale (x%.1f, cap %d):" % (multiplier, cap))
    print("  net %+.2f   largest stake %.2f   worst drawdown %.2f" % (bal, worst, dd))


def chart(trades, stats, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    equity, running = [0.0], 0.0
    for t in trades:
        running += t["pl"]
        equity.append(running)

    n = len(trades)
    xs = list(range(n + 1))
    ev = [stats["expected_unit"] * stats["avg_stake"] * i for i in xs]
    band1 = [stats["sd_unit"] * stats["avg_stake"] * math.sqrt(i) for i in xs]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.fill_between(xs, [e - 2 * s for e, s in zip(ev, band1)], [e + 2 * s for e, s in zip(ev, band1)],
                    color="#8ab4f8", alpha=0.18, label="±2σ (pure chance)")
    ax.fill_between(xs, [e - s for e, s in zip(ev, band1)], [e + s for e, s in zip(ev, band1)],
                    color="#8ab4f8", alpha=0.28, label="±1σ")
    ax.plot(xs, ev, color="#d93025", linestyle="--", linewidth=1.6,
            label="expectation at a coin-flip win rate (%.1f%%/trade)" % (100 * stats["expected_unit"]))
    ax.plot(xs, equity, color="#137333", linewidth=2.0, label="actual equity")
    ax.axhline(0, color="#5f6368", linewidth=0.8)

    ax.set_xlabel("trade number")
    ax.set_ylabel("cumulative P/L (%s)" % "account currency")
    ax.set_title("Deriv Bot run — %d trades, net %+.2f" % (n, stats["net"]))
    ax.legend(loc="best", fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    print("\nchart written to %s" % path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="+", help="Deriv transaction CSV export(s)")
    parser.add_argument("--chart", metavar="PNG", help="write an equity curve chart")
    parser.add_argument("--martingale", action="store_true", help="show what a x2.1 martingale would have done")
    args = parser.parse_args()

    trades = read_trades(args.csv)
    if not trades:
        sys.exit("no trades found in: %s" % ", ".join(os.path.basename(p) for p in args.csv))

    stats = summarise(trades)
    streaks(trades)
    halts(trades)
    if args.martingale:
        martingale_what_if(trades)
    if args.chart:
        chart(trades, stats, args.chart)


if __name__ == "__main__":
    main()
