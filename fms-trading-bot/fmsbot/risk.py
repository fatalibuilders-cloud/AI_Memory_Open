"""Daily risk limits. Every entry must pass ALL checks; when a hard stop
trips, the bot pauses itself for the day (no recovery / martingale)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date

from .config import Settings

log = logging.getLogger("fmsbot.risk")


@dataclass
class DayStats:
    day: date = field(default_factory=date.today)
    start_balance: float = 0.0
    trades: int = 0
    last_entry: dict[str, float] = field(default_factory=dict)  # symbol -> ts


class RiskManager:
    def __init__(self, settings: Settings):
        self.s = settings
        self.stats = DayStats()

    def _roll(self, balance: float) -> None:
        if self.stats.day != date.today():
            self.stats = DayStats(start_balance=balance)
            log.info("New trading day, start balance %.2f", balance)
        elif self.stats.start_balance == 0.0:
            self.stats.start_balance = balance

    def can_enter(self, symbol: str, balance: float, equity: float,
                  open_total: int, open_symbol: int) -> tuple[bool, str]:
        self._roll(balance)
        s, st = self.s, self.stats
        if st.trades >= s.max_trades_per_day:
            return False, f"daily trade cap ({s.max_trades_per_day}) reached"
        if open_total >= s.max_open_positions:
            return False, f"max open positions ({s.max_open_positions})"
        if open_symbol >= s.max_positions_per_symbol:
            return False, f"already positioned in {symbol}"
        if st.start_balance > 0:
            dd = (equity - st.start_balance) / st.start_balance * 100.0
            if dd <= -s.daily_loss_limit_pct:
                return False, f"daily loss limit hit ({dd:+.2f}%)"
        last = st.last_entry.get(symbol, 0.0)
        wait = s.cooldown_seconds - (time.time() - last)
        if wait > 0:
            return False, f"{symbol} cooldown ({wait:.0f}s left)"
        return True, ""

    def risk_amount(self, balance: float) -> float:
        return balance * self.s.risk_pct / 100.0

    def record_entry(self, symbol: str) -> None:
        self.stats.trades += 1
        self.stats.last_entry[symbol] = time.time()

    def day_summary(self, balance: float, equity: float) -> str:
        self._roll(balance)
        st = self.stats
        pnl = equity - st.start_balance if st.start_balance else 0.0
        return (f"today: {st.trades}/{self.s.max_trades_per_day} trades, "
                f"day PnL {pnl:+.2f}")

    def explain(self, balance: float, equity: float,
                open_total: int, symbols: list[str]) -> list[str]:
        """Human-readable state of every gate, for the /why command."""
        self._roll(balance)
        s, st = self.s, self.stats
        out = [f"trades today: {st.trades}/{s.max_trades_per_day}"
               + ("  ← CAP REACHED" if st.trades >= s.max_trades_per_day else "")]

        out.append(f"open positions: {open_total}/{s.max_open_positions}"
                   + ("  ← FULL" if open_total >= s.max_open_positions else ""))

        if st.start_balance > 0:
            dd = (equity - st.start_balance) / st.start_balance * 100.0
            line = f"day PnL: {equity - st.start_balance:+.2f} ({dd:+.2f}%)"
            if dd <= -s.daily_loss_limit_pct:
                line += f"  ← DAILY LOSS LIMIT ({s.daily_loss_limit_pct}%) HIT"
            else:
                line += f", limit -{s.daily_loss_limit_pct}%"
            out.append(line)

        now = time.time()
        cooling = []
        for symbol in symbols:
            wait = s.cooldown_seconds - (now - st.last_entry.get(symbol, 0.0))
            if wait > 0:
                cooling.append(f"{symbol} {wait:.0f}s")
        out.append("cooldown: " + (", ".join(cooling) if cooling else "none active"))
        return out
