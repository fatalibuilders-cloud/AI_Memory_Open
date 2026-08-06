#!/usr/bin/env python3
r"""What did the bot ACTUALLY do? Reads real closed trades from the account.

    .\.venv\Scripts\python.exe report.py              # last 7 days
    .\.venv\Scripts\python.exe report.py --days 30
    .\.venv\Scripts\python.exe report.py --all        # include manual trades

Backtests are estimates. This reads the broker's own deal history, so it
is the record of what happened: win rate, profit factor, average win and
loss, best and worst trade, per-symbol and per-day breakdown.

By default it counts only trades this bot placed (magic number 984512),
so your manual trades do not flatter or spoil the numbers.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from fmsbot.config import Settings

MAGIC = 984512


def main() -> int:
    p = argparse.ArgumentParser(description="Report the bot's real trading results")
    p.add_argument("--days", type=int, default=7, help="how far back (default 7)")
    p.add_argument("--all", action="store_true",
                   help="include trades not placed by this bot")
    p.add_argument("--account", help="which account, when several are configured")
    args = p.parse_args()

    settings = Settings.load()
    configs = settings.broker_configs()
    if args.account:
        matches = [c for c in configs if c.name.lower() == args.account.lower()]
        if not matches:
            print(f"No account '{args.account}'. Configured: "
                  f"{', '.join(c.name for c in configs)}", file=sys.stderr)
            return 1
        cfg = matches[0]
    else:
        cfg = configs[0]

    if cfg.kind not in ("mt5", "exness", "deriv", "vantage"):
        print(f"report.py currently reads MetaTrader 5 history; "
              f"'{cfg.name}' is a {cfg.kind} account.", file=sys.stderr)
        return 1

    from fmsbot.broker import build_broker_from_config
    broker = build_broker_from_config(cfg)
    broker.connect()
    try:
        mt5 = broker.mt5
        end = datetime.now()
        start = end - timedelta(days=args.days)
        deals = mt5.history_deals_get(start, end)
        if deals is None:
            print(f"Could not read history: {mt5.last_error()}", file=sys.stderr)
            return 1

        # Only closing deals carry the realised profit of a position.
        closed = [d for d in deals if d.entry == 1]
        if not args.all:
            closed = [d for d in closed if d.magic == MAGIC]

        print("=" * 70)
        print(f"REAL TRADING RESULTS — {cfg.name} ({cfg.kind}), last {args.days} days")
        print("=" * 70)
        if not closed:
            print("\nNo closed trades in this period.")
            if not args.all:
                print("(Only counting this bot's trades — add --all to include "
                      "manual ones.)")
            print("\nIf you expected trades, check /why on your phone.")
            return 0

        results = []
        for d in closed:
            net = float(d.profit) + float(d.commission) + float(d.swap)
            results.append((d.time, d.symbol, net, float(d.volume)))
        results.sort()

        wins = [r for r in results if r[2] > 0]
        losses = [r for r in results if r[2] <= 0]
        gross_win = sum(r[2] for r in wins)
        gross_loss = -sum(r[2] for r in losses)
        net = gross_win - gross_loss
        pf = gross_win / gross_loss if gross_loss > 0 else float("inf")

        print(f"\n  trades          : {len(results)}")
        print(f"  wins / losses   : {len(wins)} / {len(losses)}")
        print(f"  win rate        : {100*len(wins)/len(results):.1f}%")
        print(f"  gross profit    : {gross_win:+,.2f}")
        print(f"  gross loss      : {-gross_loss:+,.2f}")
        print(f"  NET             : {net:+,.2f}")
        print(f"  profit factor   : {'inf' if pf == float('inf') else f'{pf:.2f}'}"
              f"    (>1 profitable, >1.5 good)")
        if wins:
            print(f"  average win     : {gross_win/len(wins):+,.2f}")
        if losses:
            print(f"  average loss    : {-gross_loss/len(losses):+,.2f}")
        print(f"  best / worst    : {max(r[2] for r in results):+,.2f} / "
              f"{min(r[2] for r in results):+,.2f}")

        by_symbol = defaultdict(list)
        for _, symbol, pnl, _ in results:
            by_symbol[symbol].append(pnl)
        print("\n  by symbol:")
        for symbol, pnls in sorted(by_symbol.items(), key=lambda x: -sum(x[1])):
            w = len([p for p in pnls if p > 0])
            print(f"     {symbol:16} {len(pnls):4} trades  "
                  f"{100*w/len(pnls):5.1f}% win  net {sum(pnls):+10,.2f}")

        by_day = defaultdict(list)
        for ts, _, pnl, _ in results:
            by_day[datetime.fromtimestamp(ts).date()].append(pnl)
        print("\n  by day:")
        for day in sorted(by_day):
            pnls = by_day[day]
            w = len([p for p in pnls if p > 0])
            print(f"     {day}  {len(pnls):4} trades  {100*w/len(pnls):5.1f}% win  "
                  f"net {sum(pnls):+10,.2f}")

        balance = broker.balance()
        print("\n" + "=" * 70)
        print("VERDICT")
        print("=" * 70)
        days_traded = len(by_day)
        print(f"  {len(results)} trades over {days_traded} trading day(s) "
              f"= {len(results)/max(days_traded,1):.0f}/day")
        print(f"  net {net:+,.2f} on a {balance:,.2f} balance "
              f"= {100*net/balance if balance else 0:+.3f}%")

        # Sample size decides whether the profit factor means anything at all,
        # so it is stated FIRST — a 100% win rate over one trade is not a
        # promising strategy, it is one trade.
        if len(results) < 30:
            print(f"\n  NOT ENOUGH DATA — {len(results)} trade(s).")
            print("  No conclusion can be drawn, good or bad. A 100% win rate over")
            print("  a handful of trades is luck, not edge.")
            print("  Come back at 100+ trades before reading anything into it.")
        elif len(results) < 100:
            print(f"\n  THIN DATA — {len(results)} trades. Indicative at best;")
            print("  wait for 100+ before acting on it.")
        elif pf >= 1.5:
            print("  Profit factor above 1.5 over a real sample — genuinely")
            print("  promising. Keep running it and re-check monthly.")
        elif pf > 1.0:
            print("  Marginally profitable over a real sample. Too close to call —")
            print("  keep collecting before drawing conclusions.")
        else:
            print("  LOSING configuration: it pays out less than it loses.")
            print("  More trades will lose more money, not less. Change the strategy")
            print("  (preset.py balanced, or optimize.py to search) rather than")
            print("  raising frequency or size.")
        return 0
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
