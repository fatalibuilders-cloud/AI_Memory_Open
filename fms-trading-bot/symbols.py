#!/usr/bin/env python3
r"""List the symbols your broker account actually offers.

    .\.venv\Scripts\python.exe symbols.py              # everything, grouped
    .\.venv\Scripts\python.exe symbols.py BTC          # only names containing BTC
    .\.venv\Scripts\python.exe symbols.py --tradeable  # skip disabled symbols

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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tradeable_only = "--tradeable" in sys.argv
    needle = args[0].upper() if args else None

    settings = Settings.load()
    from fmsbot.broker import build_broker
    broker = build_broker(settings)
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
