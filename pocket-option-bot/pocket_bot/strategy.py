"""Trading strategies. A strategy looks at closed candles and emits a signal."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from .candles import CandleBuilder
from .config import Settings
from .indicators import bollinger, ema, rsi

log = logging.getLogger("pocket_bot.strategy")

CALL = "call"   # price will go UP
PUT = "put"     # price will go DOWN


class Strategy(ABC):
    def __init__(self, settings: Settings):
        self.settings = settings

    @abstractmethod
    def signal(self, candles: CandleBuilder) -> Optional[str]:
        """Return CALL, PUT or None after each closed candle."""


class RsiEmaStrategy(Strategy):
    """Mean-reversion RSI with an EMA trend filter.

    CALL when RSI is oversold AND price is at/above the EMA (buying a dip
    in an uptrend); PUT when RSI is overbought AND price is at/below the
    EMA (selling a spike in a downtrend). Trading against the trend is
    what kills most reversal bots, hence the filter.
    """

    def signal(self, candles: CandleBuilder) -> Optional[str]:
        closes = candles.closes
        s = self.settings
        if len(closes) < max(s.min_candles, s.ema_period, s.rsi_period + 1):
            return None
        r = rsi(closes, s.rsi_period)
        e = ema(closes, s.ema_period)
        if r is None or e is None:
            return None
        price = closes[-1]
        log.debug("RSI=%.1f EMA=%.5f price=%.5f", r, e, price)
        if r <= s.rsi_oversold and price >= e:
            return CALL
        if r >= s.rsi_overbought and price <= e:
            return PUT
        return None


class BollingerReversalStrategy(Strategy):
    """CALL on close below the lower band, PUT on close above the upper band."""

    def signal(self, candles: CandleBuilder) -> Optional[str]:
        closes = candles.closes
        if len(closes) < max(self.settings.min_candles, 20):
            return None
        bands = bollinger(closes, period=20, num_std=2.0)
        if bands is None:
            return None
        lower, _, upper = bands
        price = closes[-1]
        if price < lower:
            return CALL
        if price > upper:
            return PUT
        return None


STRATEGIES = {
    "rsi_ema": RsiEmaStrategy,
    "bollinger": BollingerReversalStrategy,
}


def build_strategy(settings: Settings) -> Strategy:
    cls = STRATEGIES.get(settings.strategy)
    if cls is None:
        raise ValueError(f"Unknown strategy '{settings.strategy}'. Options: {list(STRATEGIES)}")
    return cls(settings)
