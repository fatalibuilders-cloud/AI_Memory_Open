"""Build OHLC candles from the live tick stream."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Candle:
    start: int          # unix timestamp of candle open (aligned to timeframe)
    open: float
    high: float
    low: float
    close: float
    ticks: int = 1

    def update(self, price: float) -> None:
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.ticks += 1


class CandleBuilder:
    """Aggregates ticks into fixed-interval candles for a single asset."""

    def __init__(self, timeframe_seconds: int, max_history: int = 500):
        self.timeframe = timeframe_seconds
        self.max_history = max_history
        self.current: Optional[Candle] = None
        self.history: list[Candle] = []

    def add_tick(self, timestamp: float, price: float) -> Optional[Candle]:
        """Feed one tick. Returns the just-CLOSED candle when a new one starts."""
        bucket = int(timestamp // self.timeframe) * self.timeframe
        if self.current is None:
            self.current = Candle(bucket, price, price, price, price)
            return None
        if bucket == self.current.start:
            self.current.update(price)
            return None
        closed = self.current
        self.history.append(closed)
        if len(self.history) > self.max_history:
            del self.history[: len(self.history) - self.max_history]
        self.current = Candle(bucket, price, price, price, price)
        return closed

    @property
    def closes(self) -> list[float]:
        return [c.close for c in self.history]

    def __len__(self) -> int:
        return len(self.history)
