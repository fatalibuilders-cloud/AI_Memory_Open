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
from . import evidence
from .config import Settings
from .indicators import atr
from .session import RECONNECT_DELAYS, BrokerSession, _Pending, build_sessions
from .live import build_strategy, strategy_name
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


#: The link to the broker is down — never keep firing orders into that.
_CONNECTION_ERRORS = ("10031", "absence of network connection",
                      "no connection", "not connected", "connection lost")


def _is_connection_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _CONNECTION_ERRORS)


def sizing_label(settings) -> str:
    if settings.fixed_lot > 0:
        return f"{settings.fixed_lot} lot (fixed)"
    return f"{settings.risk_pct}% risk"


class TradingBot:
    def __init__(self, settings: Settings, sessions: Optional[list[BrokerSession]] = None):
        self.s = settings
        self.strategy = build_strategy(settings)
        self.sessions = (sessions if sessions is not None
                         else build_sessions(settings,
                                             strategy_name(self.strategy)))
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
        self._check_pending(session)
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
        cfg = self.s.for_symbol(symbol)
        bars = session.broker.bars(
            symbol, self.s.timeframe,
            max(self.s.history_bars, self.strategy.min_bars() + 2))
        if len(bars) < 3:
            return
        closed = bars[:-1]                     # last bar is still forming

        if self.s.entry_mode == "interval":
            elapsed = time.time() - session.last_entry_attempt.get(symbol, 0.0)
            interval = cfg.entry_interval_seconds
            if session.pace:
                interval = session.pace.effective_interval(
                    cfg.entry_interval_seconds, len(session.active_symbols()),
                    session.risk.stats.entry_times)
            if elapsed < interval:
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

        # Optionally require the market to prove the signal first: a setup
        # that reverses immediately is exactly the one that goes straight to
        # the stop without ever being far enough ahead to protect.
        if cfg.entry_confirm_money > 0:
            session.pending[symbol] = _Pending(
                side=signal.side, signal=signal,
                price_at_signal=closed[-1].close,
                expires=time.time() + cfg.entry_confirm_seconds)
            log.debug("[%s] %s %s pending confirmation",
                      session.name, symbol, signal.side)
            return

        with self._trade_lock:
            self._maybe_trade(session, symbol, signal, closed[-1].close)

    def _check_pending(self, session: BrokerSession) -> None:
        """Take pending signals that the market has since confirmed."""
        if not session.pending:
            return
        now = time.time()
        for symbol, pending in list(session.pending.items()):
            if now > pending.expires:
                del session.pending[symbol]
                log.debug("[%s] %s confirmation expired", session.name, symbol)
                continue
            cfg = self.s.for_symbol(symbol)
            try:
                price = session.broker.current_price(symbol, pending.side)
                per_price = session.broker.value_per_price(
                    symbol, cfg.fixed_lot or 0.01)
            except BrokerError:
                continue
            if per_price <= 0:
                continue
            moved = ((price - pending.price_at_signal) if pending.side == "buy"
                     else (pending.price_at_signal - price)) * per_price
            # Tolerance: price subtraction loses precision, so an exact
            # one-pip move can compute a hair under the threshold.
            if moved < cfg.entry_confirm_money - 1e-6:
                continue
            del session.pending[symbol]
            log.info("[%s] %s confirmed: moved %+.2f in %ss — entering",
                     session.name, symbol, moved,
                     int(cfg.entry_confirm_seconds - (pending.expires - now)))
            with self._trade_lock:
                self._maybe_trade(session, symbol, pending.signal, price)

    def _maybe_trade(self, session: BrokerSession, symbol: str,
                     signal, price: float) -> None:
        broker, risk = session.broker, session.risk
        # Gold, Bitcoin and forex differ by orders of magnitude in spread and
        # volatility, so a symbol may override the shared tuning.
        cfg = self.s.for_symbol(symbol)
        balance = broker.balance()
        equity = broker.equity()
        all_pos = broker.positions()
        # broker may report its own spelling (EURUSDm vs a config typo EURUSDM)
        sym_pos = [p for p in all_pos if p.symbol.lower() == symbol.lower()]
        blocked = self._evidence_blocks(session)
        if blocked:
            log.info("[%s] %s signal %s blocked: %s",
                     session.name, symbol, signal.side, blocked)
            session.last_block = f"{symbol} {signal.side} blocked — {blocked}"
            if session.pace:
                session.pace.record_block(blocked)
            return

        ok, reason = risk.can_enter(symbol, balance, equity, len(all_pos), len(sym_pos))
        if not ok:
            log.info("[%s] %s signal %s blocked: %s",
                     session.name, symbol, signal.side, reason)
            session.last_block = f"{symbol} {signal.side} blocked — {reason}"
            if session.pace:
                session.pace.record_block(reason)
            return

        risk_amount = risk.risk_amount(balance)
        try:
            if cfg.fixed_lot > 0:
                volume = broker.volume_from_lots(symbol, cfg.fixed_lot)
                sizing = f"fixed {cfg.fixed_lot} lot"
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
        if cfg.tp_money or cfg.sl_money:
            try:
                per_price = broker.value_per_price(symbol, volume)
            except BrokerError:
                per_price = 0.0
            if per_price > 0:
                if cfg.sl_money:
                    sl_distance = cfg.sl_money / per_price
                if cfg.tp_money:
                    tp_distance = cfg.tp_money / per_price
            else:
                log.warning("[%s] %s: cannot convert money targets, "
                            "falling back to ATR distances", session.name, symbol)
        if cfg.max_spread_ratio > 0:
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
                    if typical > 0 and spread > typical * cfg.spread_spike_factor:
                        reason = (f"spread {spread:.5f} is {spread/typical:.1f}x its "
                                  f"typical {typical:.5f} — abnormal conditions")
                        log.info("[%s] %s skipped: %s", session.name, symbol, reason)
                        session.last_block = f"{symbol} skipped — {reason}"
                        if session.pace:
                            session.pace.record_block(reason)
                        return
                history.append(spread)
                del history[:-100]

            if spread > 0 and sl_distance > 0:
                ratio = spread / sl_distance
                if ratio > cfg.max_spread_ratio:
                    reason = (f"spread {spread:.5f} is {ratio*100:.0f}% of the "
                              f"{sl_distance:.5f} stop (limit "
                              f"{cfg.max_spread_ratio*100:.0f}%)")
                    log.info("[%s] %s %s skipped: %s",
                             session.name, symbol, signal.side, reason)
                    session.last_block = f"{symbol} skipped — {reason}"
                    if session.pace:
                        session.pace.record_block(reason)
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
        if cfg.min_reward_cost_ratio > 0:
            try:
                per_price = broker.value_per_price(symbol, volume)
                cost = broker.spread(symbol) * per_price
            except BrokerError:
                per_price = cost = 0.0
            if cost > 0 and per_price > 0:
                reward = tp_distance * per_price
                if reward < cost * cfg.min_reward_cost_ratio:
                    reason = (f"target ${reward:.3f} is below {cfg.min_reward_cost_ratio}x "
                              f"the ${cost:.3f} cost of the trade")
                    log.info("[%s] %s skipped: %s", session.name, symbol, reason)
                    session.last_block = f"{symbol} skipped — {reason}"
                    if session.pace:
                        session.pace.record_block(reason)
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
            if _is_connection_error(exc):
                # The terminal lost the broker. Entering blind is exactly what
                # the emergency controls exist to prevent, so stand down and
                # let the reconnect logic re-establish first.
                session.connection_failures += 1
                if session.connection_failures in (1, 10):
                    self.remote.broadcast(
                        f"📡 {session.name}: no connection to the trade server — "
                        f"new entries paused until it returns. Open positions keep "
                        f"their broker-side stops.")
                raise BrokerError(f"trade server unreachable: {exc}")
            session.connection_failures = 0
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
        if (cfg.max_slippage_ratio > 0 and signal.sl_distance > 0
                and slip > signal.sl_distance * cfg.max_slippage_ratio):
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
            if session.evidence:
                session.evidence.record(pnl)
                self._announce_verdict(session)
        session.known_tickets |= current
        # let go of state for positions that no longer exist
        for ticket in vanished:
            session.stage_done.pop(ticket, None)
            session.peak_price.pop(ticket, None)
        self._check_money_scale(session, positions)
        positions = self._enforce_loss_cap(session, positions)
        self._protect_profits(session, positions)
        self._trail_stops(session, positions)
        if session.pace:
            report = session.pace.shortfall_report(
                session.risk.stats.entry_times, len(session.active_symbols()))
            if report:
                log.info("[%s] behind pace:\n%s", session.name, report)
                self.remote.broadcast(f"🐢 [{session.name}] behind pace\n\n{report}")

    def _ladder_for(self, session: BrokerSession, cfg, p) -> list:
        """This position's protection rungs, in cash.

        With PROFIT_STAGES_PCT the rungs are a share of the trade's own
        take-profit, which is the only definition that cannot be mis-scaled:
        it is measured against what this trade was aiming at, so it adapts
        to the instrument, the volatility and the lot size at once.
        """
        if not cfg.profit_stages_pct:
            return cfg.stages()
        if not p.tp or not p.entry_price:
            return cfg.stages()
        try:
            per_price = session.broker.value_per_price(p.symbol, p.volume)
        except BrokerError:
            return cfg.stages()
        target = abs(p.tp - p.entry_price) * per_price
        if target <= 0:
            return cfg.stages()
        return sorted((target * trigger / 100.0, target * lock / 100.0)
                      for trigger, lock in cfg.profit_stages_pct)

    def _warn_if_ladder_caps(self, session: BrokerSession, ladder, p) -> None:
        """Say so when the ladder is about to throw the trade away.

        Once the last rung is applied the stop stops moving, so the trade
        can never make more than that rung's lock. If the lock is a small
        fraction of the target, every winner is converted into that
        fraction -- a position reaching +2.20 closing at +0.10 is the
        ladder working exactly as configured, and it is a losing structure
        because the losses are still full size.
        """
        if session.ladder_warned:
            return
        top_lock = ladder[-1][1]
        try:
            per_price = session.broker.value_per_price(p.symbol, p.volume)
        except BrokerError:
            return
        target = abs(p.tp - p.entry_price) * per_price if p.tp else 0.0
        if target <= 0 or top_lock <= 0 or top_lock >= target * 0.2:
            return
        session.ladder_warned = True
        log.warning("[%s] %s ladder caps every winner at %.2f against a %.2f "
                    "target", session.name, p.symbol, top_lock, target)
        self.remote.broadcast(
            f"⚠️ [{session.name}] YOUR LADDER IS CAPPING EVERY WINNER.\n\n"
            f"{p.symbol} is aiming at {target:.2f}, but the last rung locks "
            f"{top_lock:.2f} and the stop never moves again. So a trade that "
            f"reaches {target:.2f} still closes at {top_lock:.2f} — you keep "
            f"{top_lock/target*100:.0f}% of every winner while the losses stay "
            f"full size.\n\n"
            f"Fix it with rungs measured against the target instead of in "
            f"fixed dollars:\n"
            f"  PROFIT_STAGES_PCT=50:0,75:50\n"
            f"and clear PROFIT_STAGES. Or set TRAIL_ATR_MULT so the stop "
            f"keeps following.")

    def _enforce_loss_cap(self, session: BrokerSession, positions) -> list:
        """Close anything losing more than the cap, without waiting.

        A stop loss is the broker's promise, and it can fail: placed at the
        wrong distance, rejected and silently lost, or gapped straight
        through. This does not trust it. It is a backstop, not a
        replacement -- between two polls the price can still run further,
        so the number here is a ceiling on what the bot will tolerate, not
        a guarantee of the exact loss.
        """
        cap = self.s.max_loss_per_trade
        if cap <= 0:
            return positions
        survivors = []
        for p in positions:
            limit = self.s.for_symbol(p.symbol).max_loss_per_trade
            if limit <= 0 or p.profit > -limit:
                survivors.append(p)
                continue
            try:
                realised = session.broker.close_position(p.ticket)
            except BrokerError as exc:
                log.error("[%s] %s #%s is at %.2f, past the %.2f cap, and would "
                          "not close: %s", session.name, p.symbol, p.ticket,
                          p.profit, limit, exc)
                self.remote.broadcast(
                    f"⚠️ [{session.name}] {p.symbol} #{p.ticket} is at "
                    f"{p.profit:.2f}, past the {limit:.2f} loss cap, and the "
                    f"broker refused to close it: {exc}")
                survivors.append(p)
                continue
            log.warning("[%s] %s #%s closed at %.2f by the loss cap (%.2f)",
                        session.name, p.symbol, p.ticket, realised, limit)
            self.remote.broadcast(
                f"🚨 [{session.name}] {p.symbol} #{p.ticket} closed at "
                f"{realised:+.2f} — past the {limit:.2f} loss cap.\n"
                f"The stop did not hold it. Check /diag.")
        return survivors

    def _check_money_scale(self, session: BrokerSession, positions) -> None:
        """Warn when the money settings are the wrong size for the account.

        Money settings are in whatever units the broker reports, and those
        are not always dollars: on an Exness cent account balance, equity
        and profit are all in cents, so a 0.10 rung means a tenth of a cent
        and every trade clears it instantly. The symptom is a position
        showing +2000 triggering a stage meant for +0.10, which is
        protection in name only.
        """
        if session.scale_checked or not positions:
            return
        ladder = self.s.stages()
        top = max((trigger for trigger, _ in ladder), default=0.0)
        if top <= 0:
            session.scale_checked = True
            return
        worst = max(abs(p.profit) for p in positions)
        if worst < top * 100:
            return
        session.scale_checked = True
        try:
            currency = session.broker.account_currency()
        except BrokerError:
            currency = ""
        log.warning("[%s] money settings look mis-scaled: a position is at "
                    "%.2f %s while the top rung is %.2f",
                    session.name, worst, currency, top)
        self.remote.broadcast(
            f"⚠️ [{session.name}] YOUR MONEY SETTINGS ARE THE WRONG SIZE.\n\n"
            f"A position reached {worst:.2f} {currency} while the highest "
            f"protection rung is {top:.2f}. Every trade clears that instantly, "
            f"so the stop jumps to break-even at once and the protection is "
            f"doing nothing.\n\n"
            f"If this is an Exness CENT account, the broker reports cents, not "
            f"dollars: your {top:.2f} rung is {top/100:.4f} of a dollar. "
            f"Multiply every money setting by 100, or move to a standard "
            f"account.\n\n"
            f"Run tune_symbols.py to re-derive them from this account.")

    def _trail_stops(self, session: BrokerSession, positions) -> None:
        """Chandelier exit: follow the best price the trade has reached.

        The cash ladder locks a fixed amount and then stops helping, so a
        move that runs far gives back everything above the last rung. This
        keeps the stop a fixed volatility distance behind the trade's own
        high-water mark.

        Two properties matter and both are easy to get wrong. It measures
        from the PEAK, not the current price, or the stop would follow the
        trade back down. And it only ever tightens, so a stop can never be
        moved further away from price to give a losing trade more room.
        """
        atr_cache: dict[str, float] = {}
        for p in positions:
            cfg = self.s.for_symbol(p.symbol)
            if cfg.trail_atr_mult <= 0:
                continue
            if p.profit < cfg.trail_start_money:
                continue

            # The exit side: a long is closed at the bid, a short at the ask.
            # Using the entry side would flatter every trade by one spread.
            exit_side = "sell" if p.side == "buy" else "buy"
            try:
                price = session.broker.current_price(p.symbol, exit_side)
                if p.symbol not in atr_cache:
                    bars = session.broker.bars(p.symbol, cfg.timeframe,
                                               cfg.atr_period + 2)
                    value = atr([b.high for b in bars], [b.low for b in bars],
                                [b.close for b in bars], cfg.atr_period)
                    atr_cache[p.symbol] = value or 0.0
                floor = session.broker.min_stop_distance(p.symbol)
            except BrokerError as exc:
                log.debug("[%s] cannot trail %s: %s", session.name, p.symbol, exc)
                continue
            value = atr_cache.get(p.symbol, 0.0)
            if value <= 0 or price <= 0:
                continue

            peak = session.peak_price.get(p.ticket)
            peak = price if peak is None else (max(peak, price) if p.side == "buy"
                                               else min(peak, price))
            session.peak_price[p.ticket] = peak

            distance = value * cfg.trail_atr_mult
            candidate = peak - distance if p.side == "buy" else peak + distance

            # Brokers reject a stop sitting closer than their minimum (10011),
            # so pull it back to the closest legal place rather than losing
            # the update entirely.
            if floor > 0:
                if p.side == "buy":
                    candidate = min(candidate, price - floor)
                else:
                    candidate = max(candidate, price + floor)

            current = p.sl
            if current and current > 0:
                ratcheted = (max(current, candidate) if p.side == "buy"
                             else min(current, candidate))
            else:
                ratcheted = candidate
            if ratcheted == current:
                continue
            # Only act on a move worth a request. Without this the stop is
            # nudged by a fraction of a tick every loop, which floods the
            # trade server and gets throttled.
            if current and abs(ratcheted - current) < distance * 0.1:
                continue

            try:
                session.broker.modify_position(p.ticket, ratcheted, p.tp)
            except BrokerError as exc:
                log.debug("[%s] trailing stop move failed on %s: %s",
                          session.name, p.symbol, exc)
                continue
            log.info("[%s] %s #%s at %+.2f — trailing stop to %.5f "
                     "(%.1f ATR behind %.5f)", session.name, p.symbol, p.ticket,
                     p.profit, ratcheted, cfg.trail_atr_mult, peak)

    def _announce_verdict(self, session: BrokerSession) -> None:
        """Say it once when the record reaches a verdict, not every loop."""
        ev = session.evidence
        if ev is None:
            return
        verdict = ev.verdict()
        if verdict == ev.announced or verdict == evidence.PROVING:
            return
        ev.announced = verdict
        ev.save()
        if verdict == evidence.FAILED:
            log.warning("[%s] evidence FAILED after %d trades: net %.2f, "
                        "profit factor %.2f, z %.2f",
                        session.name, ev.count, ev.net, ev.profit_factor, ev.z)
            self.remote.broadcast(
                f"🛑 [{session.name}] STOPPED — the record says this loses.\n\n"
                f"{ev.explain()}\n\n"
                f"Trading more will not change the answer, only the amount. "
                f"Change something real — /symbols, the timeframe, the "
                f"strategy — then /evidence reset to score the new "
                f"configuration from zero.")
        else:
            self.remote.broadcast(
                f"✅ [{session.name}] the record now beats chance.\n\n"
                f"{ev.explain()}\n\n"
                f"This is permission to keep testing, not to add money.")

    def _evidence_blocks(self, session: BrokerSession) -> Optional[str]:
        """Why this account must not open a trade right now, if it must not.

        Two separate gates. One stops a configuration the record has already
        convicted; the other stops real money being risked on a
        configuration that has never proved anything.
        """
        # A missing record is not an absent objection: it means this
        # configuration has proved nothing, which is exactly what the live
        # gate is for. A safety gate that fails open is not a safety gate.
        ev = session.evidence
        verdict = ev.verdict() if ev else evidence.PROVING
        if ev and self.s.halt_on_failed_evidence and verdict == evidence.FAILED:
            return (f"the record over {ev.count} trades says this configuration "
                    f"loses (profit factor {ev.profit_factor:.2f}, z {ev.z:+.2f}). "
                    f"Change something, then /evidence reset")
        if not self.s.live_requires_evidence or verdict == evidence.PASSED:
            return None
        try:
            demo = session.broker.is_demo()
        except BrokerError:
            demo = None
        if demo:
            return None
        # None means the broker would not say. Real money is the assumption
        # that costs least when wrong.
        which = "a real account" if demo is False else "an account of unknown type"
        done = ev.count if ev else 0
        need = ev.min_trades if ev else self.s.evidence_min_trades
        return (f"this is {which} and the configuration has not proved itself "
                f"({done}/{need} trades). Run it on demo first, or "
                f"set LIVE_REQUIRES_EVIDENCE=false to override")

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

        The ladder is read per symbol: $0.25 of profit is half a EURUSD
        target and rounding error on gold, so a single set of rungs would
        protect one instrument and never trigger on another.
        """
        for p in positions:
            cfg = self.s.for_symbol(p.symbol)
            ladder = self._ladder_for(session, cfg, p)
            if not ladder:
                continue
            self._warn_if_ladder_caps(session, ladder, p)
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

        if command == "pace":
            out = []
            for s in sessions:
                out.append(f"— {s.name} —")
                if not s.pace or s.pace.target_per_hour <= 0:
                    out.append("  no rate target (MIN_TRADES_PER_HOUR is 0)")
                    continue
                times = s.risk.stats.entry_times
                done = s.pace.rate(times)
                short = s.pace.deficit(times)
                interval = s.pace.effective_interval(
                    self.s.entry_interval_seconds, len(s.active_symbols()), times)
                out.append(f"  {done} trades in the last hour, target "
                           f"{s.pace.target_per_hour:.0f}")
                out.append(f"  interval now {interval}s across "
                           f"{len(s.active_symbols())} symbol(s)")
                out.append(f"  {'behind by %.0f' % short if short > 0 else 'on or ahead of pace'}")
                if s.pace.blocks:
                    out.append("  refused this hour:")
                    for label, count in s.pace.blocks.most_common(4):
                        out.append(f"    {count} x {label}")
            return "\n".join(out)

        if command == "evidence":
            if args and args[0].lower() == "reset":
                for s in sessions:
                    if s.evidence:
                        s.evidence.reset()
                return ("Record cleared. Scoring starts from the next closed "
                        "trade.\n\nThis only makes sense if you changed "
                        "something real. Clearing it to keep trading the same "
                        "losing settings just repeats the test you already "
                        "failed.")
            out = []
            for s in sessions:
                out.append(f"— {s.name} —")
                out.append(s.evidence.explain() if s.evidence
                           else "  no record kept")
            return "\n".join(out)

        if command == "why":
            lines = []
            if self.paused:
                lines.append("⏸ THE BOT IS PAUSED — send /resume.\n")
            for s in sessions:
                blocked = self._evidence_blocks(s)
                if blocked:
                    lines.append(f"🛑 {s.name}: {blocked}\n")
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
