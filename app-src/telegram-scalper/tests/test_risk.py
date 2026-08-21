"""Sizing arithmetic and the guards. These rules are what protect the account."""

from __future__ import annotations

from datetime import datetime

import pytest
from conftest import eurusd_info, gold_info

from tgscalper import risk as risk_rules
from tgscalper.models import Action, Side, Signal
from tgscalper.parser import parse
from tgscalper.risk import RiskState


def gold_buy(entry: float = 2350.0, stop: float = 2344.0, tps=(2360.0,)) -> Signal:
    return Signal(
        action=Action.OPEN,
        symbol="XAUUSD",
        side=Side.BUY,
        entry=entry,
        stop_loss=stop,
        take_profits=list(tps),
    )


def state(**overrides) -> RiskState:
    defaults = dict(
        now=datetime(2026, 7, 22, 12, 0),  # a Wednesday, mid-session
        open_total=0,
        open_for_symbol=0,
        signals_last_hour=0,
        equity=10_000.0,
        day_start_balance=10_000.0,
        duplicate_of=None,
    )
    defaults.update(overrides)
    return RiskState(**defaults)


class TestSizing:
    def test_one_percent_of_ten_thousand_on_gold(self):
        # $100 risk / ($6 stop * $100 per $1 per lot) = 0.1666 -> 0.16 lots
        sizing = risk_rules.size_position(gold_buy(), gold_info(), 10_000.0, self_config())
        assert sizing.ok
        assert sizing.volume == pytest.approx(0.16)
        assert sizing.actual_risk == pytest.approx(96.0)

    def test_never_rounds_up_past_the_risk_budget(self):
        sizing = risk_rules.size_position(gold_buy(), gold_info(), 10_000.0, self_config())
        assert sizing.actual_risk <= sizing.risk_amount

    def test_wider_stop_means_smaller_size(self):
        tight = risk_rules.size_position(
            gold_buy(stop=2347.0), gold_info(), 10_000.0, self_config()
        )
        wide = risk_rules.size_position(
            gold_buy(stop=2330.0), gold_info(), 10_000.0, self_config()
        )
        assert wide.volume < tight.volume

    def test_eurusd_sizing(self):
        # $100 risk / (0.0030 stop * $100k per lot) = 0.33 lots
        signal = Signal(
            action=Action.OPEN,
            symbol="EURUSD",
            side=Side.BUY,
            entry=1.08500,
            stop_loss=1.08200,
            take_profits=[1.09000],
        )
        sizing = risk_rules.size_position(signal, eurusd_info(), 10_000.0, self_config())
        assert sizing.volume == pytest.approx(0.33)

    def test_max_lot_caps_the_size(self):
        config = self_config()
        config.risk.max_lot = 0.05
        sizing = risk_rules.size_position(gold_buy(), gold_info(), 10_000.0, config)
        assert sizing.volume == 0.05

    def test_group_multiplier_halves_the_size(self):
        full = risk_rules.size_position(gold_buy(), gold_info(), 10_000.0, self_config())
        half = risk_rules.size_position(
            gold_buy(), gold_info(), 10_000.0, self_config(), group_multiplier=0.5
        )
        assert half.volume == pytest.approx(round(full.volume / 2, 2), abs=0.01)

    def test_splitting_across_legs_divides_the_size(self):
        one = risk_rules.size_position(gold_buy(), gold_info(), 10_000.0, self_config(), legs=1)
        three = risk_rules.size_position(gold_buy(), gold_info(), 10_000.0, self_config(), legs=3)
        assert three.volume < one.volume

    def test_fixed_lot_bypasses_percentage_sizing(self):
        config = self_config()
        config.risk.fixed_lot = 0.2
        sizing = risk_rules.size_position(gold_buy(), gold_info(), 10_000.0, config)
        assert sizing.volume == pytest.approx(0.2)

    def test_tiny_account_with_a_wide_stop_is_refused(self):
        # 0.01 lots with a $50 stop risks $50 — far past 1% of a $200 account.
        sizing = risk_rules.size_position(
            gold_buy(entry=2350.0, stop=2300.0), gold_info(), 200.0, self_config()
        )
        assert not sizing.ok
        assert "too wide for this account" in sizing.error

    def test_missing_stop_cannot_be_sized_by_percentage(self):
        signal = gold_buy()
        signal.stop_loss = None
        sizing = risk_rules.size_position(signal, gold_info(), 10_000.0, self_config())
        assert not sizing.ok
        assert "without a stop loss" in sizing.error

    def test_pip_stop_is_converted_to_a_price(self):
        signal = parse("BUY EURUSD 1.08500\nSL 30 pips\nTP 1.09000").signal
        sizing = risk_rules.size_position(signal, eurusd_info(), 10_000.0, self_config())
        assert sizing.ok
        # 30 pips below entry on a 5-digit quote.
        assert sizing.stop_loss == pytest.approx(1.08200)

    def test_fallback_stop_applies_when_configured(self):
        config = self_config()
        config.risk.fallback_stop_points = 500  # $5 on gold
        signal = gold_buy()
        signal.stop_loss = None
        sizing = risk_rules.size_position(signal, gold_info(), 10_000.0, config)
        assert sizing.ok
        assert sizing.stop_loss == pytest.approx(2345.0)


