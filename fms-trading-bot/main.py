#!/usr/bin/env python3
"""FMS trading bot — Forex / Metals / Stocks with a Telegram phone remote.

    cp .env.example .env    # fill in Telegram + MT5 credentials
    pip install -r requirements.txt
    python main.py

Then on your phone, open your bot in Telegram and send:
    /login <your TG_PASSWORD>
    /resume
"""

from __future__ import annotations

import logging
import signal
import sys

from fmsbot.bot import TradingBot
from fmsbot.broker.mt5 import MT5Broker
from fmsbot.config import Settings


def main() -> int:
    settings = Settings.load()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    problems = settings.validate()
    if problems:
        for p in problems:
            print(f"CONFIG ERROR: {p}", file=sys.stderr)
        return 2

    broker = MT5Broker(settings.mt5_login, settings.mt5_password,
                       settings.mt5_server, settings.mt5_path)
    bot = TradingBot(settings, broker)

    def _shutdown(signum, frame):  # noqa: ARG001
        bot.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    bot.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
