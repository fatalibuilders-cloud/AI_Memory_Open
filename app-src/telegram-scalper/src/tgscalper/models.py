"""Core data types shared by the parser, risk engine, brokers and journal."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

    @property
    def opposite(self) -> "Side":
        return Side.SELL if self is Side.BUY else Side.BUY

    @property
    def sign(self) -> int:
        """+1 when price moving up is profit, -1 when down is profit."""
        return 1 if self is Side.BUY else -1


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"  # entry better than current price
    STOP = "STOP"  # entry worse than current price (breakout)


class Action(str, Enum):
    """What a parsed message is asking us to do."""

    OPEN = "OPEN"
    CLOSE = "CLOSE"
    CLOSE_PARTIAL = "CLOSE_PARTIAL"
    BREAKEVEN = "BREAKEVEN"
    MOVE_SL = "MOVE_SL"
    CANCEL_PENDING = "CANCEL_PENDING"


@dataclass(frozen=True)
class MessageRef:
    """Where a message came from, so trades can be traced back to a post."""

    chat_id: int
    message_id: int
    sender_id: Optional[int] = None
    chat_title: str = ""
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Set when the admin replied to an earlier post ("close this one", "SL to BE").
    reply_to_message_id: Optional[int] = None


@dataclass
class Signal:
    """A parsed instruction to open a position."""

    action: Action
    symbol: str  # as written in the message, e.g. "GOLD"
    side: Optional[Side] = None
    order_type: OrderType = OrderType.MARKET
    entry: Optional[float] = None
    entry_zone: Optional[tuple[float, float]] = None
    stop_loss: Optional[float] = None
    take_profits: list[float] = field(default_factory=list)
    # Some groups post distances instead of prices ("SL 30 pips"). Converted to
    # absolute prices by the engine, which knows the symbol's point size.
    sl_pips: Optional[float] = None
    tp_pips: list[float] = field(default_factory=list)
    # Management payloads
    new_sl: Optional[float] = None
    close_fraction: Optional[float] = None
    # Provenance
    raw_text: str = ""
    source: Optional[MessageRef] = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_open(self) -> bool:
        return self.action is Action.OPEN

    def fingerprint(self) -> str:
        """Stable hash used to drop duplicate reposts of the same setup.

        Deliberately excludes the message id and timestamp: the same setup
        forwarded twice, or reposted with different emoji, collapses to one
        fingerprint. Chat id is excluded too, so cross-posting the same signal
        into three of your groups only opens one trade.
        """
        parts = [
            self.action.value,
            self.symbol.upper(),
            self.side.value if self.side else "-",
            _fmt(self.entry),
            _fmt(self.stop_loss),
            ",".join(_fmt(tp) for tp in sorted(self.take_profits)),
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]

    def summary(self) -> str:
        if not self.is_open:
            detail = ""
            if self.action is Action.MOVE_SL and self.new_sl is not None:
                detail = f" -> {self.new_sl}"
            elif self.action is Action.CLOSE_PARTIAL and self.close_fraction:
                detail = f" {self.close_fraction:.0%}"
            return f"{self.action.value} {self.symbol}{detail}"
        bits = [f"{self.side.value if self.side else '?'} {self.symbol}"]
        if self.order_type is not OrderType.MARKET:
            bits.append(self.order_type.value)
        bits.append(f"@ {self.entry if self.entry is not None else 'MKT'}")
        if self.stop_loss is not None:
            bits.append(f"SL {self.stop_loss}")
        if self.take_profits:
            bits.append("TP " + "/".join(str(tp) for tp in self.take_profits))
        return " ".join(bits)


@dataclass(frozen=True)
class SymbolInfo:
    """Contract specification pulled from the broker, needed for lot sizing."""

    name: str
    digits: int
    point: float  # smallest price increment, e.g. 0.01 for XAUUSD
    tick_size: float
    tick_value: float  # account currency gained per tick_size move, per 1.0 lot
    volume_min: float
    volume_max: float
    volume_step: float
    bid: float
    ask: float
    stops_level_points: int = 0  # broker's minimum SL/TP distance, in points

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread_points(self) -> float:
        return (self.ask - self.bid) / self.point if self.point else 0.0

    def value_per_price_unit(self) -> float:
        """Account-currency P&L per 1.0 price unit, per 1.0 lot."""
        if self.tick_size <= 0:
            return 0.0
        return self.tick_value / self.tick_size


@dataclass(frozen=True)
class AccountInfo:
    balance: float
    equity: float
    currency: str = "USD"
    leverage: int = 0
    margin_free: float = 0.0
    # What kind of account the broker says this is: DEMO, CONTEST, REAL, PAPER
    # or UNKNOWN. Sending orders to a broker and risking actual money are two
    # different decisions, and only the broker can tell us which one this is.
    trade_mode: str = "UNKNOWN"
    login: str = ""
    server: str = ""

    @property
    def is_real_money(self) -> bool:
        return self.trade_mode.upper() == "REAL"


@dataclass
class OrderRequest:
    symbol: str  # broker symbol, already resolved (suffix applied)
    side: Side
    order_type: OrderType
    volume: float
    price: Optional[float] = None  # None => market
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = "tgscalper"
    # Which leg of a multi-TP signal this is (1-based), for the journal.
    leg: int = 1


@dataclass
class OrderResult:
    ok: bool
    ticket: Optional[int] = None
    filled_price: Optional[float] = None
    volume: float = 0.0
    error: str = ""
    retcode: Optional[int] = None


@dataclass
class Position:
    ticket: int
    symbol: str
    side: Side
    volume: float
    open_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    profit: float = 0.0
    comment: str = ""


@dataclass
class Decision:
    """Outcome of routing one Telegram message. Everything is logged."""

    accepted: bool
    reason: str = ""
    signal: Optional[Signal] = None
    orders: list[OrderResult] = field(default_factory=list)
    # A refusal worth reporting: the message looked like a signal. Plain
    # conversation is not, and reporting it drowns out everything else.
    near_miss: bool = False

    @property
    def placed(self) -> int:
        return sum(1 for order in self.orders if order.ok)


def _fmt(value: Optional[float]) -> str:
    return "-" if value is None else f"{value:.5f}".rstrip("0").rstrip(".")
