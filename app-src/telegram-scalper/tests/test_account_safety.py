"""The real-money guard.

"Send orders to the broker" and "risk actual money" are separate decisions.
These tests pin down the second one, because getting it wrong is the only
mistake in this project that costs money directly.
"""

from __future__ import annotations

import pytest

from tgscalper import config as config_module
from tgscalper.brokers.base import BrokerError
from tgscalper.brokers.paper import PaperBroker
from tgscalper.engine import Engine
from tgscalper.journal import Journal
from tgscalper.models import AccountInfo


class FakeLiveBroker(PaperBroker):
    """A paper book that claims to be a live broker, for testing the guard."""

    name = "fake-mt5"

    def __init__(self, trade_mode: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.trade_mode = trade_mode

    @property
    def is_live(self) -> bool:
        return True

    def account_info(self) -> AccountInfo:
        base = super().account_info()
        return AccountInfo(
            balance=base.balance,
            equity=base.equity,
            currency=base.currency,
            margin_free=base.margin_free,
            trade_mode=self.trade_mode,
            login="41187584",
            server="Deriv-Demo" if self.trade_mode == "DEMO" else "Deriv-Server",
        )


@pytest.fixture
def config():
    return config_module.load("does-not-exist.yaml", env={})


def engine_for(broker, config, tmp_path) -> Engine:
    return Engine(config, broker, Journal(tmp_path / "journal.sqlite"))


class TestAccountTypeReporting:
    def test_paper_broker_says_paper(self):
        assert PaperBroker().account_info().trade_mode == "PAPER"

    def test_paper_is_never_real_money(self):
        assert not PaperBroker().account_info().is_real_money

    def test_real_is_flagged(self):
        assert FakeLiveBroker("REAL").account_info().is_real_money

    def test_demo_is_not_real_money(self):
        assert not FakeLiveBroker("DEMO").account_info().is_real_money

    def test_contest_is_not_real_money(self):
        assert not FakeLiveBroker("CONTEST").account_info().is_real_money

    def test_unknown_is_not_treated_as_real(self):
        # Refusing every account we cannot classify would block legitimate
        # brokers that do not report a type; the live kill switch still applies.
        assert not FakeLiveBroker("UNKNOWN").account_info().is_real_money


class TestRealMoneyGuard:
    def test_demo_account_starts_normally(self, config, tmp_path):
        engine = engine_for(FakeLiveBroker("DEMO"), config, tmp_path)
        engine.start()  # must not raise
        assert engine.broker.is_live

    def test_real_account_is_refused_by_default(self, config, tmp_path):
        engine = engine_for(FakeLiveBroker("REAL"), config, tmp_path)
        with pytest.raises(BrokerError) as excinfo:
            engine.start()
        message = str(excinfo.value)
        assert "REAL MONEY" in message
        # The message must name the account, or it is not actionable.
        assert "41187584" in message
        assert "allow_real_money" in message

    def test_real_account_runs_once_explicitly_allowed(self, config, tmp_path):
        config.execution.allow_real_money = True
        engine = engine_for(FakeLiveBroker("REAL"), config, tmp_path)
        engine.start()  # must not raise

    def test_the_flag_is_off_by_default(self, config):
        assert not config.execution.allow_real_money

    def test_paper_broker_ignores_the_flag(self, config, tmp_path):
        # The guard only applies to brokers that actually send orders.
        engine = engine_for(PaperBroker(), config, tmp_path)
        engine.start()

    def test_flag_loads_from_yaml(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("execution:\n  allow_real_money: true\n")
        assert config_module.load(path, env={}).execution.allow_real_money


class TestLiveSwitchIsStillRequired:
    """allow_real_money does not bypass the paper/live switch."""

    def test_live_still_needs_both_switches(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("execution:\n  mode: live\n  allow_real_money: true\n")
        config = config_module.load(path, env={})
        assert not config.execution.live_enabled

    def test_both_switches_plus_the_flag(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("execution:\n  mode: live\n  allow_real_money: true\n")
        config = config_module.load(
            path, env={"TGSCALPER_ALLOW_LIVE": config_module.LIVE_ACK}
        )
        assert config.execution.live_enabled
        assert config.execution.allow_real_money
