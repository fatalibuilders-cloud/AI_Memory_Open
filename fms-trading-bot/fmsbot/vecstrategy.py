"""Vectorised strategies for backtesting and parameter search.

Each strategy precomputes its indicator arrays once over the whole bar
series, then answers "what is the signal at bar i?" in constant time. This
is what makes searching thousands of parameter combinations practical.

The `ema_cross` strategy here is the exact logic the live bot trades
(`fmsbot.strategy.EmaCrossStrategy`); the others exist so you can measure
whether any of them clears its own trading costs before you consider
running one live.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .broker.base import Bar
from .series import (atr_full, bollinger_full, ema_full, rolling_max,
                     rolling_min, rsi_full)


@dataclass
class VecSignal:
    side: str
    sl_distance: float
    tp_distance: float
    reason: str


class VecStrategy:
    name = "base"

    def __init__(self, settings):
        self.s = settings

    def warmup(self) -> int:
        raise NotImplementedError

    def precompute(self, bars: list[Bar]) -> dict:
        raise NotImplementedError

    def at(self, i: int, a: dict) -> Optional[VecSignal]:
        raise NotImplementedError

    # shared helper: ATR-based exits
    def _exits(self, atr_value: float) -> tuple[float, float]:
        return atr_value * self.s.atr_sl_mult, atr_value * self.s.atr_tp_mult


class EmaCross(VecStrategy):
    """Trend following: fast EMA crosses slow EMA, RSI confirms."""
    name = "ema_cross"

    def warmup(self) -> int:
        return max(self.s.ema_slow + 2, self.s.rsi_period + 2, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "fast": ema_full(closes, self.s.ema_fast),
            "slow": ema_full(closes, self.s.ema_slow),
            "rsi": rsi_full(closes, self.s.rsi_period),
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        f, fp = a["fast"][i], a["fast"][i - 1]
        s, sp = a["slow"][i], a["slow"][i - 1]
        r, v = a["rsi"][i], a["atr"][i]
        if None in (f, fp, s, sp, r, v) or v <= 0:
            return None
        sl, tp = self._exits(v)
        if fp <= sp and f > s and r > self.s.rsi_floor:
            return VecSignal("buy", sl, tp, f"EMA cross up, RSI {r:.0f}")
        if fp >= sp and f < s and r < self.s.rsi_ceiling:
            return VecSignal("sell", sl, tp, f"EMA cross down, RSI {r:.0f}")
        return None


class MeanReversion(VecStrategy):
    """Fade extremes: buy a close below the lower Bollinger band with RSI
    oversold, sell a close above the upper band with RSI overbought."""
    name = "mean_reversion"

    def warmup(self) -> int:
        return max(self.s.bb_period + 2, self.s.rsi_period + 2, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        lower, mid, upper = bollinger_full(closes, self.s.bb_period, self.s.bb_std)
        return {
            "lower": lower, "mid": mid, "upper": upper,
            "rsi": rsi_full(closes, self.s.rsi_period),
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
            "close": closes,
        }

    def at(self, i, a):
        lo, up, r, v = a["lower"][i], a["upper"][i], a["rsi"][i], a["atr"][i]
        if None in (lo, up, r, v) or v <= 0:
            return None
        price = a["close"][i]
        sl, tp = self._exits(v)
        if price < lo and r <= self.s.rsi_oversold:
            return VecSignal("buy", sl, tp, f"below lower band, RSI {r:.0f}")
        if price > up and r >= self.s.rsi_overbought:
            return VecSignal("sell", sl, tp, f"above upper band, RSI {r:.0f}")
        return None


class Breakout(VecStrategy):
    """Donchian breakout: buy a close above the highest high of the last N
    bars, sell below the lowest low."""
    name = "breakout"

    def warmup(self) -> int:
        return max(self.s.donchian_period + 2, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "hh": rolling_max([b.high for b in bars], self.s.donchian_period),
            "ll": rolling_min([b.low for b in bars], self.s.donchian_period),
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
            "close": closes,
        }

    def at(self, i, a):
        # compare against the channel formed BEFORE this bar
        hh, ll, v = a["hh"][i - 1], a["ll"][i - 1], a["atr"][i]
        if None in (hh, ll, v) or v <= 0:
            return None
        price = a["close"][i]
        sl, tp = self._exits(v)
        if price > hh:
            return VecSignal("buy", sl, tp, f"breakout above {self.s.donchian_period}-bar high")
        if price < ll:
            return VecSignal("sell", sl, tp, f"breakdown below {self.s.donchian_period}-bar low")
        return None


class TrendAlways(VecStrategy):
    """Interval mode's logic: always positioned with the EMA trend."""
    name = "trend_always"

    def warmup(self) -> int:
        return max(self.s.ema_slow + 2, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "fast": ema_full(closes, self.s.ema_fast),
            "slow": ema_full(closes, self.s.ema_slow),
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        f, s, v = a["fast"][i], a["slow"][i], a["atr"][i]
        if None in (f, s, v) or v <= 0:
            return None
        sl, tp = self._exits(v)
        side = "buy" if f > s else "sell"
        return VecSignal(side, sl, tp, f"trend {side}")


VEC_STRATEGIES: dict[str, type[VecStrategy]] = {
    cls.name: cls for cls in (EmaCross, MeanReversion, Breakout, TrendAlways)
}
