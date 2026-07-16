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

    @abstractmethod
    def positions(self, symbol: Optional[str] = None) -> list[Position]: ...

    @abstractmethod
    def close_position(self, ticket: int) -> float:
        """Close by ticket; returns realized profit."""

    @abstractmethod
    def volume_for_risk(self, symbol: str, sl_distance: float, risk_amount: float) -> float:
        """Position size such that hitting the SL loses ~risk_amount, clamped
        to the symbol's min/max/step volume rules."""