class TestRoundToStep:
    def test_rounds_down_by_default(self):
        assert risk_rules.round_to_step(0.1666, 0.01) == 0.16
        assert risk_rules.round_to_step(0.999, 0.1) == 0.9

    def test_exact_multiples_are_untouched(self):
        assert risk_rules.round_to_step(0.16, 0.01) == 0.16
        assert risk_rules.round_to_step(1.0, 0.01) == 1.0


class TestGuards:
    def test_a_clean_signal_passes(self):
        assert risk_rules.check_guards(gold_buy(), gold_info(), state(), self_config()).ok

    def test_duplicate_is_blocked(self):
        gate = risk_rules.check_guards(
            gold_buy(), gold_info(), state(duplicate_of="2026-07-22T11:59:00"), self_config()
        )
        assert not gate.ok
        assert "duplicate" in gate.reason

    def test_daily_loss_halt(self):
        config = self_config()
        config.risk.max_daily_loss_pct = 5.0
        gate = risk_rules.check_guards(
            gold_buy(), gold_info(), state(equity=9_400.0), config
        )
        assert not gate.ok
        assert "daily loss halt" in gate.reason

    def test_max_open_trades(self):
        config = self_config()
        config.risk.max_open_trades = 2
        gate = risk_rules.check_guards(gold_buy(), gold_info(), state(open_total=2), config)
        assert not gate.ok
        assert "positions open" in gate.reason

    def test_max_open_per_symbol(self):
        config = self_config()
        config.risk.max_open_per_symbol = 1
        gate = risk_rules.check_guards(gold_buy(), gold_info(), state(open_for_symbol=1), config)
        assert not gate.ok
        assert "per symbol" in gate.reason

    def test_hourly_signal_cap(self):
        config = self_config()
        config.risk.max_signals_per_hour = 3
        gate = risk_rules.check_guards(gold_buy(), gold_info(), state(signals_last_hour=3), config)
        assert not gate.ok

    def test_symbol_blocklist(self):
        config = self_config()
        config.risk.block_symbols = ["XAUUSD"]
        gate = risk_rules.check_guards(gold_buy(), gold_info(), state(), config)
        assert not gate.ok
        assert "block_symbols" in gate.reason

    def test_symbol_allowlist_excludes_others(self):
        config = self_config()
        config.risk.allow_symbols = ["EURUSD"]
        gate = risk_rules.check_guards(gold_buy(), gold_info(), state(), config)
        assert not gate.ok
        assert "allow_symbols" in gate.reason

    def test_outside_trading_hours(self):
        config = self_config()
        config.risk.hours.start = "07:00"
        config.risk.hours.end = "10:00"
        gate = risk_rules.check_guards(gold_buy(), gold_info(), state(), config)
        assert not gate.ok
        assert "outside trading hours" in gate.reason

    def test_weekend_is_blocked(self):
        gate = risk_rules.check_guards(
            gold_buy(), gold_info(), state(now=datetime(2026, 7, 26, 12, 0)), self_config()
        )
        assert not gate.ok
        assert "outside risk.hours.days" in gate.reason

    def test_wide_spread_is_blocked(self):
        config = self_config()
        config.risk.max_spread_points = 30
        # A 100-point spread on gold ($1.00).
        gate = risk_rules.check_guards(
            gold_buy(), gold_info(bid=2349.5, ask=2350.5), state(), config
        )
        assert not gate.ok
        assert "spread" in gate.reason

    def test_stop_tighter_than_the_minimum(self):
        config = self_config()
        config.risk.min_stop_points = 100  # $1.00 on gold
        gate = risk_rules.check_guards(
            gold_buy(entry=2350.0, stop=2349.5), gold_info(), state(), config
        )
        assert not gate.ok
        assert "points away" in gate.reason

    def test_broker_minimum_stop_distance(self):
        gate = risk_rules.check_guards(
            gold_buy(entry=2350.0, stop=2349.0),
            gold_info(stops_level_points=200),
            state(),
            self_config(),
        )
        assert not gate.ok
        assert "broker's minimum" in gate.reason

    def test_management_messages_bypass_entry_guards(self):
        # A daily-loss halt must not strand an open position: closing still works.
        config = self_config()
        config.risk.max_daily_loss_pct = 5.0
        close = Signal(action=Action.CLOSE, symbol="XAUUSD")
        gate = risk_rules.check_guards(close, gold_info(), state(equity=9_000.0), config)
        assert gate.ok

    def test_management_still_respects_dedupe(self):
        close = Signal(action=Action.CLOSE, symbol="XAUUSD")
        gate = risk_rules.check_guards(
            close, gold_info(), state(duplicate_of="earlier"), self_config()
        )
        assert not gate.ok


