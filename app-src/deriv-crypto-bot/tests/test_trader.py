"""Tests for the trader's account guard — the check that stands between the
bot and real money — and for its reconnection behaviour."""

import asyncio

import pytest

from deriv_bot.api import ConnectionLost, DerivError
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


class TestReconnection:
    """A 24/7 bot must treat a failed connection as a retry, not an exit.

    These cover the case that a real run hit: a proxy rejecting the socket.
    That surfaces as ConnectionLost now, and must not end the process.
    """

    def drive(self, tmp_path, error, *, attempts_before_stop=2, **overrides):
        trader = build(tmp_path, VIRTUAL, **overrides)
        attempts: list[int] = []

        async def failing_connect():
            attempts.append(1)
            if len(attempts) >= attempts_before_stop:
                trader.request_stop()
            raise error

        trader.api.connect = failing_connect
        asyncio.run(trader.run())
        return attempts

    def test_a_rejecting_proxy_is_retried(self, tmp_path):
        attempts = self.drive(tmp_path, ConnectionLost("proxy rejected connection: HTTP 403"))
        assert len(attempts) >= 2, "expected the trader to retry rather than exit"

    def test_a_network_error_is_retried(self, tmp_path):
        attempts = self.drive(tmp_path, OSError("name resolution failed"))
        assert len(attempts) >= 2

    def test_a_transient_api_error_is_retried(self, tmp_path):
        attempts = self.drive(tmp_path, DerivError("RateLimit", "slow down"))
        assert len(attempts) >= 2

    def test_an_invalid_token_stops_instead_of_looping_forever(self, tmp_path):
        # Retrying a permanently bad token would spin uselessly and hide the
        # real problem, so this one propagates.
        trader = build(tmp_path, VIRTUAL)

        async def bad_token():
            raise DerivError("InvalidToken", "token is invalid")

        trader.api.connect = bad_token
        with pytest.raises(DerivError):
            asyncio.run(trader.run())

    def test_an_unsafe_account_stops_immediately(self, tmp_path):
        trader = build(tmp_path, REAL)  # real account, no opt-in

        async def connect():
            return REAL

        trader.api.connect = connect
        with pytest.raises(UnsafeAccount):
            asyncio.run(trader.run())


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
