"""Signal generation.

The default strategy is an EMA crossover with an RSI exhaustion filter and an
ATR-based separation filter. It is deliberately simple and fully deterministic
so that a signal can always be explained after the fact from the candles alone.

Swapping in another strategy means writing a callable with the same shape as
`evaluate` and pointing the trader at it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from .config import Config
from .indicators import Candle, atr, ema, rsi

Direction = Literal["CALL", "PUT"]


@dataclass(frozen=True)
class Signal:
    """A decision about one symbol at one point in time.

    `direction` is None when the strategy declines to trade; `reason` always
    explains the outcome, whether or not a trade is proposed.
    """

    symbol: str
    direction: Direction | None
    reason: str
    close: float | None = None
    ema_fast: float | None = None
    ema_slow: float | None = None
    rsi: float | None = None
    atr: float | None = None

    @property
    def is_trade(self) -> bool:
        return self.direction is not None


def evaluate(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """Evaluate the newest closed candle and decide whether to trade.

    A CALL is proposed when the fast EMA crosses above the slow EMA while RSI
    is below `rsi_upper` (i.e. the move is not already exhausted), and a PUT on
    the mirrored condition. Both require the EMAs to be separated by at least
    `min_separation_atr` times ATR, which suppresses crossovers in flat markets.
    """
    needed = config.ema_slow + max(config.rsi_period, config.atr_period) + 2
    if len(candles) < needed:
        return Signal(symbol, None, f"insufficient history: {len(candles)}/{needed} candles")

    closes = [candle.close for candle in candles]
    fast_series = ema(closes, config.ema_fast)
    slow_series = ema(closes, config.ema_slow)
    rsi_series = rsi(closes, config.rsi_period)
    atr_series = atr(candles, config.atr_period)

    fast_now, fast_prev = fast_series[-1], fast_series[-2]
    slow_now, slow_prev = slow_series[-1], slow_series[-2]
    rsi_now = rsi_series[-1]
    atr_now = atr_series[-1]

    if None in (fast_now, fast_prev, slow_now, slow_prev, rsi_now, atr_now):
        return Signal(symbol, None, "indicators not warmed up")

    # Bind to locals so the type checker knows these are no longer Optional.
    assert fast_now is not None and fast_prev is not None
    assert slow_now is not None and slow_prev is not None
    assert rsi_now is not None and atr_now is not None

    close = closes[-1]
    context = {
        "close": close,
        "ema_fast": fast_now,
        "ema_slow": slow_now,
        "rsi": rsi_now,
        "atr": atr_now,
    }

    crossed_up = fast_prev <= slow_prev and fast_now > slow_now
    crossed_down = fast_prev >= slow_prev and fast_now < slow_now

    if not (crossed_up or crossed_down):
        return Signal(symbol, None, "no crossover on the latest candle", **context)

    separation = abs(fast_now - slow_now)
    threshold = atr_now * config.min_separation_atr
    if atr_now <= 0:
        return Signal(symbol, None, "zero volatility — market is flat", **context)
    if separation < threshold:
        return Signal(
            symbol,
            None,
            f"crossover too shallow: separation {separation:.6f} < {threshold:.6f} "
            f"({config.min_separation_atr}x ATR)",
            **context,
        )

    if crossed_up:
        if rsi_now >= config.rsi_upper:
            return Signal(
                symbol,
                None,
                f"bullish crossover rejected: RSI {rsi_now:.1f} already overbought "
                f"(>= {config.rsi_upper})",
                **context,
            )
        return Signal(
            symbol,
            "CALL",
            f"bullish crossover: EMA{config.ema_fast} crossed above EMA{config.ema_slow}, "
            f"RSI {rsi_now:.1f}",
            **context,
        )

    if rsi_now <= config.rsi_lower:
        return Signal(
            symbol,
            None,
            f"bearish crossover rejected: RSI {rsi_now:.1f} already oversold "
            f"(<= {config.rsi_lower})",
            **context,
        )
    return Signal(
        symbol,
        "PUT",
        f"bearish crossover: EMA{config.ema_fast} crossed below EMA{config.ema_slow}, "
        f"RSI {rsi_now:.1f}",
        **context,
    )
