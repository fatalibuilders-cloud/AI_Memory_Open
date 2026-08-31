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


class InvertedEmaCross(EmaCross):
    """The EMA crossover, traded the other way.

    Live results showed the plain crossover winning far less than chance on
    this market, which is information: a signal that reliably picks the
    wrong side has predictive content once flipped. Whether the edge
    survives the spread is exactly what the search has to decide.
    """
    name = "ema_cross_inverted"

    def at(self, i, a):
        signal = super().at(i, a)
        if signal is None:
            return None
        other = "sell" if signal.side == "buy" else "buy"
        return VecSignal(other, signal.sl_distance, signal.tp_distance,
                         "inverted " + signal.reason)


class RsiReversion(VecStrategy):
    """Buy oversold, sell overbought — no trend filter, RSI alone."""
    name = "rsi_reversion"

    def warmup(self) -> int:
        return max(self.s.rsi_period + 2, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "rsi": rsi_full(closes, self.s.rsi_period),
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        r, prev, v = a["rsi"][i], a["rsi"][i - 1], a["atr"][i]
        if None in (r, prev, v) or v <= 0:
            return None
        sl, tp = self._exits(v)
        # act on the turn out of the extreme, not while still in it
        if prev <= self.s.rsi_oversold < r:
            return VecSignal("buy", sl, tp, f"RSI turning up from {prev:.0f}")
        if prev >= self.s.rsi_overbought > r:
            return VecSignal("sell", sl, tp, f"RSI turning down from {prev:.0f}")
        return None


class Momentum(VecStrategy):
    """Rate of change: trade when price has moved decisively, not on a cross."""
    name = "momentum"

    def warmup(self) -> int:
        return max(self.s.ema_slow + 2, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "close": closes,
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        look = self.s.ema_slow
        if i < look:
            return None
        v = a["atr"][i]
        if v is None or v <= 0:
            return None
        change = a["close"][i] - a["close"][i - look]
        # require the move to be large relative to normal volatility
        threshold = v * self.s.atr_sl_mult
        sl, tp = self._exits(v)
        if change > threshold:
            return VecSignal("buy", sl, tp, f"momentum +{change/v:.1f} ATR")
        if change < -threshold:
            return VecSignal("sell", sl, tp, f"momentum {change/v:.1f} ATR")
        return None


class BollingerBreakout(VecStrategy):
    """Trade the break OUT of the bands, the opposite of mean reversion."""
    name = "bollinger_breakout"

    def warmup(self) -> int:
        return max(self.s.bb_period + 2, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        lower, mid, upper = bollinger_full(closes, self.s.bb_period, self.s.bb_std)
        return {
            "lower": lower, "upper": upper, "close": closes,
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        up, lo, v = a["upper"][i], a["lower"][i], a["atr"][i]
        up_prev, lo_prev = a["upper"][i - 1], a["lower"][i - 1]
        if None in (up, lo, up_prev, lo_prev, v) or v <= 0:
            return None
        price, prev = a["close"][i], a["close"][i - 1]
        sl, tp = self._exits(v)
        if prev <= up_prev and price > up:
            return VecSignal("buy", sl, tp, "broke above the upper band")
        if prev >= lo_prev and price < lo:
            return VecSignal("sell", sl, tp, "broke below the lower band")
        return None




class LiquiditySweep(VecStrategy):
    """Sweep of a session level, structure break, entry on the retest.

    The sequence this looks for, in order:

      1. **Trend.** A higher-timeframe EMA, built by aggregating the entry
         bars, decides which side may be taken. Counter-trend setups are
         discarded rather than reversed.
      2. **Liquidity.** The high and low of the previous session are where
         resting stops sit, so those are the levels price reaches for.
      3. **The sweep.** Price must trade through the level and close back
         inside it, leaving a wick beyond it worth at least `sweep_reject`
         of the bar's range. A close beyond the level is a breakout, not a
         sweep -- that is the test which separates the two.
      4. **The structure break.** Within `structure_window` bars, price
         must close beyond the swing that formed the sweep, which is what
         makes it a reversal rather than a pause.
      5. **The stop** goes beyond the sweep's extreme -- the point that
         invalidates the idea -- not at a fixed distance. The target is
         `rr_target` times that risk.

    Every part is measured on closed bars only. The sweep extreme is known
    before the entry bar, so there is no lookahead.
    """
    name = "liquidity_sweep"

    def warmup(self) -> int:
        return max(self.s.session_bars * 2,
                   self.s.htf_ratio * self.s.ema_slow,
                   self.s.atr_period + 2) + 2

    def precompute(self, bars):
        closes = [b.close for b in bars]
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]

        # Higher-timeframe trend: aggregate N entry bars into one, take an
        # EMA of those closes, then spread it back over the entry bars so
        # bar i knows the trend as of the last COMPLETED higher bar.
        ratio = max(1, self.s.htf_ratio)
        htf_close = [closes[i] for i in range(ratio - 1, len(closes), ratio)]
        fast = ema_full(htf_close, self.s.ema_fast)
        slow = ema_full(htf_close, self.s.ema_slow)
        trend: list[Optional[int]] = []
        for i in range(len(bars)):
            k = i // ratio - 1          # last completed higher-timeframe bar
            if k < 0 or k >= len(fast) or fast[k] is None or slow[k] is None:
                trend.append(None)
            else:
                trend.append(1 if fast[k] > slow[k] else -1)

        # Previous session's extremes: the pool of resting stops.
        n = self.s.session_bars
        prev_high: list[Optional[float]] = []
        prev_low: list[Optional[float]] = []
        for i in range(len(bars)):
            start, end = i - 2 * n, i - n
            if start < 0:
                prev_high.append(None)
                prev_low.append(None)
            else:
                prev_high.append(max(highs[start:end]))
                prev_low.append(min(lows[start:end]))

        return {"high": highs, "low": lows, "close": closes,
                "trend": trend, "prev_high": prev_high, "prev_low": prev_low,
                "atr": atr_full(highs, lows, closes, self.s.atr_period)}

    def _swept(self, a, i, side) -> Optional[tuple[int, float]]:
        """Index and extreme of a sweep within the structure window."""
        for j in range(max(1, i - self.s.structure_window), i):
            level = a["prev_high"][j] if side == "sell" else a["prev_low"][j]
            if level is None:
                continue
            span = a["high"][j] - a["low"][j]
            if span <= 0:
                continue
            if side == "sell":
                # Through the level, then closed back under it.
                if a["high"][j] <= level or a["close"][j] > level:
                    continue
                # And rejected: the wick above must be a real share of the
                # bar. Measuring the give-back against the poke instead
                # would be vacuous, since closing back inside the level
                # always gives the whole poke back.
                if (a["high"][j] - a["close"][j]) / span >= self.s.sweep_reject:
                    return j, a["high"][j]
            else:
                if a["low"][j] >= level or a["close"][j] < level:
                    continue
                if (a["close"][j] - a["low"][j]) / span >= self.s.sweep_reject:
                    return j, a["low"][j]
        return None

    def at(self, i, a):
        trend, v = a["trend"][i], a["atr"][i]
        if trend is None or v is None or v <= 0:
            return None
        side = "buy" if trend > 0 else "sell"

        # A buy follows a sweep of the LOW (stops taken below, then up).
        sweep = self._swept(a, i, side)
        if sweep is None:
            return None
        j, extreme = sweep

        # Structure break: close beyond the swing the sweep created.
        window = a["high"][j:i] if side == "buy" else a["low"][j:i]
        if not window:
            return None
        price = a["close"][i]
        if side == "buy":
            if price <= max(window):
                return None
            risk = price - extreme
        else:
            if price >= min(window):
                return None
            risk = extreme - price
        if risk <= 0:
            return None
        # Beyond the invalidation point, with a little air for the spread.
        risk += v * 0.1
        return VecSignal(side, risk, risk * self.s.rr_target,
                         f"{side} after sweep, {self.s.rr_target:.1f}R")


VEC_STRATEGIES: dict[str, type[VecStrategy]] = {
    cls.name: cls for cls in (EmaCross, MeanReversion, Breakout, TrendAlways,
                              InvertedEmaCross, RsiReversion, Momentum,
                              BollingerBreakout, LiquiditySweep)
}
