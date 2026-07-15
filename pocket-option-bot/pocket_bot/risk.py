"""Money management and hard risk limits.

Binary options lose the ENTIRE stake on a losing trade, so risk control
matters more than the strategy. The RiskManager decides whether a trade
is allowed and how much to stake; when a limit trips, the bot stops for
the day rather than "recovering" with bigger bets (no martingale — that
is how accounts get wiped).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date

from .config import Settings

log = logging.getLogger("pocket_bot.risk")


@dataclass
class DayStats:
    day: date = field(default_factory=date.today)
    trades: int = 0
    wins: int = 0
    losses: int = 0
    net_pnl: float = 0.0
    consecutive_losses: int = 0
    last_trade_ts: float = 0.0


class RiskManager:
    def __init__(self, settings: Settings):
        self.s = settings
        self.stats = DayStats()

    def _roll_day(self) -> None:
        if self.stats.day != date.today():
            log.info("New trading day — resetting daily stats.")
            self.stats = DayStats()

    def stake_for(self, balance: float | None) -> float:
        s = self.s
        stake = s.stake
        if s.stake_pct > 0 and balance:
            stake = balance * s.stake_pct / 100.0
        return round(min(stake, s.max_stake), 2)

    def can_trade(self) -> tuple[bool, str]:
        """Returns (allowed, reason_if_blocked)."""
        self._roll_day()
        st, s = self.stats, self.s
        if st.trades >= s.max_trades_per_day:
            return False, f"daily trade cap reached ({s.max_trades_per_day})"
        if st.consecutive_losses >= s.max_consecutive_losses:
            return False, f"{st.consecutive_losses} consecutive losses — stopped for the day"
        if s.daily_loss_limit > 0 and st.net_pnl <= -s.daily_loss_limit:
            return False, f"daily loss limit hit (net {st.net_pnl:+.2f})"
        if s.daily_profit_target > 0 and st.net_pnl >= s.daily_profit_target:
            return False, f"daily profit target reached (net {st.net_pnl:+.2f})"
        elapsed = time.time() - st.last_trade_ts
        if elapsed < s.cooldown_seconds:
            return False, f"cooldown ({s.cooldown_seconds - elapsed:.0f}s left)"
        return True, ""

    def record_open(self) -> None:
        self._roll_day()
        self.stats.trades += 1
        self.stats.last_trade_ts = time.time()

    def record_result(self, profit: float | None) -> None:
        """profit = net PnL of the closed option (None if unknown)."""
        if profit is None:
            return
        st = self.stats
        st.net_pnl += profit
        if profit > 0:
            st.wins += 1
            st.consecutive_losses = 0
        else:
            st.losses += 1
            st.consecutive_losses += 1
        log.info(
            "Day so far: %d trades, %dW/%dL, net %+.2f (streak: %d losses)",
            st.trades, st.wins, st.losses, st.net_pnl, st.consecutive_losses,
        )

    @property
    def stopped_for_day(self) -> bool:
        allowed, reason = self.can_trade()
        return (not allowed) and "cooldown" not in reason
