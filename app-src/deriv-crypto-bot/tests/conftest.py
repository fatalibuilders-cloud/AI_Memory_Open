"""Shared test helpers."""

from __future__ import annotations

from deriv_bot.config import Config

_DEFAULTS = {
    "app_id": "1089",
    "api_token": "test-token",
    "stake": 1.0,
    "daily_loss_limit": 20.0,
    "max_open_trades": 2,
    "max_trades_per_day": 40,
    "symbol_cooldown": 300,
    "max_stake_fraction": 0.02,
}


def make_config(**overrides) -> Config:
    """A valid Config for tests, with any field overridable."""
    return Config(**{**_DEFAULTS, **overrides})
