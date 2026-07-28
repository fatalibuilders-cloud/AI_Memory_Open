"""Orchestrator: broker data -> strategy -> risk checks -> orders,
with the Telegram remote as the phone-side control panel.

Several accounts can run at once (ACTIVE_BROKERS=exness,deriv). Each is a
BrokerSession with its own broker, symbols and risk state; one Telegram
remote reports and controls all of them.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from .broker.base import BrokerError
from .config import Settings
from .session import RECONNECT_DELAYS, BrokerSession, build_sessions
from .strategy import EmaCrossStrategy
from .telegram import TelegramRemote

log = logging.getLogger("fmsbot.bot")

_TF_SECONDS = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800,
               "H1": 3600, "H4": 14400, "D1": 86400}


def sizing_label(settings) -> str:
    if settings.fixed_lot > 0:
        return f"{settings.fixed_lot} lot (fixed)"
    return f"{settings.risk_pct}% risk"


class TradingBot:
    def __init__(self, settings: Settings, sessions: Optional[list[BrokerSession]] = None):
        self.s = settings
        self.sessions = sessions if sessions is not None else build_sessions(settings)
        self.strategy = EmaCrossStrategy(settings)
        self.remote = TelegramRemote(
            settings.tg_token, settings.tg_password,
            settings.tg_state_file, self._on_command)
        self.paused = settings.start_paused
        self._stop = threading.Event()
        self._trade_lock = threading.Lock()

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        for session in self.sessions:
            session.connect()
        live = [s for s in self.sessions if s.connected]
        if not live:
            raise BrokerError("no account could be connected")

        self.remote.start()
        state = "PAUSED — send /resume from your phone to begin" if self.paused else "ACTIVE"
        log.info("Bot running (%s). %d account(s), timeframe %s.",
                 state, len(live), self.s.timeframe)
        for s in self.sessions:
            log.info("  %-10s %s  symbols: %s", s.name,
                     "connected" if s.connected else "OFFLINE", ", ".join(s.symbols))
        self._warn_interval_mode()

        lines = [f"🤖 Bot online ({state}) — {len(live)} account(s):"]
        for s in self.sessions:
            mark = "" if s.connected else "  [offline]"
            lines.append(f"• {s.name}: {', '.join(s.symbols)}{mark}")
        lines.append(f"{self.s.timeframe}, size {sizing_label(self.s)}")
        self.remote.broadcast("\n".join(lines))

        try:
            while not self._stop.is_set():
                for session in self.sessions:
                    try:
                        self._tick_session(session)
                    except BrokerError as exc:
                        log.warning("[%s] broker error: %s", session.name, exc)
                        self._schedule_reconnect(session)
                time.sleep(2)
        finally:
            self.remote.broadcast("🔌 Bot shutting down.")
            self.remote.stop()
            for session in self.sessions:
                session.disconnect()

    def stop(self) -> None:
        self._stop.set()

    def _warn_interval_mode(self) -> None:
        if self.s.entry_mode != "interval":
            return
        log.warning(
            "INTERVAL MODE: attempting a trade every %ss per symbol. Every trade "
            "pays the spread, so this bleeds money steadily even when the "
            "direction calls are right. Demo accounts only.",
            self.s.entry_interval_seconds)
        for name, value, needed in (
            ("COOLDOWN_SECONDS", self.s.cooldown_seconds, self.s.entry_interval_seconds),
            ("MAX_TRADES_PER_DAY", self.s.max_trades_per_day, 100),
            ("MAX_OPEN_POSITIONS", self.s.max_open_positions, 10),
        ):
            if value < needed:
                log.warning("  %s=%s will throttle interval mode "
                            "(raise to >= %s for the full rate).", name, value, needed)

    def _schedule_reconnect(self, session: BrokerSession) -> None:
        session.disconnect()
        delay = RECONNECT_DELAYS[min(session.reconnect_attempt,
                                     len(RECONNECT_DELAYS) - 1)]
        session.reconnect_attempt += 1
        log.info("[%s] reconnecting in %ds (attempt %d)...",
                 session.name, delay, session.reconnect_attempt)
        time.sleep(delay)
        if session.connect():
            log.info("[%s] reconnected.", session.name)
        elif session.reconnect_attempt == len(RECONNECT_DELAYS):
            self.remote.broadcast(f"⚠️ {session.name}: lost connection, still retrying.")

    # ------------------------------------------------------------------
    # trading loop
    # ------------------------------------------------------------------

    def _tick_session(self, session: BrokerSession) -> None:
        if not session.connected:
            if not session.connect():
                return
        self._notify_closed_positions(session)
        if self.paused:
            return
        failures = 0
        for symbol in session.symbols:
            try:
                self._check_symbol(session, symbol)
            except BrokerError as exc:
                failures += 1
                session.warn_symbol(symbol, exc)
        if failures and failures == len(session.symbols):
            raise BrokerError(f"all {failures} symbol(s) failing on {session.name}")

    def _check_symbol(self, session: BrokerSession, symbol: str) -> None:
        bars = session.broker.bars(
            symbol, self.s.timeframe,
            max(self.s.history_bars, self.strategy.min_bars() + 2))
        if len(bars) < 3:
            return
        closed = bars[:-1]                     # last bar is still forming

        if self.s.entry_mode == "interval":
            elapsed = time.time() - session.last_entry_attempt.get(symbol, 0.0)
            if elapsed < self.s.entry_interval_seconds:
                return
            session.last_entry_attempt[symbol] = time.time()
            signal = self.strategy.trend_signal(closed)
        else:
            newest = closed[-1].time
            if session.last_bar.get(symbol) == newest:
                return                         # no new closed bar yet
            session.last_bar[symbol] = newest
            signal = self.strategy.signal(closed)

        if signal is None:
            log.debug("[%s] %s: evaluated @ %.5f — no signal",
                      session.name, symbol, closed[-1].close)
            return

        with self._trade_lock:
            self._maybe_trade(session, symbol, signal, closed[-1].close)

    def _maybe_trade(self, session: BrokerSession, symbol: str,
                     signal, price: float) -> None:
        broker, risk = session.broker, session.risk
        balance = broker.balance()
        equity = broker.equity()
        all_pos = broker.positions()
        # broker may report its own spelling (EURUSDm vs a config typo EURUSDM)
        sym_pos = [p for p in all_pos if p.symbol.lower() == symbol.lower()]
        ok, reason = risk.can_enter(symbol, balance, equity, len(all_pos), len(sym_pos))
        if not ok:
            log.info("[%s] %s signal %s blocked: %s",
                     session.name, symbol, signal.side, reason)
            return

        risk_amount = risk.risk_amount(balance)
        try:
            if self.s.fixed_lot > 0:
                volume = broker.volume_from_lots(symbol, self.s.fixed_lot)
                sizing = f"fixed {self.s.fixed_lot} lot"
            else:
                volume = broker.volume_for_risk(symbol, signal.sl_distance, risk_amount)
                sizing = f"risking ~{risk_amount:.2f}"
        except BrokerError as exc:
            log.warning("[%s] sizing failed for %s: %s", session.name, symbol, exc)
            return

        if signal.side == "buy":
            sl, tp = price - signal.sl_distance, price + signal.tp_distance
        else:
            sl, tp = price + signal.sl_distance, price - signal.tp_distance

        try:
            receipt = broker.market_order(symbol, signal.side, volume, sl, tp,
                                          comment=signal.reason[:30])
        except BrokerError as exc:
            log.error("[%s] order failed %s %s: %s",
                      session.name, symbol, signal.side, exc)
            self.remote.broadcast(f"❌ {session.name}: order failed "
                                  f"{symbol} {signal.side}: {exc}")
            return

        risk.record_entry(symbol)
        session.known_tickets.add(receipt.ticket)
        msg = (f"📈 [{session.name}] OPENED {receipt.side.upper()} {receipt.symbol} "
               f"{receipt.volume} @ {receipt.price}\n"
               f"SL {receipt.sl} | TP {receipt.tp}\n"
               f"({signal.reason}; {sizing})")
        log.info(msg.replace("\n", " | "))
        self.remote.broadcast(msg)

    def _notify_closed_positions(self, session: BrokerSession) -> None:
        """Detect positions that hit SL/TP (closed broker-side) and notify."""
        current = {p.ticket for p in session.broker.positions()}
        vanished = session.known_tickets - current
        for ticket in vanished:
            session.known_tickets.discard(ticket)
            self.remote.broadcast(
                f"🏁 [{session.name}] position {ticket} closed (SL/TP or manual). "
                f"Equity: {session.broker.equity():.2f}")
        # adopt tickets opened manually so we also notify when they close
        session.known_tickets |= current

    # ------------------------------------------------------------------
    # phone commands
    # ------------------------------------------------------------------

    def _find_sessions(self, args: list[str]) -> tuple[list[BrokerSession], list[str]]:
        """If the first argument names an account, scope the command to it."""
        if args and args[0].lower() in {s.name for s in self.sessions}:
            name = args[0].lower()
            return [s for s in self.sessions if s.name == name], args[1:]
        return list(self.sessions), args

    def _on_command(self, chat_id: int, command: str, args: list[str]) -> Optional[str]:
        try:
            return self._dispatch(command, args)
        except BrokerError as exc:
            return f"Broker error: {exc}"

    def _dispatch(self, command: str, args: list[str]) -> Optional[str]:
        sessions, args = self._find_sessions(args)

        if command == "status":
            mode = "⏸ PAUSED" if self.paused else "▶️ ACTIVE"
            if self.s.entry_mode == "interval":
                mode += f" | ⚡ interval {self.s.entry_interval_seconds}s"
            lines = [f"{mode} | {self.s.timeframe} | {sizing_label(self.s)}"]
            for s in self.sessions:
                if not s.connected:
                    lines.append(f"\n• {s.name}: OFFLINE (retrying)")
                    continue
                balance, equity = s.broker.balance(), s.broker.equity()
                lines.append(
                    f"\n• {s.name} ({s.cfg.kind})\n"
                    f"  {', '.join(s.symbols)}\n"
                    f"  bal {balance:.2f} | eq {equity:.2f} | "
                    f"open {len(s.broker.positions())}\n"
                    f"  {s.risk.day_summary(balance, equity)}")
            return "\n".join(lines)

        if command == "balance":
            lines = []
            for s in sessions:
                if s.connected:
                    lines.append(f"{s.name}: bal {s.broker.balance():.2f} | "
                                 f"eq {s.broker.equity():.2f}")
                else:
                    lines.append(f"{s.name}: offline")
            return "\n".join(lines) or "No accounts."

        if command == "positions":
            lines = []
            for s in sessions:
                if not s.connected:
                    continue
                for p in s.broker.positions():
                    lines.append(f"[{s.name}] #{p.ticket} {p.side.upper()} {p.symbol} "
                                 f"{p.volume} @ {p.entry_price} → {p.profit:+.2f}")
            return "\n".join(lines) if lines else "No open positions."

        if command == "close":
            if not args or not args[0].isdigit():
                return ("Usage: /close <ticket>  or  /close <account> <ticket>\n"
                        f"Accounts: {', '.join(s.name for s in self.sessions)}")
            ticket = int(args[0])
            for s in sessions:
                if not s.connected:
                    continue
                if any(p.ticket == ticket for p in s.broker.positions()):
                    profit = s.broker.close_position(ticket)
                    return f"[{s.name}] closed #{ticket}, realized {profit:+.2f}."
            return f"Ticket {ticket} not found on {', '.join(s.name for s in sessions)}."

        if command == "closeall":
            total, count, touched = 0.0, 0, []
            for s in sessions:
                if not s.connected:
                    continue
                positions = s.broker.positions()
                for p in positions:
                    total += s.broker.close_position(p.ticket)
                    count += 1
                if positions:
                    touched.append(s.name)
            if not count:
                return "Nothing to close."
            return (f"Closed {count} position(s) on {', '.join(touched)}, "
                    f"realized {total:+.2f}.")

        if command == "resume":
            self.paused = False
            log.info("Auto-trading RESUMED from phone.")
            return f"▶️ Auto-trading ON for {len(self.sessions)} account(s)."

        if command == "pause":
            self.paused = True
            log.info("Auto-trading PAUSED from phone.")
            return "⏸ Auto-trading OFF (open positions untouched)."

        if command == "accounts":
            lines = []
            for s in self.sessions:
                lines.append(f"{'✅' if s.connected else '❌'} {s.name} "
                             f"({s.cfg.kind}): {', '.join(s.symbols)}")
            lines.append("\nScope a command to one account, e.g. "
                         "/positions exness, /closeall deriv")
            return "\n".join(lines)

        if command == "risk":
            if not args:
                return f"Risk per trade: {self.s.risk_pct}%. Usage: /risk 0.5"
            try:
                value = float(args[0])
            except ValueError:
                return "Usage: /risk 0.5"
            if not 0 < value <= 5:
                return "Risk must be between 0 and 5 (%)."
            self.s.risk_pct = value
            if self.s.fixed_lot > 0:
                return (f"Risk set to {value}%, but FIXED_LOT={self.s.fixed_lot} is "
                        f"active so every trade still uses {self.s.fixed_lot} lot. "
                        f"Set FIXED_LOT=0 in .env to size by risk.")
            return f"Risk per trade set to {value}%."

        return "Unknown command — /help"
