"""MetaTrader 5 adapter — the live execution path.

Requires the `MetaTrader5` Python package and a running MT5 terminal, which is
Windows-only (a Windows VPS is the usual home for this bot so it keeps running
when your laptop sleeps). Everything else in this project is platform-neutral;
this file is the only place the SDK is touched.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..models import (
    AccountInfo,
    OrderRequest,
    OrderResult,
    OrderType,
    Position,
    Side,
    SymbolInfo,
)
from .base import Broker, BrokerError

log = logging.getLogger(__name__)


def _import_mt5() -> Any:
    try:
        import MetaTrader5 as mt5  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on host OS
        raise BrokerError(
            "MetaTrader5 package not installed. On the Windows trading machine run:\n"
            "    pip install MetaTrader5\n"
            "and make sure the MT5 terminal is installed and logged in."
        ) from exc
    return mt5


class MT5Broker(Broker):
    name = "mt5"

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self._mt5: Any = None

    @property
    def is_live(self) -> bool:
        return True

    # --- lifecycle ---
    def connect(self) -> None:
        mt5 = _import_mt5()
        kwargs: dict[str, Any] = {}
        if self.settings.terminal_path:
            kwargs["path"] = self.settings.terminal_path
        if self.settings.login:
            kwargs.update(
                login=int(self.settings.login),
                password=self.settings.password,
                server=self.settings.server,
            )
        if not mt5.initialize(**kwargs):
            code, message = mt5.last_error()
            raise BrokerError(f"MT5 initialize failed ({code}): {message}")
        self._mt5 = mt5

        account = mt5.account_info()
        if account is None:
            raise BrokerError("MT5 connected but no account is logged in")
        if not account.trade_allowed:
            raise BrokerError(
                "MT5 reports trading is not allowed for this account. Enable "
                "'Algo Trading' in the terminal and check the account is not read-only."
            )
        log.info(
            "MT5 connected: account %s on %s, balance %.2f %s",
            account.login,
            account.server,
            account.balance,
            account.currency,
        )

    def close(self) -> None:
        if self._mt5 is not None:
            self._mt5.shutdown()
            self._mt5 = None

    @property
    def mt5(self) -> Any:
        if self._mt5 is None:
            raise BrokerError("MT5 broker used before connect()")
        return self._mt5

    # --- account & symbols ---
    def account_info(self) -> AccountInfo:
        info = self.mt5.account_info()
        if info is None:
            raise BrokerError("MT5 account_info() returned nothing")
        return AccountInfo(
            balance=info.balance,
            equity=info.equity,
            currency=info.currency,
            leverage=info.leverage,
            margin_free=info.margin_free,
            trade_mode=self._trade_mode(getattr(info, "trade_mode", None)),
            login=str(getattr(info, "login", "")),
            server=str(getattr(info, "server", "")),
        )

    def _trade_mode(self, raw: Any) -> str:
        """Translate MT5's numeric account type into something readable.

        This is the only trustworthy source for "is this real money" — the
        server name is a convention, not a guarantee.
        """
        mt5 = self.mt5
        table = {
            getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0): "DEMO",
            getattr(mt5, "ACCOUNT_TRADE_MODE_CONTEST", 1): "CONTEST",
            getattr(mt5, "ACCOUNT_TRADE_MODE_REAL", 2): "REAL",
        }
        return table.get(raw, "UNKNOWN")

    def available_symbols(self) -> list[str]:
        symbols = self.mt5.symbols_get()
        return [symbol.name for symbol in symbols] if symbols else []

    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        info = self.mt5.symbol_info(symbol)
        if info is None:
            return None
        if not info.visible:
            # A symbol hidden from Market Watch cannot be quoted or traded until
            # it is selected.
            self.mt5.symbol_select(symbol, True)
            info = self.mt5.symbol_info(symbol)
            if info is None:
                return None
        tick = self.mt5.symbol_info_tick(symbol)
        bid = getattr(tick, "bid", 0.0) or info.bid
        ask = getattr(tick, "ask", 0.0) or info.ask
        return SymbolInfo(
            name=info.name,
            digits=info.digits,
            point=info.point,
            tick_size=info.trade_tick_size or info.point,
            tick_value=info.trade_tick_value,
            volume_min=info.volume_min,
            volume_max=info.volume_max,
            volume_step=info.volume_step,
            bid=bid,
            ask=ask,
            stops_level_points=getattr(info, "trade_stops_level", 0),
        )

    # --- orders ---
    def _order_type_const(self, side: Side, order_type: OrderType) -> int:
        mt5 = self.mt5
        table = {
            (Side.BUY, OrderType.MARKET): mt5.ORDER_TYPE_BUY,
            (Side.SELL, OrderType.MARKET): mt5.ORDER_TYPE_SELL,
            (Side.BUY, OrderType.LIMIT): mt5.ORDER_TYPE_BUY_LIMIT,
            (Side.SELL, OrderType.LIMIT): mt5.ORDER_TYPE_SELL_LIMIT,
            (Side.BUY, OrderType.STOP): mt5.ORDER_TYPE_BUY_STOP,
            (Side.SELL, OrderType.STOP): mt5.ORDER_TYPE_SELL_STOP,
        }
        return table[(side, order_type)]

    def _filling_modes(self, symbol: str) -> list[int]:
        """Filling modes to try, most-likely-supported first.

        Brokers differ on which they accept and rejecting on the first
        UNSUPPORTED_FILLING would drop a good signal, so we try in order.
        """
        mt5 = self.mt5
        info = self.mt5.symbol_info(symbol)
        preferred: list[int] = []
        filling = getattr(info, "filling_mode", 0) if info else 0
        # filling_mode is a bit mask: 1 = FOK allowed, 2 = IOC allowed.
        if filling & 2:
            preferred.append(mt5.ORDER_FILLING_IOC)
        if filling & 1:
            preferred.append(mt5.ORDER_FILLING_FOK)
        for mode in (mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN):
            if mode not in preferred:
                preferred.append(mode)
        return preferred

    def place_order(self, request: OrderRequest) -> OrderResult:
        mt5 = self.mt5
        info = self.symbol_info(request.symbol)
        if info is None:
            return OrderResult(ok=False, error=f"symbol {request.symbol} not available in MT5")

        is_market = request.order_type is OrderType.MARKET
        price = request.price
        if is_market:
            price = info.ask if request.side is Side.BUY else info.bid
        if not price:
            return OrderResult(ok=False, error="no price available for order")

        base: dict[str, Any] = {
            "action": mt5.TRADE_ACTION_DEAL if is_market else mt5.TRADE_ACTION_PENDING,
            "symbol": request.symbol,
            "volume": float(request.volume),
            "type": self._order_type_const(request.side, request.order_type),
            "price": round(price, info.digits),
            "deviation": int(self.settings.deviation_points),
            "magic": int(self.settings.magic),
            "comment": request.comment[:31],  # MT5 truncates past 31 chars
            "type_time": mt5.ORDER_TIME_GTC,
        }
        if request.stop_loss is not None:
            base["sl"] = round(request.stop_loss, info.digits)
        if request.take_profit is not None:
            base["tp"] = round(request.take_profit, info.digits)

        last: Optional[Any] = None
        for filling in self._filling_modes(request.symbol):
            payload = dict(base, type_filling=filling)
            result = mt5.order_send(payload)
            if result is None:
                code, message = mt5.last_error()
                return OrderResult(ok=False, error=f"order_send returned None ({code}): {message}")
            last = result
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return OrderResult(
                    ok=True,
                    ticket=result.order or getattr(result, "deal", None),
                    filled_price=result.price or price,
                    volume=result.volume or request.volume,
                    retcode=result.retcode,
                )
            if result.retcode not in {
                mt5.TRADE_RETCODE_INVALID_FILL,
                getattr(mt5, "TRADE_RETCODE_UNSUPPORTED_FILL_POLICY", -1),
            }:
                break  # a real rejection, not a filling-mode mismatch

        retcode = getattr(last, "retcode", None)
        comment = getattr(last, "comment", "unknown error")
        return OrderResult(ok=False, error=f"MT5 rejected order ({retcode}): {comment}", retcode=retcode)

    def positions(self, symbol: Optional[str] = None) -> list[Position]:
        raw = self.mt5.positions_get(symbol=symbol) if symbol else self.mt5.positions_get()
        return [self._to_position(item) for item in (raw or [])]

    def pending_orders(self, symbol: Optional[str] = None) -> list[Position]:
        raw = self.mt5.orders_get(symbol=symbol) if symbol else self.mt5.orders_get()
        out: list[Position] = []
        for item in raw or []:
            out.append(
                Position(
                    ticket=item.ticket,
                    symbol=item.symbol,
                    side=Side.BUY if "BUY" in str(item.type) or item.type % 2 == 0 else Side.SELL,
                    volume=item.volume_current,
                    open_price=item.price_open,
                    stop_loss=item.sl or None,
                    take_profit=item.tp or None,
                    comment=item.comment,
                )
            )
        return out

    def _to_position(self, item: Any) -> Position:
        return Position(
            ticket=item.ticket,
            symbol=item.symbol,
            side=Side.BUY if item.type == self.mt5.POSITION_TYPE_BUY else Side.SELL,
            volume=item.volume,
            open_price=item.price_open,
            stop_loss=item.sl or None,
            take_profit=item.tp or None,
            profit=item.profit,
            comment=item.comment,
        )

    def modify_position(
        self,
        ticket: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> bool:
        mt5 = self.mt5
        existing = mt5.positions_get(ticket=ticket)
        if not existing:
            log.warning("cannot modify %s: position not found", ticket)
            return False
        position = existing[0]
        info = self.symbol_info(position.symbol)
        digits = info.digits if info else 5
        payload = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": position.symbol,
            "sl": round(stop_loss, digits) if stop_loss is not None else position.sl,
            "tp": round(take_profit, digits) if take_profit is not None else position.tp,
        }
        result = mt5.order_send(payload)
        ok = result is not None and result.retcode == mt5.TRADE_RETCODE_DONE
        if not ok:
            log.warning(
                "modify %s failed: %s",
                ticket,
                getattr(result, "comment", mt5.last_error()),
            )
        return ok

    def close_position(self, ticket: int, volume: Optional[float] = None) -> OrderResult:
        mt5 = self.mt5
        existing = mt5.positions_get(ticket=ticket)
        if not existing:
            return OrderResult(ok=False, error=f"position {ticket} not found")
        position = existing[0]
        info = self.symbol_info(position.symbol)
        if info is None:
            return OrderResult(ok=False, error=f"symbol {position.symbol} unavailable")

        closing = min(volume or position.volume, position.volume)
        closing = max(_round_to_step(closing, info.volume_step), info.volume_min)
        is_buy = position.type == mt5.POSITION_TYPE_BUY
        base: dict[str, Any] = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": position.symbol,
            "volume": float(closing),
            "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
            "price": info.bid if is_buy else info.ask,
            "deviation": int(self.settings.deviation_points),
            "magic": int(self.settings.magic),
            "comment": "tgscalper close",
        }
        last: Optional[Any] = None
        for filling in self._filling_modes(position.symbol):
            result = mt5.order_send(dict(base, type_filling=filling))
            if result is None:
                code, message = mt5.last_error()
                return OrderResult(ok=False, error=f"close failed ({code}): {message}")
            last = result
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return OrderResult(
                    ok=True, ticket=ticket, filled_price=result.price, volume=closing
                )
        return OrderResult(
            ok=False,
            error=f"close rejected: {getattr(last, 'comment', 'unknown')}",
            retcode=getattr(last, "retcode", None),
        )

    def cancel_order(self, ticket: int) -> bool:
        mt5 = self.mt5
        result = mt5.order_send({"action": mt5.TRADE_ACTION_REMOVE, "order": ticket})
        return result is not None and result.retcode == mt5.TRADE_RETCODE_DONE


def _round_to_step(volume: float, step: float) -> float:
    if step <= 0:
        return round(volume, 2)
    return round(round(volume / step) * step, 8)
