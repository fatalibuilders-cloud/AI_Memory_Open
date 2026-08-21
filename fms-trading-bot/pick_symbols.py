#!/usr/bin/env python3
r"""Find which instruments your account can actually TRADE, and set them up.

    .\.venv\Scripts\python.exe pick_symbols.py                 # show what is available
    .\.venv\Scripts\python.exe pick_symbols.py --apply         # write them into .env
    .\.venv\Scripts\python.exe pick_symbols.py --baskets majors,metals --apply
    .\.venv\Scripts\python.exe pick_symbols.py --account deriv --apply

Symbol naming is broker- and account-specific (Exness EURUSDm, others
EURUSD, some XAUUSD247m), and a symbol can stream prices while the broker
still refuses orders on it — which is exactly what produced repeated
"Trade disabled (10017)" and "does not exist" failures. This resolves each
instrument against the account's real symbol list AND checks that trading
is permitted, so only names that will actually work get written.

Stop the bot before running this: two processes sharing one MT5 terminal
interfere.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from fmsbot.config import Settings

BASKETS = {
    "majors": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF",
               "AUDUSD", "USDCAD", "NZDUSD"],
    "minors": ["EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURAUD", "CADJPY"],
    "metals": ["XAUUSD", "XAGUSD"],
    "crypto": ["BTCUSD", "ETHUSD"],
}

# MT5 trade_mode: 0 disabled, 1 long only, 2 short only, 3 close only, 4 full
TRADE_MODE_LABEL = {
    0: "trading disabled",
    1: "long only",
    2: "short only",
    3: "close only",
    4: "tradeable",
}


def candidates(available: list[str], canonical: str) -> list[str]:
    """Account symbols that plausibly represent `canonical`, best first.

    Prefers an exact match, then the shortest name starting with it — so
    EURUSDm beats EURUSDm.raw, and XAUUSDm beats XAUUSD247m.
    """
    lower = canonical.lower()
    exact = [s for s in available if s.lower() == lower]
    prefixed = sorted((s for s in available if s.lower().startswith(lower)
                       and s.lower() != lower), key=len)
    return exact + prefixed


def main() -> int:
    p = argparse.ArgumentParser(
        description="Discover tradeable instruments and write them to .env")
    p.add_argument("--baskets", default="majors,metals,crypto",
                   help="comma-separated: " + ", ".join(BASKETS))
    p.add_argument("--account", help="which account, when several are configured")
    p.add_argument("--apply", action="store_true", help="write the result into .env")
    args = p.parse_args()

    wanted_baskets = [b.strip().lower() for b in args.baskets.split(",") if b.strip()]
    unknown = [b for b in wanted_baskets if b not in BASKETS]
    if unknown:
        print(f"Unknown basket(s): {', '.join(unknown)}. "
              f"Available: {', '.join(BASKETS)}", file=sys.stderr)
        return 2

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
        if len(configs) > 1:
            print(f"Using account '{cfg.name}' "
                  f"(others: {', '.join(c.name for c in configs[1:])})\n")

    from fmsbot.broker import build_broker_from_config
    broker = build_broker_from_config(cfg)
    broker.connect()
    try:
        is_mt5 = cfg.kind in ("mt5", "exness", "deriv", "vantage")
        if is_mt5:
            raw = broker.mt5.symbols_get() or []
            available = [s.name for s in raw]
            trade_mode = {s.name: getattr(s, "trade_mode", 4) for s in raw}
        else:
            from symbols import list_symbols
            available = [name for name, _ in list_symbols(cfg.kind, broker)]
            trade_mode = {name: 4 for name in available}

        print("=" * 68)
        print(f"TRADEABLE INSTRUMENTS — {cfg.name} ({cfg.kind})")
        print("=" * 68)

        chosen: list[str] = []
        for basket in wanted_baskets:
            print(f"\n-- {basket} --")
            for canonical in BASKETS[basket]:
                options = candidates(available, canonical)
                if not options:
                    print(f"  {canonical:8} not offered on this account")
                    continue
                picked = None
                for option in options:
                    if trade_mode.get(option, 4) == 4:
                        picked = option
                        break
                if picked:
                    extra = ""
                    rejected = [o for o in options if o != picked
                                and trade_mode.get(o, 4) != 4]
                    if rejected:
                        label = TRADE_MODE_LABEL.get(trade_mode.get(rejected[0]), "?")
                        extra = f"   (skipped {rejected[0]}: {label})"
                    print(f"  {canonical:8} -> {picked}{extra}")
                    chosen.append(picked)
                else:
                    state = TRADE_MODE_LABEL.get(trade_mode.get(options[0]), "?")
                    print(f"  {canonical:8} -> {options[0]} but {state.upper()} "
                          f"— cannot be traded")

        print("\n" + "=" * 68)
        if not chosen:
            print("Nothing tradeable found. Check the account type with your broker.")
            return 1
        line = ",".join(chosen)
        print(f"{len(chosen)} tradeable instrument(s):\n  {line}")

        # More symbols means more concurrent exposure, which is easy to miss.
        size = f"{settings.fixed_lot} lot" if settings.fixed_lot else \
               f"{settings.risk_pct}% risk"
        print(f"\n  Exposure note: {len(chosen)} symbols at {size} each, up to "
              f"{settings.max_open_positions} positions open at once.")
        print(f"  The daily cap of {settings.max_trades_per_day} trades is now "
              f"shared across all of them.")

        if not args.apply:
            print("\nRe-run with --apply to write this into .env.")
            return 0

        env_path = Path(".env")
        if not env_path.is_file():
            print(".env not found — run this from the fms-trading-bot folder.",
                  file=sys.stderr)
            return 1
        key = (f"BROKER_{cfg.name.upper()}_SYMBOLS"
               if settings.active_broker or len(configs) > 1 else "SYMBOLS")
        lines = env_path.read_text(encoding="utf-8").splitlines()
        out, seen = [], False
        for text in lines:
            if re.match(rf"^\s*{key}\s*=", text):
                out.append(f"{key}={line}")
                seen = True
            else:
                out.append(text)
        if not seen:
            out += ["", f"{key}={line}"]
        shutil.copyfile(env_path, Path(".env.bak"))
        env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"\nWrote {key} to .env (backup in .env.bak).")
        print("Restart the bot to apply:  .\\update.ps1")
        return 0
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
