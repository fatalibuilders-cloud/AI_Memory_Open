"""Which groups are being watched, when chosen from Telegram rather than YAML.

`/selectgroup` needs somewhere to record its choices. Rewriting config.yaml
would work but would strip every comment out of it, so selections live in a
small JSON file instead and take precedence over the YAML list at startup.

config.yaml therefore stays the hand-edited default, and the bot's choices are
a separate, disposable layer on top — delete the file and you are back to the
YAML.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import Config, GroupConfig

log = logging.getLogger(__name__)


@dataclass
class GroupSelection:
    """The chat ids chosen from Telegram, with titles for display."""

    enabled: list[int] = field(default_factory=list)
    titles: dict[str, str] = field(default_factory=dict)
    multipliers: dict[str, float] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> Optional["GroupSelection"]:
        file = Path(path)
        if not file.is_file():
            return None
        try:
            raw = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("ignoring unreadable group selection %s: %s", file, exc)
            return None
        return cls(
            enabled=[int(item) for item in raw.get("enabled", [])],
            titles={str(k): str(v) for k, v in (raw.get("titles") or {}).items()},
            multipliers={str(k): float(v) for k, v in (raw.get("multipliers") or {}).items()},
        )

    def save(self, path: str | Path) -> None:
        file = Path(path)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(
            json.dumps(
                {
                    "enabled": self.enabled,
                    "titles": self.titles,
                    "multipliers": self.multipliers,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def toggle(self, chat_id: int, title: str = "", limit: int = 0) -> tuple[bool, str]:
        """Add or remove a chat. Returns (now_enabled, message).

        `limit` of 0 means no cap.
        """
        if chat_id in self.enabled:
            self.enabled.remove(chat_id)
            return False, f"Stopped watching {title or chat_id}"
        if limit > 0 and len(self.enabled) >= limit:
            return False, (
                f"Already watching {limit} groups, which is the maximum. "
                "Turn one off first."
            )
        self.enabled.append(chat_id)
        if title:
            self.titles[str(chat_id)] = title
        return True, f"Now watching {title or chat_id}"

    def to_groups(self) -> list[GroupConfig]:
        return [
            GroupConfig(
                id=chat_id,
                title=self.titles.get(str(chat_id), ""),
                enabled=True,
                risk_multiplier=self.multipliers.get(str(chat_id), 1.0),
            )
            for chat_id in self.enabled
        ]


def selection_path(config: Config) -> Path:
    return Path(config.telegram.session_dir) / "groups.json"


def apply_selection(config: Config) -> Optional[GroupSelection]:
    """Overlay the saved selection onto the config, if one exists.

    Returns the selection so callers can report where the group list came from;
    None means config.yaml is still in charge.
    """
    selection = GroupSelection.load(selection_path(config))
    if selection is None or not selection.enabled:
        return None
    config.telegram.groups = selection.to_groups()
    log.info(
        "group selection from %s is in effect (%d group(s)); config.yaml groups ignored",
        selection_path(config),
        len(selection.enabled),
    )
    return selection
