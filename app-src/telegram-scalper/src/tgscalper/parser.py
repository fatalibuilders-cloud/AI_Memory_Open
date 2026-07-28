"""Read a Telegram message and work out what trade it is asking for.

Signal groups do not follow a spec. The same setup shows up as any of:

    🔥 GOLD BUY NOW 2350.5        BUY XAUUSD @ 2350-2352      SELL LIMIT EURUSD
    SL 2344                       SL: 2344                    Entry: 1.0850
    TP1 2355 TP2 2360 TP3 2370    TP 2355, 2360, 2370         SL 1.0880
                                                              TP 1.0800

...plus follow-ups that manage a live trade ("SL to BE", "close half",
"cancel that one"). This module normalises the text, pulls out the parts, and
refuses anything that does not make arithmetic sense — a misread digit is far
more expensive than a missed signal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .models import Action, MessageRef, OrderType, Side, Signal
from .symbols import DEFAULT_ALIASES, find_symbol

NUM = r"\d{1,7}(?:[.,]\d{1,6})?"
_NUM_RE = re.compile(NUM)

# --- keyword vocabulary ------------------------------------------------------

# Deliberately excludes BULLISH/BEARISH: commentary uses those constantly
# ("gold looking bullish on H4") and they are never how an actual order is given.
_BUY_WORDS = r"BUY|LONG"
_SELL_WORDS = r"SELL|SHORT"

# Hedging language that marks a post as analysis rather than an instruction.
# Such a message must carry a full SL + TP structure before we act on it.
_COMMENTARY_RE = re.compile(
    r"\b(?:ANALYSIS|IDEA|OUTLOOK|FORECAST|WATCH(?:ING|LIST)?|LOOKING|LOOKS|MAYBE|"
    r"EXPECT(?:ING)?|PROBABLY|POSSIBLE|POSSIBLY|IF\s+IT|WAIT(?:ING)?\s+FOR|"
    r"PREPARE|GET\s+READY|POTENTIAL|SETUP\s+FORMING|PLAN\s+FOR)\b"
)
_DIRECTION_RE = re.compile(
    rf"\b(?P<side>{_BUY_WORDS}|{_SELL_WORDS})\b\s*(?P<kind>LIMIT|STOP|NOW|MARKET)?"
)

_SL_RE = re.compile(rf"\bSL\b\s*[:=@\-]*\s*(?P<value>{NUM})\s*(?P<pips>PIPS?)?")
_TP_RE = re.compile(
    rf"\bTP\s*(?:(?P<label>\d)(?=[^\d.]|$))?\s*[:=@\-]*\s*"
    rf"(?P<values>(?:{NUM}[\s,;/]*)+)(?P<pips>PIPS?)?"
)
_ENTRY_RE = re.compile(
    rf"\bENTRY\b\s*[:=@\-]*\s*(?P<low>{NUM})(?:\s*[-/]\s*(?P<high>{NUM}))?"
)
_AT_PRICE_RE = re.compile(rf"@\s*(?P<low>{NUM})(?:\s*[-/]\s*(?P<high>{NUM}))?")

# Noise that contains digits and would otherwise be mistaken for a price.
_NOISE_PATTERNS = [
    r"\b[MH]\d{1,3}\b",                      # timeframes: M15, H4
    r"\b[DW]1\b",                            # D1, W1
    r"\bRR?\s*[:=]?\s*\d+(?:[.,]\d+)?\s*[:/]\s*\d+(?:[.,]\d+)?",  # RR 1:2
    r"\b\d+(?:[.,]\d+)?\s*[:/]\s*\d+(?:[.,]\d+)?\s*R{1,2}\b",     # 1:2 RR
    r"\b(?:LOT|LOTS|VOLUME|VOL|SIZE)\b\s*[:=]?\s*\d+(?:[.,]\d+)?",
    r"\b(?:RISK|EQUITY|BALANCE)\b\s*[:=]?\s*\d+(?:[.,]\d+)?\s*%?",
    r"\d+(?:[.,]\d+)?\s*%",                  # percentages
    r"\b(?:TP|SL)\s*\d\b(?=\s*(?:HIT|REACHED|DONE|SECURED|CLOSED))",
]

# "BE" on its own is far too loose — "be careful today" must never move a stop.
# It only counts as break-even when it sits in a stop-loss context.
_BREAKEVEN_RE = re.compile(
    r"\b(?:BREAK\s?EVEN"
    r"|(?:SL|STOPS?)\s*(?:TO|AT|@|=)\s*(?:BE\b|BREAK\s?EVEN|ENTRY|OPEN|COST)"
    r"|MOVE\s*(?:YOUR\s*)?(?:SL|STOPS?)\s*(?:TO|AT)\s*(?:ENTRY|BE\b|BREAK\s?EVEN|OPEN)"
    r"|RISK\s*FREE|SECURE\s*(?:YOUR\s*)?(?:TRADE|POSITION|ENTRY))"
)
_MOVE_SL_RE = re.compile(
    rf"\b(?:MOVE|CHANGE|ADJUST|SHIFT|TRAIL|NEW|UPDATE|SET)\b[^\n]*?\bSL\b\s*"
    rf"(?:TO|AT|@|[:=\-])?\s*(?P<value>{NUM})"
    rf"|\bSL\s*(?:TO|AT|@)\s*(?P<value2>{NUM})"
)
_PARTIAL_RE = re.compile(
    r"\b(?:CLOSE|BOOK|TAKE|SECURE|EXIT)\b[^\n]{0,20}?"
    r"(?:(?P<pct>\d{1,3})\s*%|(?P<half>HALF)|(?P<partial>PARTIAL(?:LY)?)|"
    r"(?P<third>THIRD|1/3)|(?P<quarter>QUARTER|1/4))"
)
# Only the imperative counts. "CLOSED" is nearly always commentary ("market
# closed", "closed at TP1"), and \b after CLOSE excludes it automatically.
_CLOSE_VERB_RE = re.compile(r"\b(?:CLOSE|EXIT|FLATTEN)\b")
_CLOSE_AT_START_RE = re.compile(r"(?:^|\n)\s*(?:PLEASE\s+|GUYS\s+|NOW\s+)?(?:CLOSE|EXIT|FLATTEN)\b")
_CLOSE_OBJECT_RE = re.compile(
    r"\b(?:CLOSE|EXIT|FLATTEN)\s+(?:THE\s+|YOUR\s+|ALL\s+|OUR\s+)?"
    r"(?:ALL|EVERYTHING|EVERY\s+TRADE|NOW|TRADES?|POSITIONS?|ORDERS?|IT|THIS|THAT|THEM|"
    r"REST|REMAINING|BUY|SELL|LONGS?|SHORTS?|MANUALLY|FULLY|FULL|HALF|\d{1,3}\s*%)\b"
)
_CANCEL_RE = re.compile(
    r"\b(?:CANCEL(?:LED|LLED)?|DELETE\s+(?:THE\s+)?PENDING|IGNORE\s+(?:THIS|THAT|"
    r"THE)?\s*(?:SIGNAL|TRADE|ORDER)?|SIGNAL\s+(?:IS\s+)?(?:VOID|INVALID|OFF))"
)


@dataclass
class ParseResult:
    """Either a usable signal, or a reason nothing was acted on."""

    signal: Optional[Signal] = None
    error: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.signal is not None


def normalize(raw: str) -> str:
    """Upper-case, de-emoji and standardise the vocabulary.

    Non-ASCII characters become spaces rather than being deleted, so
    "🔥GOLD" separates into two tokens instead of fusing.
    """
    text = raw.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = text.upper()
    # Collapse the many spellings of SL / TP / ENTRY into canonical keywords.
    text = re.sub(r"\bS\s*[/\\.]\s*L\b", "SL", text)
    text = re.sub(r"\bT\s*[/\\.]\s*P\b", "TP", text)
    text = re.sub(r"\bSTOP\s*[-]?\s*(?:LOSS|LOSE|LOST)\b", "SL", text)
    text = re.sub(r"\bSTOPLOSS\b", "SL", text)
    text = re.sub(r"\bTAKE\s*[-]?\s*PROFITS?\b", "TP", text)
    text = re.sub(r"\bTAKEPROFITS?\b", "TP", text)
    text = re.sub(r"\bTARGETS?\b", "TP", text)
    text = re.sub(r"\bTGT\b", "TP", text)
    text = re.sub(r"\bENTR(?:Y|IES)\s*(?:PRICE|POINT|ZONE|LEVEL)?\b", "ENTRY", text)
    text = re.sub(r"\bENT\b", "ENTRY", text)
    text = re.sub(r"[ \t]+", " ", text)
    return "\n".join(line.strip() for line in text.splitlines())


def _to_float(token: str) -> float:
    """Parse a price, coping with both decimal commas and thousands separators."""
    token = token.strip()
    if "," in token and "." in token:
        token = token.replace(",", "")
    elif "," in token:
        head, _, tail = token.partition(",")
        # "44,250" is forty-four thousand; "2350,50" is a decimal comma.
        token = head + tail if len(tail) == 3 and len(head) <= 3 else f"{head}.{tail}"
    return float(token)


def _blank(match: re.Match[str]) -> str:
    """Replace a match with spaces, preserving length so offsets stay valid."""
    return " " * len(match.group(0))


def _mask(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        text = re.sub(pattern, _blank, text)
    return text


def _mask_symbol(text: str, canonical: str, aliases: dict[str, list[str]]) -> str:
    """Blank out the instrument name so "US30" stops looking like the price 30."""
    spellings = [canonical, *aliases.get(canonical, [])]
    for spelling in sorted(spellings, key=len, reverse=True):
        spelling = re.sub(r"\s+", " ", spelling.upper()).strip()
        pattern = r"(?<![A-Z0-9])" + re.escape(spelling).replace(r"\ ", r"\s?") + r"(?![A-Z0-9])"
        text = re.sub(pattern, _blank, text)
    return text


def _numbers(blob: str) -> list[float]:
    return [_to_float(token) for token in _NUM_RE.findall(blob)]


# --- extraction --------------------------------------------------------------


def _extract_direction(text: str) -> tuple[Optional[Side], OrderType]:
    match = _DIRECTION_RE.search(text)
    if not match:
        return None, OrderType.MARKET
    word = match.group("side")
    side = Side.BUY if re.fullmatch(_BUY_WORDS, word) else Side.SELL
    kind = match.group("kind") or ""
    if kind == "LIMIT":
        return side, OrderType.LIMIT
    if kind == "STOP":
        return side, OrderType.STOP
    return side, OrderType.MARKET


def _extract_sl(text: str) -> tuple[Optional[float], Optional[float]]:
    match = _SL_RE.search(text)
    if not match:
        return None, None
    value = _to_float(match.group("value"))
    if match.group("pips"):
        return None, value
    return value, None


def _extract_tps(text: str) -> tuple[list[float], list[float]]:
    prices: list[float] = []
    pips: list[float] = []
    for match in _TP_RE.finditer(text):
        values = _numbers(match.group("values"))
        if match.group("pips"):
            pips.extend(values)
        else:
            prices.extend(values)
    # Preserve order but drop repeats (groups often restate TP1 in a footer).
    return _dedupe(prices), _dedupe(pips)


def _dedupe(values: list[float]) -> list[float]:
    seen: set[float] = set()
    out: list[float] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _extract_entry(text: str) -> tuple[Optional[float], Optional[tuple[float, float]], bool]:
    """Return (entry, zone, is_explicit_market)."""
    explicit_market = bool(re.search(r"\b(?:NOW|MARKET|MKT|CMP|RUNNING)\b", text))

    for pattern in (_ENTRY_RE, _AT_PRICE_RE):
        match = pattern.search(text)
        if match:
            low = _to_float(match.group("low"))
            high = match.group("high")
            if high:
                pair = tuple(sorted((low, _to_float(high))))
                return None, (pair[0], pair[1]), explicit_market
            return low, None, explicit_market

    # Fall back to the first number on the direction line, ignoring anything
    # after an SL/TP keyword on that line.
    for line in text.splitlines():
        direction = _DIRECTION_RE.search(line)
        if not direction:
            continue
        tail = line[direction.end():]
        cut = re.search(r"\b(?:SL|TP)\b", tail)
        if cut:
            tail = tail[: cut.start()]
        zone = re.search(rf"(?P<low>{NUM})\s*[-/]\s*(?P<high>{NUM})", tail)
        if zone:
            pair = tuple(sorted((_to_float(zone.group("low")), _to_float(zone.group("high")))))
            return None, (pair[0], pair[1]), explicit_market
        found = _NUM_RE.search(tail)
        if found:
            return _to_float(found.group(0)), None, explicit_market
        break
    return None, None, explicit_market


def _expand_shorthand(reference: float, value: float) -> Optional[float]:
    """Rebuild "SL 44" into 2344 when the entry is 2350.

    Groups routinely abbreviate to the last two digits. Only applied when the
    value is at least ten times too small, and the rebuilt price must land
    within 5% of the reference — otherwise we give up rather than guess.
    """
    if reference <= 0 or value <= 0 or value >= reference / 10:
        return None
    digits = len(str(int(value)))
    scale = 10 ** digits
    head = int(reference // scale) * scale
    for candidate in (head + value, head + value - scale, head + value + scale):
        if candidate > 0 and abs(candidate - reference) / reference <= 0.05:
            return round(candidate, 6)
    return None


# --- management messages -----------------------------------------------------


def _is_close_instruction(text: str, has_symbol: bool) -> bool:
    """Distinguish "close gold now" from "market closed today".

    A close verb counts as an instruction when it opens a line (imperative), or
    names what to close, or appears alongside an instrument. Bare commentary
    that merely contains the word does not qualify.
    """
    if not _CLOSE_VERB_RE.search(text):
        return False
    if _CLOSE_AT_START_RE.search(text) or _CLOSE_OBJECT_RE.search(text):
        return True
    return has_symbol


def _parse_management(text: str, source: Optional[MessageRef], raw: str) -> Optional[Signal]:
    symbol = find_symbol(text) or ""

    def build(action: Action, **kwargs: object) -> Signal:
        return Signal(action=action, symbol=symbol, raw_text=raw, source=source, **kwargs)  # type: ignore[arg-type]

    if _CANCEL_RE.search(text):
        return build(Action.CANCEL_PENDING)

    # Break-even is checked before a generic SL move: "SL to BE" carries no price.
    if _BREAKEVEN_RE.search(text):
        return build(Action.BREAKEVEN)

    partial = _PARTIAL_RE.search(text)
    if partial:
        if partial.group("pct"):
            fraction = min(max(int(partial.group("pct")) / 100, 0.01), 1.0)
        elif partial.group("third"):
            fraction = 1 / 3
        elif partial.group("quarter"):
            fraction = 0.25
        else:
            fraction = 0.5
        if fraction >= 1.0:
            return build(Action.CLOSE)
        return build(Action.CLOSE_PARTIAL, close_fraction=fraction)

    if _is_close_instruction(text, bool(symbol)):
        return build(Action.CLOSE)

    move = _MOVE_SL_RE.search(text)
    if move:
        value = move.group("value") or move.group("value2")
        if value:
            return build(Action.MOVE_SL, new_sl=_to_float(value))

    return None


# --- entry point -------------------------------------------------------------


def parse(
    raw: str,
    source: Optional[MessageRef] = None,
    aliases: Optional[dict[str, list[str]]] = None,
    require_sl: bool = True,
) -> ParseResult:
    """Parse one message. Returns a ParseResult; `error` explains any refusal."""
    aliases = aliases or DEFAULT_ALIASES
    if not raw or not raw.strip():
        return ParseResult(error="empty message")

    text = normalize(raw)
    warnings: list[str] = []

    side, order_type = _extract_direction(text)
    canonical = find_symbol(text, aliases)

    # No direction word means this cannot be an entry; try management verbs.
    if side is None:
        managed = _parse_management(text, source, raw)
        if managed:
            return ParseResult(signal=managed)
        return ParseResult(error="no trade direction found")

    # A direction word plus a management verb and no fresh levels is a
    # follow-up ("close the buy"), not a new entry.
    if (
        _is_close_instruction(text, canonical is not None)
        or _CANCEL_RE.search(text)
        or _BREAKEVEN_RE.search(text)
    ):
        if not _SL_RE.search(text) and not _TP_RE.search(text):
            managed = _parse_management(text, source, raw)
            if managed:
                return ParseResult(signal=managed)

    if canonical is None:
        return ParseResult(error="no tradable symbol found")

    working = _mask_symbol(text, canonical, aliases)
    working = _mask(working, _NOISE_PATTERNS)

    stop_loss, sl_pips = _extract_sl(working)
    take_profits, tp_pips = _extract_tps(working)
    entry, zone, explicit_market = _extract_entry(working)

    if zone is not None:
        # A zone is a range to enter within; the midpoint is the reference price.
        entry = round((zone[0] + zone[1]) / 2, 6)
        warnings.append(f"entry zone {zone[0]}-{zone[1]}, using midpoint {entry}")

    reference = entry or stop_loss or (take_profits[0] if take_profits else None)

    # Rebuild two-digit shorthand ("SL 44" against an entry of 2350).
    if entry and stop_loss is not None:
        expanded = _expand_shorthand(entry, stop_loss)
        if expanded is not None:
            warnings.append(f"expanded shorthand SL {stop_loss} -> {expanded}")
            stop_loss = expanded
    if entry:
        rebuilt: list[float] = []
        for tp in take_profits:
            expanded = _expand_shorthand(entry, tp)
            if expanded is not None:
                warnings.append(f"expanded shorthand TP {tp} -> {expanded}")
                rebuilt.append(expanded)
            else:
                rebuilt.append(tp)
        take_profits = rebuilt

    if explicit_market and order_type is OrderType.MARKET and entry is not None:
        # "BUY NOW 2350" — the price is context for sizing, not a pending level.
        warnings.append("message says NOW; entering at market")

    signal = Signal(
        action=Action.OPEN,
        symbol=canonical,
        side=side,
        order_type=order_type,
        entry=entry,
        entry_zone=zone,
        stop_loss=stop_loss,
        take_profits=take_profits,
        sl_pips=sl_pips,
        tp_pips=tp_pips,
        raw_text=raw,
        source=source,
        warnings=warnings,
    )

    if _COMMENTARY_RE.search(text) and not (signal.stop_loss and signal.take_profits):
        return ParseResult(
            error="reads as analysis, not an order (hedging language without full SL/TP)",
            warnings=warnings,
        )

    error = _validate(signal, require_sl=require_sl, reference=reference)
    if error:
        return ParseResult(error=error, warnings=warnings)
    return ParseResult(signal=signal, warnings=warnings)


def _validate(signal: Signal, require_sl: bool, reference: Optional[float]) -> str:
    """Reject anything internally inconsistent. Silence is approval."""
    if signal.side is None:
        return "missing direction"
    if require_sl and signal.stop_loss is None and signal.sl_pips is None:
        return "no stop loss in message (execution.require_stop_loss is on)"
    if signal.order_type is not OrderType.MARKET and signal.entry is None:
        return f"{signal.order_type.value} order without an entry price"

    sign = signal.side.sign
    entry = signal.entry

    if signal.stop_loss is not None and entry is not None:
        # For a BUY the stop must sit below entry; inverted means a misread.
        if (signal.stop_loss - entry) * sign >= 0:
            return (
                f"stop loss {signal.stop_loss} is on the wrong side of entry "
                f"{entry} for a {signal.side.value}"
            )
    for tp in signal.take_profits:
        if entry is not None and (tp - entry) * sign <= 0:
            return f"take profit {tp} is on the wrong side of entry {entry} for a {signal.side.value}"
        if signal.stop_loss is not None and (tp - signal.stop_loss) * sign <= 0:
            return f"take profit {tp} is beyond stop loss {signal.stop_loss}"

    # Guard against a stray digit: every level should be in the same ballpark.
    if reference:
        for label, value in [("SL", signal.stop_loss), *[("TP", tp) for tp in signal.take_profits]]:
            if value is None:
                continue
            if value <= 0 or abs(value - reference) / reference > 0.25:
                return f"{label} {value} is implausibly far from {reference} (>25%)"
    return ""