class TestTakeProfitSelection:
    def test_first_mode_takes_tp1(self):
        config = self_config()
        config.execution.tp_mode = "first"
        assert risk_rules.select_take_profits(gold_buy(tps=(2360, 2370, 2380)), config) == [2360]

    def test_last_mode_takes_the_furthest(self):
        config = self_config()
        config.execution.tp_mode = "last"
        assert risk_rules.select_take_profits(gold_buy(tps=(2360, 2370, 2380)), config) == [2380]

    def test_split_mode_returns_every_target(self):
        config = self_config()
        config.execution.tp_mode = "split"
        assert risk_rules.select_take_profits(gold_buy(tps=(2360, 2370, 2380)), config) == [
            2360,
            2370,
            2380,
        ]

    def test_max_tps_truncates(self):
        config = self_config()
        config.execution.tp_mode = "split"
        config.execution.max_tps = 2
        assert risk_rules.select_take_profits(gold_buy(tps=(2360, 2370, 2380)), config) == [
            2360,
            2370,
        ]

    def test_no_targets_means_one_leg_without_a_tp(self):
        assert risk_rules.select_take_profits(gold_buy(tps=()), self_config()) == [None]


class TestBreakeven:
    def test_buy_stop_moves_above_entry(self):
        price = risk_rules.breakeven_price(2350.0, Side.BUY, gold_info(), offset_points=20)
        assert price == pytest.approx(2350.20)

    def test_sell_stop_moves_below_entry(self):
        price = risk_rules.breakeven_price(2350.0, Side.SELL, gold_info(), offset_points=20)
        assert price == pytest.approx(2349.80)


def self_config():
    """A fresh default config per assertion, so mutations do not leak."""
    from tgscalper import config as config_module

    return config_module.load("does-not-exist.yaml", env={})


class TestPerSymbolLimits:
    """One points value cannot suit gold, EURUSD and Bitcoin at once.

    100 points is $1.00 on gold, one pip on EURUSD and one cent on Bitcoin. As
    a single global spread ceiling it blocks every crypto signal while barely
    constraining gold, which is exactly what a mixed watchlist runs into.
    """

    def _config(self):
        config = self_config()
        config.risk.max_spread_points = 100
        config.risk.min_stop_points = 50
        config.risk.symbol_limits = {
            "BTCUSD": {"max_spread_points": 20000, "min_stop_points": 5000}
        }
        return config

    def test_the_global_still_applies_to_gold(self):
        config = self._config()
        # $1.20 spread = 120 points, past the 100-point gold limit.
        gate = risk_rules.check_guards(
            gold_buy(), gold_info(bid=2349.4, ask=2350.6), state(), config
        )
        assert not gate.ok
        assert "XAUUSD" in gate.reason

    def test_an_override_widens_it_for_crypto(self):
        config = self._config()
        btc = Signal(
            action=Action.OPEN,
            symbol="BTCUSD",
            side=Side.BUY,
            entry=61000.0,
            stop_loss=60000.0,
            take_profits=[62000.0],
        )
        # A $150 spread: far past the gold limit, fine for Bitcoin.
        info = gold_info(bid=60925.0, ask=61075.0, name="BTCUSD")
        assert risk_rules.check_guards(btc, info, state(), config).ok

    def test_a_symbol_without_an_override_uses_the_global(self):
        config = self._config()
        assert config.risk.limits_for("EURUSD") == (50.0, 100.0)

    def test_overrides_are_case_insensitive(self):
        config = self._config()
        assert config.risk.limits_for("btcusd") == (5000.0, 20000.0)

    def test_a_partial_override_keeps_the_other_global(self):
        config = self_config()
        config.risk.min_stop_points = 50
        config.risk.max_spread_points = 100
        config.risk.symbol_limits = {"XAGUSD": {"max_spread_points": 200}}
        assert config.risk.limits_for("XAGUSD") == (50.0, 200.0)

    def test_limits_load_from_yaml(self, tmp_path):
        from tgscalper import config as config_module

        path = tmp_path / "config.yaml"
        path.write_text(
            "risk:\n"
            "  max_spread_points: 100\n"
            "  symbol_limits:\n"
            "    btcusd:\n"
            "      max_spread_points: 20000\n"
        )
        config = config_module.load(path, env={})
        # Keys are upper-cased on load, so YAML casing does not matter.
        assert config.risk.limits_for("BTCUSD")[1] == 20000.0
