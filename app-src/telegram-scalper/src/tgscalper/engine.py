"""The decision path: one Telegram message in, orders (or a logged refusal) out.

Kept free of Telethon so it can be driven from a test, a text file or the live
listener. `Engine.handle()` is the whole contract.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from . import risk as risk_rules
from .brokers.base import Broker
from .brokers.paper import PaperBroker
from .config import Config, GroupConfig
from .journal import Journal
from .models import (
    Action,
    Decision,
    MessageRef,
    OrderRequest,
    OrderResult,
    OrderType,
    Side,
    Signal,
    SymbolInfo,
)
from .parser import parse
from .symbols import SymbolResolver

log = logging.getLogger(__name__)


class Engine:
    def __init__(
        self,
        config: Config,
        broker: Broker,
        journal: Journal,
        resolver: Optional[SymbolResolver] = None,
    ) -> None:
        self.config = config
        self.broker = broker
        self.journal = journal
        self.resolver = resolver or SymbolResolver(
            suffix=config.broker.suffix,
            overrides=config.broker.symbol_overrides,
            aliases=config.aliases,
        )
        self._halted_reason = ""

    # --- lifecycle ---

    def start(self) -> None:
        self.broker.connect()
        symbols = self.broker.available_symbols()
        if symbols:
            self.resolver.load_available(symbols)
            log.info("broker %s exposes %d symbols", self.broker.name, len(symbols))
        account = self.broker.account_info()
        self.journal.day_start_balance(account.balance)
        self.journal.record_event(
            "start",
            f"broker={self.broker.name} live={self.broker.is_live} "
            f"balance={account.balance:.2f} {account.currency}",
        )
        if not self.broker.is_live:
            log.warning(
                "PAPER MODE — no real orders will be placed (%s)",
                self.config.execution.live_block_reason or "paper broker selected",
            )

    def stop(self) -> None:
        self.broker.close()

    # --- main entry point ---

    def handle(
        self,
        text: str,
        source: Optional[MessageRef] = None,
        group: Optional[GroupConfig] = None,
    ) -> Decision:
        """Route one message. Never raises; every outcome is journalled."""
        try:
            return self._handle(text, source, group)
        except Exception as exc:  # a bad message must not kill the listener
            log.exception("error handling message")
            self.journal.record_event("error", f"{type(exc).__name__}: {exc}")
            return Decision(accepted=False, reason=f"internal error: {exc}")

    def _handle(
        self, text: str, source: Optional[MessageRef], group: Optional[GroupConfig]
    ) -> Decision:
        result = parse(
            text,
            source=source,
            aliases=self.config.aliases,
            require_sl=self.config.execution.require_stop_loss,
        )
        if not result.ok or result.signal is None:
            self.journal.record_skip(source, result.error, text)
            log.debug("ignored message: %s", result.error)
            return Decision(accepted=False, reason=result.error)

        signal = result.signal
        for note in result.warnings:
            log.info("parse note [%s]: %s", signal.symbol, note)

        if signal.action is not Action.OPEN:
            return self._handle_management(signal, source)
        return self._handle_open(signal, source, group)

    # --- opening trades ---

    def _handle_open(
        self, signal: Signal, source: Optional[MessageRef], group: Optional[GroupConfig]
    ) -> Decision:
        broker_symbol = self.resolver.resolve(signal.symbol)
        if broker_symbol is None:
            reason = (
                f"{signal.symbol} is not tradable on this account "
                f"(check broker.suffix / broker.symbol_overrides)"
            )
            self.journal.record_signal(signal, accepted=False, reason=reason)
            log.warning(reason)
            return Decision(accepted=False, reason=reason, signal=signal)

        info = self.broker.symbol_info(broker_symbol)
        if info is None:
            reason = f"no symbol info for {broker_symbol}"
            self.journal.record_signal(signal, accepted=False, reason=reason)
            return Decision(accepted=False, reason=reason, signal=signal)

        # The paper book has no feed of its own, so the posted entry becomes its
        # market — but only for a symbol it has never priced. Overwriting a known
        # price would erase the gap between "what the admin posted" and "where
        # the market actually is", which is exactly what the slippage guard reads.
        if isinstance(self.broker, PaperBroker):
            seed = signal.entry or signal.stop_loss
            if seed and self.broker.last_price(broker_symbol) is None:
                self.broker.seed_price(broker_symbol, seed)
                info = self.broker.symbol_info(broker_symbol) or info

        state = self._risk_state(signal, broker_symbol)
        gate = risk_rules.check_guards(signal, info, state, self.config)
        if not gate.ok:
            self.journal.record_signal(signal, accepted=False, reason=gate.reason)
            log.info("rejected %s: %s", signal.summary(), gate.reason)
            return Decision(accepted=False, reason=gate.reason, signal=signal)

        entry_plan = self._plan_entry(signal, info)
        if entry_plan is None:
            reason = "no usable entry price"
            self.journal.record_signal(signal, accepted=False, reason=reason)
            return Decision(accepted=False, reason=reason, signal=signal)
        order_type, price, reference = entry_plan

        slip = self._slippage_reason(signal, info, reference)
        if slip:
            self.journal.record_signal(signal, accepted=False, reason=slip)
            log.info("rejected %s: %s", signal.summary(), slip)
            return Decision(accepted=False, reason=slip, signal=signal)

        take_profits = risk_rules.select_take_profits(signal, self.config)
        multiplier = group.risk_multiplier if group else 1.0
        sizing = risk_rules.size_position(
            signal,
            info,
            self.broker.account_info().balance,
            self.config,
            reference_price=reference,
            group_multiplier=multiplier,
            legs=len(take_profits),
        )
        if not sizing.ok:
            self.journal.record_signal(signal, accepted=False, reason=sizing.error)
            log.warning("cannot size %s: %s", signal.summary(), sizing.error)
            return Decision(accepted=False, reason=sizing.error, signal=signal)
        for note in sizing.notes:
            log.info("sizing note [%s]: %s", broker_symbol, note)

        signal_id = self.journal.record_signal(signal, accepted=True, reason="")
        orders: list[OrderResult] = []
        for index, take_profit in enumerate(take_profits, start=1):
            request = OrderRequest(
                symbol=broker_symbol,
                side=signal.side,  # validated non-None by the parser
                order_type=order_type,
                volume=sizing.volume,
                price=None if order_type is OrderType.MARKET else price,
                stop_loss=sizing.stop_loss,
                take_profit=take_profit,
                comment=self._comment(signal, index),
                leg=index,
            )
            result = self.broker.place_order(request)
            self.journal.record_order(signal_id, source, request, result, self.broker.is_live)
            orders.append(result)
            if result.ok:
                log.info(
                    "%s %s %.2f lots @ %s (SL %s TP %s) ticket %s%s",
                    "LIVE" if self.broker.is_live else "PAPER",
                    f"{signal.side.value} {broker_symbol}",
                    result.volume,
                    result.filled_price,
                    sizing.stop_loss,
                    take_profit,
                    result.ticket,
                    f" [leg {index}/{len(take_profits)}]" if len(take_profits) > 1 else "",
                )
            else:
                log.error("order failed for %s: %s", broker_symbol, result.error)

        placed = sum(1 for order in orders if order.ok)
        return Decision(
            accepted=placed > 0,
            reason="" if placed else (orders[0].error if orders else "no orders placed"),
            signal=signal,
            orders=orders,
        )

    def _plan_entry(
        self, signal: Signal, info: SymbolInfo
    ) -> Optional[tuple[OrderType, Optional[float], float]]:
        """Decide market vs pending, and the price to sit at.

        Returns (order_type, order_price, reference_price) where the reference is
        what sizing measures the stop against.
        """
        market_price = (info.ask if signal.side is Side.BUY else info.bid) or info.mid

        if self.config.execution.entry.lower() == "market":
            return OrderType.MARKET, None, market_price or signal.entry or 0.0

        if signal.entry is None:
            return OrderType.MARKET, None, market_price or 0.0

        # A pending order's type follows from which side of the market it sits on:
        # buying below the market is a limit, buying above it is a breakout stop.
        if not market_price:
            return signal.order_type, signal.entry, signal.entry
        if signal.side is Side.BUY:
            order_type = OrderType.LIMIT if signal.entry < market_price else OrderType.STOP
        else:
            order_type = OrderType.LIMIT if signal.entry > market_price else OrderType.STOP
        return order_type, signal.entry, signal.entry

    def _slippage_reason(self, signal: Signal, info: SymbolInfo, reference: float) -> str:
        """Refuse a market fill once price has run past the posted entry.

        Copying a signal always arrives late; this is the guard against entering
        a move that has already happened.

        Two limits, either of which can be disabled with 0:

        * `max_entry_slippage_pct_of_stop` — how far price has run, as a share of
          the trade's own stop distance. This is the one to prefer: it means the
          same thing on gold, EURUSD and Volatility 75 without retuning, because
          the signal's own stop sets the scale.
        * `max_entry_slippage_points` — a raw point distance. Precise, but
          instrument-specific: 150 points is $1.50, which is a sane limit on gold
          and a meaningless one on an index priced at 250,000.
        """
        execution = self.config.execution
        if signal.entry is None or not reference or info.point <= 0:
            return ""
        if execution.entry.lower() != "market":
            return ""

        # Adverse means price moved the trade's way before we got in — i.e. we
        # would be entering worse than the admin did.
        adverse = (reference - signal.entry) * signal.side.sign
        if adverse <= 0:
            return ""

        stop = signal.stop_loss
        pct_limit = execution.max_entry_slippage_pct_of_stop
        if pct_limit > 0 and stop is not None:
            distance = abs(signal.entry - stop)
            if distance > 0:
                used = adverse / distance * 100
                if used > pct_limit:
                    return (
                        f"price already ran {used:.0f}% of the way to the stop before entry "
                        f"(limit {pct_limit:.0f}%) — the move is gone"
                    )

        point_limit = execution.max_entry_slippage_points
        if point_limit > 0 and adverse / info.point > point_limit:
            return (
                f"price already moved {adverse / info.point:.0f} points past the posted "
                f"entry {signal.entry} (limit {point_limit:.0f})"
            )
        return ""

    def _comment(self, signal: Signal, leg: int) -> str:
        source = signal.source
        chat = source.chat_id if source else 0
        message = source.message_id if source else 0
        # MT5 truncates comments at 31 characters, so keep it terse but traceable.
        return f"tg{abs(chat) % 1000000}:{message}:{leg}"[:31]

    def _risk_state(self, signal: Signal, broker_symbol: str) -> risk_rules.RiskState:
        account = self.broker.account_info()
        positions = self.broker.positions()
        return risk_rules.RiskState(
            now=datetime.now().astimezone(),
            open_total=len(positions),
            open_for_symbol=sum(
                1 for position in positions if position.symbol.upper() == broker_symbol.upper()
            ),
            signals_last_hour=self.journal.accepted_since(60),
            equity=account.equity,
            day_start_balance=self.journal.day_start_balance(account.balance),
            duplicate_of=self.journal.seen_fingerprint(
                signal.fingerprint(), self.config.risk.dedupe_window_minutes
            ),
        )

    # --- managing trades the admin already opened ---

    def _handle_management(self, signal: Signal, source: Optional[MessageRef]) -> Decision:
        tickets = self._target_tickets(signal, source)
        if not tickets:
            reason = f"{signal.action.value}: no matching open position found"
            self.journal.record_signal(signal, accepted=False, reason=reason)
            log.info(reason)
            return Decision(accepted=False, reason=reason, signal=signal)

        self.journal.record_signal(signal, accepted=True, reason="")
        results: list[OrderResult] = []

        for ticket in tickets:
            if signal.action is Action.CLOSE:
                result = self.broker.close_position(ticket)
                if result.ok:
                    self.journal.record_close(ticket, result.filled_price)
                results.append(result)

            elif signal.action is Action.CLOSE_PARTIAL:
                fraction = signal.close_fraction or self.config.risk.partial_close_default
                position = self._position(ticket)
                if position is None:
                    results.append(OrderResult(ok=False, error=f"position {ticket} gone"))
                    continue
                info = self.broker.symbol_info(position.symbol)
                volume = position.volume * fraction
                if info:
                    volume = max(
                        risk_rules.round_to_step(volume, info.volume_step), info.volume_min
                    )
                if volume >= position.volume:
                    # Cannot part-close below the minimum lot; close it outright.
                    log.info(
                        "partial close of %s rounds up to the full %.2f lots; closing fully",
                        ticket,
                        position.volume,
                    )
                    result = self.broker.close_position(ticket)
                    if result.ok:
                        self.journal.record_close(ticket, result.filled_price)
                else:
                    result = self.broker.close_position(ticket, volume=volume)
                results.append(result)

            elif signal.action is Action.BREAKEVEN:
                position = self._position(ticket)
                info = self.broker.symbol_info(position.symbol) if position else None
                if position is None or info is None:
                    results.append(OrderResult(ok=False, error=f"position {ticket} gone"))
                    continue
                new_stop = risk_rules.breakeven_price(
                    position.open_price,
                    position.side,
                    info,
                    self.config.risk.breakeven_offset_points,
                )
                ok = self.broker.modify_position(ticket, stop_loss=new_stop)
                results.append(
                    OrderResult(
                        ok=ok,
                        ticket=ticket,
                        error="" if ok else "broker rejected the stop move",
                    )
                )
                if ok:
                    log.info("moved %s stop to break-even %s", ticket, new_stop)

            elif signal.action is Action.MOVE_SL and signal.new_sl is not None:
                position = self._position(ticket)
                if position is None:
                    results.append(OrderResult(ok=False, error=f"position {ticket} gone"))
                    continue
                # A "new stop" that is worse than the current one increases risk;
                # the admin may be averaging, we are not.
                if position.stop_loss is not None:
                    improving = (
                        signal.new_sl - position.stop_loss
                    ) * position.side.sign > 0
                    if not improving:
                        results.append(
                            OrderResult(
                                ok=False,
                                ticket=ticket,
                                error=(
                                    f"refused to widen stop on {ticket} from "
                                    f"{position.stop_loss} to {signal.new_sl}"
                                ),
                            )
                        )
                        continue
                ok = self.broker.modify_position(ticket, stop_loss=signal.new_sl)
                results.append(
                    OrderResult(ok=ok, ticket=ticket, error="" if ok else "stop move rejected")
                )

            elif signal.action is Action.CANCEL_PENDING:
                ok = self.broker.cancel_order(ticket)
                results.append(
                    OrderResult(ok=ok, ticket=ticket, error="" if ok else "cancel rejected")
                )

        for result in results:
            if not result.ok and result.error:
                log.warning("%s on %s: %s", signal.action.value, result.ticket, result.error)

        done = sum(1 for result in results if result.ok)
        return Decision(
            accepted=done > 0,
            reason="" if done else "no positions were changed",
            signal=signal,
            orders=results,
        )

    def _position(self, ticket: int):
        for position in self.broker.positions():
            if position.ticket == ticket:
                return position
        return None

    def _target_tickets(self, signal: Signal, source: Optional[MessageRef]) -> list[int]:
        """Work out which positions a follow-up message refers to.

        Preference order, most specific first:
          1. The post it replies to — unambiguous, this is how admins do it.
          2. The symbol named in the follow-up itself.
          3. Everything still open from that same group.
        """
        if signal.action is Action.CANCEL_PENDING:
            pending = self.broker.pending_orders()
            symbol = self.resolver.resolve(signal.symbol) if signal.symbol else None
            return [
                order.ticket
                for order in pending
                if symbol is None or order.symbol.upper() == symbol.upper()
            ]

        open_tickets = {position.ticket for position in self.broker.positions()}

        if source and source.reply_to_message_id:
            tickets = self.journal.tickets_for_message(
                source.chat_id, source.reply_to_message_id
            )
            matched = [ticket for ticket in tickets if ticket in open_tickets]
            if matched:
                return matched

        if signal.symbol:
            broker_symbol = self.resolver.resolve(signal.symbol)
            if broker_symbol:
                return [
                    position.ticket
                    for position in self.broker.positions(broker_symbol)
                ]

        if source:
            return [
                ticket
                for ticket in self.journal.open_tickets(chat_id=source.chat_id)
                if ticket in open_tickets
            ]
        return []
