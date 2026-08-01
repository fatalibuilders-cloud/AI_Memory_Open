"""Tests for the preflight check.

The property that matters most: the check must never buy anything. It is the
first thing a new user runs, often against a live token.
"""

import asyncio

import pytest

from deriv_bot.api import DerivError
from deriv_bot.check import Report, _account_checks, _pricing_checks, _universe_checks, run_checks

from conftest import make_config
from test_cycle import FakeAPI, crypto, forex, signalling_candles


class CheckAPI(FakeAPI):
    """FakeAPI that also records connect/close and can fail on demand."""

    def __init__(self, *args, connect_error=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect_error = connect_error
        self.connected = False
        self.closed = False

    async def connect(self):
        if self.connect_error:
            raise self.connect_error
        self.connected = True
        return self.account

    async def close(self):
        self.closed = True


def build(monkeypatch, universe, candle_data, *, account=None, **overrides):
    config = make_config(min_separation_atr=0.0, **overrides)
    api = CheckAPI(universe, candle_data)
    if account is not None:
        api.account = account
    monkeypatch.setattr("deriv_bot.check.DerivAPI", lambda cfg: api)
    return config, api, Report(colour=False)


VIRTUAL = {"loginid": "VRTC1", "currency": "USD", "is_virtual": 1}
REAL = {"loginid": "CR1", "currency": "USD", "is_virtual": 0}


class TestNeverTrades:
    def test_a_full_successful_check_buys_nothing(self, monkeypatch, capsys):
        config, api, report = build(monkeypatch, [crypto("cryBTCUSD")], signalling_candles())
        asyncio.run(run_checks(config, report))
        assert api.buys == [], "the preflight check must never place a trade"

    def test_it_prices_a_contract_without_buying(self, monkeypatch, capsys):
        config, api, report = build(monkeypatch, [crypto("cryBTCUSD")], signalling_candles())
        asyncio.run(run_checks(config, report))
        assert api.contract_requests, "expected it to request contract pricing"
        assert api.buys == []

    def test_it_closes_the_connection(self, monkeypatch, capsys):
        config, api, report = build(monkeypatch, [crypto("cryBTCUSD")], signalling_candles())
        asyncio.run(run_checks(config, report))
        assert api.closed


class TestAccountReporting:
    def run_account(self, monkeypatch, account, **overrides):
        config, api, report = build(
            monkeypatch, [crypto("cryBTCUSD")], signalling_candles(), account=account, **overrides
        )
        asyncio.run(_account_checks(api, config, account, report))
        return report

    def test_virtual_account_passes(self, monkeypatch, capsys):
        report = self.run_account(monkeypatch, VIRTUAL)
        assert not report.failures
        assert "no real funds at risk" in capsys.readouterr().out.lower()

    def test_real_account_without_opt_in_fails(self, monkeypatch, capsys):
        report = self.run_account(monkeypatch, REAL)
        assert report.failures
        assert "refuse to start" in capsys.readouterr().out.lower()

    def test_real_account_with_opt_in_warns_loudly(self, monkeypatch, capsys):
        report = self.run_account(monkeypatch, REAL, allow_real_money=True)
        assert not report.failures
        assert report.warnings
        assert "live funds are at risk" in capsys.readouterr().out.lower()

    def test_loss_limit_larger_than_balance_warns(self, monkeypatch, capsys):
        report = self.run_account(monkeypatch, VIRTUAL, daily_loss_limit=99999.0)
        assert any("loss limit" in w.lower() for w in report.warnings)


class TestUniverseReporting:
    def run_universe(self, monkeypatch, universe, **overrides):
        config, api, report = build(monkeypatch, universe, signalling_candles(), **overrides)
        asyncio.run(_universe_checks(api, config, report))
        return report, api

    def test_counts_crypto_and_excludes_the_rest(self, monkeypatch, capsys):
        universe = [crypto("cryBTCUSD"), crypto("cryETHUSD"), forex("frxEURUSD")]
        report, api = self.run_universe(monkeypatch, universe)
        out = capsys.readouterr().out
        assert "2 cryptocurrency symbols" in out
        assert "1 non-crypto symbols excluded" in out
        assert not report.failures

    def test_no_crypto_available_is_a_failure(self, monkeypatch, capsys):
        report, _ = self.run_universe(monkeypatch, [forex("frxEURUSD")])
        assert report.failures

    def test_bad_symbol_allowlist_explains_itself(self, monkeypatch, capsys):
        report, _ = self.run_universe(
            monkeypatch, [crypto("cryBTCUSD")], symbols=("cryTYPOUSD",)
        )
        assert report.failures
        assert "typos" in capsys.readouterr().out.lower()

    def test_it_only_ever_fetches_candles_for_crypto(self, monkeypatch, capsys):
        universe = [crypto("cryBTCUSD"), forex("frxEURUSD")]
        _, api = self.run_universe(monkeypatch, universe)
        assert all(s.startswith("cry") for s in api.candle_requests)


class TestPricing:
    def test_reports_the_measured_payout_ratio(self, monkeypatch, capsys):
        config, api, report = build(monkeypatch, [crypto("cryBTCUSD")], signalling_candles())
        asyncio.run(_pricing_checks(api, config, report, "cryBTCUSD"))
        out = capsys.readouterr().out
        # FakeAPI quotes payout = stake * 1.85, so the ratio is 0.85.
        assert "0.850" in out
        assert "break even" in out.lower()
        assert api.buys == []

    def test_missing_contract_is_a_failure(self, monkeypatch, capsys):
        config, api, report = build(monkeypatch, [crypto("cryBTCUSD")], signalling_candles())

        async def no_contracts(symbol, currency):
            return {"available": []}

        api.contracts_for = no_contracts
        asyncio.run(_pricing_checks(api, config, report, "cryBTCUSD"))
        assert report.failures

    def test_permission_denied_suggests_the_trade_scope(self, monkeypatch, capsys):
        config, api, report = build(monkeypatch, [crypto("cryBTCUSD")], signalling_candles())

        async def denied(request):
            raise DerivError("PermissionDenied", "not allowed")

        api.proposal = denied
        asyncio.run(_pricing_checks(api, config, report, "cryBTCUSD"))
        assert report.failures
        assert "trade" in capsys.readouterr().out.lower()


class TestConnectionFailures:
    def test_invalid_token_explains_how_to_fix_it(self, monkeypatch, capsys):
        config, api, report = build(monkeypatch, [crypto("cryBTCUSD")], signalling_candles())
        api.connect_error = DerivError("InvalidToken", "token is invalid")
        asyncio.run(run_checks(config, report))
        out = capsys.readouterr().out.lower()
        assert report.failures
        assert "api token" in out
        assert "not payments" in out

    def test_network_failure_is_reported_clearly(self, monkeypatch, capsys):
        config, api, report = build(monkeypatch, [crypto("cryBTCUSD")], signalling_candles())
        api.connect_error = OSError("no route to host")
        asyncio.run(run_checks(config, report))
        assert report.failures
        assert "could not reach deriv" in capsys.readouterr().out.lower()


class TestReport:
    def test_tracks_outcomes(self):
        report = Report(colour=False)
        report.ok("fine")
        report.warn("hmm")
        report.fail("broken")
        assert report.warnings == ["hmm"]
        assert report.failures == ["broken"]

    def test_colour_can_be_disabled(self, capsys):
        Report(colour=False).ok("plain")
        assert "\033[" not in capsys.readouterr().out
