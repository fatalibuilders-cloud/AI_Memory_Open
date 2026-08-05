"""A broker that fills everything on paper.

This is the default, and it is the only broker that runs until you explicitly
turn on live trading. Use it to watch real signals from your real groups get
parsed, sized and "filled" for a few days — the journal then tells you exactly
what the bot would have done before any money is involved.

Fills happen at the requested price (or the last seeded price for market
orders), so paper P&L ignores spread and slippage. It validates plumbing and
sizing, not strategy edge.
"""

from __future__ import annotations

import itertools
import re
from typing import Optional

from ..models import (
    AccountInfo,
    OrderRequest,
    OrderResult,
    OrderType,
    Position,
    Side,
    SymbolInfo,
)
from .base import Broker

# Approximate contract specs, good enough for sizing arithmetic in a dry run.
# These are ONLY used on paper: the live path reads the real specification from
# the broker terminal, which is authoritative. Treat any number here as a
# plausible default, not as your broker's actual contract.
#
# (pattern, digits, point, tick_value_per_lot, volume_min, volume_step)
_SPECS: list[tuple[str, int, float, float, float, float]] = [
    (r"^XAUUSD", 2, 0.01, 1.0, 0.01, 0.01),      # 100 oz/lot -> $100 per $1 move
    (r"^XAGUSD", 3, 0.001, 5.0, 0.01, 0.01),     # 5000 oz/lot
    (r"^(US30|GER40|UK100|SPX500|NAS100|US100|USTEC)", 1, 0.1, 0.1, 0.01, 0.01),
    (r"^(BTC|ETH)", 2, 0.01, 0.01, 0.01, 0.01),
    (r"^(USOIL|UKOIL|WTI|BRENT)", 2, 0.01, 1.0, 0.01, 0.01),  # 1000 bbl/lot
    # --- Deriv synthetics. Contract size is 1, i.e. ~1 unit of account currency
    # per 1.0 index point per lot, so tick_value equals tick_size. Minimum lots
    # differ sharply between families (Boom/Crash ~0.2, Volatility ~0.001) —
    # exactly the sort of thing a dry run should surface before you go live.
    (r"^(V\d+|VOLATILITY\d+INDEX|VIX\d+|R_?\d+)", 2, 0.01, 0.01, 0.001, 0.001),
    (r"^(BOOM\d+|CRASH\d+)(INDEX)?", 2, 0.01, 0.01, 0.2, 0.01),
    (r"^STEPINDEX", 1, 0.1, 0.1, 0.1, 0.1),
    (r"^JUMP\d+(INDEX)?", 2, 0.01, 0.01, 0.01, 0.01),
    (r"^RANGEBREAK\d+", 4, 0.0001, 0.0001, 0.01, 0.01),
    (r"^[A-Z]{3}JPY", 3, 0.001, 0.67, 0.01, 0.01),  # ~100k JPY/pip, USD-ish
    (r"^[A-Z]{6}", 5, 0.00001, 1.0, 0.01, 0.01),    # 100k units/lot
]


def _spec_for(symbol: str) -> tuple[int, float, float, float, float]:
    bare = re.sub(r"[^A-Z0-9]", "", symbol.upper())
    for pattern, digits, point, tick_value, volume_min, volume_step in _SPECS:
        if re.match(pattern, bare):
            return digits, point, tick_value, volume_min, volume_step
    return 2, 0.01, 1.0, 0.01, 0.01


class PaperBroker(Broker):
    name = "paper"

    def __init__(self, starting_balance: float = 10_000.0, reason: str = "") -> None:
        self.balance = starting_balance
        self.reason = reason  # why we are on paper, surfaced in logs
        self._tickets = itertools.count(900_001)
        self._positions: dict[int, Position] = {}
        self._pending: dict[int, Position] = {}
        self._prices: dict[str, float] = {}
        self._connected = False

    # --- lifecycle ---
    def connect(self) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    # --- prices ---
    def seed_price(self, symbol: str, price: float) -> None:
        """Tell the paper book what 'market' means for a symbol.

        The engine seeds this from the signal's own entry price, which is the
        only price reference available without a live feed.
        """
        if price > 0:
            self._prices[symbol.upper()] = price

    def last_price(self, symbol: str) -> Optional[float]:
        return self._prices.get(symbol.upper())

    # --- account & symbols ---
    def account_info(self) -> AccountInfo:
        floating = sum(position.profit for position in self._positions.values())
        return AccountInfo(
            balance=self.balance,
            equity=self.balance + floating,
            currency="USD",
            margin_free=self.balance,
            trade_mode="PAPER",
        )

    def available_symbols(self) -> list[str]:
        # Empty means "do not filter" — the resolver falls back to best effort,
        # so paper mode accepts whatever the groups mention.
        return []

    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        digits, point, tick_value, volume_min, volume_step = _spec_for(symbol)
        price = self._prices.get(symbol.upper(), 0.0)
        half_spread = point * 10
        return SymbolInfo(
            name=symbol,
            digits=digits,
            point=point,
            tick_size=point,
            tick_value=tick_value,
            volume_min=volume_min,
            volume_max=100.0,
            volume_step=volume_step,
            bid=max(price - half_spread, 0.0),
            ask=price + half_spread,
            stops_level_points=0,
        )

    # --- orders ---
    def place_order(self, request: OrderRequest) -> OrderResult:
        price = request.price or self._prices.get(request.symbol.upper())
        if not price:
            return OrderResult(ok=False, error="paper broker has no price for this symbol")
        ticket = next(self._tickets)
        position = Position(
            ticket=ticket,
            symbol=request.symbol,
            side=request.side,
            volume=request.volume,
            open_price=price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            comment=request.comment,
        )
        if request.order_type is OrderType.MARKET:
            self._positions[ticket] = position
            self.seed_price(request.symbol, price)
        else:
            self._pending[ticket] = position
        return OrderResult(ok=True, ticket=ticket, filled_price=price, volume=request.volume)

    def positions(self, symbol: Optional[str] = None) -> list[Position]:
        return [
            position
            for position in self._positions.values()
            if symbol is None or position.symbol.upper() == symbol.upper()
        ]

    def pending_orders(self, symbol: Optional[str] = None) -> list[Position]:
        return [
            order
            for order in self._pending.values()
            if symbol is None or order.symbol.upper() == symbol.upper()
        ]

    def modify_position(
        self,
        ticket: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> bool:
        position = self._positions.get(ticket) or self._pending.get(ticket)
        if position is None:
            return False
        if stop_loss is not None:
            position.stop_loss = stop_loss
        if take_profit is not None:
            position.take_profit = take_profit
        return True

    def close_position(self, ticket: int, volume: Optional[float] = None) -> OrderResult:
        position = self._positions.get(ticket)
        if position is None:
            return OrderResult(ok=False, error=f"no open paper position {ticket}")
        price = self._prices.get(position.symbol.upper(), position.open_price)
        closing = min(volume or position.volume, position.volume)
        info = self.symbol_info(position.symbol)
        moved = (price - position.open_price) * position.side.sign
        profit = moved * (info.value_per_price_unit() if info else 0.0) * closing
        self.balance += profit
        if closing >= position.volume:
            del self._positions[ticket]
        else:
            position.volume = round(position.volume - closing, 2)
        return OrderResult(ok=True, ticket=ticket, filled_price=price, volume=closing)

    def cancel_order(self, ticket: int) -> bool:
        return self._pending.pop(ticket, None) is not None
