"""Market universe selection and contract-shape resolution.

This module is where "crypto only" is enforced. Symbols are not hardcoded:
they are discovered from Deriv's `active_symbols` and filtered to those whose
`market` field is exactly `cryptocurrency`. A symbol the operator names in
DERIV_SYMBOLS still has to survive that filter, so a typo or a forex ticker in
the config drops the symbol rather than trading it.

Contract durations are resolved the same way — read from `contracts_for` and
clamped into the range Deriv actually advertises for that symbol, instead of
assuming a value that may be rejected at proposal time.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import CRYPTO_MARKET, Config

log = logging.getLogger(__name__)

# Deriv duration units, and how many seconds each represents. Ticks ("t") are
# a count of price updates, not a span of time, so they have no entry here.
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


@dataclass(frozen=True)
class SymbolInfo:
    symbol: str
    display_name: str
    market: str
    submarket: str
    is_open: bool

    @classmethod
    def from_api(cls, raw: dict) -> "SymbolInfo":
        return cls(
            symbol=str(raw.get("symbol", "")),
            display_name=str(raw.get("display_name", raw.get("symbol", ""))),
            market=str(raw.get("market", "")),
            submarket=str(raw.get("submarket", "")),
            is_open=bool(raw.get("exchange_is_open", 0))
            and not bool(raw.get("is_trading_suspended", 0)),
        )


def is_crypto(raw: dict) -> bool:
    """True only for cryptocurrency symbols. The bot's central invariant."""
    return str(raw.get("market", "")).strip().lower() == CRYPTO_MARKET


def select_symbols(active_symbols: list[dict], config: Config) -> list[SymbolInfo]:
    """Pick the tradable crypto universe for this cycle.

    Applies, in order: the crypto-market filter, the operator's allowlist (if
    any), the open/not-suspended filter, and finally the MAX_SYMBOLS cap.
    """
    crypto = [SymbolInfo.from_api(raw) for raw in active_symbols if is_crypto(raw)]

    rejected = {
        str(raw.get("symbol")) for raw in active_symbols if not is_crypto(raw)
    }
    if config.symbols:
        allowed = set(config.symbols)
        wrong_market = allowed & rejected
        if wrong_market:
            log.error(
                "ignoring configured symbols that are not cryptocurrency: %s",
                ", ".join(sorted(wrong_market)),
            )
        known = {info.symbol for info in crypto}
        unknown = allowed - known - wrong_market
        if unknown:
            log.error("ignoring unknown configured symbols: %s", ", ".join(sorted(unknown)))
        crypto = [info for info in crypto if info.symbol in allowed]

    open_symbols = [info for info in crypto if info.is_open]
    closed = [info.symbol for info in crypto if not info.is_open]
    if closed:
        log.info("skipping crypto symbols not currently open: %s", ", ".join(sorted(closed)))

    open_symbols.sort(key=lambda info: info.symbol)
    if config.max_symbols > 0:
        open_symbols = open_symbols[: config.max_symbols]
    return open_symbols


def parse_duration(value: str) -> tuple[int, str] | None:
    """Parse a Deriv duration string such as "5m" or "365d" into (amount, unit)."""
    text = str(value).strip().lower()
    if len(text) < 2:
        return None
    unit = text[-1]
    if unit not in _UNIT_SECONDS and unit != "t":
        return None
    try:
        amount = int(text[:-1])
    except ValueError:
        return None
    if amount <= 0:
        return None
    return amount, unit


def duration_seconds(amount: int, unit: str) -> int | None:
    """Convert a duration to seconds. Returns None for tick durations."""
    factor = _UNIT_SECONDS.get(unit)
    return None if factor is None else amount * factor


def find_contract(contracts_for: dict, direction: str) -> dict | None:
    """Find a plain spot Rise/Fall contract for `direction` (CALL or PUT).

    Restricted to the `callput` category with an at-the-money barrier, which is
    the simplest contract shape Deriv offers: no barrier to choose and a payout
    that depends only on the direction of the move.
    """
    for entry in contracts_for.get("available", []):
        if str(entry.get("contract_type", "")).upper() != direction.upper():
            continue
        if str(entry.get("contract_category", "")).lower() != "callput":
            continue
        if str(entry.get("start_type", "spot")).lower() != "spot":
            continue
        barrier = str(entry.get("barrier_category", "")).lower()
        if barrier and barrier != "euro_atm":
            continue
        return entry
    return None


def resolve_duration(entry: dict, config: Config) -> tuple[int, str]:
    """Clamp the configured duration into the range Deriv allows for a contract.

    Falls back to the contract's own minimum when the configured unit is not
    comparable with the advertised range — for example a 5-minute preference
    against a contract quoted only in ticks.
    """
    wanted = (config.trade_duration, config.trade_duration_unit)
    minimum = parse_duration(entry.get("min_contract_duration", ""))
    maximum = parse_duration(entry.get("max_contract_duration", ""))

    if minimum is None and maximum is None:
        return wanted

    fallback = minimum or wanted
    wanted_seconds = duration_seconds(*wanted)

    # Tick-quoted contracts: only a tick preference can be compared directly.
    if (minimum and minimum[1] == "t") or (maximum and maximum[1] == "t"):
        if wanted[1] != "t":
            log.info(
                "duration %s%s not comparable with tick-quoted contract — using %s%s",
                *wanted,
                *fallback,
            )
            return fallback
        amount = wanted[0]
        if minimum:
            amount = max(amount, minimum[0])
        if maximum:
            amount = min(amount, maximum[0])
        return amount, "t"

    if wanted_seconds is None:
        return fallback

    low = duration_seconds(*minimum) if minimum else None
    high = duration_seconds(*maximum) if maximum else None

    if low is not None and wanted_seconds < low:
        log.info("duration %s%s below contract minimum — using %s%s", *wanted, *minimum)
        return minimum  # type: ignore[return-value]
    if high is not None and wanted_seconds > high:
        log.info("duration %s%s above contract maximum — using %s%s", *wanted, *maximum)
        return maximum  # type: ignore[return-value]
    return wanted
