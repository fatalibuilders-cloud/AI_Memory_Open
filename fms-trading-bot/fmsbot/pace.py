"""Hold a minimum trade rate — and say plainly when it cannot be held.

Setting a target trade count does not produce it. The interval only
controls how often the bot *tries*; whether a try becomes a trade depends
on gates that have nothing to do with the clock — a symbol already
holding a position, a cooldown still running, the open-position limit,
the daily loss cap.

So this does two jobs, and the second matters more than the first:

  1. When the rate is behind target, shorten the interval to catch up,
     down to a floor. This is the part that can be enforced.

  2. When it is behind and shortening the interval will not help, name
     the gate that is actually throttling it. A bot quietly missing its
     target while the operator adjusts the wrong setting is worse than
     one that says "you are positioned in every symbol already".
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field

#: Block reasons, grouped into the thing you would actually change.
#: Order matters: the first match wins, so the specific readings of a
#: refusal must come before the general ones. Two quite different things
#: both mention the spread, and they need opposite responses -- an
#: abnormal widening is temporary and worth waiting out, while a stop too
#: tight to clear the spread is a permanent property of the settings and
#: will block every trade until they change.
CATEGORIES = (
    ("abnormal conditions", "spread spike"),
    ("stop (limit", "stop too tight for the spread"),
    ("cost of the trade", "target too small for the spread"),
    ("cooldown", "cooldown"),
    ("already positioned", "one position per symbol"),
    ("max open positions", "open-position limit"),
    ("trade cap", "trade cap"),
    ("daily trade cap", "trade cap"),
    ("daily loss limit", "daily loss limit"),
    ("paused after", "loss-streak pause"),
    ("consecutive", "loss-streak pause"),
    ("record over", "evidence halt"),
    ("has not proved", "evidence gate"),
    ("spread", "spread filter"),
)


def classify(reason: str) -> str:
    """Which knob a block is really about."""
    low = (reason or "").lower()
    for needle, label in CATEGORIES:
        if needle in low:
            return label
    return "other"


@dataclass
class Pace:
    """Trade-rate control for one account."""

    target_per_hour: float = 0.0
    floor_seconds: int = 5
    #: why entries were refused, over the trailing window
    blocks: Counter = field(default_factory=Counter)
    #: when the shortfall was last reported, so it is said once an hour
    last_warned: float = 0.0

    def record_block(self, reason: str) -> None:
        self.blocks[classify(reason)] += 1

    def rate(self, entry_times: list[float], window: float = 3600.0) -> int:
        cutoff = time.time() - window
        return sum(1 for t in entry_times if t >= cutoff)

    def deficit(self, entry_times: list[float]) -> float:
        """Trades behind the hourly target. Negative means ahead."""
        if self.target_per_hour <= 0:
            return 0.0
        return self.target_per_hour - self.rate(entry_times)

    def effective_interval(self, configured: int, symbols: int,
                           entry_times: list[float]) -> int:
        """How long to wait between attempts on one symbol, right now.

        The interval that would exactly meet the target is
        symbols * 3600 / target. Falling behind shortens it further, in
        proportion to the shortfall, so a quiet spell is made up rather
        than lost. It is never lengthened beyond what was configured and
        never shortened past the floor.
        """
        if self.target_per_hour <= 0 or symbols <= 0:
            return configured
        wanted = max(self.floor_seconds,
                     int(symbols * 3600.0 / self.target_per_hour))
        short = self.deficit(entry_times)
        if short > 0:
            # Behind by half the target halves the interval.
            factor = max(0.25, 1.0 - short / max(self.target_per_hour, 1.0))
            wanted = max(self.floor_seconds, int(wanted * factor))
        return min(configured, wanted) if configured > 0 else wanted

    def shortfall_report(self, entry_times: list[float],
                         symbols: int) -> str | None:
        """Why the target is being missed, at most once an hour."""
        if self.target_per_hour <= 0:
            return None
        done = self.rate(entry_times)
        if done >= self.target_per_hour:
            return None
        # Only judge after a full hour of running, or a fresh start always
        # looks like a shortfall.
        if entry_times and (time.time() - min(entry_times)) < 3600:
            return None
        if time.time() - self.last_warned < 3600:
            return None
        self.last_warned = time.time()

        lines = [f"{done} trades in the last hour, target "
                 f"{self.target_per_hour:.0f}."]
        if self.blocks:
            worst = self.blocks.most_common(3)
            lines.append("What refused the rest:")
            for label, count in worst:
                lines.append(f"  {count} x {label}")
            top = worst[0][0]
            if top in ("stop too tight for the spread",
                       "target too small for the spread"):
                lines.append("This is a SETTINGS problem, not a quiet market: "
                             "it will refuse every trade until the exits "
                             "change.")
            fix = {
                "one position per symbol":
                    "raise MAX_POSITIONS_PER_SYMBOL, or add symbols — the "
                    "interval cannot help while every symbol is occupied",
                "open-position limit":
                    "raise MAX_OPEN_POSITIONS",
                "cooldown":
                    "lower COOLDOWN_SECONDS",
                "trade cap":
                    "raise MAX_TRADES_PER_DAY",
                "spread spike":
                    "spreads have widened abnormally — news or thin "
                    "liquidity. This is temporary and worth waiting out",
                "stop too tight for the spread":
                    "the stop is too close to be worth taking against this "
                    "spread. This will block EVERY trade until the exits "
                    "change: run tune_symbols.py --apply, which sizes them "
                    "so they clear the spread by construction",
                "target too small for the spread":
                    "the target does not clear the round trip, so the trade "
                    "could not pay even when right: run tune_symbols.py "
                    "--apply",
                "spread filter":
                    "a spread check refused it",
                "daily loss limit":
                    "the day's loss limit is doing its job; it is not a "
                    "throughput problem",
                "loss-streak pause":
                    "consecutive losses paused trading",
                "evidence halt":
                    "the record says this configuration loses; trading is "
                    "halted deliberately",
                "evidence gate":
                    "real money needs a proven configuration first",
            }.get(top)
            if fix:
                lines.append(f"Mostly {top} — {fix}.")
        else:
            lines.append("Nothing was refused, so the strategy simply did not "
                         "signal that often. On a faster timeframe it would.")
        self.blocks.clear()
        return "\n".join(lines)
