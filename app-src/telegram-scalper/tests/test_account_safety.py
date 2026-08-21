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
from tgscalper.models import AccountInfo, MessageRef


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
        # start() must not raise: killing the process hides the reason and
        # looks identical to the bot being dead. Trading is what gets refused.
        engine.start()
        assert not engine.broker_ready
        message = engine.broker_error
        assert "REAL MONEY" in message
        # The message must name the account, or it is not actionable.
        assert "41187584" in message
        assert "allow_real_money" in message

    def test_a_refused_account_places_no_trades(self, config, tmp_path):
        config.risk.hours.days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        broker = FakeLiveBroker("REAL")
        engine = engine_for(broker, config, tmp_path)
        engine.start()
        decision = engine.handle(
            "GOLD BUY 2350\nSL 2344\nTP 2360",
            MessageRef(chat_id=-1, message_id=1),
        )
        assert not decision.accepted
        assert "broker not connected" in decision.reason
        assert broker.positions() == []

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


class UnreachableBroker(PaperBroker):
    """A broker whose connect() fails, like MT5 with the terminal closed."""

    name = "unreachable-mt5"

    def __init__(self, fail_times: int = 99) -> None:
        super().__init__()
        self.attempts = 0
        self.fail_times = fail_times

    @property
    def is_live(self) -> bool:
        return True

    def connect(self) -> None:
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise BrokerError("MT5 initialize failed (-10005): IPC timeout")
        super().connect()


class TestBrokerOutageIsNotFatal:
    """MT5 being closed must never take the Telegram side down.

    It used to raise out of start(), killing listener and control bot sixty
    seconds after every launch — indistinguishable from the bot being dead,
    and hiding the one fact that explained it.
    """

    def test_start_survives_an_unreachable_broker(self, config, tmp_path):
        engine = engine_for(UnreachableBroker(), config, tmp_path)
        engine.start()  # must not raise
        assert not engine.broker_ready
        assert "IPC timeout" in engine.broker_error

    def test_signals_are_refused_with_the_broker_reason(self, config, tmp_path):
        config.risk.hours.days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        engine = engine_for(UnreachableBroker(), config, tmp_path)
        engine.start()
        decision = engine.handle(
            "GOLD BUY 2350\nSL 2344\nTP 2360", MessageRef(chat_id=-1, message_id=1)
        )
        assert not decision.accepted
        assert "broker not connected" in decision.reason
        assert "IPC timeout" in decision.reason

    def test_the_outage_is_journalled(self, config, tmp_path):
        journal = Journal(tmp_path / "journal.sqlite")
        engine = Engine(config, UnreachableBroker(), journal)
        engine.start()
        rows = journal._read("SELECT kind, detail FROM events WHERE kind = 'broker_error'")
        assert rows and "IPC timeout" in rows[0]["detail"]

    def test_it_recovers_when_the_terminal_comes_back(self, config, tmp_path):
        broker = UnreachableBroker(fail_times=1)
        engine = engine_for(broker, config, tmp_path)
        engine.start()
        assert not engine.broker_ready
        # MT5 has since been opened; the next retry should succeed.
        assert engine.retry_broker(min_interval=0)
        assert engine.broker_ready
        assert engine.broker_error == ""

    def test_retries_are_rate_limited(self, config, tmp_path):
        broker = UnreachableBroker()
        engine = engine_for(broker, config, tmp_path)
        engine.start()
        attempts = broker.attempts
        # A failing MT5 connect blocks for a minute; retrying per signal would
        # stall every message behind a dead terminal.
        for _ in range(5):
            engine.retry_broker(min_interval=120)
        assert broker.attempts == attempts

    def test_a_healthy_broker_reports_ready(self, config, tmp_path):
        engine = engine_for(PaperBroker(), config, tmp_path)
        engine.start()
        assert engine.broker_ready
        assert engine.broker_error == ""
