"""Tests for the strategy library and the comparison harness.

The controls carry the weight here. `always_call`, `coin_flip`, and
`never_trade` are what stop a comparison from flattering a rule that is
actually detecting nothing, so their behaviour is pinned down precisely.
"""

import pytest

from deriv_bot import strategies
from deriv_bot.backtest import compare, format_comparison, format_sweep, simulate, sweep_durations
from deriv_bot.indicators import Candle
from deriv_bot.strategies import CONTROLS, DESCRIPTIONS, REGISTRY

from conftest import make_config
from test_backtest import bt_config, candles
from test_strategy import PEAK, VALLEY

WAVES = [*range(50, 20, -1), *range(20, 50)] * 6
FLAT = [100.0] * 400
RISING = [100.0 + i * 0.05 for i in range(400)]
FALLING = [100.0 - i * 0.05 for i in range(400)]


class TestRegistry:
    def test_every_strategy_is_described(self):
        assert set(REGISTRY) == set(DESCRIPTIONS)

    def test_controls_are_registered(self):
        assert CONTROLS <= set(REGISTRY)

    def test_get_returns_a_callable(self):
        assert callable(strategies.get("ema_cross"))

    def test_unknown_strategy_names_the_alternatives(self):
        with pytest.raises(KeyError, match="ema_cross"):
            strategies.get("no_such_strategy")

    @pytest.mark.parametrize("name", sorted(REGISTRY))
    def test_every_strategy_survives_an_empty_series(self, name):
        signal = REGISTRY[name]("cryBTCUSD", [], make_config())
        assert signal.symbol == "cryBTCUSD"
        assert signal.reason

    @pytest.mark.parametrize("name", sorted(REGISTRY))
    def test_every_strategy_survives_a_flat_market(self, name):
        signal = REGISTRY[name]("cryBTCUSD", candles(FLAT), make_config())
        assert signal.direction in {None, "CALL", "PUT"}

    @pytest.mark.parametrize("name", sorted(REGISTRY))
    def test_every_strategy_reports_the_symbol_it_was_given(self, name):
        assert REGISTRY[name]("cryETHUSD", candles(WAVES), make_config()).symbol == "cryETHUSD"


class TestControls:
    def test_always_call_never_says_put(self):
        for series in (RISING, FALLING, FLAT, WAVES):
            signal = strategies.always_call("cryBTCUSD", candles(series), make_config())
            assert signal.direction == "CALL"

    def test_never_trade_never_trades(self):
        for series in (RISING, FALLING, FLAT, WAVES):
            signal = strategies.never_trade("cryBTCUSD", candles(series), make_config())
            assert not signal.is_trade

    def test_coin_flip_is_deterministic(self):
        bars = candles(WAVES)
        first = strategies.coin_flip("cryBTCUSD", bars, make_config())
        second = strategies.coin_flip("cryBTCUSD", bars, make_config())
        assert first.direction == second.direction

    def test_coin_flip_differs_across_symbols(self):
        # Same bar, different symbol: the seed must actually vary.
        bars = candles(WAVES)
        directions = {
            strategies.coin_flip(sym, bars, make_config()).direction
            for sym in ("cryBTCUSD", "cryETHUSD", "cryLTCUSD", "cryXRPUSD")
        }
        assert directions == {"CALL", "PUT"}

    def test_coin_flip_produces_both_directions_over_time(self):
        seen = set()
        for end in range(50, 200):
            seen.add(strategies.coin_flip("cryBTCUSD", candles(WAVES)[:end], make_config()).direction)
        assert seen == {"CALL", "PUT"}


class TestTrendStrategies:
    def test_donchian_calls_a_breakout_up(self):
        # A genuine breakout: quiet range, then a close above every prior high.
        series = [100.0] * 25 + [110.0]
        assert strategies.donchian_breakout("cryBTCUSD", candles(series), make_config()).direction == "CALL"

    def test_donchian_puts_a_breakout_down(self):
        series = [100.0] * 25 + [90.0]
        assert strategies.donchian_breakout("cryBTCUSD", candles(series), make_config()).direction == "PUT"

    def test_donchian_ignores_a_drift_inside_the_channel(self):
        # A slow climb that never exceeds the padded prior highs is not a
        # breakout, and must not be traded as one.
        assert not strategies.donchian_breakout(
            "cryBTCUSD", candles(RISING), make_config()
        ).is_trade

    def test_donchian_stays_out_of_a_flat_channel(self):
        assert not strategies.donchian_breakout("cryBTCUSD", candles(FLAT), make_config()).is_trade

    def test_trend_200_needs_deep_history(self):
        signal = strategies.trend_200("cryBTCUSD", candles(RISING[:100]), make_config())
        assert not signal.is_trade
        assert "insufficient history" in signal.reason

    def test_trend_200_follows_a_rising_market(self):
        assert strategies.trend_200("cryBTCUSD", candles(RISING), make_config()).direction == "CALL"

    def test_trend_200_follows_a_falling_market(self):
        assert strategies.trend_200("cryBTCUSD", candles(FALLING), make_config()).direction == "PUT"

    def test_macd_produces_signals_on_reversals(self):
        found = set()
        for end in range(45, len(WAVES)):
            s = strategies.macd_cross("cryBTCUSD", candles(WAVES)[:end], make_config())
            if s.is_trade:
                found.add(s.direction)
        assert found == {"CALL", "PUT"}


