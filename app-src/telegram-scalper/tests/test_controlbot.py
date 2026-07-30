"""Control bot: group selection, owner locking, pause behaviour."""

from __future__ import annotations

import pytest

from tgscalper import config as config_module
from tgscalper.brokers.paper import PaperBroker
from tgscalper.controlbot import ControlBot
from tgscalper.engine import Engine
from tgscalper.groupstate import GroupSelection, apply_selection, selection_path
from tgscalper.journal import Journal
from tgscalper.models import MessageRef

CHAT_ID = -1001234567890


@pytest.fixture
def config(tmp_path):
    cfg = config_module.load("does-not-exist.yaml", env={})
    cfg.telegram.session_dir = str(tmp_path)
    cfg.control_bot.enabled = True
    cfg.control_bot.owner_id = 42
    cfg.control_bot.token = "123456:FAKE"
    return cfg


@pytest.fixture
def bot(config, tmp_path):
    journal = Journal(tmp_path / "journal.sqlite")
    engine = Engine(config, PaperBroker(), journal)
    instance = ControlBot(config, engine, journal)
    yield instance
    journal.close()


class TestGroupSelection:
    def test_toggle_adds_and_removes(self):
        selection = GroupSelection()
        enabled, _ = selection.toggle(-100, "Gold VIP")
        assert enabled and selection.enabled == [-100]
        enabled, _ = selection.toggle(-100, "Gold VIP")
        assert not enabled and selection.enabled == []

    def test_five_is_the_ceiling(self):
        selection = GroupSelection()
        for index in range(5):
            assert selection.toggle(-100 - index, f"G{index}", limit=5)[0]
        added, message = selection.toggle(-999, "One too many", limit=5)
        assert not added
        assert "maximum" in message
        assert len(selection.enabled) == 5

    def test_removing_frees_a_slot(self):
        selection = GroupSelection()
        for index in range(5):
            selection.toggle(-100 - index, f"G{index}", limit=5)
        selection.toggle(-100, "G0", limit=5)  # remove one
        assert selection.toggle(-999, "New one", limit=5)[0]
        assert len(selection.enabled) == 5

    def test_limit_is_configurable(self):
        selection = GroupSelection()
        assert selection.toggle(-1, "a", limit=1)[0]
        assert not selection.toggle(-2, "b", limit=1)[0]

    def test_titles_are_remembered(self):
        selection = GroupSelection()
        selection.toggle(-100, "Gold Signals VIP")
        assert selection.titles["-100"] == "Gold Signals VIP"

    def test_survives_a_round_trip(self, tmp_path):
        path = tmp_path / "groups.json"
        selection = GroupSelection()
        selection.toggle(-100, "Gold VIP")
        selection.toggle(-200, "FX Scalps")
        selection.save(path)

        reloaded = GroupSelection.load(path)
        assert reloaded.enabled == [-100, -200]
        assert reloaded.titles["-100"] == "Gold VIP"

    def test_missing_file_loads_as_none(self, tmp_path):
        assert GroupSelection.load(tmp_path / "nope.json") is None

    def test_corrupt_file_is_ignored_rather_than_fatal(self, tmp_path):
        path = tmp_path / "groups.json"
        path.write_text("{not json at all")
        assert GroupSelection.load(path) is None

    def test_converts_to_group_configs(self):
        selection = GroupSelection()
        selection.toggle(-100, "Gold VIP")
        groups = selection.to_groups()
        assert len(groups) == 1
        assert groups[0].id == -100
        assert groups[0].title == "Gold VIP"
        assert groups[0].enabled


class TestApplySelection:
    def test_selection_overrides_the_yaml_groups(self, config, tmp_path):
        config.telegram.groups = []
        selection = GroupSelection()
        selection.toggle(-555, "Chosen in Telegram")
        selection.save(selection_path(config))

        assert apply_selection(config) is not None
        assert [group.id for group in config.telegram.groups] == [-555]

    def test_no_file_leaves_the_yaml_alone(self, config):
        from tgscalper.config import GroupConfig

        config.telegram.groups = [GroupConfig(id=-1, title="From YAML")]
        assert apply_selection(config) is None
        assert config.telegram.groups[0].title == "From YAML"

    def test_empty_selection_leaves_the_yaml_alone(self, config):
        from tgscalper.config import GroupConfig

        config.telegram.groups = [GroupConfig(id=-1, title="From YAML")]
        GroupSelection().save(selection_path(config))
        assert apply_selection(config) is None
        assert config.telegram.groups[0].title == "From YAML"


