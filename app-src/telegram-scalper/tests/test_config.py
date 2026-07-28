"""Configuration loading, the group cap and the live-trading kill switch."""

from __future__ import annotations

import pytest

from tgscalper import config as config_module


def write(tmp_path, body: str):
    path = tmp_path / "config.yaml"
    path.write_text(body)
    return path


def groups_yaml(count: int, enabled: bool = True, start: int = 1) -> str:
    lines = ["telegram:", "  groups:"]
    for index in range(start, start + count):
        lines.append(f"    - id: -100{index}")
        lines.append(f'      title: "Group {index}"')
        lines.append(f"      enabled: {str(enabled).lower()}")
    return "\n".join(lines) + "\n"


class TestGroupLimit:
    def test_default_limit_is_five(self, tmp_path):
        config = config_module.load(write(tmp_path, groups_yaml(5)), env={})
        assert config.telegram.max_groups == 5
        assert len(config.telegram.enabled_groups) == 5

    def test_five_enabled_is_accepted(self, tmp_path):
        config = config_module.load(write(tmp_path, groups_yaml(5)), env={})
        assert len(config.telegram.enabled_groups) == 5

    def test_six_enabled_is_rejected(self, tmp_path):
        with pytest.raises(ValueError) as excinfo:
            config_module.load(write(tmp_path, groups_yaml(6)), env={})
        message = str(excinfo.value)
        assert "6 groups are enabled but the limit is 5" in message
        # The error must name the groups so it is obvious which to bench.
        assert "Group 1" in message

    def test_extra_groups_may_be_listed_while_disabled(self, tmp_path):
        # Ten configured, five live: the whole point of the enabled flag.
        body = groups_yaml(5, enabled=True) + groups_yaml(5, enabled=False, start=6).replace(
            "telegram:\n  groups:\n", ""
        )
        config = config_module.load(write(tmp_path, body), env={})
        assert len(config.telegram.groups) == 10
        assert len(config.telegram.enabled_groups) == 5

    def test_limit_can_be_lowered(self, tmp_path):
        body = "telegram:\n  max_groups: 2\n" + groups_yaml(2).replace("telegram:\n", "")
        config = config_module.load(write(tmp_path, body), env={})
        assert config.telegram.max_groups == 2

    def test_lowered_limit_is_enforced(self, tmp_path):
        body = "telegram:\n  max_groups: 2\n" + groups_yaml(3).replace("telegram:\n", "")
        with pytest.raises(ValueError, match="limit is 2"):
            config_module.load(write(tmp_path, body), env={})

    def test_limit_above_ten_is_rejected(self, tmp_path):
        body = "telegram:\n  max_groups: 50\n"
        with pytest.raises(ValueError, match="between 1 and 10"):
            config_module.load(write(tmp_path, body), env={})

    def test_duplicate_group_is_rejected(self, tmp_path):
        body = (
            "telegram:\n  groups:\n"
            "    - id: -1001\n      title: A\n"
            "    - id: -1001\n      title: B\n"
        )
        with pytest.raises(ValueError, match="listed twice"):
            config_module.load(write(tmp_path, body), env={})

    def test_group_without_id_or_username_is_rejected(self, tmp_path):
        body = 'telegram:\n  groups:\n    - title: "No id"\n'
        with pytest.raises(ValueError, match="needs an id or username"):
            config_module.load(write(tmp_path, body), env={})

    def test_username_only_group_is_allowed(self, tmp_path):
        body = "telegram:\n  groups:\n    - username: publicsignals\n"
        config = config_module.load(write(tmp_path, body), env={})
        assert config.telegram.groups[0].username == "publicsignals"


class TestValidation:
    def test_missing_file_yields_defaults(self):
        config = config_module.load("nope.yaml", env={})
        assert config.execution.mode == "paper"
        assert config.risk.risk_per_trade_pct == 1.0

    def test_unknown_keys_are_ignored(self, tmp_path):
        config = config_module.load(
            write(tmp_path, "execution:\n  mode: paper\n  nonsense: 42\n"), env={}
        )
        assert config.execution.mode == "paper"

    def test_bad_mode_is_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="execution.mode"):
            config_module.load(write(tmp_path, "execution:\n  mode: yolo\n"), env={})

    def test_bad_tp_mode_is_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="tp_mode"):
            config_module.load(write(tmp_path, "execution:\n  tp_mode: middle\n"), env={})

    def test_absurd_risk_percentage_is_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="risk_per_trade_pct"):
            config_module.load(write(tmp_path, "risk:\n  risk_per_trade_pct: 60\n"), env={})

    def test_zero_risk_percentage_is_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="risk_per_trade_pct"):
            config_module.load(write(tmp_path, "risk:\n  risk_per_trade_pct: 0\n"), env={})

    def test_trading_hours_are_parsed(self, tmp_path):
        body = 'risk:\n  hours:\n    start: "08:30"\n    end: "17:45"\n    days: [MON, FRI]\n'
        config = config_module.load(write(tmp_path, body), env={})
        start, end, days = config.risk.hours.parsed()
        assert (start.hour, start.minute) == (8, 30)
        assert (end.hour, end.minute) == (17, 45)
        assert days == {0, 4}

    def test_custom_aliases_merge_with_the_defaults(self, tmp_path):
        body = 'symbols:\n  aliases:\n    XAUUSD: ["GOLDIE"]\n'
        config = config_module.load(write(tmp_path, body), env={})
        assert "GOLDIE" in config.aliases["XAUUSD"]
        assert "GOLD" in config.aliases["XAUUSD"]  # built-ins survive


class TestSecrets:
    def test_credentials_come_from_the_environment(self, tmp_path):
        config = config_module.load(
            write(tmp_path, "telegram:\n  session_name: test\n"),
            env={"TG_API_ID": "12345", "TG_API_HASH": "abc", "MT5_LOGIN": "5001"},
        )
        assert config.telegram.api_id == 12345
        assert config.telegram.api_hash == "abc"
        assert config.broker.login == "5001"

    def test_non_numeric_api_id_is_treated_as_missing(self, tmp_path):
        config = config_module.load(
            write(tmp_path, "telegram: {}\n"), env={"TG_API_ID": "not-a-number"}
        )
        assert config.telegram.api_id is None
