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


def sma(values: Sequence[float], period: int) -> list[float | None]:
    """Simple moving average."""
    if period < 1:
        raise ValueError("period must be >= 1")
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    running = sum(values[:period])
    out[period - 1] = running / period
    for i in range(period, len(values)):
        running += values[i] - values[i - period]
        out[i] = running / period
    return out


def stddev(values: Sequence[float], period: int) -> list[float | None]:
    """Population standard deviation over a rolling window."""
    if period < 1:
        raise ValueError("period must be >= 1")
    out: list[float | None] = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        mean = sum(window) / period
        out[i] = (sum((v - mean) ** 2 for v in window) / period) ** 0.5
    return out


def bollinger(
    values: Sequence[float], period: int = 20, deviations: float = 2.0
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    """Bollinger bands: (lower, middle, upper)."""
    middle = sma(values, period)
    spread = stddev(values, period)
    lower: list[float | None] = [None] * len(values)
    upper: list[float | None] = [None] * len(values)
    for i, (mid, dev) in enumerate(zip(middle, spread)):
        if mid is not None and dev is not None:
            lower[i] = mid - deviations * dev
            upper[i] = mid + deviations * dev
    return lower, middle, upper


def donchian(
    candles: Sequence[Candle], period: int = 20
) -> tuple[list[float | None], list[float | None]]:
    """Donchian channel: (lowest low, highest high) over the prior `period`
    candles, excluding the current one — the classic Turtle breakout rule."""
    lows: list[float | None] = [None] * len(candles)
    highs: list[float | None] = [None] * len(candles)
    for i in range(period, len(candles)):
        window = candles[i - period : i]
        lows[i] = min(c.low for c in window)
        highs[i] = max(c.high for c in window)
    return lows, highs


def macd(
    values: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[list[float | None], list[float | None]]:
    """MACD line and its signal line."""
    fast_line = ema(values, fast)
    slow_line = ema(values, slow)
    macd_line: list[float | None] = [
        (f - s) if (f is not None and s is not None) else None
        for f, s in zip(fast_line, slow_line)
    ]

    # The signal line is an EMA of the MACD line, which only exists after warm-up.
    defined = [(i, v) for i, v in enumerate(macd_line) if v is not None]
    signal_line: list[float | None] = [None] * len(values)
    if len(defined) >= signal:
        smoothed = ema([v for _, v in defined], signal)
        for (index, _), value in zip(defined, smoothed):
            signal_line[index] = value
    return macd_line, signal_line
