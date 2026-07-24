"""EMA-crossover strategy with RSI filter and ATR-based exits.

Signal on the last CLOSED bar:
  LONG : fast EMA crosses above slow EMA and RSI > rsi_floor
  SHORT: fast EMA crosses below slow EMA and RSI < rsi_ceiling
  SL = entry -/+ ATR * atr_sl_mult, TP = entry +/- ATR * atr_tp_mult
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .broker.base import Bar
from .config import Settings
from .indicators import atr, ema_series, rsi


@dataclass
class Signal:
    side: str           # "buy" | "sell"
    sl_distance: float  # price units from entry to stop
    tp_distance: float
    reason: str


class EmaCrossStrategy:
    def __init__(self, settings: Settings):
        self.s = settings

    def min_bars(self) -> int:
        return max(self.s.ema_slow + 2, self.s.rsi_period + 2, self.s.atr_period + 2)

    def signal(self, bars: list[Bar]) -> Optional[Signal]:
        """`bars` oldest-first; the last element must be a CLOSED bar."""
        if len(bars) < self.min_bars():
            return None
        closes = [b.close for b in bars]
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]

        fast = ema_series(closes, self.s.ema_fast)
        slow = ema_series(closes, self.s.ema_slow)
        if not fast or not slow or len(fast) < 2 or len(slow) < 2:
            return None
        # align series tails (they have different lengths)
        f_now, f_prev = fast[-1], fast[-2]
        s_now, s_prev = slow[-1], slow[-2]

        r = rsi(closes, self.s.rsi_period)
        a = atr(highs, lows, closes, self.s.atr_period)
        if r is None or a is None or a <= 0:
            return None

        return self._cross_signal(f_now, f_prev, s_now, s_prev, r, a)

    def trend_signal(self, bars: list[Bar]) -> Optional[Signal]:
        """Direction of the CURRENT trend, without waiting for a crossover.

        Used by interval entry mode: fast EMA above slow EMA means buy,
        below means sell. Fires on every call, so the caller must rate-limit.
        """
        if len(bars) < self.min_bars():
            return None
        closes = [b.close for b in bars]
        fast = ema_series(closes, self.s.ema_fast)
        slow = ema_series(closes, self.s.ema_slow)
        a = atr([b.high for b in bars], [b.low for b in bars], closes, self.s.atr_period)
        if not fast or not slow or a is None or a <= 0:
            return None
        side = "buy" if fast[-1] > slow[-1] else "sell"
        return Signal(side, a * self.s.atr_sl_mult, a * self.s.atr_tp_mult,
                      f"interval entry, trend {side}")

    def _cross_signal(self, f_now, f_prev, s_now, s_prev, r, a) -> Optional[Signal]:
        crossed_up = f_prev <= s_prev and f_now > s_now
        crossed_down = f_prev >= s_prev and f_now < s_now
        if crossed_up and r > self.s.rsi_floor:
            return Signal("buy", a * self.s.atr_sl_mult, a * self.s.atr_tp_mult,
                          f"EMA{self.s.ema_fast}x{self.s.ema_slow} up, RSI {r:.0f}")
        if crossed_down and r < self.s.rsi_ceiling:
            return Signal("sell", a * self.s.atr_sl_mult, a * self.s.atr_tp_mult,
                          f"EMA{self.s.ema_fast}x{self.s.ema_slow} down, RSI {r:.0f}")
        return None
