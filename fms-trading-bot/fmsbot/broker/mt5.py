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


#: Rejection codes that have a specific, actionable cause.
_RETCODE_HELP = {
    10027: ("AutoTrading is switched OFF in the MetaTrader 5 terminal. "
            "Click the 'Algo Trading' button in the toolbar so it turns green "
            "(or Tools -> Options -> Expert Advisors -> Allow algorithmic trading). "
            "NOTHING will trade until you do."),
    10017: ("Trading is disabled for this SYMBOL on your account type. The "
            "symbol exists and streams prices, but the broker will not accept "
            "orders on it — remove it from SYMBOLS, or ask the broker to enable "
            "it. (Exness 24/7 variants like XAUUSD247m are often view-only on "
            "trial accounts.)"),
    10031: ("No connection to the trade server. The terminal lost its link to "
            "the broker — usually the internet dropped or the PC slept. New "
            "entries pause until it returns; open positions keep their stops, "
            "which sit on the broker's side and still work."),
    10018: "The market for this symbol is closed right now.",
    10019: "Not enough money in the account for this volume.",
    10014: "Invalid volume — below the symbol's minimum or off its step size.",
    10016: "Invalid stops — SL/TP too close to price for this symbol.",
    10030: ("Unsupported filling mode for this broker. The bot picks one per "
            "symbol; if this persists the symbol may be trade-disabled."),
    10006: "The broker rejected the request.",
}


