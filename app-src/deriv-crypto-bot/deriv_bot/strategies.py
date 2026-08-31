"""A library of classic strategies, plus the controls that keep you honest.

Every entry has the same signature as `strategy.evaluate`, so any of them can
drive the live bot (`STRATEGY=` in .env) or the backtester (`--strategy`).

Three of these are not strategies at all, and they are the most important
entries in any comparison:

  always_call   Always predicts "up". Over a rising market this is the
                buy-and-hold analogue — and buy-and-hold is the approach that
                has actually made money on Bitcoin across its history. A real
                strategy must beat it, or holding would have served you better.

  coin_flip     A seeded random choice. Any strategy that cannot clearly beat
                this is producing noise, however sophisticated it looks.

  never_trade   Trades nothing. The only strategy that cannot lose. When the
                payout is unfavourable enough, this genuinely wins the table,
                and that is a real result rather than a joke.

A comparison in which your clever strategy loses to these is not a
disappointing outcome — it is the outcome telling you something true.
"""

from __future__ import annotations

import hashlib
from typing import Callable, Sequence

from .config import Config
from .indicators import Candle, bollinger, donchian, ema, macd, rsi, sma
from .strategy import Signal
from .strategy import evaluate as ema_crossover

StrategyFn = Callable[[str, Sequence[Candle], Config], Signal]


def _context(candles: Sequence[Candle], **extra) -> dict:
    return {"close": candles[-1].close, **extra}


def _insufficient(symbol: str, have: int, need: int) -> Signal:
    return Signal(symbol, None, f"insufficient history: {have}/{need} candles")


# -- trend following -------------------------------------------------------


