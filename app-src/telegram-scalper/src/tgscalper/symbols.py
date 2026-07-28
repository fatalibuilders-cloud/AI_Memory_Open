"""Turn whatever the admin typed into a symbol your broker actually accepts.

Two separate problems live here:

1. Vocabulary — signal groups write "GOLD", "gold", "XAU/USD" and "XAUUSD"
   for the same instrument. `find_symbol` picks the instrument out of free text.
2. Broker naming — one broker calls it "XAUUSD", another "XAUUSD.m",
   "XAUUSDm" or "GOLD". `SymbolResolver` maps the canonical name onto the
   exact string your terminal exposes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

# Canonical name -> spellings that mean it. Keys must be the canonical form.
DEFAULT_ALIASES: dict[str, list[str]] = {
    "XAUUSD": ["GOLD", "XAU/USD", "XAU-USD", "XAU USD", "GOLDUSD", "XAUUSD"],
    "XAGUSD": ["SILVER", "XAG/USD", "XAGUSD"],
    "US30": ["DOW", "DJ30", "DOWJONES", "US 30", "US30USD", "WALLSTREET", "WS30"],
    "NAS100": ["NASDAQ", "NAS 100", "USTEC", "US100", "NDX", "NASUSD"],
    "SPX500": ["SP500", "S&P500", "S&P 500", "US500", "SPX"],
    "GER40": ["DAX", "DAX40", "GER30", "DE40"],
    "UK100": ["FTSE", "FTSE100"],
    "BTCUSD": ["BTC", "BITCOIN", "BTC/USD", "BTCUSDT"],
    "ETHUSD": ["ETH", "ETHEREUM", "ETH/USD", "ETHUSDT"],
    "USOIL": ["OIL", "WTI", "CRUDE", "CRUDEOIL", "USOUSD", "WTIUSD"],
    "UKOIL": ["BRENT", "BRENTOIL"],
}

# Deriv's synthetic indices. They trade 24/7 and are the whole point of most
# Deriv signal groups, but their broker names contain spaces ("Volatility 75
# Index") while the groups write "V75" or "vix75".
#
# Every alias here is deliberately specific. A bare "CRASH", "BOOM" or "STEP"
# is NOT an alias: "market crash incoming" and "step by step" are ordinary
# chat, and matching them would invent trades out of conversation.
DERIV_SYNTHETICS: dict[str, list[str]] = {
    **{
        f"V{n}": [
            f"VOLATILITY {n} INDEX",
            f"VOLATILITY {n}",
            f"VOL {n}",
            f"VIX {n}",
            f"VIX{n}",
            f"V-{n}",
            f"R_{n}",
        ]
        for n in (10, 25, 50, 75, 100)
    },
    **{
        f"BOOM{n}": [f"BOOM {n} INDEX", f"BOOM {n}", f"B{n}", f"BOOM-{n}"]
        for n in (300, 500, 1000)
    },
    **{
        f"CRASH{n}": [f"CRASH {n} INDEX", f"CRASH {n}", f"C{n}", f"CRASH-{n}"]
        for n in (300, 500, 1000)
    },
    **{
        f"JUMP{n}": [f"JUMP {n} INDEX", f"JUMP {n}", f"J{n}"]
        for n in (10, 25, 50, 75, 100)
    },
    "STEPINDEX": ["STEP INDEX", "STEPINDEX", "STEP-INDEX"],
    "RANGEBREAK100": ["RANGE BREAK 100 INDEX", "RANGE BREAK 100", "RB100"],
    "RANGEBREAK200": ["RANGE BREAK 200 INDEX", "RANGE BREAK 200", "RB200"],
}

DEFAULT_ALIASES.update(DERIV_SYNTHETICS)

# Straight six-letter FX pairs are matched structurally rather than listed.
_FX_MAJORS = {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "XAU", "XAG"}
_FX_MINORS = _FX_MAJORS | {"SEK", "NOK", "DKK", "SGD", "HKD", "ZAR", "TRY", "MXN", "PLN", "CZK", "HUF", "CNH"}

_SEPARATED_PAIR = re.compile(r"\b([A-Z]{3})\s?[/\-]\s?([A-Z]{3})\b")
_JOINED_PAIR = re.compile(r"\b([A-Z]{3})([A-Z]{3})\b")

# Words that look like tickers but never are. Prevents "SELL" or "TP1" being
# read as an instrument.
_STOPWORDS = {
    "BUY", "SELL", "NOW", "SL", "TP", "STOP", "LOSS", "LIMIT", "PROFIT", "TARGET",
    "ENTRY", "CLOSE", "OPEN", "PIPS", "PIP", "LOT", "LOTS", "RISK", "AND", "THE",
    "FOR", "ALL", "OUT", "RUN", "HIT", "BOOK", "MOVE", "BREAK", "EVEN", "SECURE",
    "LONG", "SHORT", "SIGNAL", "TRADE", "ZONE", "AREA", "GOOD", "LUCK", "TEAM",
    "VIP", "FREE", "NEW", "ORDER", "PENDING", "CANCEL", "USE", "SET", "GET",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.upper()).strip()


def find_symbol(text: str, aliases: Optional[dict[str, list[str]]] = None) -> Optional[str]:
    """Extract the canonical instrument from a signal message.

    Longest aliases are tried first so "XAU/USD" wins over a bare "XAU", and
    explicit vocabulary always beats the structural FX-pair fallback.
    """
    aliases = aliases or DEFAULT_ALIASES
    upper = _norm(text)

    # 1. Alias table, longest spelling first.
    table: list[tuple[str, str]] = []
    for canonical, spellings in aliases.items():
        table.append((canonical.upper(), canonical))
        for spelling in spellings:
            table.append((_norm(spelling), canonical))
    for spelling, canonical in sorted(table, key=lambda item: -len(item[0])):
        # \b does not fire next to "/" or "&", so guard with explicit lookarounds.
        pattern = r"(?<![A-Z0-9])" + re.escape(spelling) + r"(?![A-Z0-9])"
        if re.search(pattern, upper):
            return canonical

    # 2. Separated FX pair: EUR/USD, GBP-JPY.
    for base, quote in _SEPARATED_PAIR.findall(upper):
        if base in _FX_MINORS and quote in _FX_MINORS:
            return base + quote

    # 3. Joined six-letter pair: EURUSD. Both halves must be real currencies,
    #    which rules out words like "MARKET" or "TARGET".
    for base, quote in _JOINED_PAIR.findall(upper):
        pair = base + quote
        if pair in _STOPWORDS:
            continue
        if base in _FX_MINORS and quote in _FX_MINORS and base != quote:
            return pair

    return None


@dataclass
class SymbolResolver:
    """Maps canonical symbols to the exact strings a broker exposes."""

    suffix: str = ""
    overrides: dict[str, str] = field(default_factory=dict)
    aliases: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_ALIASES))
    # Populated from the broker at startup; when empty, resolution is best-effort.
    # Keeps the broker's own casing, keyed by upper-case for lookup.
    available: dict[str, str] = field(default_factory=dict)

    def load_available(self, symbols: Iterable[str]) -> None:
        self.available = {symbol.upper(): symbol for symbol in symbols}

    def canonical(self, raw: str) -> Optional[str]:
        return find_symbol(raw, self.aliases)

    def resolve(self, raw: str) -> Optional[str]:
        """Return the broker symbol for `raw`, or None if it cannot be traded.

        Candidates are tried in decreasing specificity: an explicit override,
        the canonical name plus the configured suffix, the bare canonical name,
        then each alias spelling (some brokers really do name the instrument
        "GOLD"). If the broker's symbol list is known, only a candidate present
        in that list is returned — guessing a symbol the terminal does not have
        would fail at order time anyway.
        """
        canonical = self.canonical(raw)
        if canonical is None:
            return None

        candidates: list[str] = []
        override = self.overrides.get(canonical) or self.overrides.get(canonical.upper())
        if override:
            candidates.append(override)
        if self.suffix:
            candidates.append(canonical + self.suffix)
        candidates.append(canonical)
        for spelling in self.aliases.get(canonical, []):
            spaced = _norm(spelling).replace("/", "").replace("-", " ").strip()
            if not spaced:
                continue
            # Deriv lists synthetics as "Volatility 75 Index" — spaces and all —
            # so both the spaced and the squashed form have to be candidates.
            for variant in (spaced, spaced.replace(" ", "")):
                if self.suffix:
                    candidates.append(variant + self.suffix)
                candidates.append(variant)

        if not self.available:
            return candidates[0]
        for candidate in candidates:
            broker_name = self.available.get(candidate.upper())
            if broker_name:
                return broker_name
        return None
