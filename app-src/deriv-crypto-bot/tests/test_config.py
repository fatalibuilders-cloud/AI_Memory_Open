"""Tests for configuration loading and validation."""

import pytest

from deriv_bot.config import Config, ConfigError

from conftest import make_config

REQUIRED = {"DERIV_APP_ID": "1089", "DERIV_API_TOKEN": "secret-token"}


def set_env(monkeypatch, **values):
    for key in list(Config.__dataclass_fields__):  # clear anything leaking in
        monkeypatch.delenv(key.upper(), raising=False)
    for key, value in {**REQUIRED, **values}.items():
        monkeypatch.setenv(key, str(value))


class TestFromEnv:
    def test_minimal_environment(self, monkeypatch):
        set_env(monkeypatch)
        config = Config.from_env()
        assert config.app_id == "1089"
        assert config.api_token == "secret-token"
        assert config.allow_real_money is False  # safe by default
        assert config.dry_run is False

    def test_missing_app_id_is_an_error(self, monkeypatch):
        set_env(monkeypatch)
        monkeypatch.delenv("DERIV_APP_ID")
        with pytest.raises(ConfigError, match="DERIV_APP_ID"):
            Config.from_env()

    def test_missing_token_is_an_error(self, monkeypatch):
        set_env(monkeypatch)
        monkeypatch.delenv("DERIV_API_TOKEN")
        with pytest.raises(ConfigError, match="DERIV_API_TOKEN"):
            Config.from_env()

    def test_blank_value_counts_as_missing(self, monkeypatch):
        set_env(monkeypatch, DERIV_API_TOKEN="   ")
        with pytest.raises(ConfigError):
            Config.from_env()

    @pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on", "y"])
    def test_truthy_flags(self, monkeypatch, value):
        set_env(monkeypatch, DERIV_ALLOW_REAL_MONEY=value)
        assert Config.from_env().allow_real_money is True

    @pytest.mark.parametrize("value", ["false", "0", "no", "off", "anything-else"])
    def test_falsy_flags(self, monkeypatch, value):
        set_env(monkeypatch, DERIV_ALLOW_REAL_MONEY=value)
        assert Config.from_env().allow_real_money is False

    def test_symbol_list_is_split_and_trimmed(self, monkeypatch):
        set_env(monkeypatch, DERIV_SYMBOLS=" cryBTCUSD , cryETHUSD ,, ")
        assert Config.from_env().symbols == ("cryBTCUSD", "cryETHUSD")

    def test_empty_symbol_list_means_discover_everything(self, monkeypatch):
        set_env(monkeypatch, DERIV_SYMBOLS="")
        assert Config.from_env().symbols == ()

    def test_non_numeric_number_is_an_error(self, monkeypatch):
        set_env(monkeypatch, STAKE="a lot")
        with pytest.raises(ConfigError, match="STAKE"):
            Config.from_env()


class TestValidation:
    def test_fast_ema_must_be_shorter_than_slow(self):
        with pytest.raises(ConfigError, match="EMA_FAST"):
            make_config(ema_fast=21, ema_slow=9)

    def test_stake_must_be_positive(self):
        with pytest.raises(ConfigError, match="STAKE"):
            make_config(stake=0)

    def test_loss_limit_must_be_positive(self):
        with pytest.raises(ConfigError, match="DAILY_LOSS_LIMIT"):
            make_config(daily_loss_limit=0)

    def test_candle_count_must_cover_the_warmup(self):
        with pytest.raises(ConfigError, match="CANDLE_COUNT"):
            make_config(candle_count=10, ema_slow=21, rsi_period=14)

    def test_duration_unit_must_be_known(self):
        with pytest.raises(ConfigError, match="TRADE_DURATION_UNIT"):
            make_config(trade_duration_unit="weeks")

    def test_stake_fraction_must_be_a_fraction(self):
        with pytest.raises(ConfigError, match="MAX_STAKE_FRACTION"):
            make_config(max_stake_fraction=1.5)

    def test_max_open_trades_must_be_at_least_one(self):
        with pytest.raises(ConfigError, match="MAX_OPEN_TRADES"):
            make_config(max_open_trades=0)


class TestRedaction:
    def test_token_is_never_exposed(self):
        redacted = make_config(api_token="super-secret").redacted()
        assert redacted["api_token"] == "***redacted***"
        assert "super-secret" not in str(redacted)

    def test_other_fields_survive(self):
        assert make_config(stake=3.0).redacted()["stake"] == 3.0
