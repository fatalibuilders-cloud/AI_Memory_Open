#!/usr/bin/env python3
r"""Can this account trade these symbols at this risk cap? Per symbol.

    .\.venv\Scripts\python.exe feasible.py
    .\.venv\Scripts\python.exe feasible.py --risk 0.01

A live account spent a day refusing almost every signal:

    XAUUSDm order refused — it would risk 29.12, over the 1.02 that
    0.0011% allows, and 0.01 is the smallest size the broker takes

Nothing was broken. RISK_PCT was set so that one trade could lose about a
dollar, and the smallest position the broker accepts, with the stop the
strategy asks for, risks far more than that. Those two numbers cannot
both hold, and the bot correctly chose the risk limit over the trade.

This prints the arithmetic per symbol: what the smallest lot is worth,
the largest stop the cap can pay for, the stop the strategy actually
wants, and which of the two has to move. It is the difference between
"the bot is broken" and "these settings forbid this trade".
"""

from __future__ import annotations

import argparse
import sys

from fmsbot.config import Settings
from fmsbot.series import atr_full


def stop_wanted(bars, settings) -> float:
    """The stop distance this configuration would ask for, in price."""
    if settings.sl_money > 0:
        return 0.0                 # fixed cash stop: distance is derived
    atr = atr_full([b.high for b in bars], [b.low for b in bars],
                   [b.close for b in bars], settings.atr_period)
    recent = [v for v in atr[-200:] if v]
    if not recent:
        return 0.0
    typical = sorted(recent)[len(recent) // 2]
    # The sweep strategy's stop is structural, not an ATR multiple, and
    # runs wider than one ATR -- measured at about three on this account.
    mult = (3.0 if "sweep" in (settings.strategy or "")
            else settings.atr_sl_mult)
    return typical * mult


def assess(allowed: float, value_per_price: float, wants: float) -> dict:
    """The arithmetic behind one symbol's verdict.

    `allowed` is the money one trade may lose, `value_per_price` what a
    price unit is worth at the broker's smallest lot, `wants` the stop
    distance the strategy asks for. Everything follows from those three,
    and none of it is a judgement call.
    """
    afford = allowed / value_per_price if value_per_price > 0 else 0.0
    cost = wants * value_per_price
    return {
        "afford": afford,            # widest stop the cap can pay for
        "cost": cost,                # what the wanted stop actually risks
        "fits": wants > 0 and wants <= afford,
        "over": (cost / allowed) if allowed > 0 and wants > 0 else 0.0,
        "needed": cost,              # the cap this stop would require
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description="What each symbol can afford at the configured risk")
    p.add_argument("--account", help="which account, when several")
    p.add_argument("--risk", type=float,
                   help="test a different RISK_PCT than the configured one")
    p.add_argument("--bars", type=int, default=500)
    args = p.parse_args()

    s = Settings.load()
    if args.risk is not None:
        s.risk_pct = args.risk

    from fmsbot.broker import build_broker_from_config
    configs = s.broker_configs()
    cfg = configs[0]
    if args.account:
        match = [c for c in configs if c.name.lower() == args.account.lower()]
        if not match:
            print(f"No account '{args.account}'.", file=sys.stderr)
            return 1
        cfg = match[0]

    broker = build_broker_from_config(cfg)
    broker.connect()
    try:
        balance = broker.balance()
        print("=" * 78)
        print(f"FEASIBILITY — {cfg.name}, balance {balance:.2f}, "
              f"RISK_PCT {s.risk_pct:g}%")
        budget = balance * s.risk_pct / 100.0
        cap = s.max_loss_per_trade
        print(f"  one trade may lose {budget:.2f}"
              + (f", and MAX_LOSS_PER_TRADE caps it at {cap:.2f}" if cap else ""))
        allowed = min([v for v in (budget, cap or budget) if v > 0])
        print(f"  so the binding limit is {allowed:.2f} per trade")
        print("=" * 78)

        tradable, blocked = [], []
        for symbol in cfg.symbols:
            per = s.for_symbol(symbol)
            try:
                bars = broker.bars(symbol, s.timeframe, args.bars)
                lot = broker.volume_from_lots(symbol, 0.01)
                value = broker.value_per_price(symbol, lot)
            except Exception as exc:
                print(f"\n{symbol}: cannot price ({str(exc)[:60]})")
                continue
            if value <= 0:
                print(f"\n{symbol}: broker reports no value per price unit")
                continue

            afford = allowed / value            # widest stop the cap allows
            wants = stop_wanted(bars, per)
            print(f"\n{symbol}")
            print(f"  smallest lot {lot:g} is worth {value:.2f} per price unit")
            print(f"  the {allowed:.2f} cap therefore pays for a stop of "
                  f"{afford:.5f}")
            if wants <= 0:
                print( "  stop is a fixed cash amount (SL_MONEY), so it fits "
                       "by construction")
                tradable.append(symbol)
                continue
            print(f"  this strategy wants about {wants:.5f}")
            if wants <= afford:
                print(f"  OK — it fits, with room to spare "
                      f"({afford / wants:.1f}x)")
                tradable.append(symbol)
            else:
                short = wants * value
                print(f"  REFUSED — that stop costs {short:.2f}, which is "
                      f"{short / allowed:.1f}x the cap")
                print(f"    raise the cap to {short:.2f} (RISK_PCT "
                      f"{100 * short / balance:.4f}), or")
                print(f"    set SL_MONEY={allowed:.2f} to size the stop to "
                      f"the cap instead of to structure")
                blocked.append((symbol, short))

        print("\n" + "=" * 78)
        print("VERDICT")
        print("=" * 78)
        if not blocked:
            print(f"\n  All {len(tradable)} symbol(s) can be traded at "
                  f"{allowed:.2f} per trade.")
        else:
            print(f"\n  {len(blocked)} of {len(blocked) + len(tradable)} "
                  f"symbols cannot trade at {allowed:.2f} per trade:")
            for symbol, need in sorted(blocked, key=lambda r: -r[1]):
                print(f"    {symbol:12} needs {need:.2f}")
            worst = max(need for _, need in blocked)
            print(f"\n  To trade all of them on structural stops, one trade "
                  f"must be allowed\n  to lose {worst:.2f} — that is "
                  f"RISK_PCT={100 * worst / balance:.4f} on this balance.")
            print(f"\n  To keep the {allowed:.2f} cap instead, either drop the "
                  f"symbols above or\n  set SL_MONEY={allowed:.2f}, which "
                  f"replaces the structural stop with a\n  cash one. That is "
                  f"a different strategy, not a smaller version of\n  this "
                  f"one: the stop stops being where the idea is wrong and "
                  f"starts\n  being where the money runs out, so re-measure "
                  f"it with find_edge.py\n  before trusting it.")
        risky = max((need for _, need in blocked), default=allowed)
        print(f"\n  A cap is not a loss. Refusing a trade costs nothing; "
              f"taking one that\n  risks {risky:.2f} against a "
              f"{allowed:.2f} limit is how a 0.5% setting loses\n  3% in an "
              f"afternoon.")
        return 0
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
