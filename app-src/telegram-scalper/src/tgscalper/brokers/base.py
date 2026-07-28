"""The interface every broker adapter implements.

Keeping execution behind this narrow interface is what lets the same parser,
risk engine and journal run against a paper account, MetaTrader 5, or whatever
you switch to later — the engine never imports a broker SDK directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..models import (
    AccountInfo,
    OrderRequest,
    OrderResult,
    Position,
    SymbolInfo,
)


class BrokerError(RuntimeError):
    pass


class Broker(ABC):
    """Minimal trading surface: look at the account, place, modify, close."""

    name: str = "broker"

    @property
    def is_live(self) -> bool:
        """True when orders reach a real venue. Logged on every trade."""
        return False

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def account_info(self) -> AccountInfo: ...

    @abstractmethod
    def available_symbols(self) -> list[str]: ...

    @abstractmethod
    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]: ...

    @abstractmethod
    def place_order(self, request: OrderRequest) -> OrderResult: ...

    @abstractmethod
    def positions(self, symbol: Optional[str] = None) -> list[Position]: ...

    @abstractmethod
    def modify_position(
        self,
        ticket: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> bool: ...

    @abstractmethod
    def close_position(self, ticket: int, volume: Optional[float] = None) -> OrderResult: ...

    @abstractmethod
    def pending_orders(self, symbol: Optional[str] = None) -> list[Position]: ...

    @abstractmethod
    def cancel_order(self, ticket: int) -> bool: ...

    # Context-manager sugar so callers cannot forget to disconnect.
    def __enter__(self) -> "Broker":
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
