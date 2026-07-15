"""Pure-python technical indicators (no numpy/pandas dependency)."""

from __future__ import annotations

from typing import Optional, Sequence


def sma(values: Sequence[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema(values: Sequence[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    k = 2.0 / (period + 1)
    result = sum(values[:period]) / period  # seed with SMA
    for v in values[period:]:
        result = v * k + result * (1 - k)
    return result


def rsi(values: Sequence[float], period: int = 14) -> Optional[float]:
    """Wilder's RSI over closing prices."""
    if len(values) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        delta = values[i] - values[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses -= delta
    avg_gain = gains / period
    avg_loss = losses / period
    for i in range(period + 1, len(values)):
        delta = values[i] - values[i - 1]
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def bollinger(values: Sequence[float], period: int = 20, num_std: float = 2.0):
    """Returns (lower, middle, upper) or None if not enough data."""
    if len(values) < period:
        return None
    window = values[-period:]
    mid = sum(window) / period
    var = sum((v - mid) ** 2 for v in window) / period
    std = var ** 0.5
    return (mid - num_std * std, mid, mid + num_std * std)
