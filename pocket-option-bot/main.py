#!/usr/bin/env python3
"""Pocket Option auto-trading bot — entry point.

Usage:
    cp .env.example .env       # then fill in PO_SSID
    pip install -r requirements.txt
    python main.py             # demo mode by default
    python main.py --live      # real account (be careful!)
    python main.py --dry-run   # connect + signal, but never place orders
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys

from pocket_bot.bot import TradingBot
from pocket_bot.config import Settings


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pocket Option trading bot")
    p.add_argument("--live", action="store_true", help="trade the LIVE account (default: demo)")
    p.add_argument("--dry-run", action="store_true", help="log signals but never send orders")
    p.add_argument("--asset", help="override asset, e.g. EURUSD_otc")
    p.add_argument("--stake", type=float, help="override stake per trade")
    p.add_argument("--expiry", type=int, help="override option expiry in seconds")
    p.add_argument("--strategy", help="rsi_ema | bollinger")
    p.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    settings = Settings.load()

    if args.live:
        settings.demo = False
    if args.dry_run:
        settings.dry_run = True
    if args.asset:
        settings.asset = args.asset
    if args.stake:
        settings.stake = args.stake
    if args.expiry:
        settings.expiry_seconds = args.expiry
    if args.strategy:
        settings.strategy = args.strategy

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    problems = settings.validate()
    if problems:
        for msg in problems:
            print(f"CONFIG ERROR: {msg}", file=sys.stderr)
        return 2

    if not settings.demo and not settings.dry_run:
        print()
        print("*** LIVE TRADING MODE — this bot will place REAL-MONEY trades. ***")
        print(f"    Asset: {settings.asset} | Stake: {settings.stake} | "
              f"Daily loss limit: {settings.daily_loss_limit}")
        answer = input("    Type 'yes' to continue: ").strip().lower()
        if answer != "yes":
            print("Aborted.")
            return 1

    bot = TradingBot(settings)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, bot.stop)
        except NotImplementedError:
            pass  # windows
    try:
        loop.run_until_complete(bot.run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
