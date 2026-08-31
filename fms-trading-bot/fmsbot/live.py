"""Trade any of the searchable strategies live, alone or together.

The strategies in `vecstrategy` precompute indicator arrays over a whole
series so a parameter search can run thousands of variants. The live bot
asks a different question -- "what is the signal on the newest closed
bar?" -- so this adapts one to the other, and lets several be required to
agree before a trade is taken.

Why agreement is worth having: every strategy here has been measured
against shuffled copies of its own data and none has shown an edge on its
own. Requiring confluence does not create one either, but it does cut the
trade count sharply, and fewer trades means less spread paid while you
find out. What it must not do is quietly loosen the exits, so a combined
signal takes the WIDEST stop of its members -- nobody's invalidation
point ends up inside the stop -- and the most conservative reward:risk of
any of them.
"""

from __future__ import annotations

import logging
from typing import Optional

from .broker.base import Bar
from .strategy import Signal
from .vecstrategy import VEC_STRATEGIES, VecStrategy

log = logging.getLogger("fmsbot.live")


class VecAdapter:
    """One vectorised strategy, answering for the newest closed bar."""

    def __init__(self, vec: VecStrategy):
        self.vec = vec
        self.name = vec.name

    def min_bars(self) -> int:
        return self.vec.warmup() + 2

    def _at_last(self, bars: list[Bar]) -> Optional[Signal]:
        if len(bars) < self.min_bars():
            return None
        arrays = self.vec.precompute(bars)
        got = self.vec.at(len(bars) - 1, arrays)
        if got is None:
            return None
        return Signal(got.side, got.sl_distance, got.tp_distance, got.reason)

    def signal(self, bars: list[Bar]) -> Optional[Signal]:
        return self._at_last(bars)

    def trend_signal(self, bars: list[Bar]) -> Optional[Signal]:
        """Interval mode wants a position whichever way the market leans.

        A setup strategy has no opinion most of the time, and inventing one
        would be worse than staying out, so this is the same question --
        a strategy that is silent stays silent.
        """
        return self._at_last(bars)


class Combined:
    """Several strategies, and the rule for taking them together."""

    def __init__(self, members: list, require_all: bool):
        self.members = members
        self.require_all = require_all
        joiner = " + " if require_all else " or "
        self.name = joiner.join(m.name for m in members)

    def min_bars(self) -> int:
        return max(m.min_bars() for m in self.members)

    def _merge(self, signals: list[Signal]) -> Signal:
        widest = max(s.sl_distance for s in signals)
        # The least generous reward:risk any member asked for.
        ratio = min(s.tp_distance / s.sl_distance for s in signals
                    if s.sl_distance > 0)
        reasons = "; ".join(s.reason for s in signals)
        return Signal(signals[0].side, widest, widest * ratio, reasons)

    def _combine(self, bars: list[Bar], method: str) -> Optional[Signal]:
        got = [getattr(m, method)(bars) for m in self.members]
        live = [s for s in got if s is not None]
        if not live:
            return None
        if not self.require_all:
            return live[0]
        if len(live) != len(self.members):
            return None
        sides = {s.side for s in live}
        if len(sides) != 1:
            return None                 # they disagree, so there is no signal
        return self._merge(live)

    def signal(self, bars: list[Bar]) -> Optional[Signal]:
        return self._combine(bars, "signal")

    def trend_signal(self, bars: list[Bar]) -> Optional[Signal]:
        return self._combine(bars, "trend_signal")


def build_strategy(settings):
    """Turn the STRATEGY setting into something the bot can trade.

        STRATEGY=ema_cross                        one strategy
        STRATEGY=ema_cross+liquidity_sweep        both must agree
        STRATEGY=ema_cross,liquidity_sweep        either may fire

    Unset keeps the EMA crossover the bot has always used.
    """
    raw = (settings.strategy or "").strip()
    if not raw:
        from .strategy import EmaCrossStrategy
        return EmaCrossStrategy(settings)

    require_all = "+" in raw
    parts = [p.strip() for p in raw.replace("+", ",").split(",") if p.strip()]
    unknown = [p for p in parts if p not in VEC_STRATEGIES]
    if unknown:
        raise ValueError(
            f"unknown strategy {', '.join(unknown)}. "
            f"Available: {', '.join(sorted(VEC_STRATEGIES))}")

    members = [VecAdapter(VEC_STRATEGIES[p](settings)) for p in parts]
    if len(members) == 1:
        return members[0]
    log.info("Trading %d strategies, %s", len(members),
             "all must agree" if require_all else "any may fire")
    return Combined(members, require_all)


def strategy_name(strategy) -> str:
    """A stable label for the evidence fingerprint."""
    return getattr(strategy, "name", type(strategy).__name__)
