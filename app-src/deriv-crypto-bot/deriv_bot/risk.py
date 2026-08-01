"""Risk controls.

Every trade passes through `RiskManager.check` before a proposal is even
requested. The checks are ordered cheapest-and-most-absolute first, so an
operator-triggered kill switch or a breached daily limit short-circuits before
anything symbol-specific is considered.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime

from .config import Config
from .state import StateStore

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskDecision:
    """The outcome of a risk check.

    `stake` is the size the trade is permitted to use, which may be smaller
    than the configured stake if the balance cap bit.
    """

    allowed: bool
    reason: str
    stake: float = 0.0
    # True when the blocker applies to the whole bot rather than one symbol,
    # letting the trader skip the remaining symbols this cycle.
    global_block: bool = False


class RiskManager:
    def __init__(self, config: Config, store: StateStore) -> None:
        self.config = config
        self.store = store
        self._last_trade_at: dict[str, float] = {}

    # -- external state ---------------------------------------------------

    def kill_switch_engaged(self) -> bool:
        """An operator can stop all trading by creating the kill-switch file."""
        return os.path.exists(self.config.kill_switch_file)

    def note_trade(self, symbol: str, *, now: float | None = None) -> None:
        """Start the per-symbol cooldown. Called after a trade is placed."""
        self._last_trade_at[symbol] = now if now is not None else time.time()

    def cooldown_remaining(self, symbol: str, *, now: float | None = None) -> float:
        last = self._last_trade_at.get(symbol)
        if last is None:
            return 0.0
        moment = now if now is not None else time.time()
        return max(0.0, self.config.symbol_cooldown - (moment - last))

    # -- limit evaluation -------------------------------------------------

    def refresh_daily_limits(self, now: "datetime | None" = None) -> None:
        """Roll the day over at UTC midnight and halt if a limit is breached.

        Called once per cycle so limits are enforced even when no signal fires.
        `now` overrides the clock, which lets the backtester run the same limit
        logic against historical timestamps.
        """
        daily = self.store.daily
        if daily.roll_over_if_needed(now):
            log.info("UTC day rolled over to %s — daily counters reset", daily.day)
            self.store.save()

        if daily.halted:
            return

        if daily.realized_pnl <= -abs(self.config.daily_loss_limit):
            self.store.halt(
                f"daily loss limit reached: {daily.realized_pnl:.2f} "
                f"<= -{abs(self.config.daily_loss_limit):.2f}"
            )
            log.warning("HALTED — %s", daily.halt_reason)
            return

        target = self.config.daily_profit_target
        if target > 0 and daily.realized_pnl >= target:
            self.store.halt(
                f"daily profit target reached: {daily.realized_pnl:.2f} >= {target:.2f}"
            )
            log.info("HALTED — %s", daily.halt_reason)

    def check(
        self,
        symbol: str,
        *,
        balance: float,
        open_trades: int,
        open_symbols: set[str],
        now: float | None = None,
    ) -> RiskDecision:
        """Decide whether `symbol` may be traded right now, and with what stake."""
        config = self.config
        daily = self.store.daily

        if self.kill_switch_engaged():
            return RiskDecision(
                False,
                f"kill switch present at {config.kill_switch_file}",
                global_block=True,
            )

        if daily.halted:
            return RiskDecision(False, f"bot halted: {daily.halt_reason}", global_block=True)

        if daily.trades_opened >= config.max_trades_per_day:
            return RiskDecision(
                False,
                f"daily trade cap reached ({daily.trades_opened}/{config.max_trades_per_day})",
                global_block=True,
            )

        if open_trades >= config.max_open_trades:
            return RiskDecision(
                False,
                f"max concurrent trades reached ({open_trades}/{config.max_open_trades})",
                global_block=True,
            )

        # --- symbol-specific from here on --------------------------------

        if symbol in open_symbols:
            return RiskDecision(False, f"{symbol} already has an open position")

        remaining = self.cooldown_remaining(symbol, now=now)
        if remaining > 0:
            return RiskDecision(False, f"{symbol} cooling down for another {remaining:.0f}s")

        # --- sizing -------------------------------------------------------

        stake = config.stake
        cap = balance * config.max_stake_fraction
        if cap <= 0:
            return RiskDecision(False, f"balance {balance:.2f} leaves no room to trade", global_block=True)
        if stake > cap:
            log.info(
                "stake reduced from %.2f to %.2f (%.1f%% cap on balance %.2f)",
                stake,
                cap,
                config.max_stake_fraction * 100,
                balance,
            )
            stake = cap

        # Never risk more than the remaining daily loss budget on one trade.
        budget_left = abs(config.daily_loss_limit) + daily.realized_pnl
        if budget_left <= 0:
            return RiskDecision(False, "daily loss budget exhausted", global_block=True)
        if stake > budget_left:
            log.info(
                "stake reduced from %.2f to %.2f (remaining daily loss budget)", stake, budget_left
            )
            stake = budget_left

        stake = round(stake, 2)
        if stake <= 0:
            return RiskDecision(False, "computed stake rounded to zero", global_block=True)
        if stake > balance:
            return RiskDecision(
                False, f"stake {stake:.2f} exceeds balance {balance:.2f}", global_block=True
            )

        return RiskDecision(True, "within all risk limits", stake=stake)
