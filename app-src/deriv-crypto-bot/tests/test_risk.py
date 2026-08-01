"""Tests for the risk limits — the controls that bound what the bot can lose."""

import os

import pytest

from deriv_bot.risk import RiskManager
from deriv_bot.state import StateStore

from conftest import make_config


@pytest.fixture
def store(tmp_path):
    return StateStore(str(tmp_path / "state.json"), str(tmp_path / "trades.jsonl"))


def build(store, tmp_path, **overrides):
    config = make_config(kill_switch_file=str(tmp_path / "KILL"), **overrides)
    return RiskManager(config, store)


def check(manager, symbol="cryBTCUSD", balance=1000.0, open_trades=0, open_symbols=None, now=None):
    return manager.check(
        symbol,
        balance=balance,
        open_trades=open_trades,
        open_symbols=open_symbols or set(),
        now=now,
    )


class TestKillSwitch:
    def test_absent_by_default(self, store, tmp_path):
        assert check(build(store, tmp_path)).allowed

    def test_blocks_everything_when_present(self, store, tmp_path):
        manager = build(store, tmp_path)
        open(manager.config.kill_switch_file, "w").close()
        decision = check(manager)
        assert not decision.allowed
        assert decision.global_block
        assert "kill switch" in decision.reason

    def test_unblocks_when_removed(self, store, tmp_path):
        manager = build(store, tmp_path)
        open(manager.config.kill_switch_file, "w").close()
        assert not check(manager).allowed
        os.unlink(manager.config.kill_switch_file)
        assert check(manager).allowed


class TestDailyLimits:
    def test_loss_limit_halts_the_bot(self, store, tmp_path):
        manager = build(store, tmp_path, daily_loss_limit=10.0)
        store.daily.realized_pnl = -10.0
        manager.refresh_daily_limits()
        assert store.daily.halted
        decision = check(manager)
        assert not decision.allowed and decision.global_block

    def test_loss_limit_not_triggered_early(self, store, tmp_path):
        manager = build(store, tmp_path, daily_loss_limit=10.0)
        store.daily.realized_pnl = -9.99
        manager.refresh_daily_limits()
        assert not store.daily.halted

    def test_profit_target_halts_the_bot(self, store, tmp_path):
        manager = build(store, tmp_path, daily_profit_target=25.0)
        store.daily.realized_pnl = 30.0
        manager.refresh_daily_limits()
        assert store.daily.halted
        assert "profit target" in store.daily.halt_reason

    def test_zero_profit_target_is_disabled(self, store, tmp_path):
        manager = build(store, tmp_path, daily_profit_target=0.0)
        store.daily.realized_pnl = 5000.0
        manager.refresh_daily_limits()
        assert not store.daily.halted

    def test_trade_cap_blocks_new_trades(self, store, tmp_path):
        manager = build(store, tmp_path, max_trades_per_day=3)
        store.daily.trades_opened = 3
        decision = check(manager)
        assert not decision.allowed and decision.global_block

    def test_halt_survives_a_restart(self, tmp_path):
        state = str(tmp_path / "state.json")
        journal = str(tmp_path / "trades.jsonl")
        first = StateStore(state, journal)
        first.halt("loss limit")
        # A restart must not clear the halt — otherwise restarting the process
        # would be a way to keep trading past the daily loss limit.
        assert StateStore(state, journal).daily.halted


class TestConcurrency:
    def test_max_open_trades_blocks(self, store, tmp_path):
        manager = build(store, tmp_path, max_open_trades=2)
        decision = check(manager, open_trades=2)
        assert not decision.allowed and decision.global_block

    def test_one_position_per_symbol(self, store, tmp_path):
        manager = build(store, tmp_path)
        decision = check(manager, symbol="cryBTCUSD", open_symbols={"cryBTCUSD"})
        assert not decision.allowed
        assert not decision.global_block  # other symbols may still trade

    def test_other_symbols_still_allowed(self, store, tmp_path):
        manager = build(store, tmp_path)
        assert check(manager, symbol="cryETHUSD", open_symbols={"cryBTCUSD"}).allowed


class TestCooldown:
    def test_blocks_within_the_window(self, store, tmp_path):
        manager = build(store, tmp_path, symbol_cooldown=300)
        manager.note_trade("cryBTCUSD", now=1000.0)
        decision = check(manager, now=1100.0)
        assert not decision.allowed and "cooling down" in decision.reason

    def test_allows_after_the_window(self, store, tmp_path):
        manager = build(store, tmp_path, symbol_cooldown=300)
        manager.note_trade("cryBTCUSD", now=1000.0)
        assert check(manager, now=1301.0).allowed

    def test_is_per_symbol(self, store, tmp_path):
        manager = build(store, tmp_path, symbol_cooldown=300)
        manager.note_trade("cryBTCUSD", now=1000.0)
        assert check(manager, symbol="cryETHUSD", now=1100.0).allowed


class TestSizing:
    def test_uses_configured_stake_when_affordable(self, store, tmp_path):
        manager = build(store, tmp_path, stake=5.0, max_stake_fraction=0.5)
        assert check(manager, balance=1000.0).stake == 5.0

    def test_caps_stake_at_the_balance_fraction(self, store, tmp_path):
        manager = build(store, tmp_path, stake=100.0, max_stake_fraction=0.02)
        assert check(manager, balance=1000.0).stake == 20.0

    def test_caps_stake_at_the_remaining_loss_budget(self, store, tmp_path):
        manager = build(store, tmp_path, stake=50.0, daily_loss_limit=30.0, max_stake_fraction=1.0)
        store.daily.realized_pnl = -25.0  # only 5.00 of budget left
        assert check(manager, balance=1000.0).stake == 5.0

    def test_zero_balance_blocks(self, store, tmp_path):
        decision = check(build(store, tmp_path), balance=0.0)
        assert not decision.allowed and decision.global_block

    def test_stake_never_exceeds_balance(self, store, tmp_path):
        manager = build(store, tmp_path, stake=10.0, max_stake_fraction=1.0)
        decision = check(manager, balance=3.0)
        assert decision.stake <= 3.0
