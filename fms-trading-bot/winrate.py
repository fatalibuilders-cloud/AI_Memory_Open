#!/usr/bin/env python3
r"""Engineer a target win rate — and show what it costs.

    .\.venv\Scripts\python.exe winrate.py 90
    .\.venv\Scripts\python.exe winrate.py 90 --tp 0.50 --apply

A win rate is not a measure of skill: it is chosen by where you put the
stop relative to the target. Price hitting a near target before a distant
stop is simply more likely, so

    win rate  =  stop distance / (target + stop)

Rearranged, a target win rate p needs

    stop  =  target * p / (1 - p)

That is a ratio, not an edge. The wins get more frequent and the losses
get proportionally bigger, so the average trade is unchanged — minus the
spread. What does change is the shape of the losses: at 97% wins, a single
loss is 32x a win, and a two-loss streak that arrives roughly every 1,100
trades wipes out about 65 wins.

This prints the honest arithmetic before writing anything.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


def _p_reach(p_up: float, steps_up: int, steps_down: int) -> float:
    """Gambler's ruin: chance of touching +steps_up before -steps_down."""
    from decimal import Decimal, getcontext
    getcontext().prec = 60
    if abs(p_up - 0.5) < 1e-12:
        return steps_down / (steps_up + steps_down)
    r = Decimal(1 - p_up) / Decimal(p_up)
    return float((1 - r**steps_down) / (1 - r**(steps_up + steps_down)))


def achievable(measured_pct: float, sl_mult: float, tp_mult: float,
               tp: float, sl: float, step: float = 0.05) -> float | None:
    """What a configured target really yields on a signal of measured quality.

    A configured win rate assumes a coin flip. Calibrating a biased walk to
    the win rate actually observed at the live stop/target multiples gives
    the drift of the real signal, which is then applied to the new levels.
    """
    if not 0 < measured_pct < 100 or sl_mult <= 0 or tp_mult <= 0:
        return None
    target = measured_pct / 100.0
    lo, hi = 0.30, 0.70
    for _ in range(60):
        mid = (lo + hi) / 2
        got = _p_reach(mid, round(tp_mult / 0.05), round(sl_mult / 0.05))
        if got < target:
            lo = mid
        else:
            hi = mid
    p_up = (lo + hi) / 2
    return _p_reach(p_up, max(round(tp / step), 1), max(round(sl / step), 1))


def stop_for(target: float, win_rate: float) -> float:
    """Stop distance that yields `win_rate` for a given target."""
    p = win_rate / 100.0
    return target * p / (1.0 - p)


