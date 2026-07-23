"""MetaTrader 5 adapter.

Requires the `MetaTrader5` pip package, which only works on Windows with a
running/installed MT5 terminal (use a cheap Windows VPS for 24/7 operation).
Almost every retail forex broker offers MT5 accounts covering forex pairs,
gold/silver (XAUUSD, XAGUSD) and stock CFDs — and every broker offers a
free DEMO account: test there first.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from .base import Bar, Broker, BrokerError, OrderReceipt, Position

log = logging.getLogger("fmsbot.mt5")

_TIMEFRAMES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 16385, "H4": 16388, "D1": 16408}


def _mt5():
    try:
        import MetaTrader5 as mt5  # noqa: PLC0415 — optional, Windows-only
    except ImportError as exc:
        raise BrokerError(
            "MetaTrader5 package not available. It requires Windows + an MT5 "
            "terminal installed (pip install MetaTrader5). Run this bot on a "
            "Windows PC or VPS."
        ) from exc
    return mt5


class MT5Broker(Broker):
    def __init__(self, login: int, password: str, server: str, path: str = ""):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.mt5 = None

    # -- lifecycle ------------------------------------------------------

    def connect(self) -> None:
        mt5 = _mt5()
        kwargs = {"login": self.login, "password": self.password, "server": self.server}
        args = (self.path,) if self.path else ()
        if not mt5.initialize(*args, **kwargs):
            raise BrokerError(f"MT5 initialize failed: {mt5.last_error()}")
        info = mt5.account_info()
        if info is None:
            raise BrokerError(f"MT5 login failed: {mt5.last_error()}")
        self.mt5 = mt5
        # wait until the terminal is actually connected to the trade server —
        # market-data calls fail with 'Terminal: Call failed' before that
        deadline = time.time() + 20
        while time.time() < deadline:
            ti = mt5.terminal_info()
            if ti is not None and ti.connected:
                break
            time.sleep(0.5)
        log.info("MT5 connected: account %s (%s), balance %.2f %s, leverage 1:%s%s",
                 info.login, self.server, info.balance, info.currency, info.leverage,
                 " [DEMO]" if getattr(info, "trade_mode", 1) == 0 else "")

    def disconnect(self) -> None:
        if self.mt5:
            self.mt5.shutdown()
            self.mt5 = None

    def _require(self):
        if self.mt5 is None:
            raise BrokerError("Not connected to MT5")
        return self.mt5

    # -- account ----------------------------------------------------------

    def balance(self) -> float:
        info = self._require().account_info()
        if info is None:
            raise BrokerError("account_info failed")
        return float(info.balance)

    def equity(self) -> float:
        info = self._require().account_info()
        if info is None:
            raise BrokerError("account_info failed")
        return float(info.equity)

    # -- market data ---------------------------------------------------------

    def bars(self, symbol: str, timeframe: str, count: int) -> list[Bar]:
        mt5 = self._require()
        tf = _TIMEFRAMES.get(timeframe)
        if tf is None:
            raise BrokerError(f"Unsupported timeframe {timeframe}")
        if not mt5.symbol_select(symbol, True):
            raise BrokerError(
                f"Symbol {symbol} does not exist on this account.{self._suggest(symbol)}")
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            # right after (re)connect the terminal may still be syncing history
            time.sleep(3)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            raise BrokerError(
                f"No bars for {symbol}: {mt5.last_error()}.{self._suggest(symbol)}")
        return [Bar(int(r["time"]), float(r["open"]), float(r["high"]),
                    float(r["low"]), float(r["close"])) for r in rates]

    def _suggest(self, symbol: str) -> str:
        """Name near-miss symbols (brokers often add suffixes, e.g. EURUSDm)."""
        try:
            base = symbol[:6]
            matches = [s.name for s in (self.mt5.symbols_get(f"*{base}*") or [])]
        except Exception:
            return ""
        matches = [m for m in matches if m != symbol][:6]
        if matches:
            return (f" This broker offers similar symbols: {', '.join(matches)} — "
                    f"update SYMBOLS in .env accordingly.")
        return ""

    # -- trading ----------------------------------------------------------------

    def market_order(self, symbol: str, side: str, volume: float,
                     sl: float, tp: float, comment: str = "") -> OrderReceipt:
        mt5 = self._require()
        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)
        if tick is None or info is None:
            raise BrokerError(f"No market data for {symbol}")
        buy = side == "buy"
        price = tick.ask if buy else tick.bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": mt5.ORDER_TYPE_BUY if buy else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": round(sl, info.digits),
            "tp": round(tp, info.digits),
            "deviation": 20,
            "magic": 984512,
            "comment": (comment or "fmsbot")[:31],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise BrokerError(
                f"Order rejected ({getattr(result, 'retcode', '?')}): "
                f"{getattr(result, 'comment', mt5.last_error())}")
        return OrderReceipt(
            ticket=int(result.order), symbol=symbol, side=side,
            volume=float(result.volume), price=float(result.price),
            sl=request["sl"], tp=request["tp"],
        )

    def positions(self, symbol: Optional[str] = None) -> list[Position]:
        mt5 = self._require()
        raw = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        out = []
        for p in raw or []:
            out.append(Position(
                ticket=int(p.ticket), symbol=p.symbol,
                side="buy" if p.type == 0 else "sell",
                volume=float(p.volume), entry_price=float(p.price_open),
                sl=float(p.sl), tp=float(p.tp), profit=float(p.profit),
            ))
        return out

    def close_position(self, ticket: int) -> float:
        mt5 = self._require()
        raw = mt5.positions_get(ticket=ticket)
        if not raw:
            raise BrokerError(f"Position {ticket} not found")
        p = raw[0]
        tick = mt5.symbol_info_tick(p.symbol)
        buy_to_close = p.type == 1  # closing a sell = buy
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": p.symbol,
            "volume": float(p.volume),
            "type": mt5.ORDER_TYPE_BUY if buy_to_close else mt5.ORDER_TYPE_SELL,
            "position": int(ticket),
            "price": tick.ask if buy_to_close else tick.bid,
            "deviation": 20,
            "magic": 984512,
            "comment": "fmsbot close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise BrokerError(f"Close rejected: {getattr(result, 'comment', mt5.last_error())}")
        return float(p.profit)

    # -- sizing ----------------------------------------------------------------

    def volume_for_risk(self, symbol: str, sl_distance: float, risk_amount: float) -> float:
        mt5 = self._require()
        info = mt5.symbol_info(symbol)
        if info is None:
            raise BrokerError(f"symbol_info failed for {symbol}")
        # Money moved per 1.0 lot per 1.0 of price movement:
        if info.trade_tick_size <= 0 or info.trade_tick_value <= 0 or sl_distance <= 0:
            raise BrokerError(f"Cannot size position for {symbol}")
        per_unit = info.trade_tick_value / info.trade_tick_size
        volume = risk_amount / (sl_distance * per_unit)
        step = info.volume_step or 0.01
        volume = max(info.volume_min, min(info.volume_max, volume))
        volume = round(volume / step) * step
        return round(max(volume, info.volume_min), 8)
