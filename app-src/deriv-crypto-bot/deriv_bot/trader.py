"""The trading loop.

Structure is two nested loops. The outer one owns the connection and reconnects
with exponential backoff whenever the socket drops — this is what makes the bot
survive unattended for days. The inner one runs a trading cycle every
POLL_INTERVAL seconds: settle finished contracts, refresh limits, then look for
a signal on each open crypto symbol.

Trading is gated at three independent points, and all three must pass:
  1. the market filter (`market.select_symbols`) — cryptocurrency only,
  2. the risk manager (`risk.RiskManager.check`) — limits and sizing,
  3. a final assertion immediately before `buy` — the symbol is still in the
     verified crypto set for this cycle.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time

from .api import ConnectionLost, DerivAPI, DerivError
from .config import Config
from .indicators import Candle
from .market import find_contract, resolve_duration, select_symbols
from .risk import RiskManager
from .state import StateStore
from .strategies import get as get_strategy
from .strategy import Signal

log = logging.getLogger(__name__)


class UnsafeAccount(Exception):
    """The authorized account is real-money and that was not explicitly allowed."""


class OpenTrade:
    __slots__ = ("contract_id", "symbol", "direction", "stake", "opened_at")

    def __init__(self, contract_id: int, symbol: str, direction: str, stake: float) -> None:
        self.contract_id = contract_id
        self.symbol = symbol
        self.direction = direction
        self.stake = stake
        self.opened_at = time.time()


class Trader:
    def __init__(self, config: Config, store: StateStore) -> None:
        self.config = config
        self.store = store
        self.api = DerivAPI(config)
        self.risk = RiskManager(config, store)
        self.decide = get_strategy(config.strategy)
        self.open_trades: dict[int, OpenTrade] = {}
        self.currency: str = config.currency
        self._stopping = asyncio.Event()

    def request_stop(self) -> None:
        """Ask the loops to wind down at the next safe point."""
        log.info("shutdown requested — finishing the current cycle")
        self._stopping.set()

    # -- outer loop -------------------------------------------------------

    async def run(self) -> None:
        delay = 1.0
        while not self._stopping.is_set():
            try:
                await self.api.connect()
                self._verify_account()
                delay = 1.0  # a clean connect resets the backoff
                await self._trade_loop()
            except UnsafeAccount:
                raise
            except (ConnectionLost, OSError, asyncio.TimeoutError) as exc:
                log.warning("connection problem (%s) — reconnecting in %.1fs", exc, delay)
            except DerivError as exc:
                if exc.code in {"InvalidToken", "AuthorizationRequired"}:
                    log.error("authorization rejected by Deriv: %s", exc.message)
                    raise
                log.warning("API error (%s) — reconnecting in %.1fs", exc, delay)
            finally:
                await self.api.close()

            if self._stopping.is_set():
                break
            # Jitter keeps many bots from reconnecting in lockstep after an outage.
            await self._sleep(delay + random.uniform(0, delay * 0.25))
            delay = min(delay * 2, self.config.reconnect_max_delay)

        log.info("trader stopped")

    def _verify_account(self) -> None:
        """Refuse to touch real money unless explicitly authorized."""
        account = self.api.account
        is_virtual = bool(account.get("is_virtual", 0))
        self.currency = self.config.currency or str(account.get("currency", "USD"))

        if is_virtual:
            log.info("running on VIRTUAL account %s — no real funds at risk", account.get("loginid"))
            return
        if not self.config.allow_real_money:
            raise UnsafeAccount(
                f"token belongs to REAL-money account {account.get('loginid')} but "
                "DERIV_ALLOW_REAL_MONEY is not set. Refusing to trade. Use a demo "
                "token, or set DERIV_ALLOW_REAL_MONEY=true if that is genuinely intended."
            )
        log.warning(
            "RUNNING ON A REAL-MONEY ACCOUNT (%s, %s). Live funds are at risk.",
            account.get("loginid"),
            self.currency,
        )

    async def _sleep(self, seconds: float) -> None:
        """Sleep, but wake immediately if a shutdown was requested."""
        try:
            await asyncio.wait_for(self._stopping.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    # -- inner loop -------------------------------------------------------

    async def _trade_loop(self) -> None:
        while not self._stopping.is_set():
            started = time.monotonic()
            await self._cycle()
            elapsed = time.monotonic() - started
            await self._sleep(max(1.0, self.config.poll_interval - elapsed))

    async def _cycle(self) -> None:
        await self._settle_open_trades()
        self.risk.refresh_daily_limits()

        if self.risk.kill_switch_engaged():
            log.warning("kill switch present at %s — not opening trades", self.config.kill_switch_file)
            return
        if self.store.daily.halted:
            log.info("halted for today: %s", self.store.daily.halt_reason)
            return

        balance_info = await self.api.balance()
        balance = float(balance_info.get("balance", 0.0))

        universe = select_symbols(await self.api.active_symbols(), self.config)
        if not universe:
            log.warning("no open cryptocurrency symbols available this cycle")
            return

        tradable = {info.symbol for info in universe}
        log.info(
            "cycle: balance=%.2f %s | open=%d | pnl=%.2f | universe=%s",
            balance,
            self.currency,
            len(self.open_trades),
            self.store.daily.realized_pnl,
            ", ".join(sorted(tradable)),
        )

        for info in universe:
            if self._stopping.is_set():
                return
            try:
                await self._consider(info.symbol, balance, tradable)
            except DerivError as exc:
                log.warning("%s: skipped after API error — %s", info.symbol, exc)
            except (ConnectionLost, asyncio.TimeoutError):
                raise  # let the outer loop reconnect

    async def _consider(self, symbol: str, balance: float, tradable: set[str]) -> None:
        raw = await self.api.candles(symbol, self.config.candle_granularity, self.config.candle_count)
        if not raw:
            log.debug("%s: no candle data returned", symbol)
            return

        candles = [Candle.from_api(entry) for entry in raw]
        signal = self.decide(symbol, candles, self.config)
        if not signal.is_trade:
            log.debug("%s: %s", symbol, signal.reason)
            return

        decision = self.risk.check(
            symbol,
            balance=balance,
            open_trades=len(self.open_trades),
            open_symbols={trade.symbol for trade in self.open_trades.values()},
        )
        if not decision.allowed:
            log.info("%s: signal suppressed — %s", symbol, decision.reason)
            return

        log.info("%s: %s signal — %s", symbol, signal.direction, signal.reason)
        await self._place(signal, decision.stake, tradable)

    async def _place(self, signal: Signal, stake: float, tradable: set[str]) -> None:
        symbol = signal.symbol
        direction = signal.direction
        assert direction is not None

        contracts = await self.api.contracts_for(symbol, self.currency)
        entry = find_contract(contracts, direction)
        if entry is None:
            log.warning("%s: no spot %s contract offered — skipping", symbol, direction)
            return

        amount, unit = resolve_duration(entry, self.config)

        proposal = await self.api.proposal(
            {
                "symbol": symbol,
                "contract_type": direction,
                "amount": stake,
                "basis": "stake",
                "currency": self.currency,
                "duration": amount,
                "duration_unit": unit,
            }
        )
        proposal_id = proposal.get("id")
        ask_price = float(proposal.get("ask_price", stake))
        if not proposal_id:
            log.warning("%s: proposal returned no id — skipping", symbol)
            return

        if self.config.dry_run:
            log.info(
                "DRY RUN — would buy %s %s for %.2f %s (%s%s), payout %.2f",
                direction,
                symbol,
                ask_price,
                self.currency,
                amount,
                unit,
                float(proposal.get("payout", 0.0)),
            )
            self.risk.note_trade(symbol)
            self.store.journal(
                {
                    "event": "dry_run",
                    "symbol": symbol,
                    "direction": direction,
                    "stake": ask_price,
                    "reason": signal.reason,
                }
            )
            return

        # Final gate: the symbol must still be in this cycle's verified crypto set.
        if symbol not in tradable:
            log.error("%s: refusing to buy — not in the verified crypto universe", symbol)
            return

        result = await self.api.buy(proposal_id, ask_price)
        contract_id = result.get("contract_id")
        if not contract_id:
            log.warning("%s: buy returned no contract_id", symbol)
            return

        trade = OpenTrade(int(contract_id), symbol, direction, float(result.get("buy_price", ask_price)))
        self.open_trades[trade.contract_id] = trade
        self.risk.note_trade(symbol)
        self.store.record_open(
            {
                "contract_id": trade.contract_id,
                "symbol": symbol,
                "direction": direction,
                "stake": trade.stake,
                "duration": f"{amount}{unit}",
                "reason": signal.reason,
                "entry": signal.close,
            }
        )
        log.info(
            "BOUGHT %s %s id=%s stake=%.2f %s duration=%s%s",
            direction,
            symbol,
            trade.contract_id,
            trade.stake,
            self.currency,
            amount,
            unit,
        )

    # -- settlement -------------------------------------------------------

    async def _settle_open_trades(self) -> None:
        for contract_id, trade in list(self.open_trades.items()):
            try:
                contract = await self.api.open_contract(contract_id)
            except DerivError as exc:
                log.warning("could not poll contract %s: %s", contract_id, exc)
                continue

            if not contract.get("is_sold"):
                continue

            profit = float(contract.get("profit", 0.0))
            status = str(contract.get("status", "unknown"))
            self.open_trades.pop(contract_id, None)
            self.store.record_settlement(
                profit,
                {
                    "contract_id": contract_id,
                    "symbol": trade.symbol,
                    "direction": trade.direction,
                    "stake": trade.stake,
                    "status": status,
                    "sell_price": float(contract.get("sell_price", 0.0)),
                },
            )
            log.info(
                "SETTLED %s %s id=%s %s profit=%+.2f %s | day pnl=%+.2f (%dW/%dL)",
                trade.direction,
                trade.symbol,
                contract_id,
                status.upper(),
                profit,
                self.currency,
                self.store.daily.realized_pnl,
                self.store.daily.wins,
                self.store.daily.losses,
            )