class TestOwnerLock:
    def test_the_owner_is_allowed(self, bot):
        assert bot._authorised(42)

    def test_anyone_else_is_refused(self, bot):
        assert not bot._authorised(43)
        assert not bot._authorised(None)

    def test_string_ids_still_match(self, bot):
        # Telethon hands back ints, but a config file may carry a string.
        bot.config.control_bot.owner_id = "42"
        assert bot._authorised(42)

    def test_nobody_is_authorised_without_an_owner(self, bot):
        bot.config.control_bot.owner_id = None
        assert not bot._authorised(42)
        assert not bot._authorised(None)


class TestControlBotConfig:
    def test_enabled_without_an_owner_is_rejected(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("control_bot:\n  enabled: true\n")
        with pytest.raises(ValueError, match="owner_id"):
            config_module.load(path, env={"TG_BOT_TOKEN": "123:abc"})

    def test_enabled_without_a_token_is_rejected(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("control_bot:\n  enabled: true\n  owner_id: 42\n")
        with pytest.raises(ValueError, match="TG_BOT_TOKEN"):
            config_module.load(path, env={})

    def test_fully_configured_loads(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("control_bot:\n  enabled: true\n  owner_id: 42\n")
        cfg = config_module.load(path, env={"TG_BOT_TOKEN": "123:abc"})
        assert cfg.control_bot.enabled
        assert cfg.control_bot.owner_id == 42
        assert cfg.control_bot.token == "123:abc"

    def test_disabled_needs_nothing(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("control_bot:\n  enabled: false\n")
        assert not config_module.load(path, env={}).control_bot.enabled

    def test_the_token_never_comes_from_config_yaml(self, tmp_path):
        # A token in config.yaml must be ignored — secrets live in .env only.
        path = tmp_path / "config.yaml"
        path.write_text("control_bot:\n  enabled: false\n  token: leaked-in-yaml\n")
        assert config_module.load(path, env={}).control_bot.token == ""


class TestPause:
    @pytest.fixture
    def setup(self, config, tmp_path):
        config.risk.hours.days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        journal = Journal(tmp_path / "journal.sqlite")
        broker = PaperBroker()
        engine = Engine(config, broker, journal)
        engine.start()
        yield engine, broker
        journal.close()

    def _post(self, engine, text, message_id=1):
        return engine.handle(text, MessageRef(chat_id=CHAT_ID, message_id=message_id))

    def test_paused_blocks_new_entries(self, setup):
        engine, broker = setup
        engine.paused = True
        decision = self._post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360")
        assert not decision.accepted
        assert "paused" in decision.reason
        assert broker.positions() == []

    def test_resuming_lets_trades_through(self, setup):
        engine, broker = setup
        engine.paused = True
        self._post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=1)
        engine.paused = False
        assert self._post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=2).accepted

    def test_open_trades_are_still_managed_while_paused(self, setup):
        """The point of pause: stop entering, keep protecting what is open."""
        engine, broker = setup
        assert self._post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=1).accepted
        engine.paused = True
        # A close from the admin must still be obeyed, or a paused bot would
        # strand a live position with nobody managing it.
        assert self._post(engine, "close all trades", message_id=2).accepted
        assert broker.positions() == []

    def test_break_even_still_works_while_paused(self, setup):
        engine, broker = setup
        self._post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=1)
        engine.paused = True
        assert self._post(engine, "SL to BE", message_id=2).accepted
        assert broker.positions()[0].stop_loss == pytest.approx(2350.0)

    def test_paused_skips_are_journalled(self, setup):
        engine, _ = setup
        engine.paused = True
        self._post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360")
        assert engine.journal.summary(days=1)["signals_skipped"] >= 1
