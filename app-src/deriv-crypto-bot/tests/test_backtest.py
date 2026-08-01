"""Tests for the backtester.

The important properties are that it drives the real strategy and risk code,
that its accounting is arithmetically correct, and that its headline statistics
(especially breakeven win rate) cannot silently flatter a losing strategy.
"""

import json
import math

import pytest

from deriv_bot.backtest import (
    BacktestResult,
    SimulatedTrade,
    _candles_per_contract,
    format_report,
    load_candles,
    main,
    simulate,
)
from deriv_bot.config import ConfigError
from deriv_bot.indicators import Candle

from conftest import make_config
from test_strategy import PEAK, VALLEY


def candles(closes, start=1_700_000_000, step=60):
    return [
        Candle(epoch=start + i * step, open=c, high=c + 0.5, low=c - 0.5, close=c)
        for i, c in enumerate(float(c) for c in closes)
    ]


# A long series with repeated reversals, so the strategy has something to trade.
WAVES = ([*range(50, 20, -1), *range(20, 50)] * 6)


def bt_config(**overrides):
    return make_config(min_separation_atr=0.0, candle_count=200, **overrides)


class TestContractSpan:
    def test_minutes_map_onto_candles(self):
        config = bt_config(trade_duration=5, trade_duration_unit="m", candle_granularity=60)
        assert _candles_per_contract(config) == 5

    def test_hours_map_onto_candles(self):
        config = bt_config(trade_duration=1, trade_duration_unit="h", candle_granularity=60)
        assert _candles_per_contract(config) == 60

    def test_tick_durations_are_rejected(self):
        config = bt_config(trade_duration=5, trade_duration_unit="t")
        with pytest.raises(ConfigError, match="tick durations"):
            _candles_per_contract(config)

    def test_contract_shorter_than_a_candle_is_rejected(self):
        config = bt_config(trade_duration=30, trade_duration_unit="s", candle_granularity=60)
        with pytest.raises(ConfigError, match="shorter than one candle"):
            _candles_per_contract(config)


class TestSimulation:
    def test_produces_trades_on_a_reversing_series(self):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config())
        assert result.trades, "expected trades from a repeatedly reversing series"
        assert result.wins + result.losses == len(result.trades)

    def test_flat_market_produces_no_trades(self):
        result = simulate("cryBTCUSD", candles([100.0] * 500), bt_config())
        assert result.trades == []

    def test_short_history_produces_no_trades(self):
        result = simulate("cryBTCUSD", candles(range(20)), bt_config())
        assert result.trades == []

    def test_every_trade_is_the_requested_symbol(self):
        result = simulate("cryETHUSD", candles(WAVES), bt_config())
        assert all(t.symbol == "cryETHUSD" for t in result.trades)

    def test_trades_respect_the_contract_span(self):
        config = bt_config(trade_duration=5, trade_duration_unit="m", candle_granularity=60)
        result = simulate("cryBTCUSD", candles(WAVES), config)
        for trade in result.trades:
            assert trade.exit_epoch - trade.entry_epoch == 300

    def test_call_wins_when_price_rises(self):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config())
        for trade in result.trades:
            if trade.direction == "CALL":
                assert trade.won == (trade.exit_price > trade.entry_price)
            else:
                assert trade.won == (trade.exit_price < trade.entry_price)

    def test_profit_matches_the_payout_ratio(self):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config(), payout_ratio=0.9)
        for trade in result.trades:
            expected = trade.stake * 0.9 if trade.won else -trade.stake
            assert trade.profit == pytest.approx(expected)

    def test_max_open_trades_is_enforced(self):
        config = bt_config(max_open_trades=1, symbol_cooldown=0)
        result = simulate("cryBTCUSD", candles(WAVES), config)
        # One symbol and a one-position cap: no two trades may overlap.
        for earlier, later in zip(result.trades, result.trades[1:]):
            assert later.entry_epoch >= earlier.exit_epoch

    def test_cooldown_spaces_trades_out(self):
        config = bt_config(symbol_cooldown=3600, max_open_trades=5)
        result = simulate("cryBTCUSD", candles(WAVES), config)
        for earlier, later in zip(result.trades, result.trades[1:]):
            assert later.entry_epoch - earlier.entry_epoch >= 3600

    def test_daily_loss_limit_halts_the_simulation(self):
        # A tiny limit relative to the stake must stop trading almost at once.
        config = bt_config(stake=10.0, daily_loss_limit=10.0, max_stake_fraction=1.0)
        result = simulate("cryBTCUSD", candles(WAVES), config, payout_ratio=0.85)
        if result.losses:
            assert result.halted_days >= 1

    def test_does_not_open_a_contract_it_cannot_resolve(self):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config())
        last_epoch = candles(WAVES)[-1].epoch
        assert all(t.exit_epoch <= last_epoch for t in result.trades)


