#!/usr/bin/env python3
"""Validate .env and print a one-line summary. Exits 1 if unusable.

Used by update.ps1 before restarting the bot, and handy on its own:

    .\.venv\\Scripts\\python.exe check_config.py
"""

from __future__ import annotations

import sys

from fmsbot.config import Settings


def main() -> int:
    settings = Settings.load()
    problems = settings.validate()
    if problems:
        print("      CONFIG ERRORS:")
        for p in problems:
            print(f"        - {p}")
        return 1

    accounts = settings.broker_configs()
    names = ", ".join(f"{c.name}({c.kind})" for c in accounts)
    print(f"      OK: {len(accounts)} account(s) - {names}")
    sizing = (f"{settings.fixed_lot} lot" if settings.fixed_lot > 0
              else f"{settings.risk_pct}% risk")
    print(f"      {settings.timeframe} | EMA{settings.ema_fast}/{settings.ema_slow} "
          f"| {sizing} | entry: {settings.entry_mode}")
    for cfg in accounts:
        print(f"      {cfg.name}: {', '.join(cfg.symbols)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
