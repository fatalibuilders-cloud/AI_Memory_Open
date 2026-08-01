"""Tests for signal generation.

Rather than hand-computing the exact bar a crossover lands on, most tests walk
a price series forward one candle at a time and assert on the signals produced.
That keeps the tests readable and still pins down real behaviour.
"""

import pytest

from deriv_bot.indicators import Candle
from deriv_bot.strategy import evaluate

from conftest import make_config


def candles(closes):
    return [
        Candle(epoch=1000 + i * 60, open=c, high=c + 0.5, low=c - 0.5, close=c)
        for i, c in enumerate(float(c) for c in closes)
    ]


def scan(series, config, symbol="cryBTCUSD"):
    """Evaluate every prefix of the series, returning the signals that traded."""
    bars = candles(series)
    results = []
    for end in range(len(bars) + 1):
        signal = evaluate(symbol, bars[:end], config)
        if signal.is_trade:
            results.append((end, signal))
    return results


VALLEY = list(range(50, 20, -1)) + list(range(20, 50))  # down then up
PEAK = list(range(20, 50)) + list(range(50, 20, -1))  # up then down


class TestWarmup:
    def test_empty_history(self):
        signal = evaluate("cryBTCUSD", [], make_config())
        assert not signal.is_trade
        assert "insufficient history" in signal.reason

    def test_too_few_candles(self):
        signal = evaluate("cryBTCUSD", candles(range(10)), make_config())
        assert not signal.is_trade
        assert "insufficient history" in signal.reason

    def test_reports_the_symbol_it_was_asked_about(self):
        assert evaluate("cryETHUSD", [], make_config()).symbol == "cryETHUSD"


class TestSignals:
    def test_valley_eventually_produces_a_call(self):
        trades = scan(VALLEY, make_config(min_separation_atr=0.0))
        assert trades, "expected at least one signal from a V-shaped reversal"
        assert any(signal.direction == "CALL" for _, signal in trades)

    def test_peak_eventually_produces_a_put(self):
        trades = scan(PEAK, make_config(min_separation_atr=0.0))
        assert trades
        assert any(signal.direction == "PUT" for _, signal in trades)

    def test_steady_uptrend_has_no_crossover_after_warmup(self):
        # A monotonic climb crosses once during warm-up and never again.
        config = make_config(min_separation_atr=0.0)
        signal = evaluate("cryBTCUSD", candles(range(100, 200)), config)
        assert not signal.is_trade
        assert "no crossover" in signal.reason

    def test_flat_market_never_trades(self):
        config = make_config(min_separation_atr=0.0)
        signal = evaluate("cryBTCUSD", candles([100.0] * 80), config)
        assert not signal.is_trade

    def test_signal_carries_its_indicator_context(self):
        trades = scan(VALLEY, make_config(min_separation_atr=0.0))
        _, signal = trades[0]
        assert signal.close is not None
        assert signal.ema_fast is not None and signal.ema_slow is not None
        assert signal.rsi is not None and signal.atr is not None
        assert signal.reason


def first_trade_window(series, **overrides):
    """The candle prefix on which the strategy first decides to trade."""
    config = make_config(min_separation_atr=0.0, **overrides)
    trades = scan(series, config)
    assert trades, "fixture series produced no signal"
    end, signal = trades[0]
    return candles(series)[:end], signal


class TestFilters:
    def test_atr_separation_filter_rejects_a_shallow_crossover(self):
        window, baseline = first_trade_window(VALLEY)
        assert baseline.is_trade
        # Same candles, but demanding an implausibly wide EMA separation.
        strict = evaluate("cryBTCUSD", window, make_config(min_separation_atr=1000.0))
        assert not strict.is_trade
        assert "too shallow" in strict.reason

    def test_rsi_filter_rejects_an_overbought_bullish_crossover(self):
        window, baseline = first_trade_window(VALLEY)
        assert baseline.direction == "CALL"
        strict = evaluate(
            "cryBTCUSD", window, make_config(min_separation_atr=0.0, rsi_upper=1.0)
        )
        assert not strict.is_trade
        assert "overbought" in strict.reason

    def test_rsi_filter_rejects_an_oversold_bearish_crossover(self):
        window, baseline = first_trade_window(PEAK)
        assert baseline.direction == "PUT"
        strict = evaluate(
            "cryBTCUSD", window, make_config(min_separation_atr=0.0, rsi_lower=99.0)
        )
        assert not strict.is_trade
        assert "oversold" in strict.reason

    def test_zero_volatility_is_rejected(self):
        # Constant prices: ATR is zero, so no crossover can qualify.
        config = make_config(min_separation_atr=0.0)
        signal = evaluate("cryBTCUSD", candles([42.0] * 80), config)
        assert not signal.is_trade


class TestDirectionIsNeverAmbiguous:
    @pytest.mark.parametrize("series", [VALLEY, PEAK])
    def test_direction_is_call_or_put_or_none(self, series):
        for _, signal in scan(series, make_config(min_separation_atr=0.0)):
            assert signal.direction in {"CALL", "PUT"}
