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
from dataclasses import replace
from typing import Optional

from .broker.base import BrokerError
from .config import Settings
from .session import RECONNECT_DELAYS, BrokerSession, build_sessions
from .strategy import EmaCrossStrategy
from .telegram import TelegramRemote

log = logging.getLogger("fmsbot.bot")

_TF_SECONDS = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800,
               "H1": 3600, "H4": 14400, "D1": 86400}


#: Order rejections that will not resolve by retrying: the account simply
#: cannot trade this instrument.
_PERMANENT_SYMBOL_ERRORS = (
    "10017",             # trade disabled for the symbol
    "trade disabled",
    "does not exist",
    "not offered",
    "market closed" ,    # not permanent, but retrying all session is pointless
)


def _is_permanent_symbol_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _PERMANENT_SYMBOL_ERRORS[:4])


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
        active = session.active_symbols()
        if not active:
            return
        failures = 0
        for symbol in active:
            try:
                self._check_symbol(session, symbol)
            except BrokerError as exc:
                failures += 1
                session.warn_symbol(symbol, exc)
        if failures and failures == len(active):
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
            session.last_block = f"{symbol} {signal.side} blocked — {reason}"
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

        # Measure the stop and target from the price we would fill at NOW, not
        # from the signal candle's close. On fast timeframes the drift between
        # them is a large share of the stop distance, which silently turns an
        # intended 1:1.5 reward:risk into something far worse.
        try:
            reference = broker.current_price(symbol, signal.side)
        except BrokerError:
            reference = price

        # A stop only a little wider than the spread is close to unwinnable:
        # the trade starts that far behind and must recover it before the
        # signal can pay anything. Silver and gold on M1 are the usual cases.
        sl_distance, tp_distance = signal.sl_distance, signal.tp_distance

        # Fixed cash exits, when configured, replace the ATR multiples.
        # money = distance * lots * value-per-price-unit.
        if self.s.tp_money or self.s.sl_money:
            try:
                per_price = broker.value_per_price(symbol, volume)
            except BrokerError:
                per_price = 0.0
            if per_price > 0:
                if self.s.sl_money:
                    sl_distance = self.s.sl_money / per_price
                if self.s.tp_money:
                    tp_distance = self.s.tp_money / per_price
            else:
                log.warning("[%s] %s: cannot convert money targets, "
                            "falling back to ATR distances", session.name, symbol)
        if self.s.max_spread_ratio > 0:
            try:
                spread = broker.spread(symbol)
            except BrokerError:
                spread = 0.0
            # A sudden widening usually means news or thin liquidity — the
            # worst moments to be opening short-duration trades.
            if spread > 0:
                history = session.spread_history.setdefault(symbol, [])
                if len(history) >= 20:
                    typical = sorted(history)[len(history) // 2]
                    if typical > 0 and spread > typical * self.s.spread_spike_factor:
                        reason = (f"spread {spread:.5f} is {spread/typical:.1f}x its "
                                  f"typical {typical:.5f} — abnormal conditions")
                        log.info("[%s] %s skipped: %s", session.name, symbol, reason)
                        session.last_block = f"{symbol} skipped — {reason}"
                        return
                history.append(spread)
                del history[:-100]

            if spread > 0 and sl_distance > 0:
                ratio = spread / sl_distance
                if ratio > self.s.max_spread_ratio:
                    reason = (f"spread {spread:.5f} is {ratio*100:.0f}% of the "
                              f"{sl_distance:.5f} stop (limit "
                              f"{self.s.max_spread_ratio*100:.0f}%)")
                    log.info("[%s] %s %s skipped: %s",
                             session.name, symbol, signal.side, reason)
                    session.last_block = f"{symbol} skipped — {reason}"
                    return

        # Brokers reject stops closer than their minimum distance (10011 "bad
        # stops"). Widen both legs together so the reward:risk is preserved.
        try:
            floor = broker.min_stop_distance(symbol)
        except BrokerError:
            floor = 0.0
        if floor > 0 and sl_distance < floor:
            scale = floor / sl_distance
            log.info("[%s] %s stop %.5f below broker minimum %.5f — widening "
                     "both legs x%.2f", session.name, symbol, sl_distance, floor, scale)
            sl_distance, tp_distance = floor, tp_distance * scale

        # The target has to beat the round trip, or the trade cannot pay even
        # when it is right. Costs are the spread plus any commission.
        if self.s.min_reward_cost_ratio > 0:
            try:
                per_price = broker.value_per_price(symbol, volume)
                cost = broker.spread(symbol) * per_price
            except BrokerError:
                per_price = cost = 0.0
            if cost > 0 and per_price > 0:
                reward = tp_distance * per_price
                if reward < cost * self.s.min_reward_cost_ratio:
                    reason = (f"target ${reward:.3f} is below {self.s.min_reward_cost_ratio}x "
                              f"the ${cost:.3f} cost of the trade")
                    log.info("[%s] %s skipped: %s", session.name, symbol, reason)
                    session.last_block = f"{symbol} skipped — {reason}"
                    return

        signal = replace(signal, sl_distance=sl_distance, tp_distance=tp_distance)

        if signal.side == "buy":
            sl, tp = reference - signal.sl_distance, reference + signal.tp_distance
        else:
            sl, tp = reference + signal.sl_distance, reference - signal.tp_distance

        try:
            receipt = broker.market_order(symbol, signal.side, volume, sl, tp,
                                          comment=signal.reason[:30])
        except BrokerError as exc:
            log.error("[%s] order failed %s %s: %s",
                      session.name, symbol, signal.side, exc)
            if _is_permanent_symbol_error(exc):
                # Retrying this every signal only spams the phone — the broker
                # will keep refusing until the account or symbol list changes.
                reason = str(exc).split("\n")[0]
                session.disabled_symbols[symbol] = reason
                remaining = session.active_symbols()
                log.warning("[%s] disabling %s for this session: %s",
                            session.name, symbol, reason)
                self.remote.broadcast(
                    f"🚫 {session.name}: {symbol} disabled — the broker refuses "
                    f"orders on it.\n{reason}\n"
                    f"Still trading: {', '.join(remaining) or 'nothing'}\n"
                    f"Fix it permanently with:  python pick_symbols.py --apply")
            else:
                self.remote.broadcast(f"❌ {session.name}: order failed "
                                      f"{symbol} {signal.side}: {exc}")
            return

        # A fill far from the quote means the market moved through us. Close
        # it immediately rather than run a trade whose terms we did not agree.
        slip = abs(receipt.price - reference)
        if (self.s.max_slippage_ratio > 0 and signal.sl_distance > 0
                and slip > signal.sl_distance * self.s.max_slippage_ratio):
            log.warning("[%s] %s slipped %.5f (%.0f%% of the stop) — closing it",
                        session.name, symbol, slip, 100*slip/signal.sl_distance)
            try:
                broker.close_position(receipt.ticket)
                self.remote.broadcast(
                    f"⚠️ [{session.name}] {symbol} filled {slip:.5f} away from the "
                    f"quote ({100*slip/signal.sl_distance:.0f}% of the stop) — "
                    f"closed immediately.")
                return
            except BrokerError as exc:
                log.error("[%s] could not close slipped position: %s",
                          session.name, exc)

        # If the fill still landed away from the reference, the stop and target
        # are no longer the distances the strategy asked for. Restore them.
        receipt = self._correct_exits(session, receipt, signal)

        risk.record_entry(symbol)
        session.known_tickets.add(receipt.ticket)
        msg = (f"📈 [{session.name}] OPENED {receipt.side.upper()} {receipt.symbol} "
               f"{receipt.volume} @ {receipt.price}\n"
               f"SL {receipt.sl} | TP {receipt.tp}\n"
               f"({signal.reason}; {sizing})")
        log.info(msg.replace("\n", " | "))
        self.remote.broadcast(msg)

    def _correct_exits(self, session: BrokerSession, receipt, signal):
        """Re-anchor SL/TP to the actual fill when slippage moved them.

        Fixed once in the wrong place, a 1:1.5 reward:risk can become 1:0.45,
        which destroys the strategy's edge regardless of how good the signals
        are. Only corrects when the drift is material, to avoid pointless
        modify requests.
        """
        fill = receipt.price
        if not fill:
            return receipt
        if signal.side == "buy":
            want_sl, want_tp = fill - signal.sl_distance, fill + signal.tp_distance
            actual_risk = fill - receipt.sl
        else:
            want_sl, want_tp = fill + signal.sl_distance, fill - signal.tp_distance
            actual_risk = receipt.sl - fill

        drift = abs(actual_risk - signal.sl_distance)
        if drift <= signal.sl_distance * 0.10:      # within 10% — leave it
            return receipt
        try:
            session.broker.modify_position(receipt.ticket, want_sl, want_tp)
        except BrokerError as exc:
            log.warning("[%s] could not re-anchor SL/TP on %s: %s",
                        session.name, receipt.symbol, exc)
            return receipt
        log.info("[%s] %s re-anchored to fill %.5f: SL %.5f TP %.5f "
                 "(was risking %.5f, wanted %.5f)",
                 session.name, receipt.symbol, fill, want_sl, want_tp,
                 actual_risk, signal.sl_distance)
        receipt.sl, receipt.tp = want_sl, want_tp
        return receipt

    def _notify_closed_positions(self, session: BrokerSession) -> None:
        """Detect positions closed broker-side, record the result, notify."""
        positions = session.broker.positions()
        current = {p.ticket for p in positions}
        vanished = session.known_tickets - current
        for ticket in vanished:
            session.known_tickets.discard(ticket)
            pnl = self._realised_pnl(session, ticket)
            equity = session.broker.equity()
            if pnl is None:
                self.remote.broadcast(
                    f"🏁 [{session.name}] position {ticket} closed. "
                    f"Equity: {equity:.2f}")
                continue
            mark = "✅" if pnl > 0 else "🔻"
            self.remote.broadcast(
                f"{mark} [{session.name}] position {ticket} closed "
                f"{pnl:+.2f}. Equity: {equity:.2f}")
            pause_msg = session.risk.record_result(pnl)
            if pause_msg:
                self.remote.broadcast(f"⏸ [{session.name}] {pause_msg}")
        session.known_tickets |= current
        self._protect_profits(session, positions)

    def _realised_pnl(self, session: BrokerSession, ticket: int) -> Optional[float]:
        """Profit of a just-closed position, from the broker's own history."""
        broker = session.broker
        mt5 = getattr(broker, "mt5", None)
        if mt5 is None:
            return None
        try:
            from datetime import datetime, timedelta
            deals = mt5.history_deals_get(datetime.now() - timedelta(hours=12),
                                          datetime.now() + timedelta(minutes=5))
            for d in deals or []:
                if int(getattr(d, "position_id", 0)) == int(ticket) and d.entry == 1:
                    return (float(d.profit) + float(d.commission) + float(d.swap))
        except Exception as exc:
            log.debug("Could not read realised PnL for %s: %s", ticket, exc)
        return None

    def _protect_profits(self, session: BrokerSession, positions) -> None:
        """Once a position is far enough ahead, pull its stop up to protect it.

        Only ever tightens: a stop is never moved further from price. With
        BREAKEVEN_LOCK_MONEY set the stop guarantees that much profit instead
        of merely removing the loss.
        """
        ladder = self.s.stages()
        if not ladder:
            return
        for p in positions:
            # Highest stage this position has earned, if any beyond the last
            # one already applied.
            reached = [i for i, (trigger, _) in enumerate(ladder)
                       if p.profit >= trigger]
            if not reached:
                continue
            stage_index = reached[-1]
            if session.stage_done.get(p.ticket, -1) >= stage_index:
                continue
            lock = ladder[stage_index][1]

            target_sl = p.entry_price
            if lock > 0:
                try:
                    per_price = session.broker.value_per_price(p.symbol, p.volume)
                except BrokerError:
                    per_price = 0.0
                if per_price > 0:
                    offset = lock / per_price
                    target_sl = (p.entry_price + offset if p.side == "buy"
                                 else p.entry_price - offset)

            already = ((p.sl >= target_sl) if p.side == "buy"
                       else (0 < p.sl <= target_sl))
            if p.sl and already:
                session.stage_done[p.ticket] = stage_index
                continue
            try:
                session.broker.modify_position(p.ticket, target_sl, p.tp)
            except BrokerError as exc:
                log.debug("[%s] protective stop move failed on %s: %s",
                          session.name, p.symbol, exc)
                continue
            session.stage_done[p.ticket] = stage_index
            step = f"stage {stage_index + 1}/{len(ladder)}"
            if lock > 0:
                log.info("[%s] %s #%s at +%.2f — %s: stop raised to lock +%.2f (%.5f)",
                         session.name, p.symbol, p.ticket, p.profit, step, lock, target_sl)
                self.remote.broadcast(
                    f"🔒 [{session.name}] {p.symbol} #{p.ticket} at {p.profit:+.2f} — "
                    f"{step}: stop raised to lock in +{lock:.2f}. Guaranteed profit.")
            else:
                log.info("[%s] %s #%s at +%.2f — %s: stop to break-even %.5f",
                         session.name, p.symbol, p.ticket, p.profit, step, target_sl)
                self.remote.broadcast(
                    f"🔒 [{session.name}] {p.symbol} #{p.ticket} at {p.profit:+.2f} — "
                    f"{step}: stop moved to break-even. This trade can no longer lose.")

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
                symbol_line = ", ".join(s.active_symbols()) or "none active"
                if s.disabled_symbols:
                    symbol_line += (f"\n  🚫 disabled: "
                                    f"{', '.join(s.disabled_symbols)}")
                lines.append(
                    f"\n• {s.name} ({s.cfg.kind})\n"
                    f"  {symbol_line}\n"
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

        if command == "why":
            lines = []
            if self.paused:
                lines.append("⏸ THE BOT IS PAUSED — send /resume.\n")
            for s in sessions:
                lines.append(f"— {s.name} —")
                if not s.connected:
                    lines.append("  OFFLINE (retrying)")
                    continue
                balance, equity = s.broker.balance(), s.broker.equity()
                positions = s.broker.positions()
                for line in s.risk.explain(balance, equity, len(positions),
                                           s.active_symbols()):
                    lines.append(f"  {line}")
                for symbol, reason in s.disabled_symbols.items():
                    lines.append(f"  🚫 {symbol} disabled: {reason[:90]}")
                # when was the last signal actually seen, per symbol
                for symbol in s.symbols:
                    seen = s.last_bar.get(symbol)
                    if seen:
                        age = (time.time() - seen) / 60.0
                        lines.append(f"  {symbol}: last candle checked "
                                     f"{age:.0f} min ago")
                    else:
                        lines.append(f"  {symbol}: no candles processed yet")
                blocked = s.last_block
                if blocked:
                    lines.append(f"  last block: {blocked}")
            lines.append(f"\nstrategy: EMA{self.s.ema_fast}/{self.s.ema_slow} "
                         f"on {self.s.timeframe}")
            lines.append("No signal = no trade. Quiet spells are normal.")
            return "\n".join(lines)

        if command in ("diag", "autotrade", "enable"):
            lines = []
            for s in self.sessions:
                if not s.connected:
                    lines.append(f"{s.name}: offline")
                    continue
                mt5 = getattr(s.broker, "mt5", None)
                if mt5 is None:
                    lines.append(f"{s.name} ({s.cfg.kind}): connected — "
                                 f"no terminal setting to check")
                    continue
                term = mt5.terminal_info()
                allowed = getattr(term, "trade_allowed", None) if term else None
                if allowed is False:
                    lines.append(
                        f"❌ {s.name}: ALGO TRADING OFF in the MT5 terminal.\n"
                        f"   Orders are rejected with 10027.\n"
                        f"   This cannot be switched on from the phone — it is a "
                        f"setting inside MetaTrader 5 on the PC:\n"
                        f"   Tools → Options → Expert Advisors → tick 'Allow "
                        f"algorithmic trading', or click the Algo Trading toolbar "
                        f"button until it is green.\n"
                        f"   Terminal in use: {getattr(term, 'path', '?')}")
                elif allowed:
                    lines.append(f"✅ {s.name}: algo trading enabled in the terminal")
                else:
                    lines.append(f"{s.name}: terminal state unknown")
            lines.append("\n(/resume only arms the BOT — this checks MetaTrader.)")
            return "\n".join(lines)

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
