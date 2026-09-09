#!/usr/bin/env python3
r"""Is a daily profit goal consistent with the risk rules? Solve it.

    .\.venv\Scripts\python.exe plan.py --profit 150 --trades 1000 --rr 3
    .\.venv\Scripts\python.exe plan.py --profit 150 --trades 20 --rr 3

Four numbers fight each other and only three can be chosen freely: how
many trades a day, how much each risks, the reward-to-risk, and the win
rate. The daily loss cap fixes the second once the first is chosen -- if
1000 trades a day means 600 losing ones, each may only risk a six-hundredth
of the day's budget -- and then the profit target fixes the win rate.

This prints the win rate each plan requires. A plan needing more than
about 60% is not a plan; sustained win rates above that, after costs, are
rare enough that assuming one is the same as assuming the answer.

The spread is charged on every trade, win or lose, so trading more often
multiplies it exactly. That term is why "more trades" is not free.
"""

from __future__ import annotations

import argparse
import sys

from fmsbot.config import Settings

#: Above this, a required win rate is not a plan, it is a wish.
PLAUSIBLE = 60.0


def required_win_rate(profit: float, trades: int, risk: float, rr: float,
                      cost_ratio: float) -> float:
    """The win rate a plan needs, as a percentage.

    The spread is charged per trade, but it is NOT a fixed sum: a smaller
    position pays proportionally less, because cost is the spread times
    the position size and size is set by the risk. So the cost of a trade
    is a fixed FRACTION of what that trade risks -- the spread divided by
    the stop distance -- and it stays that fraction however small the
    position gets. Treating it as a fixed dollar amount makes small
    positions look far worse than they are, and badly overstates the win
    rate a high-frequency plan needs.

    Per trade the expectation is r*[w*(R+1) - 1 - k]. Setting the day's
    total to the target and solving for w gives this.
    """
    if trades <= 0 or risk <= 0 or rr <= 0:
        return float("inf")
    return 100.0 * (profit / (trades * risk) + 1.0 + cost_ratio) / (rr + 1.0)


def max_risk(balance: float, daily_loss_pct: float, trades: int,
             win_rate: float) -> float:
    """The most one trade may risk before a normal day breaches the cap."""
    losses = trades * (1.0 - win_rate / 100.0)
    if losses <= 0:
        return float("inf")
    return balance * daily_loss_pct / 100.0 / losses


def main() -> int:
    p = argparse.ArgumentParser(description="Solve a daily profit plan")
    p.add_argument("--profit", type=float, default=150.0, help="target per day")
    p.add_argument("--trades", type=int, default=1000, help="trades per day")
    p.add_argument("--rr", type=float, default=3.0, help="reward to risk")
    p.add_argument("--balance", type=float)
    p.add_argument("--cost-ratio", type=float,
                   help="spread as a share of the stop (measured if omitted); "
                        "this is what MAX_SPREAD_RATIO caps")
    p.add_argument("--daily-loss-pct", type=float)
    args = p.parse_args()

    s = Settings.load()
    balance = args.balance
    cost = args.cost_ratio
    daily_pct = args.daily_loss_pct or s.daily_loss_limit_pct or 2.0

    if balance is None or cost is None:
        try:
            from fmsbot.broker import build_broker
            broker = build_broker(s)
            broker.connect()
            try:
                if balance is None:
                    balance = broker.balance()
                if cost is None:
                    # spread / stop distance, the fraction of each trade's
                    # risk that goes to the broker whatever the size
                    from fmsbot.indicators import atr
                    ratios = []
                    for symbol in s.symbols:
                        try:
                            bars = broker.bars(symbol, s.timeframe, 200)
                            value = atr([b.high for b in bars],
                                        [b.low for b in bars],
                                        [b.close for b in bars], s.atr_period)
                            stop = (value or 0) * s.atr_sl_mult
                            if stop > 0:
                                ratios.append(broker.spread(symbol) / stop)
                        except Exception:
                            continue
                    cost = sum(ratios) / len(ratios) if ratios else None
            finally:
                broker.disconnect()
        except Exception as exc:
            print(f"Could not reach the broker ({str(exc)[:50]}).")
            print("Pass --balance and --cost to plan without it.", file=sys.stderr)
            if balance is None:
                return 1
    if cost is None:
        cost = 0.0

    print("=" * 78)
    print(f"PLAN — ${args.profit:,.0f}/day from {args.trades:,} trades at "
          f"{args.rr:.1f}R")
    print("=" * 78)
    print(f"\n  balance {balance:,.2f}, daily loss cap {daily_pct}% "
          f"= {balance * daily_pct / 100:,.2f}")
    print(f"  spread costs {cost * 100:.1f}% of whatever each trade risks "
          f"(it scales with size)")

    breakeven = 100.0 / (args.rr + 1.0)
    after = 100.0 * (1.0 + cost) / (args.rr + 1.0)
    print(f"\n  At {args.rr:.1f}R, break-even is {breakeven:.1f}% wins before "
          f"costs, {after:.1f}% after.")

    print(f"\n  {'risk/trade':>11} {'losses/day':>11} {'day at cap':>11} "
          f"{'needs':>8}   verdict")
    print("  " + "-" * 62)

    feasible = []
    budget = balance * daily_pct / 100.0
    for risk in (1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 465.0):
        need = required_win_rate(args.profit, args.trades, risk, args.rr, cost)
        if need >= 100 or need <= 0:
            verdict = "impossible"
        else:
            losses_allowed = budget / risk
            expected_losses = args.trades * (1 - need / 100.0)
            if expected_losses > losses_allowed:
                verdict = "breaches the daily cap"
            elif need > PLAUSIBLE:
                verdict = f"needs {need:.0f}% wins — a wish"
            else:
                verdict = "consistent"
                feasible.append((risk, need))
            print(f"  {risk:11.2f} {expected_losses:11.0f} "
                  f"{losses_allowed:11.0f} {need:7.1f}%   {verdict}")
            continue
        print(f"  {risk:11.2f} {'':>11} {'':>11} {'':>8}   {verdict}")

    print("\n" + "=" * 78)
    if feasible:
        risk, need = feasible[0]
        print(f"WORKABLE: risk {risk:.2f} a trade at {args.rr:.1f}R, needing "
              f"{need:.1f}% wins.")
        print(f"  That is {risk / balance * 100:.4f}% of the account per trade, "
              f"not {s.risk_pct}%.")
        print(f"  RISK_PCT={risk / balance * 100:.4f}")
        print(f"  MIN_REWARD_RISK={args.rr:.1f}")
        print(f"\n  {need:.1f}% is the number to test, not to assume. "
              f"find_edge.py measures it.")
    else:
        print("NOT CONSISTENT at any size.")
        print(f"  Every risk that reaches ${args.profit:,.0f}/day from "
              f"{args.trades:,} trades either")
        print( "  needs a win rate nobody sustains, or breaches the daily loss cap")
        print( "  on an ordinary day. Fewer trades, a higher reward:risk, or a")
        print( "  smaller target — those are the three dials, and the spread")
        print(f"  takes {cost * 100:.0f}% of every trade's risk whatever the size.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
