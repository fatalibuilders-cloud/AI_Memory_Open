"""Bot orchestrator: stream ticks -> candles -> strategy -> risk -> order."""

from __future__ import annotations

import asyncio
import logging

from .candles import CandleBuilder
from .client import PocketOptionClient, PocketOptionError
from .config import Settings
from .risk import RiskManager
from .strategy import build_strategy

log = logging.getLogger("pocket_bot.bot")

RECONNECT_DELAYS = [2, 4, 8, 16, 30, 60]


class TradingBot:
    def __init__(self, settings: Settings):
        self.s = settings
        self.client = PocketOptionClient(settings.ssid, demo=settings.demo)
        self.candles = CandleBuilder(settings.candle_seconds)
        self.strategy = build_strategy(settings)
        self.risk = RiskManager(settings)
        self._trade_lock = asyncio.Lock()   # one open position at a time
        self._stop = asyncio.Event()

    # ------------------------------------------------------------------

    async def run(self) -> None:
        mode = "DEMO" if self.s.demo else "LIVE"
        log.info("=== Pocket Option bot starting — %s mode, asset %s, strategy %s ===",
                 mode, self.s.asset, self.s.strategy)
        if not self.s.demo:
            log.warning("LIVE MODE: real money at risk. Stake=%.2f, daily loss limit=%.2f",
                        self.s.stake, self.s.daily_loss_limit)
        if self.s.dry_run:
            log.info("DRY RUN: signals will be logged but no orders sent.")

        attempt = 0
        while not self._stop.is_set():
            try:
                await self._session()
                attempt = 0
            except (PocketOptionError, OSError) as exc:
                delay = RECONNECT_DELAYS[min(attempt, len(RECONNECT_DELAYS) - 1)]
                attempt += 1
                log.warning("Session ended (%s). Reconnecting in %ds...", exc, delay)
                await asyncio.sleep(delay)

    def stop(self) -> None:
        self._stop.set()

    # ------------------------------------------------------------------

    async def _session(self) -> None:
        self.client = PocketOptionClient(self.s.ssid, demo=self.s.demo)
        self.client.on_tick(self._on_tick)
        await self.client.connect()
        await self.client.subscribe(self.s.asset, self.s.candle_seconds)
        log.info("Warming up: need %d closed candles (~%d min on %ds timeframe) before trading.",
                 self.s.min_candles, self.s.min_candles * self.s.candle_seconds // 60,
                 self.s.candle_seconds)
        try:
            while not self._stop.is_set():
                if not self.client.connected:
                    raise PocketOptionError("connection lost")
                await asyncio.sleep(1)
        finally:
            await self.client.close()

    async def _on_tick(self, asset: str, ts: float, price: float) -> None:
        if asset != self.s.asset:
            return
        closed = self.candles.add_tick(ts, price)
        if closed is None:
            return
        log.debug("Candle closed: O=%.5f H=%.5f L=%.5f C=%.5f (%d in history)",
                  closed.open, closed.high, closed.low, closed.close, len(self.candles))
        signal = self.strategy.signal(self.candles)
        if signal is None:
            return
        # Never block the tick stream — trade in the background.
        asyncio.create_task(self._maybe_trade(signal))

    async def _maybe_trade(self, direction: str) -> None:
        if self._trade_lock.locked():
            log.info("Signal %s skipped — a position is already open.", direction.upper())
            return
        async with self._trade_lock:
            allowed, reason = self.risk.can_trade()
            if not allowed:
                log.info("Signal %s blocked by risk manager: %s", direction.upper(), reason)
                return
            stake = self.risk.stake_for(self.client.balance)
            if stake <= 0:
                log.warning("Computed stake is 0 — check PO_STAKE settings.")
                return
            if self.s.dry_run:
                log.info("[DRY RUN] Would trade %s %s $%.2f for %ds",
                         self.s.asset, direction.upper(), stake, self.s.expiry_seconds)
                return
            try:
                order = await self.client.buy(
                    self.s.asset, stake, direction, self.s.expiry_seconds)
            except Exception as exc:
                log.error("Order failed: %s", exc)
                return
            self.risk.record_open()
            log.info("Position open (id=%s). Waiting %ds for expiry...",
                     order.order_id, self.s.expiry_seconds)
            order = await self.client.wait_result(order, self.s.expiry_seconds)
            if order.profit is None:
                log.warning("Result unknown for order %s — not counted in stats.", order.order_id)
            else:
                outcome = "WIN" if order.profit > 0 else ("PUSH" if order.profit == 0 else "LOSS")
                log.info("Result: %s %+0.2f", outcome, order.profit)
                self.risk.record_result(order.profit)
            if self.risk.stopped_for_day:
                log.warning("Risk limit reached — bot is done trading for today. "
                            "It stays connected but will not place more orders.")
