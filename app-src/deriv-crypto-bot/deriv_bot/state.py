"""Durable bot state.

Daily counters live on disk so that a restart — deliberate or after a crash —
cannot be used, accidentally, to escape a daily loss limit that has already
been hit. Every settled trade is also appended to a JSON Lines journal.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

log = logging.getLogger(__name__)


def utc_day(now: datetime | None = None) -> str:
    """The current UTC calendar day as YYYY-MM-DD — the daily-limit window."""
    moment = now or datetime.now(timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class DailyState:
    """Counters that reset at UTC midnight."""

    day: str = field(default_factory=utc_day)
    realized_pnl: float = 0.0
    trades_opened: int = 0
    trades_settled: int = 0
    wins: int = 0
    losses: int = 0
    halted: bool = False
    halt_reason: str = ""

    def roll_over_if_needed(self, now: datetime | None = None) -> bool:
        """Reset the counters if the UTC day has changed. Returns True if it did."""
        today = utc_day(now)
        if today == self.day:
            return False
        self.day = today
        self.realized_pnl = 0.0
        self.trades_opened = 0
        self.trades_settled = 0
        self.wins = 0
        self.losses = 0
        self.halted = False
        self.halt_reason = ""
        return True


class StateStore:
    """Loads and atomically persists DailyState, and appends the trade journal."""

    def __init__(self, state_path: str, journal_path: str) -> None:
        self.state_path = state_path
        self.journal_path = journal_path
        self.daily = self._load()

    def _load(self) -> DailyState:
        try:
            with open(self.state_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except FileNotFoundError:
            return DailyState()
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("could not read state file %s (%s) — starting fresh", self.state_path, exc)
            return DailyState()

        known = {f for f in DailyState.__dataclass_fields__}  # type: ignore[attr-defined]
        return DailyState(**{k: v for k, v in raw.items() if k in known})

    def save(self) -> None:
        """Write state atomically so a crash mid-write cannot corrupt it."""
        directory = os.path.dirname(os.path.abspath(self.state_path))
        os.makedirs(directory, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
        )
        try:
            with handle:
                json.dump(asdict(self.daily), handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(handle.name, self.state_path)
        except BaseException:
            # Never leave a stray temp file behind if the write failed.
            try:
                os.unlink(handle.name)
            except OSError:
                pass
            raise

    def journal(self, event: dict) -> None:
        """Append one event to the trade journal. Never raises into the trade loop."""
        record = {"ts": datetime.now(timezone.utc).isoformat(), **event}
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.journal_path)), exist_ok=True)
            with open(self.journal_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
        except OSError as exc:
            log.warning("could not append to journal %s: %s", self.journal_path, exc)

    def record_open(self, event: dict) -> None:
        self.daily.trades_opened += 1
        self.journal({"event": "open", **event})
        self.save()

    def record_settlement(self, profit: float, event: dict) -> None:
        self.daily.trades_settled += 1
        self.daily.realized_pnl += profit
        if profit >= 0:
            self.daily.wins += 1
        else:
            self.daily.losses += 1
        self.journal({"event": "settled", "profit": profit, **event})
        self.save()

    def halt(self, reason: str) -> None:
        if self.daily.halted:
            return
        self.daily.halted = True
        self.daily.halt_reason = reason
        self.journal({"event": "halt", "reason": reason})
        self.save()
