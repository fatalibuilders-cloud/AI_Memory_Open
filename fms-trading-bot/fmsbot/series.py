"""Whole-series indicator computation for backtesting.

`fmsbot.indicators` computes one value from a window, which is what the live
bot needs (one call per closed bar). Replaying thousands of bars that way is
O(n^2) and unusably slow, so these functions compute the entire series in a
single pass and return lists aligned index-for-index with the input bars
(None where there is not yet enough history).
"""

from __future__ import annotations

from typing import Optional, Sequence


def ema_full(values: Sequence[float], period: int) -> list[Optional[float]]:
    out: list[Optional[float]] = [None] * len(values)
    if len(values) < period:
        return out
    k = 2.0 / (period + 1)
    value = sum(values[:period]) / period
    out[period - 1] = value
    for i in range(period, len(values)):
        value = values[i] * k + value * (1 - k)
        out[i] = value
    return out


def rsi_full(values: Sequence[float], period: int = 14) -> list[Optional[float]]:
    out: list[Optional[float]] = [None] * len(values)
    if len(values) < period + 1:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = values[i] - values[i - 1]
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    avg_gain, avg_loss = gains / period, losses / period
    out[period] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    for i in range(period + 1, len(values)):
        d = values[i] - values[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(d, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-d, 0.0)) / period
        out[i] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return out


def bollinger_full(values: Sequence[float], period: int = 20, num_std: float = 2.0):
    """Returns (lower, mid, upper) lists aligned with `values`."""
    n = len(values)
    lower: list[Optional[float]] = [None] * n
    mid: list[Optional[float]] = [None] * n
    upper: list[Optional[float]] = [None] * n
    if n < period:
        return lower, mid, upper
    total = sum(values[:period])
    total_sq = sum(v * v for v in values[:period])
    for i in range(period - 1, n):
        if i >= period:
            out = values[i - period]
            total += values[i] - out
            total_sq += values[i] * values[i] - out * out
        m = total / period
        var = max(total_sq / period - m * m, 0.0)
        sd = var ** 0.5
        lower[i], mid[i], upper[i] = m - num_std * sd, m, m + num_std * sd
    return lower, mid, upper


def rolling_max(values: Sequence[float], period: int) -> list[Optional[float]]:
    out: list[Optional[float]] = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = max(values[i - period + 1: i + 1])
    return out


def rolling_min(values: Sequence[float], period: int) -> list[Optional[float]]:
    out: list[Optional[float]] = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = min(values[i - period + 1: i + 1])
    return out


def atr_full(highs: Sequence[float], lows: Sequence[float],
             closes: Sequence[float], period: int = 14) -> list[Optional[float]]:
    n = len(closes)
    out: list[Optional[float]] = [None] * n
    if n < period + 1:
        return out
    trs = [0.0]
    for i in range(1, n):
        trs.append(max(highs[i] - lows[i],
                       abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    value = sum(trs[1:period + 1]) / period
    out[period] = value
    for i in range(period + 1, n):
        value = (value * (period - 1) + trs[i]) / period
        out[i] = value
    return out