def _explain(retcode) -> str:
    help_text = _RETCODE_HELP.get(retcode)
    return f"\n  -> {help_text}" if help_text else ""


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
    #: Preferred order-filling mode name, overridden by broker subclasses.
    #: Brokers differ here and a wrong mode is rejected as "Unsupported
    #: filling mode", so the actual mode is detected per symbol at runtime
    #: with this as the tie-breaker.
    preferred_filling = "IOC"

    #: Human label used in logs and /status.
    broker_name = "MT5"

    def __init__(self, login: int, password: str, server: str, path: str = ""):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.mt5 = None
        self._resolved: dict[str, str] = {}
        self._filling: dict[str, int] = {}

    # -- lifecycle ------------------------------------------------------

    def connect(self) -> None:
        mt5 = _mt5()
        info = None

        # Prefer attaching to a terminal the user already has open and logged
        # into: initialising with credentials can start a SEPARATE instance
        # whose settings (notably Algo Trading) are at defaults, so a terminal
        # the user carefully enabled appears to be ignored.
        args = (self.path,) if self.path else ()
        if mt5.initialize(*args):
            current = mt5.account_info()
            if current is not None and int(current.login) == int(self.login):
                info = current
                log.info("Attached to the running MT5 terminal (account %s).",
                         current.login)
            else:
                mt5.shutdown()

        if info is None:
            kwargs = {"login": self.login, "password": self.password,
                      "server": self.server}
            if not mt5.initialize(*args, **kwargs):
                err = mt5.last_error()
                hint = ""
                if "Authorization failed" in str(err) or "-6" in str(err):
                    hint = (
                        "\n  -> The terminal could not log in with the credentials in "
                        ".env.\n"
                        "     Note the bot normally ATTACHES to an MT5 terminal you "
                        "already have\n"
                        "     open and logged in, so it can run fine even when these "
                        "are wrong.\n"
                        "     Easiest fix: open MetaTrader 5, log into the account "
                        "manually,\n"
                        "     leave it running, and re-run this — it will attach.\n"
                        "     Otherwise check MT5_PASSWORD (the TRADING password, not "
                        "the investor\n"
                        "     one) and MT5_SERVER, and note that broker demo accounts "
                        "expire\n"
                        "     after a period of inactivity.")
                raise BrokerError(f"MT5 initialize failed: {err}{hint}")
            info = mt5.account_info()
            if info is None:
                raise BrokerError(f"MT5 login failed: {mt5.last_error()}")

        self.mt5 = mt5
        term = mt5.terminal_info()
        if term is not None and not getattr(term, "trade_allowed", True):
            log.error("ALGO TRADING IS OFF in the MT5 terminal — every order will be "
                      "rejected with 10027. Click the 'Algo Trading' toolbar button "
                      "so it turns green.")
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

    def is_demo(self):
        """MT5 reports 0 = demo, 1 = contest, 2 = real."""
        info = self._require().account_info()
        mode = getattr(info, "trade_mode", None) if info else None
        if mode is None:
            return None
        return int(mode) != 2

    # -- market data ---------------------------------------------------------

    def bars(self, symbol: str, timeframe: str, count: int) -> list[Bar]:
        mt5 = self._require()
        tf = _TIMEFRAMES.get(timeframe)
        if tf is None:
            raise BrokerError(f"Unsupported timeframe {timeframe}")
        symbol = self._resolve(symbol)
        if not mt5.symbol_select(symbol, True):
            raise BrokerError(
                f"Symbol {symbol} does not exist on this account.{self._suggest(symbol)}")
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        # A symbol added to Market Watch for the first time has no local
        # history yet; the terminal downloads it in the background.
        for wait in (2, 5, 8):
            if rates is not None and len(rates):
                break
            log.info("Waiting %ss for %s history to download...", wait, symbol)
            time.sleep(wait)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            err = mt5.last_error()
            hint = self._suggest(symbol)
            if "Call failed" in str(err):
                hint += (" If the bot is running, stop it before using the "
                         "analysis tools — two processes sharing one terminal "
                         "interfere: Stop-ScheduledTask -TaskName FMSTradingBot")
            raise BrokerError(f"No bars for {symbol}: {err}.{hint}")
        return [Bar(int(r["time"]), float(r["open"]), float(r["high"]),
                    float(r["low"]), float(r["close"])) for r in rates]

    def _filling_for(self, symbol: str) -> int:
        """Pick a filling mode the symbol actually allows.

        MT5 rejects orders with "Unsupported filling mode" when the broker
        does not permit the requested one, and brokers genuinely differ
        (Deriv usually needs FOK where Exness accepts IOC). The symbol's
        filling_mode field is a bitmask of what is allowed.
        """
        cached = self._filling.get(symbol)
        if cached is not None:
            return cached
        mt5 = self._require()
        allowed = getattr(mt5.symbol_info(symbol), "filling_mode", 0) or 0
        # bit 1 = FOK permitted, bit 2 = IOC permitted
        modes = []
        if self.preferred_filling == "FOK":
            modes = [(1, mt5.ORDER_FILLING_FOK), (2, mt5.ORDER_FILLING_IOC)]
        else:
            modes = [(2, mt5.ORDER_FILLING_IOC), (1, mt5.ORDER_FILLING_FOK)]
        chosen = None
        for bit, mode in modes:
            if allowed & bit:
                chosen = mode
                break
        if chosen is None:                     # broker reported nothing useful
            chosen = (mt5.ORDER_FILLING_FOK if self.preferred_filling == "FOK"
                      else mt5.ORDER_FILLING_IOC)
        self._filling[symbol] = chosen
        return chosen

    def _resolve(self, symbol: str) -> str:
        """Map a symbol to the broker's exact spelling, ignoring case only.

        Broker names are case-sensitive (Exness: EURUSDm), so a config typo
        like EURUSDM would otherwise fail even though the symbol exists.
        """
        cached = self._resolved.get(symbol)
        if cached:
            return cached
        mt5 = self._require()
        if mt5.symbol_info(symbol) is not None:
            self._resolved[symbol] = symbol
            return symbol
        for s in (mt5.symbols_get() or []):
            if s.name.lower() == symbol.lower():
                log.info("Symbol %s resolved to %s (case corrected).", symbol, s.name)
                self._resolved[symbol] = s.name
                return s.name
        return symbol

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
        symbol = self._resolve(symbol)
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
            "type_filling": self._filling_for(symbol),
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            retcode = getattr(result, "retcode", None)
            comment = getattr(result, "comment", mt5.last_error())
            raise BrokerError(
                f"Order rejected ({retcode}): {comment}{_explain(retcode)}")
        return OrderReceipt(
            ticket=int(result.order), symbol=symbol, side=side,
            volume=float(result.volume), price=float(result.price),
            sl=request["sl"], tp=request["tp"],
        )

    def value_per_price(self, symbol: str, volume: float) -> float:
        mt5 = self._require()
        info = mt5.symbol_info(self._resolve(symbol))
        if info is None or not info.trade_tick_size:
            return 0.0
        return (info.trade_tick_value / info.trade_tick_size) * float(volume)

    def spread(self, symbol: str) -> float:
        mt5 = self._require()
        tick = mt5.symbol_info_tick(self._resolve(symbol))
        if tick is None or not tick.ask or not tick.bid:
            return 0.0
        return float(tick.ask - tick.bid)

    def min_stop_distance(self, symbol: str) -> float:
        """Brokers refuse stops closer than trade_stops_level points (10011)."""
        mt5 = self._require()
        info = mt5.symbol_info(self._resolve(symbol))
        if info is None:
            return 0.0
        level = getattr(info, "trade_stops_level", 0) or 0
        point = getattr(info, "point", 0.0) or 0.0
        return float(level) * point

    def current_price(self, symbol: str, side: str) -> float:
        mt5 = self._require()
        symbol = self._resolve(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise BrokerError(f"No tick for {symbol}")
        return float(tick.ask if side == "buy" else tick.bid)

    def modify_position(self, ticket: int, sl: float, tp: float) -> None:
        mt5 = self._require()
        raw = mt5.positions_get(ticket=ticket)
        if not raw:
            raise BrokerError(f"Position {ticket} not found")
        info = mt5.symbol_info(raw[0].symbol)
        digits = info.digits if info else 5
        result = mt5.order_send({
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(ticket),
            "symbol": raw[0].symbol,
            "sl": round(sl, digits),
            "tp": round(tp, digits),
        })
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            retcode = getattr(result, "retcode", None)
            raise BrokerError(
                f"Could not adjust SL/TP on {ticket} ({retcode}): "
                f"{getattr(result, 'comment', mt5.last_error())}{_explain(retcode)}")

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
            "type_filling": self._filling_for(p.symbol),
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise BrokerError(f"Close rejected: {getattr(result, 'comment', mt5.last_error())}")
        return float(p.profit)

    # -- sizing ----------------------------------------------------------------

    def volume_from_lots(self, symbol: str, lots: float) -> float:
        """MT5 already trades in lots — just clamp to the symbol's rules."""
        mt5 = self._require()
        info = mt5.symbol_info(self._resolve(symbol))
        if info is None:
            raise BrokerError(f"symbol_info failed for {symbol}")
        step = info.volume_step or 0.01
        volume = max(info.volume_min, min(info.volume_max, float(lots)))
        volume = round(round(volume / step) * step, 8)
        if abs(volume - lots) > 1e-9:
            log.info("%s: lot size %.4f adjusted to %.4f (min %.2f, step %.2f).",
                     symbol, lots, volume, info.volume_min, step)
        return volume

    def volume_for_risk(self, symbol: str, sl_distance: float, risk_amount: float) -> float:
        mt5 = self._require()
        info = mt5.symbol_info(self._resolve(symbol))
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
