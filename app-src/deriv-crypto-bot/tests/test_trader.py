"""Tests for the trader's account guard — the check that stands between the
bot and real money."""

import pytest

from deriv_bot.state import StateStore
from deriv_bot.trader import Trader, UnsafeAccount

from conftest import make_config


def build(tmp_path, account, **overrides):
    config = make_config(**overrides)
    store = StateStore(str(tmp_path / "state.json"), str(tmp_path / "trades.jsonl"))
    trader = Trader(config, store)
    trader.api.account = account
    return trader


VIRTUAL = {"loginid": "VRTC1234", "currency": "USD", "is_virtual": 1}
REAL = {"loginid": "CR1234", "currency": "USD", "is_virtual": 0}


class TestAccountGuard:
    def test_virtual_account_is_always_allowed(self, tmp_path):
        build(tmp_path, VIRTUAL)._verify_account()  # must not raise

    def test_real_account_is_refused_by_default(self, tmp_path):
        trader = build(tmp_path, REAL)
        with pytest.raises(UnsafeAccount, match="CR1234"):
            trader._verify_account()

    def test_real_account_allowed_only_with_explicit_opt_in(self, tmp_path):
        build(tmp_path, REAL, allow_real_money=True)._verify_account()  # must not raise

    def test_opt_in_does_not_change_virtual_behaviour(self, tmp_path):
        trader = build(tmp_path, VIRTUAL, allow_real_money=True)
        trader._verify_account()
        assert trader.currency == "USD"

    def test_missing_is_virtual_is_treated_as_real(self, tmp_path):
        # Fail closed: an unexpected payload must not be assumed to be a demo.
        trader = build(tmp_path, {"loginid": "CR9999", "currency": "USD"})
        with pytest.raises(UnsafeAccount):
            trader._verify_account()


class TestCurrencyResolution:
    def test_takes_currency_from_the_account(self, tmp_path):
        trader = build(tmp_path, {**VIRTUAL, "currency": "EUR"})
        trader._verify_account()
        assert trader.currency == "EUR"

    def test_configuration_overrides_the_account(self, tmp_path):
        trader = build(tmp_path, {**VIRTUAL, "currency": "EUR"}, currency="BTC")
        trader._verify_account()
        assert trader.currency == "BTC"

    def test_falls_back_to_usd(self, tmp_path):
        trader = build(tmp_path, {"loginid": "VRTC1", "is_virtual": 1})
        trader._verify_account()
        assert trader.currency == "USD"
