"""Orchestrator: broker data -> strategy -> risk checks -> orders,
with the Telegram remote as the phone-side control panel."""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from .broker.base import Broker, BrokerError
from .config import Settings
from .risk import RiskManager
from .strategy import EmaCrossStrategy
from .telegram import TelegramRemote

log = logging.getLogger("fmsbot.bot")

_TF_SECONDS = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800,
               "H1": 3600, "H4": 14400, "D1": 86400}


class TradingBot:
    def __init__(self, settings: Settings, broker: Broker):
        self.s = settings
        self.broker = broker
        self.strategy = EmaCrossStrategy(settings)
        self.risk = RiskManager(settings)
        self.remote = TelegramRemote(
            settings.tg_token, settings.tg_password,
            settings.tg_state_file, self._on_command)
        self.paused = settings.start_paused
        self._stop = threading.Event()
        self._last_bar: dict[str, int] = {}       # symbol -> last processed bar time
        self._symbol_warned: dict[str, float] = {}  # symbol -> last warning ts
        self._known_tickets: set[int] = set()

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        self.broker.connect()
        self.remote.start()
        state = "PAUSED — send /resume from your phone to begin" if self.paused else "ACTIVE"
        log.info("Bot running (%s). Symbols: %s, timeframe %s.",
                 state, ", ".join(self.s.symbols), self.s.timeframe)
        self.remote.broadcast(
            f"🤖 Bot online ({state}).\nSymbols: {', '.join(self.s.symbols)} "
            f"@ {self.s.timeframe}, risk {self.s.risk_pct}%/trade.")
        try:
            while not self._stop.is_set():
                try:
                    self._tick()
                except BrokerError as exc:
                    log.warning("Broker error: %s — reconnecting in 10s", exc)
                    self._reconnect()
                time.sleep(2)
        finally:
            self.remote.broadcast("🔌 Bot shutting down.")
            self.remote.stop()
            self.broker.disconnect()

    def stop(self) -> None:
        self._stop.set()

    def _reconnect(self) -> None:
        try:
            self.broker.disconnect()
        except Exception:
            pass
        for delay in (10, 20, 40, 60):
            if self._stop.is_set():
                return
            time.sleep(delay)
            try:
                self.broker.connect()
                log.info("Reconnected to broker.")
                return
            except BrokerError as exc:
                log.warning("Reconnect failed: %s", exc)
        self.remote.broadcast("⚠️ Lost broker connection and could not reconnect. Retrying...")

    # ------------------------------------------------------------------
    # trading loop
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        self._notify_closed_positions()
        if self.paused:
            return
        failures = 0
        for symbol in self.s.symbols:
            try:
                self._check_symbol(symbol)
            except BrokerError as exc:
                # One unavailable symbol (history not downloaded, market for
                # that instrument closed) must not stop the others or force a
                # reconnect — only a total failure means the session is dead.
                failures += 1
                self._warn_symbol(symbol, exc)
        if failures and failures == len(self.s.symbols):
            raise BrokerError(f"all {failures} symbol(s) failing")

    def _warn_symbol(self, symbol: str, exc: Exception) -> None:
        """Warn about a broken symbol at most once every 15 minutes."""
        now = time.time()
        if now - self._symbol_warned.get(symbol, 0.0) < 900:
            return
        self._symbol_warned[symbol] = now
        log.warning("%s unavailable, skipping it: %s", symbol, exc)

    def _check_symbol(self, symbol: str) -> None:
        bars = self.broker.bars(symbol, self.s.timeframe,
                                max(self.s.history_bars, self.strategy.min_bars() + 2))
        if len(bars) < 3:
            return
        closed = bars[:-1]                     # last bar is still forming
        newest = closed[-1].time
        if self._last_bar.get(symbol) == newest:
            return                             # no new closed bar yet
        self._last_bar[symbol] = newest

        signal = self.strategy.signal(closed)
        if signal is None:
            log.debug("%s: candle closed @ %.5f — no signal", symbol, closed[-1].close)
            return

        balance = self.broker.balance()
        equity = self.broker.equity()
        all_pos = self.broker.positions()
        # broker may report its own spelling (EURUSDm vs a config typo EURUSDM)
        sym_pos = [p for p in all_pos if p.symbol.lower() == symbol.lower()]
        ok, reason = self.risk.can_enter(symbol, balance, equity,
                                         len(all_pos), len(sym_pos))
        if not ok:
            log.info("%s signal %s blocked: %s", symbol, signal.side, reason)
            return

        risk_amount = self.risk.risk_amount(balance)
        try:
            volume = self.broker.volume_for_risk(symbol, signal.sl_distance, risk_amount)
        except BrokerError as exc:
            log.warning("Sizing failed for %s: %s", symbol, exc)
            return

        price = closed[-1].close
        if signal.side == "buy":
            sl, tp = price - signal.sl_distance, price + signal.tp_distance
        else:
            sl, tp = price + signal.sl_distance, price - signal.tp_distance

        try:
            receipt = self.broker.market_order(symbol, signal.side, volume, sl, tp,
                                               comment=signal.reason[:30])
        except BrokerError as exc:
            log.error("Order failed %s %s: %s", symbol, signal.side, exc)
            self.remote.broadcast(f"❌ Order failed {symbol} {signal.side}: {exc}")
            return

        self.risk.record_entry(symbol)
        self._known_tickets.add(receipt.ticket)
        msg = (f"📈 OPENED {receipt.side.upper()} {receipt.symbol} "
               f"{receipt.volume} @ {receipt.price}\n"
               f"SL {receipt.sl} | TP {receipt.tp}\n"
               f"({signal.reason}; risking ~{risk_amount:.2f})")
        log.info(msg.replace("\n", " | "))
        self.remote.broadcast(msg)

    def _notify_closed_positions(self) -> None:
        """Detect positions that hit SL/TP (closed broker-side) and notify."""
        current = {p.ticket for p in self.broker.positions()}
        vanished = self._known_tickets - current
        for ticket in vanished:
            self._known_tickets.discard(ticket)
            self.remote.broadcast(f"🏁 Position {ticket} closed (SL/TP or manual). "
                                  f"Equity: {self.broker.equity():.2f}")
        # adopt tickets opened manually so we also notify when they close
        self._known_tickets |= current

    # ------------------------------------------------------------------
    # phone commands
    # ------------------------------------------------------------------

    def _on_command(self, chat_id: int, command: str, args: list[str]) -> Optional[str]:
        try:
            return self._dispatch(command, args)
        except BrokerError as exc:
            return f"Broker error: {exc}"

    def _dispatch(self, command: str, args: list[str]) -> Optional[str]:
        if command == "status":
            balance, equity = self.broker.balance(), self.broker.equity()
            mode = "⏸ PAUSED" if self.paused else "▶️ ACTIVE"
            return (f"{mode} | {', '.join(self.s.symbols)} @ {self.s.timeframe}\n"
                    f"Balance {balance:.2f} | Equity {equity:.2f}\n"
                    f"Open positions: {len(self.broker.positions())}\n"
                    f"Risk/trade: {self.s.risk_pct}% | {self.risk.day_summary(balance, equity)}")
        if command == "balance":
            return f"Balance: {self.broker.balance():.2f}\nEquity: {self.broker.equity():.2f}"
        if command == "positions":
            pos = self.broker.positions()
            if not pos:
                return "No open positions."
            lines = [f"#{p.ticket} {p.side.upper()} {p.symbol} {p.volume} "
                     f"@ {p.entry_price} → PnL {p.profit:+.2f}" for p in pos]
            return "\n".join(lines)
        if command == "close":
            if not args or not args[0].isdigit():
                return "Usage: /close <ticket>"
            profit = self.broker.close_position(int(args[0]))
            return f"Closed #{args[0]}, realized {profit:+.2f}."
        if command == "closeall":
            pos = self.broker.positions()
            if not pos:
                return "Nothing to close."
            total = 0.0
            for p in pos:
                total += self.broker.close_position(p.ticket)
            return f"Closed {len(pos)} position(s), realized {total:+.2f}."
        if command == "resume":
            self.paused = False
            log.info("Auto-trading RESUMED from phone.")
            return "▶️ Auto-trading ON."
        if command == "pause":
            self.paused = True
            log.info("Auto-trading PAUSED from phone.")
            return "⏸ Auto-trading OFF (open positions untouched)."
        if command == "risk":
            if not args:
                return f"Risk per trade: {self.s.risk_pct}%. Usage: /risk 0.5"
            try:
                value = float(args[0])
            except ValueError:
                return "Usage: /risk 0.5"
            if not 0 < value <= 5:
                return "Risk must be between 0 and 5 (%.)"
            self.s.risk_pct = value
            return f"Risk per trade set to {value}%."
        return "Unknown command — /help"