class TestReversionStrategies:
    def test_bollinger_fades_a_drop_below_the_band(self):
        series = [100.0] * 40 + [80.0]
        assert strategies.bollinger_reversion("cryBTCUSD", candles(series), make_config()).direction == "CALL"

    def test_bollinger_fades_a_spike_above_the_band(self):
        series = [100.0] * 40 + [120.0]
        assert strategies.bollinger_reversion("cryBTCUSD", candles(series), make_config()).direction == "PUT"

    def test_bollinger_stays_out_inside_the_bands(self):
        # Needs real variance, or the bands collapse to zero width and any
        # move at all reads as an excursion.
        series = [99.0, 101.0] * 15 + [100.0]
        assert not strategies.bollinger_reversion(
            "cryBTCUSD", candles(series), make_config()
        ).is_trade

    def test_zero_variance_collapses_the_bands(self):
        # Documented consequence: with no volatility the bands have no width,
        # so the smallest move counts as outside them.
        signal = strategies.bollinger_reversion(
            "cryBTCUSD", candles([100.0] * 30 + [100.5]), make_config()
        )
        assert signal.direction == "PUT"

    def test_rsi_reversion_trades_the_exit_not_the_extreme(self):
        # Deep in oversold with no recovery yet: it must wait.
        signal = strategies.rsi_reversion("cryBTCUSD", candles(FALLING), make_config())
        assert not signal.is_trade

    def test_rsi_reversion_calls_a_recovery(self):
        series = list(range(200, 150, -1)) + [155.0, 162.0]
        found = [
            strategies.rsi_reversion("cryBTCUSD", candles(series)[:end], make_config())
            for end in range(25, len(series) + 1)
        ]
        assert any(s.direction == "CALL" for s in found)


class TestComparison:
    def test_runs_every_registered_strategy(self):
        results = compare("cryBTCUSD", candles(WAVES), bt_config())
        assert {r.strategy for r in results} == set(REGISTRY)

    def test_results_are_ranked_by_pnl(self):
        results = compare("cryBTCUSD", candles(WAVES), bt_config())
        assert results == sorted(results, key=lambda r: r.total_pnl, reverse=True)

    def test_every_result_saw_the_same_candles(self):
        results = compare("cryBTCUSD", candles(WAVES), bt_config())
        assert len({r.candles for r in results}) == 1

    def test_never_trade_scores_exactly_zero(self):
        results = compare("cryBTCUSD", candles(WAVES), bt_config())
        control = next(r for r in results if r.strategy == "never_trade")
        assert control.total_pnl == 0.0
        assert control.trades == []

    def test_report_marks_the_controls(self):
        text = format_comparison(compare("cryBTCUSD", candles(WAVES), bt_config()), bt_config())
        assert "control, not a strategy" in text
        assert "always_call" in text and "coin_flip" in text

    def test_report_names_the_breakeven_requirement(self):
        text = format_comparison(compare("cryBTCUSD", candles(WAVES), bt_config()), bt_config())
        assert "Breakeven" in text
        assert "54.1%" in text

    def test_report_warns_about_testing_many_strategies(self):
        text = format_comparison(compare("cryBTCUSD", candles(WAVES), bt_config()), bt_config())
        assert "partly" in text and "luck" in text

    def test_losing_to_the_controls_is_said_plainly(self):
        # A flat market: nothing can win, and the report must not dress it up.
        text = format_comparison(compare("cryBTCUSD", candles(FLAT), bt_config()), bt_config())
        assert "No strategy beat the controls" in text or "lost money" in text


class TestDurationSweep:
    def test_runs_each_requested_duration(self):
        rows = sweep_durations("cryBTCUSD", candles(WAVES), bt_config(), [5, 15, 30])
        assert [minutes for minutes, _ in rows] == [5, 15, 30]

    def test_skips_durations_the_config_rejects(self):
        # Shorter than one candle cannot be resolved; it is dropped, not fatal.
        config = bt_config(candle_granularity=3600)
        rows = sweep_durations("cryBTCUSD", candles(WAVES), config, [5, 60, 120])
        assert all(minutes >= 60 for minutes, _ in rows)

    def test_report_explains_why_duration_matters(self):
        rows = sweep_durations("cryBTCUSD", candles(WAVES), bt_config(), [5, 30])
        text = format_sweep(rows, "ema_cross")
        assert "square root" in text
        assert "cuts both ways" in text


class TestSimulateWithStrategies:
    @pytest.mark.parametrize("name", sorted(REGISTRY))
    def test_every_strategy_can_drive_a_backtest(self, name):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config(), strategy=name)
        assert result.strategy == name
        assert result.wins + result.losses == len(result.trades)

    def test_an_unknown_strategy_is_rejected(self):
        with pytest.raises(KeyError):
            simulate("cryBTCUSD", candles(WAVES), bt_config(), strategy="nope")

    def test_always_call_only_ever_buys_calls(self):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config(), strategy="always_call")
        assert result.trades
        assert all(t.direction == "CALL" for t in result.trades)

    def test_never_trade_produces_no_trades(self):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config(), strategy="never_trade")
        assert result.trades == []