def macd_cross(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """MACD line crossing its signal line. A slower trend rule than the EMA
    crossover, so it fires less often and whipsaws less in sideways markets."""
    need = 40
    if len(candles) < need:
        return _insufficient(symbol, len(candles), need)

    closes = [c.close for c in candles]
    line, signal_line = macd(closes)
    now, prev = line[-1], line[-2]
    sig_now, sig_prev = signal_line[-1], signal_line[-2]
    if None in (now, prev, sig_now, sig_prev):
        return Signal(symbol, None, "MACD not warmed up")

    context = _context(candles, ema_fast=now, ema_slow=sig_now)
    if prev <= sig_prev and now > sig_now:
        return Signal(symbol, "CALL", "MACD crossed above its signal line", **context)
    if prev >= sig_prev and now < sig_now:
        return Signal(symbol, "PUT", "MACD crossed below its signal line", **context)
    return Signal(symbol, None, "no MACD crossover", **context)


def donchian_breakout(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """Turtle-style breakout: trade in the direction of a new N-period extreme.

    This is the strategy family that genuinely worked on Bitcoin historically —
    but on daily bars held for weeks, not five-minute binaries. Included so the
    comparison is fair rather than flattering to the fast rules.
    """
    period = 20
    need = period + 2
    if len(candles) < need:
        return _insufficient(symbol, len(candles), need)

    lows, highs = donchian(candles, period)
    low, high = lows[-1], highs[-1]
    if low is None or high is None:
        return Signal(symbol, None, "channel not warmed up")

    close = candles[-1].close
    context = _context(candles)
    if close > high:
        return Signal(symbol, "CALL", f"broke above the {period}-candle high", **context)
    if close < low:
        return Signal(symbol, "PUT", f"broke below the {period}-candle low", **context)
    return Signal(symbol, None, "inside the channel", **context)


def trend_200(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """Trade only with the 200-period trend.

    The short-horizon analogue of the 200-day moving average rule, which is the
    best-documented long-run trend signal on Bitcoin.
    """
    period = 200
    need = period + 5
    if len(candles) < need:
        return _insufficient(symbol, len(candles), need)

    closes = [c.close for c in candles]
    trend = sma(closes, period)
    fast = ema(closes, config.ema_fast)
    if trend[-1] is None or fast[-1] is None or fast[-2] is None:
        return Signal(symbol, None, "trend not warmed up")

    close = closes[-1]
    context = _context(candles, ema_fast=fast[-1], ema_slow=trend[-1])
    rising = fast[-1] > fast[-2]

    if close > trend[-1] and rising:
        return Signal(symbol, "CALL", "above the 200-period trend and rising", **context)
    if close < trend[-1] and not rising:
        return Signal(symbol, "PUT", "below the 200-period trend and falling", **context)
    return Signal(symbol, None, "price and trend disagree", **context)


# -- mean reversion --------------------------------------------------------


def rsi_reversion(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """Buy oversold, sell overbought — the opposite bet to trend following.

    Included because trend and reversion fail in opposite conditions. If both
    lose on your data, the problem is the payout, not the rule.
    """
    need = config.rsi_period + 5
    if len(candles) < need:
        return _insufficient(symbol, len(candles), need)

    closes = [c.close for c in candles]
    series = rsi(closes, config.rsi_period)
    now, prev = series[-1], series[-2]
    if now is None or prev is None:
        return Signal(symbol, None, "RSI not warmed up")

    context = _context(candles, rsi=now)
    # Trade the exit from the extreme, not the extreme itself — an oversold
    # market can stay oversold for a long time.
    if prev <= config.rsi_lower < now:
        return Signal(symbol, "CALL", f"RSI recovering out of oversold ({now:.1f})", **context)
    if prev >= config.rsi_upper > now:
        return Signal(symbol, "PUT", f"RSI falling out of overbought ({now:.1f})", **context)
    return Signal(symbol, None, f"RSI {now:.1f} not leaving an extreme", **context)


def bollinger_reversion(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """Fade a close outside the Bollinger bands, betting on a return to the mean."""
    period = 20
    need = period + 5
    if len(candles) < need:
        return _insufficient(symbol, len(candles), need)

    closes = [c.close for c in candles]
    lower, _middle, upper = bollinger(closes, period, 2.0)
    if lower[-1] is None or upper[-1] is None:
        return Signal(symbol, None, "bands not warmed up")

    close = closes[-1]
    context = _context(candles)
    if close < lower[-1]:
        return Signal(symbol, "CALL", "closed below the lower band", **context)
    if close > upper[-1]:
        return Signal(symbol, "PUT", "closed above the upper band", **context)
    return Signal(symbol, None, "inside the bands", **context)


# -- controls --------------------------------------------------------------


def always_call(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """Always predict "up" — the buy-and-hold benchmark."""
    if not candles:
        return _insufficient(symbol, 0, 1)
    return Signal(
        symbol, "CALL", "control: always up (buy-and-hold analogue)", **_context(candles)
    )


def coin_flip(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """A seeded coin flip — the noise floor.

    Deterministic on symbol and candle time, so a backtest is reproducible.
    """
    if not candles:
        return _insufficient(symbol, 0, 1)
    digest = hashlib.sha256(f"{symbol}:{candles[-1].epoch}".encode()).digest()[0]
    return Signal(
        symbol, "CALL" if digest % 2 else "PUT", "control: coin flip", **_context(candles)
    )


def never_trade(symbol: str, candles: Sequence[Candle], config: Config) -> Signal:
    """Trades nothing. The only strategy guaranteed not to lose money."""
    return Signal(symbol, None, "control: never trades")


REGISTRY: dict[str, StrategyFn] = {
    "ema_cross": ema_crossover,
    "macd_cross": macd_cross,
    "donchian": donchian_breakout,
    "trend_200": trend_200,
    "rsi_reversion": rsi_reversion,
    "bollinger": bollinger_reversion,
    "always_call": always_call,
    "coin_flip": coin_flip,
    "never_trade": never_trade,
}

DESCRIPTIONS: dict[str, str] = {
    "ema_cross": "EMA 9/21 crossover, with RSI and ATR filters (the default)",
    "macd_cross": "MACD line crossing its signal line",
    "donchian": "Breakout beyond the 20-candle range (Turtle-style)",
    "trend_200": "Trade only with the 200-period trend",
    "rsi_reversion": "Buy exits from oversold, sell exits from overbought",
    "bollinger": "Fade closes outside the 2-sigma Bollinger bands",
    "always_call": "CONTROL: always up - the buy-and-hold benchmark",
    "coin_flip": "CONTROL: random - the noise floor",
    "never_trade": "CONTROL: no trades - cannot lose",
}

CONTROLS = frozenset({"always_call", "coin_flip", "never_trade"})


def get(name: str) -> StrategyFn:
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"unknown strategy {name!r}. Available: {', '.join(sorted(REGISTRY))}"
        ) from None
