"""Daily risk limits. Every entry must pass ALL checks; when a hard stop
trips, the bot pauses itself for the day (no recovery / martingale)."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from .config import Settings

log = logging.getLogger("fmsbot.risk")


@dataclass
class DayStats:
    day: date = field(default_factory=date.today)
    start_balance: float = 0.0
    trades: int = 0
    last_entry: dict[str, float] = field(default_factory=dict)  # symbol -> ts
    #: entry timestamps inside the rolling window, for the trade cap
    entry_times: list[float] = field(default_factory=list)
    #: losses since the last winner — a streak means the regime is against us
    consecutive_losses: int = 0
    #: when the streak pause expires (unix ts); 0 when not paused
    paused_until: float = 0.0


class RiskManager:
    """Daily limits, persisted across restarts.

    Keeping this in memory alone meant every restart reset the day's trade
    count and its starting balance, so the daily loss limit silently began
    again — a crash loop or a few manual restarts could lose far more than
    the configured cap. State is written to disk after each entry and
    reloaded when the saved day is still today.
    """

    def __init__(self, settings: Settings, state_file: Optional[str] = None):
        self.s = settings
        self.state_path = Path(state_file) if state_file else None
        self.stats = DayStats()
        self._load()

    # -- persistence -----------------------------------------------------

    def _load(self) -> None:
        if not self.state_path or not self.state_path.is_file():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            saved_day = date.fromisoformat(data["day"])
        except (OSError, ValueError, KeyError):
            return
        if saved_day != date.today():
            return                      # yesterday's numbers do not carry over
        self.stats = DayStats(
            day=saved_day,
            start_balance=float(data.get("start_balance", 0.0)),
            trades=int(data.get("trades", 0)),
            last_entry={k: float(v) for k, v in data.get("last_entry", {}).items()},
            entry_times=[float(t) for t in data.get("entry_times", [])],
            consecutive_losses=int(data.get("consecutive_losses", 0)),
            paused_until=float(data.get("paused_until", 0.0)),
        )
        log.info("Restored today's risk state: %d trade(s), start balance %.2f",
                 self.stats.trades, self.stats.start_balance)

    def _save(self) -> None:
        if not self.state_path:
            return
        try:
            self.state_path.write_text(json.dumps({
                "day": self.stats.day.isoformat(),
                "start_balance": self.stats.start_balance,
                "trades": self.stats.trades,
                "last_entry": self.stats.last_entry,
                "entry_times": self.stats.entry_times,
                "consecutive_losses": self.stats.consecutive_losses,
                "paused_until": self.stats.paused_until,
            }), encoding="utf-8")
        except OSError:
            log.exception("Could not persist risk state")

    def _roll(self, balance: float) -> None:
        if self.stats.day != date.today():
            self.stats = DayStats(start_balance=balance)
            log.info("New trading day, start balance %.2f", balance)
            self._save()
        elif self.stats.start_balance == 0.0:
            self.stats.start_balance = balance
            self._save()

    def rolling_trades(self) -> int:
        """Entries inside the rolling window, pruning what has aged out."""
        window = self.s.rolling_trade_window_hours * 3600
        if window <= 0:
            return self.stats.trades
        cutoff = time.time() - window
        self.stats.entry_times = [t for t in self.stats.entry_times if t >= cutoff]
        return len(self.stats.entry_times)

    def record_result(self, pnl: float) -> Optional[str]:
        """Record a closed trade. Returns a message when a pause begins."""
        st, s = self.stats, self.s
        if pnl > 0:
            st.consecutive_losses = 0
            self._save()
            return None
        st.consecutive_losses += 1
        message = None
        if s.max_consecutive_losses and st.consecutive_losses >= s.max_consecutive_losses:
            st.paused_until = time.time() + s.loss_pause_minutes * 60
            message = (f"{st.consecutive_losses} losses in a row — pausing entries "
                       f"for {s.loss_pause_minutes} min. Existing positions keep "
                       f"their stops.")
            log.warning(message)
        self._save()
        return message

    def clear_pause(self) -> None:
        self.stats.consecutive_losses = 0
        self.stats.paused_until = 0.0
        self._save()

    def can_enter(self, symbol: str, balance: float, equity: float,
                  open_total: int, open_symbol: int) -> tuple[bool, str]:
        self._roll(balance)
        s, st = self.s, self.stats

        if st.paused_until > time.time():
            left = (st.paused_until - time.time()) / 60.0
            return False, (f"paused after {st.consecutive_losses} consecutive "
                           f"losses ({left:.0f} min left)")
        if st.paused_until and st.paused_until <= time.time():
            # pause served; start the streak count again
            st.consecutive_losses = 0
            st.paused_until = 0.0
            self._save()

        # The rolling window replaces the calendar-day cap when enabled; using
        # both would keep blocking after old entries have aged out.
        if s.rolling_trade_window_hours > 0:
            rolling = self.rolling_trades()
            if rolling >= s.max_trades_per_day:
                return False, (f"trade cap ({s.max_trades_per_day}) reached for the "
                               f"rolling {s.rolling_trade_window_hours}h window")
        elif st.trades >= s.max_trades_per_day:
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
        now = time.time()
        self.stats.trades += 1
        self.stats.last_entry[symbol] = now
        self.stats.entry_times.append(now)
        self._save()

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
        out = []
        if st.paused_until > time.time():
            left = (st.paused_until - time.time()) / 60.0
            out.append(f"⏸ PAUSED after {st.consecutive_losses} consecutive "
                       f"losses — {left:.0f} min left")
        rolling = self.rolling_trades()
        out.append(f"trades in last {s.rolling_trade_window_hours}h: "
                   f"{rolling}/{s.max_trades_per_day}"
                   + ("  ← CAP REACHED" if rolling >= s.max_trades_per_day else ""))
        out.append(f"consecutive losses: {st.consecutive_losses}"
                   + (f"/{s.max_consecutive_losses}" if s.max_consecutive_losses
                      else " (pause disabled)"))
        out.append(f"trades today: {st.trades}/{s.max_trades_per_day}")

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
