"""Parse trading signals out of free-text Telegram messages.

Signal groups have no standard format, so this recognises the common
shapes and refuses anything ambiguous. Refusing is the correct behaviour:
a misparsed signal trades the wrong direction or the wrong size, which is
far worse than a missed signal.

Handled shapes include:

    BUY EURUSD @ 1.0850 SL 1.0820 TP 1.0900
    🔴 SELL GOLD 2350
    SL: 2360  TP1: 2340  TP2: 2330
    XAUUSD BUY NOW
    Stop loss 2340 / Take profit 2370
    LONG BTCUSD entry 61000 stop 60000 target 63000
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Common aliases used in signal groups -> canonical base symbol
SYMBOL_ALIASES = {
    "GOLD": "XAUUSD", "XAU": "XAUUSD", "XAUUSD": "XAUUSD",
    "SILVER": "XAGUSD", "XAG": "XAGUSD",
    "BITCOIN": "BTCUSD", "BTC": "BTCUSD",
    "ETHEREUM": "ETHUSD", "ETH": "ETHUSD",
    "US30": "US30", "NAS100": "NAS100", "NASDAQ": "NAS100",
    "SPX500": "US500", "SP500": "US500", "US500": "US500",
    "OIL": "USOIL", "WTI": "USOIL", "CRUDE": "USOIL",
}

FX_CURRENCIES = ("USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD",
                 "XAU", "XAG", "BTC", "ETH")

BUY_WORDS = ("buy", "long", "bullish")
SELL_WORDS = ("sell", "short", "bearish")

# Words that mean "this is not a tradeable signal"
SKIP_WORDS = ("closed", "close now", "tp hit", "sl hit", "breakeven", "break even",
              "cancel", "cancelled", "result", "pips profit", "running",
              "move sl", "modify", "update", "in profit", "book profit")


@dataclass
class ParsedSignal:
    side: str                       # "buy" | "sell"
    symbol: str                     # canonical, e.g. XAUUSD (no broker suffix)
    entry: Optional[float] = None   # None = market order
    sl: Optional[float] = None
    tps: list[float] = field(default_factory=list)
    raw: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def tp(self) -> Optional[float]:
        return self.tps[0] if self.tps else None

    @property
    def tradeable(self) -> bool:
        """Only trade signals with an explicit stop and target."""
        return self.sl is not None and self.tp is not None

    def __str__(self) -> str:
        parts = [f"{self.side.upper()} {self.symbol}"]
        parts.append(f"@ {self.entry}" if self.entry else "@ market")
        if self.sl:
            parts.append(f"SL {self.sl}")
        if self.tps:
            parts.append("TP " + "/".join(str(t) for t in self.tps))
        return " ".join(parts)


def _numbers_after(text: str, patterns: tuple[str, ...]) -> list[float]:
    """Collect numbers that follow any of the given keyword patterns."""
    found = []
    for pattern in patterns:
        for m in re.finditer(pattern + r"[^0-9\-]{0,12}(\d+(?:[.,]\d+)?)",
                             text, re.IGNORECASE):
            try:
                found.append(float(m.group(1).replace(",", ".")))
            except ValueError:
                continue
    return found


def normalize_symbol(token: str) -> Optional[str]:
    """Map a token from a message to a canonical symbol name."""
    t = re.sub(r"[^A-Za-z0-9]", "", token).upper()
    if not t:
        return None
    if t in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[t]
    # FX pair written as EURUSD or EUR/USD
    if len(t) == 6 and t[:3] in FX_CURRENCIES and t[3:] in FX_CURRENCIES:
        return t
    return None


def find_symbol(text: str) -> Optional[str]:
    # try alias words first (GOLD, BITCOIN...)
    upper = text.upper()
    for alias in sorted(SYMBOL_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{alias}\b", upper):
            return SYMBOL_ALIASES[alias]
    # then any 6-letter FX pair, with or without separator
    for m in re.finditer(r"\b([A-Z]{3})\s*[/\-]?\s*([A-Z]{3})\b", upper):
        candidate = normalize_symbol(m.group(1) + m.group(2))
        if candidate:
            return candidate
    return None


def parse_signal(text: str) -> Optional[ParsedSignal]:
    """Return a ParsedSignal, or None if the message is not a new signal."""
    if not text or not text.strip():
        return None
    lowered = text.lower()

    # management/result messages are not entries
    for word in SKIP_WORDS:
        if word in lowered:
            return None

    # direction — require a word boundary so "buyers" doesn't count
    side = None
    for word in BUY_WORDS:
        if re.search(rf"\b{word}\b", lowered):
            side = "buy"
            break
    if side is None:
        for word in SELL_WORDS:
            if re.search(rf"\b{word}\b", lowered):
                side = "sell"
                break
    if side is None:
        return None

    # both directions mentioned -> ambiguous, refuse
    has_buy = any(re.search(rf"\b{w}\b", lowered) for w in BUY_WORDS)
    has_sell = any(re.search(rf"\b{w}\b", lowered) for w in SELL_WORDS)
    if has_buy and has_sell:
        return None

    symbol = find_symbol(text)
    if symbol is None:
        return None

    sig = ParsedSignal(side=side, symbol=symbol, raw=text.strip())

    sls = _numbers_after(text, (r"\bs\.?l\.?\b", r"\bstop\s*loss\b", r"\bstop\b"))
    if sls:
        sig.sl = sls[0]

    # NOTE: the optional index in TP1/TP2 must be attached to the keyword.
    # Allowing whitespace ("TP \d?") makes it swallow the first digit of a
    # decimal price: "TP 1.0900" parsed as index=1, price=0900.
    tps = _numbers_after(text, (r"\bt\.?p\.?\d?\b", r"\btake\s*profit\d?\b",
                                r"\btarget\d?\b"))
    # de-duplicate, preserve order
    seen = set()
    sig.tps = [t for t in tps if not (t in seen or seen.add(t))]

    entries = _numbers_after(text, (r"\bentry\b", r"\bentr[ye]\s*price\b",
                                    r"\bat\b", r"@"))
    if entries:
        sig.entry = entries[0]
    else:
        # a bare number right after the direction/symbol, e.g. "SELL GOLD 2350"
        m = re.search(r"\b(?:buy|sell|long|short)\b[^0-9\n]{0,20}(\d+(?:[.,]\d+)?)",
                      text, re.IGNORECASE)
        if m:
            value = float(m.group(1).replace(",", "."))
            if value not in (sig.sl,) and value not in sig.tps:
                sig.entry = value

    # sanity: stop and target must sit on the correct sides of entry
    reference = sig.entry
    if reference is None and sig.sl is not None and sig.tp is not None:
        reference = (sig.sl + sig.tp) / 2
    if reference is not None:
        if sig.sl is not None:
            wrong = (sig.sl > reference) if side == "buy" else (sig.sl < reference)
            if wrong:
                sig.warnings.append(
                    f"SL {sig.sl} is on the wrong side of {reference} for a {side}")
        if sig.tp is not None:
            wrong = (sig.tp < reference) if side == "buy" else (sig.tp > reference)
            if wrong:
                sig.warnings.append(
                    f"TP {sig.tp} is on the wrong side of {reference} for a {side}")

    if sig.sl is None:
        sig.warnings.append("no stop-loss found — will not be traded")
    if sig.tp is None:
        sig.warnings.append("no take-profit found — will not be traded")

    return sig


def broker_symbol(canonical: str, suffix: str = "", available: Optional[list[str]] = None) -> Optional[str]:
    """Map a canonical symbol to this broker's spelling.

    If `available` is given (the account's real symbol list) it is searched
    case-insensitively for an exact or suffixed match, which is safer than
    assuming a suffix.
    """
    if available:
        lowered = {s.lower(): s for s in available}
        for candidate in (canonical + suffix, canonical):
            if candidate.lower() in lowered:
                return lowered[candidate.lower()]
        # any symbol that starts with the canonical name (EURUSDm, EURUSD.a)
        for s in available:
            if s.lower().startswith(canonical.lower()):
                return s
        return None
    return canonical + suffix