class TestStatistics:
    def make(self, profits, *, stake=1.0, balance=100.0, ratio=0.85):
        result = BacktestResult("cryBTCUSD", 500, balance, ratio)
        equity = balance
        for i, profit in enumerate(profits):
            equity += profit
            result.equity_curve.append(equity)
            result.trades.append(
                SimulatedTrade(
                    "cryBTCUSD", "CALL", 1000 + i * 60, 1300 + i * 60, 1.0, 1.1, stake, profit, ""
                )
            )
        return result

    def test_win_rate(self):
        result = self.make([0.85, -1.0, 0.85, -1.0])
        assert result.wins == 2 and result.losses == 2
        assert result.win_rate == pytest.approx(50.0)

    def test_breakeven_win_rate_matches_the_payout(self):
        # At 0.85 payout you need better than 1/1.85 = 54.05% just to break even.
        assert self.make([], ratio=0.85).breakeven_win_rate == pytest.approx(54.0540, abs=1e-3)
        assert self.make([], ratio=1.0).breakeven_win_rate == pytest.approx(50.0)

    def test_fifty_percent_win_rate_loses_at_standard_payout(self):
        # The property that matters: a coin-flip strategy must show a loss.
        result = self.make([0.85, -1.0] * 10)
        assert result.total_pnl < 0
        assert result.win_rate < result.breakeven_win_rate

    def test_pnl_and_ending_balance(self):
        result = self.make([0.85, -1.0, 0.85], balance=100.0)
        assert result.total_pnl == pytest.approx(0.70)
        assert result.ending_balance == pytest.approx(100.70)
        assert result.return_pct == pytest.approx(0.70)

    def test_profit_factor(self):
        result = self.make([2.0, -1.0, 2.0, -1.0])
        assert result.profit_factor == pytest.approx(2.0)

    def test_profit_factor_is_infinite_with_no_losses(self):
        assert math.isinf(self.make([1.0, 1.0]).profit_factor)

    def test_max_drawdown(self):
        # 100 -> 110 -> 90 -> 95 : the worst peak-to-trough fall is 20.
        result = self.make([10.0, -20.0, 5.0], balance=100.0)
        assert result.max_drawdown == pytest.approx(20.0)
        assert result.max_drawdown_pct == pytest.approx(20.0)

    def test_longest_losing_streak(self):
        result = self.make([1.0, -1.0, -1.0, -1.0, 1.0, -1.0])
        assert result.longest_losing_streak == 3

    def test_empty_result_is_safe(self):
        result = self.make([])
        assert result.win_rate == 0.0
        assert result.total_pnl == 0.0
        assert result.max_drawdown == 0.0
        assert result.longest_losing_streak == 0


class TestReport:
    def test_names_the_symbol_and_breakeven(self):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config())
        report = format_report(result, bt_config())
        assert "cryBTCUSD" in report
        assert "Breakeven win rate" in report

    def test_no_trades_explains_itself(self):
        result = simulate("cryBTCUSD", candles([100.0] * 300), bt_config())
        report = format_report(result, bt_config())
        assert "No trades were taken" in report

    def test_a_losing_run_is_called_a_loss(self):
        result = BacktestResult("cryBTCUSD", 100, 100.0, 0.85)
        result.trades = [
            SimulatedTrade("cryBTCUSD", "CALL", 1000, 1300, 1.0, 0.9, 1.0, -1.0, "") for _ in range(5)
        ]
        result.equity_curve = [99.0, 98.0, 97.0, 96.0, 95.0]
        assert "LOSS" in format_report(result, bt_config())

    def test_report_warns_that_one_period_is_not_evidence(self):
        result = simulate("cryBTCUSD", candles(WAVES), bt_config())
        assert "One period is not evidence" in format_report(result, bt_config())


class TestLoading:
    def test_json_array(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(
            json.dumps(
                [{"epoch": 200, "open": 2, "high": 3, "low": 1, "close": 2.5},
                 {"epoch": 100, "open": 1, "high": 2, "low": 0.5, "close": 1.5}]
            )
        )
        loaded = load_candles(str(path))
        assert [c.epoch for c in loaded] == [100, 200]  # sorted oldest-first

    def test_jsonl(self, tmp_path):
        path = tmp_path / "c.jsonl"
        path.write_text(
            '{"epoch": 100, "open": 1, "high": 2, "low": 0.5, "close": 1.5}\n'
            '{"epoch": 160, "open": 1.5, "high": 2, "low": 1, "close": 1.8}\n'
        )
        assert len(load_candles(str(path))) == 2

    def test_empty_file(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text("")
        assert load_candles(str(path)) == []


class TestCli:
    def write(self, tmp_path, closes):
        path = tmp_path / "candles.json"
        path.write_text(
            json.dumps(
                [
                    {"epoch": c.epoch, "open": c.open, "high": c.high, "low": c.low, "close": c.close}
                    for c in candles(closes)
                ]
            )
        )
        return str(path)

    def test_runs_from_a_file(self, tmp_path, capsys):
        assert main(["--from-file", self.write(tmp_path, WAVES), "--symbol", "cryBTCUSD"]) == 0
        assert "BACKTEST" in capsys.readouterr().out

    def test_json_output_is_parseable(self, tmp_path, capsys):
        assert main(["--from-file", self.write(tmp_path, WAVES), "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert "win_rate" in payload and "breakeven_win_rate" in payload

    def test_no_data_source_prints_help(self, capsys):
        assert main([]) == 2
        assert "Give it data" in capsys.readouterr().out

    def test_missing_file_is_reported(self):
        assert main(["--from-file", "/nonexistent/candles.json"]) == 2
