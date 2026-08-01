"""Technical indicators in pure Python.

No numpy or pandas: the bot's only runtime dependency is a WebSocket client,
which keeps the container small and the maths auditable line by line.

Every function takes oldest-first sequences and returns an oldest-first list
whose length matches the input, padding the warm-up region with None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Candle:
    """One OHLC bar as returned by Deriv's ticks_history in candle style."""

    epoch: int
    open: float
    high: float
    low: float
    close: float

    @classmethod
    def from_api(cls, raw: dict) -> "Candle":
        return cls(
            epoch=int(raw["epoch"]),
            open=float(raw["open"]),
            high=float(raw["high"]),
            low=float(raw["low"]),
            close=float(raw["close"]),
        )


def ema(values: Sequence[float], period: int) -> list[float | None]:
    """Exponential moving average, seeded with the simple average of the
    first `period` values (the conventional seeding used by charting tools)."""
    if period < 1:
        raise ValueError("period must be >= 1")
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out

    seed = sum(values[:period]) / period
    out[period - 1] = seed
    multiplier = 2.0 / (period + 1)
    prev = seed
    for i in range(period, len(values)):
        prev = (values[i] - prev) * multiplier + prev
        out[i] = prev
    return out


def rsi(values: Sequence[float], period: int = 14) -> list[float | None]:
    """Relative Strength Index using Wilder's smoothing."""
    if period < 1:
        raise ValueError("period must be >= 1")
    out: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return out

    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        change = values[i] - values[i - 1]
        if change >= 0:
            gains += change
        else:
            losses -= change

    avg_gain = gains / period
    avg_loss = losses / period
    out[period] = _rsi_from_averages(avg_gain, avg_loss)

    for i in range(period + 1, len(values)):
        change = values[i] - values[i - 1]
        gain = change if change > 0 else 0.0
        loss = -change if change < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = _rsi_from_averages(avg_gain, avg_loss)
    return out


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        # No downward movement in the window: RSI is defined as 100.
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def atr(candles: Sequence[Candle], period: int = 14) -> list[float | None]:
    """Average True Range using Wilder's smoothing.

    Used only as a volatility yardstick, to require that an EMA crossover is
    wide enough to be meaningful rather than noise.
    """
    if period < 1:
        raise ValueError("period must be >= 1")
    out: list[float | None] = [None] * len(candles)
    if len(candles) <= period:
        return out

    true_ranges: list[float] = [candles[0].high - candles[0].low]
    for i in range(1, len(candles)):
        prev_close = candles[i - 1].close
        current = candles[i]
        true_ranges.append(
            max(
                current.high - current.low,
                abs(current.high - prev_close),
                abs(current.low - prev_close),
            )
        )

    prev = sum(true_ranges[1 : period + 1]) / period
    out[period] = prev
    for i in range(period + 1, len(candles)):
        prev = (prev * (period - 1) + true_ranges[i]) / period
        out[i] = prev
    return out
