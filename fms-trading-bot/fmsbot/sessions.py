"""Trading hours.

The blueprint asks for "a trading-session filter focused on liquid market
periods", and it belongs here rather than inside a strategy: it is a rule
about when the account trades, not about what a pattern means. Both the
simulator and the live bot ask this same object, so a backtest and a live
session cannot disagree about when the market was open to them.

The hours are UTC, because a broker's server time drifts with its own
daylight-saving rules and an account that silently shifts an hour twice a
year is worse than one that never moves.
"""

from __future__ import annotations

from datetime import datetime, timezone


class Sessions:
    """Hours the account may open trades in. Empty spec means always."""

    def __init__(self, spec: str = ""):
        self.spec = (spec or "").strip()
        self.windows: list[tuple[int, int]] = []
        for part in self.spec.split(","):
            part = part.strip()
            if not part:
                continue
            start, _, end = part.partition("-")
            if not end:
                raise ValueError(f"wants ranges like 7-16, not {part!r}")
            a, b = int(start), int(end)
            if not (0 <= a <= 23 and 0 < b <= 24):
                raise ValueError(f"hour out of range in {part!r}")
            self.windows.append((a, b))

    @property
    def enabled(self) -> bool:
        return bool(self.windows)

    def allows(self, timestamp: float) -> bool:
        """May a trade be opened at this moment?"""
        if not self.windows:
            return True
        hour = datetime.fromtimestamp(timestamp, timezone.utc).hour
        for start, end in self.windows:
            # A window like 22-3 crosses midnight and covers both ends.
            if start < end:
                if start <= hour < end:
                    return True
            elif hour >= start or hour < end:
                return True
        return False

    def describe(self) -> str:
        if not self.windows:
            return "any hour"
        return ", ".join(f"{a:02d}:00-{b:02d}:00 UTC" for a, b in self.windows)
