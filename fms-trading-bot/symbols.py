#!/usr/bin/env python3
r"""List the symbols your broker account actually offers.

    .\.venv\Scripts\python.exe symbols.py              # everything, grouped
    .\.venv\Scripts\python.exe symbols.py BTC          # only names containing BTC
    .\.venv\Scripts\python.exe symbols.py --tradeable  # skip disabled symbols
    .\.venv\Scripts\python.exe symbols.py BTC --account deriv   # a specific account

With several accounts active (ACTIVE_BROKERS), the first one is checked
unless --account names another.

Use the exact names it prints in SYMBOLS in your .env — they are
case-sensitive and broker-specific (Exness adds an 'm' suffix on some
account types, other brokers use 'z', '.a', or no suffix at all).
"""

from __future__ import annotations

import sys

from fmsbot.config import Settings

GROUPS = (
    ("Synthetics (24/7, simulated)",
     ("VOLATILITY", "BOOM", "CRASH", "STEP INDEX", "JUMP", "RANGE BREAK", "DRIFT SWITCH")),
    ("Crypto", ("BTC", "ETH", "XRP", "LTC", "SOL", "DOGE", "ADA", "BNB", "CRYPTO")),
    ("Metals", ("XAU", "XAG", "XPT", "XPD", "GOLD", "SILVER")),
    ("Energy", ("OIL", "BRENT", "WTI", "USOIL", "UKOIL", "NGAS")),
    ("Indices", ("US30", "US500", "NAS", "SPX", "GER", "UK100", "JP225", "DE30", "HK50")),
)
FX_MAJORS = ("EUR", "GBP", "USD", "JPY", "CHF", "AUD", "NZD", "CAD")


def classify(name: str) -> str:
    upper = name.upper()
    for label, keys in GROUPS:
        if any(k in upper for k in keys):
            return label
    if sum(c in upper for c in ("EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "USD")) >= 2:
        return "Forex"
    if any(upper.startswith(c) for c in FX_MAJORS):
        return "Forex"
    return "Other (stocks/CFDs)"


def list_symbols(backend: str, broker) -> list[tuple[str, bool]]:
    """(name, tradeable) for every instrument the account offers."""
    if backend in ("mt5", "exness", "deriv", "vantage"):
        # trade_mode 0 = disabled, 4 = full access
        return [(s.name, getattr(s, "trade_mode", 4) != 0)
                for s in (broker.mt5.symbols_get() or [])]
    if backend == "oanda":
        return [(name, True) for name in broker._instruments]
    if backend == "binance":
        return [(name, True) for name in broker._filters]
    raise SystemExit(f"Unknown broker backend '{backend}'.")


def main() -> int:
    argv = sys.argv[1:]
    tradeable_only = "--tradeable" in argv
    account = None
    if "--account" in argv:
        i = argv.index("--account")
        if i + 1 < len(argv):
            account = argv[i + 1].lower()
            del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    needle = args[0].upper() if args else None

    settings = Settings.load()
    configs = settings.broker_configs()
    if account:
        matches = [c for c in configs if c.name.lower() == account]
        if not matches:
            print(f"No account '{account}'. Active: "
                  f"{', '.join(c.name for c in configs)}", file=sys.stderr)
            return 1
        cfg = matches[0]
    else:
        cfg = configs[0]
        if len(configs) > 1:
            print(f"Checking account '{cfg.name}' "
                  f"(others: {', '.join(c.name for c in configs[1:])} "
                  f"— use --account <name>)\n")

    from fmsbot.broker import build_broker_from_config
    broker = build_broker_from_config(cfg)
    broker.connect()
    try:
        rows = []
        for name, enabled in list_symbols(settings.broker, broker):
            if needle and needle not in name.upper():
                continue
            if tradeable_only and not enabled:
                continue
            rows.append((classify(name), name, enabled))

        if not rows:
            print(f"No symbols matching '{needle}'." if needle else "No symbols found.")
            if needle:
                print("Your account type may not offer this instrument. Ask the "
                      "broker's support, or open an account type that includes it.")
            return 0

        account = (f"{settings.mt5_login} ({settings.mt5_server})"
                   if settings.broker in ("mt5", "exness", "deriv", "vantage")
                   else settings.broker)
        print(f"{len(rows)} symbol(s)"
              + (f" matching '{needle}'" if needle else "")
              + f" on {account}:\n")
        current = None
        for group, name, enabled in sorted(rows):
            if group != current:
                current = group
                print(f"  --- {group} ---")
            flag = "" if enabled else "   [trading disabled]"
            print(f"    {name}{flag}")
        print("\nCopy the exact names into SYMBOLS in .env, comma-separated.")
        return 0
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