def main() -> int:
    p = argparse.ArgumentParser(description="Engineer a target win rate")
    p.add_argument("win_rate", type=float, help="target win rate, e.g. 90")
    p.add_argument("--tp", type=float, default=0.50, help="cash target (default 0.50)")
    p.add_argument("--max-loss-pct", type=float,
                   help="cap each loss at this %% of the balance; the target is "
                        "then solved for instead of taken from --tp")
    p.add_argument("--spread-cost", type=float, default=0.12,
                   help="spread paid per trade (default 0.12, EURUSD at 0.01 lot)")
    p.add_argument("--balance", type=float, default=50.0,
                   help="account balance for the ruin check (default 50)")
    p.add_argument("--apply", action="store_true", help="write it into .env")
    p.add_argument("--measured-win-rate", type=float,
                   help="your real win rate %% from report.py, to show what the "
                        "target actually becomes on YOUR signal")
    p.add_argument("--measured-sl-mult", type=float, default=1.5)
    p.add_argument("--measured-tp-mult", type=float, default=2.0)
    args = p.parse_args()

    if not 1 <= args.win_rate <= 99:
        print("Win rate must be between 1 and 99.", file=sys.stderr)
        return 2

    p_win = args.win_rate / 100.0
    if args.max_loss_pct:
        # The loss cap fixes the stop, so the target is what has to give:
        # win rate = SL / (TP + SL)  =>  TP = SL * (1 - p) / p
        sl = args.balance * args.max_loss_pct / 100.0
        tp = sl * (1 - p_win) / p_win
        print("=" * 68)
        print(f"TARGET WIN RATE {args.win_rate:.0f}%, LOSS CAPPED AT "
              f"{args.max_loss_pct:.0f}% OF ${args.balance:,.0f}")
        print("=" * 68)
        print(f"  stop loss   : ${sl:.2f}   (the cap you set)")
        print(f"  take profit : ${tp:.4f}  (forced by the win rate)")
    else:
        tp = args.tp
        sl = stop_for(tp, args.win_rate)
        print("=" * 68)
        print(f"TARGET WIN RATE: {args.win_rate:.0f}%")
        print("=" * 68)
        print(f"  take profit : ${tp:.2f}")
        print(f"  stop loss   : ${sl:.2f}   (= {sl/tp:.1f}x the target)")

    # A target smaller than the spread cannot be reached profitably: the
    # position starts further behind than the target is away.
    if tp <= args.spread_cost:
        print(f"\n  ** THE TARGET (${tp:.4f}) IS SMALLER THAN THE SPREAD "
              f"(${args.spread_cost:.2f}). **")
        print(f"  Every 'win' still loses ${args.spread_cost - tp:.4f}. This "
              f"configuration")
        print(f"  cannot make money on any trade, won or lost.")

    gross = p_win * tp - (1 - p_win) * sl
    net = gross - args.spread_cost
    print(f"\n  per trade, before costs : ${gross:+.4f}")
    print(f"  spread                  : ${-args.spread_cost:.4f}")
    print(f"  per trade, net          : ${net:+.4f}")
    print(f"\n  over 1,000 trades       : ${net*1000:+,.2f}")

    print("\n  What the win rate hides:")
    print(f"    one loss cancels {sl/tp:.0f} wins")
    # probability of two consecutive losses, and how often that recurs
    p_lose = 1 - p_win
    if p_lose > 0:
        streak2 = p_lose ** 2
        every = 1 / streak2 if streak2 else float("inf")
        print(f"    two losses in a row happen every ~{every:,.0f} trades "
              f"and cost ${2*sl:.2f} (= {2*sl/tp:.0f} wins)")
    risk_pct = 100 * sl / args.balance if args.balance else 0
    print(f"    on a ${args.balance:,.0f} account, ONE loss is "
          f"{risk_pct:.1f}% of it")
    if risk_pct >= 50:
        print("    -> a single loss would take half the account or more")
    if 2 * sl >= args.balance:
        print("    -> TWO losses would end the account")

    if args.measured_win_rate:
        actual = achievable(args.measured_win_rate, args.measured_sl_mult,
                            args.measured_tp_mult, tp, sl)
        if actual is not None:
            ev = actual * tp - (1 - actual) * sl - args.spread_cost
            print("\n  ON YOUR OWN SIGNAL (calibrated from report.py):")
            print(f"    you configured        : {args.win_rate:.0f}% wins")
            print(f"    you would ACTUALLY get: {100*actual:.1f}%")
            print(f"    per trade             : ${ev:+.4f}")
            print(f"    per 1,000 trades      : ${1000*ev:+,.2f}")
            if actual < p_win - 0.02:
                print("    The configured rate assumes a coin flip. Your entries")
                print("    lean the wrong way, so you get fewer wins AND the same")
                print("    oversized losses.")

    print("\n" + "=" * 68)
    if net < 0:
        print("  This configuration LOSES money. The win rate is real; the")
        print("  profit is not. Wins get more frequent and losses get bigger")
        print("  by exactly the same factor, so only the spread remains.")
    else:
        print("  Positive only because the assumed spread is below the real one.")
    print("  A win rate is chosen. An edge has to be found — try optimize.py.")

    if not args.apply:
        print("\n  Re-run with --apply to write it into .env anyway.")
        return 0

    env_path = Path(".env")
    if not env_path.is_file():
        print(".env not found — run this from the fms-trading-bot folder.",
              file=sys.stderr)
        return 1
    values = {"TP_MONEY": f"{tp:.2f}", "SL_MONEY": f"{sl:.2f}",
              "TP_RUNNER_MONEY": "0"}
    lines = env_path.read_text(encoding="utf-8").splitlines()
    out, seen = [], set()
    for text in lines:
        key = text.split("=")[0].strip() if "=" in text else ""
        if key in values and not text.strip().startswith("#"):
            out.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            out.append(text)
    missing = [k for k in values if k not in seen]
    if missing:
        out.append("")
        out.append(f"# win-rate target {args.win_rate:.0f}% (winrate.py)")
        for k in missing:
            out.append(f"{k}={values[k]}")
    shutil.copyfile(env_path, Path(".env.bak"))
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\n  Wrote TP_MONEY={tp:.2f}, SL_MONEY={sl:.2f} to .env "
          f"(backup in .env.bak).")
    print("  Restart the bot to apply:  .\\update.ps1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
