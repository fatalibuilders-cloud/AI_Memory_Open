"""Counting the independent reasons a setup has to be taken.

The price-action literature's central filter: a pin bar in open space is
noise, the same pin bar where a support level, a moving average and a
Fibonacci retracement all sit is a setup. The rule is not that more
factors make a pattern more likely to work -- nobody has shown that -- it
is that requiring several is a way to trade far less and pay the spread
far less often while you find out whether the pattern works at all.

The factors here are the ones that can be computed from bars alone:

  * **trend** -- the slower average is sloping the way the trade wants
  * **ma8 / ma21** -- price is at one of the two dynamic levels
  * **fib50 / fib61** -- price is at the halfway or 61.8% retracement of
    the most recent swing
  * **level** -- price is at a prior swing high or low

Trend-line and supply-zone factors are deliberately absent: both need a
judgement about which lines matter, and a rule invented to stand in for
that judgement would be counted as evidence without being any.
"""

from __future__ import annotations

from .series import (efficiency_full, ema_full, rolling_max,
                     rolling_min)

#: Golden-ratio retracements, as fractions of the swing.
FIB_LEVELS = ((0.5, "fib50"), (0.618, "fib61"))


def arrays(bars, settings) -> dict:
    """Everything the factor count needs, computed once over the series."""
    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    look = max(2, settings.fib_lookback)
    return {
        "ma_fast": ema_full(closes, settings.ma_fast_period),
        "ma_slow": ema_full(closes, settings.pin_ma_period),
        "swing_high": rolling_max(highs, look),
        "swing_low": rolling_min(lows, look),
        # A prior swing high/low over a shorter window is the horizontal
        # level price has already turned at.
        "level_high": rolling_max(highs, max(2, look // 4)),
        "level_low": rolling_min(lows, max(2, look // 4)),
        # Not a confluence factor: a separate question about whether this
        # market is worth trading at all.
        "efficiency": efficiency_full(closes, settings.efficiency_lookback),
    }


def factors(a: dict, i: int, side: str, settings, price: float,
            atr_value: float) -> list[str]:
    """Which factors line up at bar `i` for a trade on `side`."""
    if atr_value <= 0:
        return []
    near = atr_value * settings.pin_level_atr
    found = []

    slow, prev_slow = a["ma_slow"][i], a["ma_slow"][i - 2]
    if slow is not None and prev_slow is not None:
        rising = slow > prev_slow
        if (side == "buy") == rising:
            found.append("trend")
        if abs(price - slow) <= near:
            found.append("ma21")
    fast = a["ma_fast"][i]
    if fast is not None and abs(price - fast) <= near:
        found.append("ma8")

    high, low = a["swing_high"][i - 1], a["swing_low"][i - 1]
    if high is not None and low is not None and high > low:
        span = high - low
        for ratio, name in FIB_LEVELS:
            # Retracing from the swing's far end, whichever way it ran.
            for level in (high - span * ratio, low + span * ratio):
                if abs(price - level) <= near:
                    found.append(name)
                    break

    for key in ("level_high", "level_low"):
        level = a[key][i - 1]
        if level is not None and abs(price - level) <= near:
            found.append("level")
            break

    return found
