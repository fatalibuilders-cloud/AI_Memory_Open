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




class PinBar(VecStrategy):
    """Rejection at the moving average, traded with the trend.

    The price-action reading: in a trend, price pulls back to the 21
    moving average, the side in control rejects it, and the bar closes
    having given back most of its own range. The long wick is the
    rejection; the small body is what makes it a rejection rather than a
    directional bar that happens to have a tail.

    Three conditions, all measured on the closed bar:

      * **Shape.** The wick on the rejected side is at least
        `pin_wick_ratio` of the bar's range and the body at most
        `pin_body_max` of it.
      * **Level.** The bar must reach the moving average -- within
        `pin_level_atr` ATR of it. A pin bar in open space is just a bar
        with a wick, and that is the difference between this and noise.
      * **Trend.** Only with the moving average's slope. A rejection
        against the trend is somebody else's trade.

    The stop goes beyond the wick's tip, which is the price that says the
    rejection failed, and the target is `rr_target` times that distance.
    """
    name = "pin_bar"

    def warmup(self) -> int:
        return max(self.s.pin_ma_period + 3, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "open": [b.open for b in bars],
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": closes,
            "ma": ema_full(closes, self.s.pin_ma_period),
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        ma, prev_ma, v = a["ma"][i], a["ma"][i - 2], a["atr"][i]
        if None in (ma, prev_ma, v) or v <= 0:
            return None
        high, low = a["high"][i], a["low"][i]
        opened, close = a["open"][i], a["close"][i]
        span = high - low
        if span <= 0:
            return None
        body = abs(close - opened)
        if body > span * self.s.pin_body_max:
            return None

        upper = high - max(opened, close)
        lower = min(opened, close) - low
        near = abs(ma - close) <= v * self.s.pin_level_atr or (low <= ma <= high)
        if not near:
            return None

        rising = ma > prev_ma
        if upper >= span * self.s.pin_wick_ratio and not rising:
            # sellers rejected the move up to the average, in a downtrend
            risk = high - close + v * 0.1
            if risk <= 0:
                return None
            return VecSignal("sell", risk, risk * self.s.rr_target,
                             f"pin rejection at the {self.s.pin_ma_period} MA")
        if lower >= span * self.s.pin_wick_ratio and rising:
            risk = close - low + v * 0.1
            if risk <= 0:
                return None
            return VecSignal("buy", risk, risk * self.s.rr_target,
                             f"pin rejection at the {self.s.pin_ma_period} MA")
        return None


class InsideBarFakeout(VecStrategy):
    """The inside bar false breakout: a stop run that fails.

    Three bars. A mother bar, an inside bar contained within it, then a
    bar that breaks out of the mother's range and closes back inside it.
    The break takes the stops resting beyond the mother bar; the close
    back inside says the move had nothing behind it, so the trade is the
    other way.

    The distinguishing test is the close, and it is the whole pattern: a
    bar that breaks the mother's high and CLOSES above it is a breakout,
    and trading that as a reversal is how the pattern loses money. The
    stop goes beyond the false break's extreme.
    """
    name = "inside_bar_fakeout"

    def warmup(self) -> int:
        return max(self.s.atr_period + 4, 6)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": closes,
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        v = a["atr"][i]
        if v is None or v <= 0 or i < 3:
            return None
        mh, ml = a["high"][i - 2], a["low"][i - 2]       # mother bar
        ih, il = a["high"][i - 1], a["low"][i - 1]       # inside bar
        if not (ih < mh and il > ml):
            return None                                  # not an inside bar
        if mh - ml <= 0:
            return None

        high, low, close = a["high"][i], a["low"][i], a["close"][i]
        if high > mh and ml <= close <= mh:
            # broke the mother's high and closed back inside it
            risk = high - close + v * 0.1
            if risk <= 0:
                return None
            return VecSignal("sell", risk, risk * self.s.rr_target,
                             "inside bar false breakout, upside")
        if low < ml and ml <= close <= mh:
            risk = close - low + v * 0.1
            if risk <= 0:
                return None
            return VecSignal("buy", risk, risk * self.s.rr_target,
                             "inside bar false breakout, downside")
        return None




class EngulfingBar(VecStrategy):
    """A bar whose body swallows the one before it, at a level, with trend.

    The reading: the previous bar's participants are all offside at once.
    A bullish engulfing opens at or below the prior close and closes at or
    above the prior open, so everyone who sold that bar is now underwater.

    As with the pin bar, the level is what separates this from noise --
    engulfing bodies happen constantly in open space. The stop goes beyond
    the engulfing bar's own extreme, which is where the reading fails.
    """
    name = "engulfing"

    def warmup(self) -> int:
        return max(self.s.pin_ma_period + 3, self.s.atr_period + 2)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "open": [b.open for b in bars],
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": closes,
            "ma": ema_full(closes, self.s.pin_ma_period),
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        ma, prev_ma, v = a["ma"][i], a["ma"][i - 2], a["atr"][i]
        if None in (ma, prev_ma, v) or v <= 0:
            return None
        o, c = a["open"][i], a["close"][i]
        po, pc = a["open"][i - 1], a["close"][i - 1]
        high, low = a["high"][i], a["low"][i]
        if abs(c - o) <= abs(pc - po):
            return None                      # not engulfing the prior body
        near = abs(ma - c) <= v * self.s.pin_level_atr or (low <= ma <= high)
        if not near:
            return None
        rising = ma > prev_ma

        if c > o and pc < po and o <= pc and c >= po and rising:
            risk = c - low + v * 0.1
            if risk <= 0:
                return None
            return VecSignal("buy", risk, risk * self.s.rr_target,
                             "bullish engulfing at the level")
        if c < o and pc > po and o >= pc and c <= po and not rising:
            risk = high - c + v * 0.1
            if risk <= 0:
                return None
            return VecSignal("sell", risk, risk * self.s.rr_target,
                             "bearish engulfing at the level")
        return None


class InsideBarBreakout(VecStrategy):
    """The inside bar as a continuation: a pause, then the trend resumes.

    A mother bar, an inside bar showing the market hesitating, then a
    close beyond the mother bar in the direction the trend was already
    going. The stop goes on the far side of the mother bar, which is what
    the pattern says should not be revisited.

    This is the OPPOSITE trade to `inside_bar_fakeout`, and the difference
    is entirely in where the bar closes: beyond the mother bar is a
    continuation, back inside it is a failed break. Both are real; taking
    the wrong one is how the inside bar earns its reputation for losing
    money.
    """
    name = "inside_bar_breakout"

    def warmup(self) -> int:
        return max(self.s.pin_ma_period + 4, self.s.atr_period + 4, 6)

    def precompute(self, bars):
        closes = [b.close for b in bars]
        return {
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": closes,
            "ma": ema_full(closes, self.s.pin_ma_period),
            "atr": atr_full([b.high for b in bars], [b.low for b in bars],
                            closes, self.s.atr_period),
        }

    def at(self, i, a):
        ma, prev_ma, v = a["ma"][i], a["ma"][i - 2], a["atr"][i]
        if None in (ma, prev_ma, v) or v <= 0 or i < 3:
            return None
        mh, ml = a["high"][i - 2], a["low"][i - 2]
        ih, il = a["high"][i - 1], a["low"][i - 1]
        if not (ih < mh and il > ml) or mh - ml <= 0:
            return None
        close = a["close"][i]
        rising = ma > prev_ma

        if close > mh and rising:
            risk = close - ml + v * 0.1          # stop below the mother bar
            if risk <= 0:
                return None
            return VecSignal("buy", risk, risk * self.s.rr_target,
                             "inside bar breakout with the trend")
        if close < ml and not rising:
            risk = mh - close + v * 0.1
            if risk <= 0:
                return None
            return VecSignal("sell", risk, risk * self.s.rr_target,
                             "inside bar breakdown with the trend")
        return None


VEC_STRATEGIES: dict[str, type[VecStrategy]] = {
    cls.name: cls for cls in (EmaCross, MeanReversion, Breakout, TrendAlways,
                              InvertedEmaCross, RsiReversion, Momentum,
                              BollingerBreakout, LiquiditySweep, PinBar,
                              InsideBarFakeout, EngulfingBar,
                              InsideBarBreakout)
}
