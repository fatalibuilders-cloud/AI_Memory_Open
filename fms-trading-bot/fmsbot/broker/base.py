"""Broker interface + shared data types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class BrokerError(RuntimeError):
    pass


@dataclass
class Bar:
    time: int      # unix timestamp of bar open
    open: float
    high: float
    low: float
    close: float


@dataclass
class Position:
    ticket: int
    symbol: str
    side: str          # "buy" | "sell"
    volume: float      # lots / units, broker-native
    entry_price: float
    sl: float
    tp: float
    profit: float      # floating PnL in account currency


@dataclass
class OrderReceipt:
    ticket: int
    symbol: str
    side: str
    volume: float
    price: float
    sl: float
    tp: float


class Broker(ABC):
    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def balance(self) -> float: ...

    @abstractmethod
    def equity(self) -> float: ...

    @abstractmethod
    def bars(self, symbol: str, timeframe: str, count: int) -> list[Bar]:
        """Most-recent `count` bars, oldest first. The LAST bar may be forming."""

    @abstractmethod
    def market_order(self, symbol: str, side: str, volume: float,
                     sl: float, tp: float, comment: str = "") -> OrderReceipt: ...

    def value_per_price(self, symbol: str, volume: float) -> float:
        """Account currency gained per 1.0 of price movement at this size.

        Lets a cash target be turned into a price distance:
        distance = money / value_per_price. 0.0 when unknown.
        """
        return 0.0

    def account_currency(self) -> str:
        """The currency the broker reports balance and profit in.

        Not cosmetic. On an Exness "cent" account every money figure --
        balance, equity, a position's profit -- is in cents, so a $0.10
        setting means a tenth of a cent and fires on every trade.
        """
        return ""

    def is_demo(self) -> Optional[bool]:
        """True on a practice account, False on real money, None if unknown.

        Unknown is not "safe": a caller deciding whether to risk real money
        must treat None as possibly-real.
        """
        return None

    def spread(self, symbol: str) -> float:
        """Current ask - bid, in price units. 0.0 if the broker cannot say."""
        return 0.0

    def min_stop_distance(self, symbol: str) -> float:
        """Closest a stop or target may sit to price. 0.0 if unrestricted."""
        return 0.0

    @abstractmethod
    def current_price(self, symbol: str, side: str) -> float:
        """The price a market order would fill at right now.

        Ask for a buy, bid for a sell. Stops and targets must be measured
        from this, not from the signal candle's close: on fast timeframes
        the gap between them is a large share of the stop distance and
        silently ruins the intended reward:risk.
        """

    def modify_position(self, ticket: int, sl: float, tp: float) -> None:
        """Adjust an open position's stop and target. Optional per broker."""
        raise BrokerError("modify_position is not supported by this broker")

    @abstractmethod
    def positions(self, symbol: Optional[str] = None) -> list[Position]: ...

    @abstractmethod
    def close_position(self, ticket: int) -> float:
        """Close by ticket; returns realized profit."""

    @abstractmethod
    def volume_for_risk(self, symbol: str, sl_distance: float, risk_amount: float) -> float:
        """Position size such that hitting the SL loses ~risk_amount, clamped
        to the symbol's min/max/step volume rules."""

    @abstractmethod
    def volume_from_lots(self, symbol: str, lots: float) -> float:
        """Convert a standard-lot figure to this broker's volume unit,
        clamped to the symbol's rules. MT5 trades in lots; OANDA in units
        (1 lot = 100,000 units)."""
