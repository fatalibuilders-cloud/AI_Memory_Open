"""Typed configuration loaded from config.yaml plus secrets from the environment.

Nothing secret belongs in config.yaml — credentials come from .env only, so the
config file stays safe to read out loud when you want help debugging it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Any, Optional

import yaml

from .symbols import DEFAULT_ALIASES

LIVE_ACK = "I_UNDERSTAND_THE_RISK"
_DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


@dataclass
class GroupConfig:
    """One Telegram chat to watch."""

    id: Optional[int] = None
    username: Optional[str] = None  # e.g. "goldsignalsvip" (public groups)
    title: str = ""
    enabled: bool = True
    # Numeric user ids allowed to trigger trades. Empty means "whoever the
    # admin_only setting permits".
    senders: list[int] = field(default_factory=list)
    # Scale this group's position size, e.g. 0.5 while you still distrust it.
    risk_multiplier: float = 1.0

    @property
    def key(self) -> str:
        return str(self.id) if self.id is not None else (self.username or self.title)


DEFAULT_MAX_GROUPS = 5


@dataclass
class TelegramConfig:
    session_name: str = "tgscalper"
    session_dir: str = "data"
    # You can list as many candidate groups as you like; at most `max_groups`
    # of them may be enabled at once. Switching which five are live is then a
    # one-word edit (`enabled: false`) instead of deleting configuration.
    groups: list[GroupConfig] = field(default_factory=list)
    max_groups: int = DEFAULT_MAX_GROUPS
    # Only act on messages from chat admins/owners. Signal groups have chatty
    # members; this is the single most effective noise filter.
    admin_only: bool = True
    # Where trade receipts go. "me" = your own Saved Messages.
    notify_to: str = "me"
    notify_skips: bool = False  # also report messages that were ignored
    # Re-read pinned admin lists this often (seconds).
    admin_refresh_seconds: int = 3600

    api_id: Optional[int] = None
    api_hash: str = ""
    phone: str = ""
    twofa_password: str = ""

    @property
    def enabled_groups(self) -> list[GroupConfig]:
        return [group for group in self.groups if group.enabled]


@dataclass
class ExecutionConfig:
    mode: str = "paper"  # "paper" | "live"
    # "market" ignores the posted entry price and fills now (correct for
    # scalping, where you are already seconds behind the admin).
    # "as_stated" places a pending order at the posted price.
    entry: str = "market"
    # How to spread size across multiple take profits.
    #   first  -> one position, TP1 (tightest, highest hit rate)
    #   last   -> one position, furthest TP
    #   split  -> one position per TP, size divided between them
    tp_mode: str = "first"
    max_tps: int = 3
    require_stop_loss: bool = True
    # Refuse a market entry once price has run past the posted entry — the move
    # is gone and you would be buying the top. Either limit can be disabled
    # with 0; when both are set, whichever trips first wins.
    #
    # Measured as a share of the signal's own stop distance. Instrument-agnostic,
    # so one value works for gold, EURUSD and Volatility 75 alike. Prefer this.
    max_entry_slippage_pct_of_stop: float = 50.0
    # Measured in raw points. Precise but instrument-specific: 150 points is
    # $1.50, sensible on gold and meaningless on an index priced at 250,000.
    max_entry_slippage_points: float = 0.0
    paper_balance: float = 10_000.0
    # Set by load(): live needs the config flag AND the env acknowledgement.
    live_enabled: bool = False
    live_block_reason: str = ""


@dataclass
class TradingHours:
    start: str = "00:00"
    end: str = "23:59"
    days: list[str] = field(default_factory=lambda: ["MON", "TUE", "WED", "THU", "FRI"])

    def parsed(self) -> tuple[time, time, set[int]]:
        start_h, _, start_m = self.start.partition(":")
        end_h, _, end_m = self.end.partition(":")
        days = {_DAYS.index(day.upper()[:3]) for day in self.days if day.upper()[:3] in _DAYS}
        return (
            time(int(start_h), int(start_m or 0)),
            time(int(end_h), int(end_m or 0)),
            days,
        )


@dataclass
class RiskConfig:
    # Percent of balance risked per signal, sized off the stop distance.
    risk_per_trade_pct: float = 1.0
    # Set to a number to bypass percentage sizing entirely.
    fixed_lot: Optional[float] = None
    max_lot: float = 1.0
    max_open_trades: int = 5
    max_open_per_symbol: int = 1
    # Stop trading for the rest of the day after this much drawdown.
    max_daily_loss_pct: float = 5.0
    max_signals_per_hour: int = 10
    # Reject signals whose stop is nonsensically tight (likely a misread).
    min_stop_points: float = 0.0
    # Reject entries when the spread is abnormally wide (news, rollover).
    max_spread_points: float = 0.0  # 0 disables
    dedupe_window_minutes: int = 30
    allow_symbols: list[str] = field(default_factory=list)  # empty = allow all
    block_symbols: list[str] = field(default_factory=list)
    hours: TradingHours = field(default_factory=TradingHours)
    breakeven_offset_points: float = 0.0
    partial_close_default: float = 0.5
    # If a signal has no stop at all and require_stop_loss is off, use this many
    # points as an emergency stop rather than trading naked.
    fallback_stop_points: float = 0.0


@dataclass
class BrokerConfig:
    provider: str = "mt5"
    suffix: str = ""  # e.g. ".m" or "m" if your broker names it XAUUSD.m
    symbol_overrides: dict[str, str] = field(default_factory=dict)
    deviation_points: int = 20
    magic: int = 770_077
    login: str = ""
    password: str = ""
    server: str = ""
    terminal_path: str = ""


@dataclass
class Config:
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    aliases: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_ALIASES))
    journal_path: str = "data/journal.sqlite"
    log_level: str = "INFO"
    log_file: str = "logs/tgscalper.log"

    @property
    def session_path(self) -> Path:
        directory = Path(self.telegram.session_dir)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / self.telegram.session_name


def _pick(data: dict[str, Any], *keys: str) -> dict[str, Any]:
    """Filter a YAML dict down to recognised keys, ignoring the rest."""
    return {key: data[key] for key in keys if key in data and data[key] is not None}


def load(path: str | os.PathLike[str] = "config.yaml", env: Optional[dict[str, str]] = None) -> Config:
    """Read config.yaml, overlay secrets from the environment, validate."""
    env = dict(os.environ if env is None else env)
    raw: dict[str, Any] = {}
    config_path = Path(path)
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text()) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"{config_path} must contain a YAML mapping")
        raw = loaded

    tg_raw = raw.get("telegram") or {}
    groups = [
        GroupConfig(
            **_pick(
                item,
                "id",
                "username",
                "title",
                "enabled",
                "senders",
                "risk_multiplier",
            )
        )
        for item in (tg_raw.get("groups") or [])
    ]
    telegram = TelegramConfig(
        **_pick(
            tg_raw,
            "session_name",
            "session_dir",
            "admin_only",
            "notify_to",
            "notify_skips",
            "admin_refresh_seconds",
            "max_groups",
        )
    )
    telegram.groups = groups

    execution = ExecutionConfig(
        **_pick(
            raw.get("execution") or {},
            "mode",
            "entry",
            "tp_mode",
            "max_tps",
            "require_stop_loss",
            "max_entry_slippage_points",
            "max_entry_slippage_pct_of_stop",
            "paper_balance",
        )
    )

    risk_raw = dict(raw.get("risk") or {})
    hours_raw = risk_raw.pop("hours", None) or risk_raw.pop("trading_hours", None) or {}
    risk = RiskConfig(
        **_pick(
            risk_raw,
            "risk_per_trade_pct",
            "fixed_lot",
            "max_lot",
            "max_open_trades",
            "max_open_per_symbol",
            "max_daily_loss_pct",
            "max_signals_per_hour",
            "min_stop_points",
            "max_spread_points",
            "dedupe_window_minutes",
            "allow_symbols",
            "block_symbols",
            "breakeven_offset_points",
            "partial_close_default",
            "fallback_stop_points",
        )
    )
    if hours_raw:
        risk.hours = TradingHours(**_pick(hours_raw, "start", "end", "days"))

    broker = BrokerConfig(
        **_pick(
            raw.get("broker") or {},
            "provider",
            "suffix",
            "symbol_overrides",
            "deviation_points",
            "magic",
        )
    )

    aliases = dict(DEFAULT_ALIASES)
    for canonical, spellings in ((raw.get("symbols") or {}).get("aliases") or {}).items():
        merged = list(aliases.get(canonical.upper(), []))
        merged.extend(spellings if isinstance(spellings, list) else [spellings])
        aliases[canonical.upper()] = merged

    config = Config(
        telegram=telegram,
        execution=execution,
        risk=risk,
        broker=broker,
        aliases=aliases,
        journal_path=(raw.get("journal") or {}).get("path", "data/journal.sqlite"),
        log_level=(raw.get("logging") or {}).get("level", "INFO"),
        log_file=(raw.get("logging") or {}).get("file", "logs/tgscalper.log"),
    )

    # --- secrets from the environment only ---
    api_id = env.get("TG_API_ID", "").strip()
    config.telegram.api_id = int(api_id) if api_id.isdigit() else None
    config.telegram.api_hash = env.get("TG_API_HASH", "").strip()
    config.telegram.phone = env.get("TG_PHONE", "").strip()
    config.telegram.twofa_password = env.get("TG_2FA_PASSWORD", "")
    config.broker.login = env.get("MT5_LOGIN", "").strip()
    config.broker.password = env.get("MT5_PASSWORD", "")
    config.broker.server = env.get("MT5_SERVER", "").strip()
    config.broker.terminal_path = env.get("MT5_TERMINAL_PATH", "").strip()

    # --- the live-trading kill switch ---
    # Two independent switches must agree. A stale config.yaml alone can never
    # start sending real orders.
    wants_live = config.execution.mode.lower() == "live"
    acknowledged = env.get("TGSCALPER_ALLOW_LIVE", "").strip() == LIVE_ACK
    config.execution.live_enabled = wants_live and acknowledged
    if wants_live and not acknowledged:
        config.execution.live_block_reason = (
            "execution.mode is 'live' but TGSCALPER_ALLOW_LIVE is not set to "
            f"{LIVE_ACK} — running on the paper broker instead"
        )
    elif not wants_live:
        config.execution.live_block_reason = "execution.mode is 'paper'"

    _validate(config)
    return config


def _validate(config: Config) -> None:
    errors: list[str] = []
    if config.execution.mode.lower() not in {"paper", "live"}:
        errors.append(f"execution.mode must be 'paper' or 'live', got {config.execution.mode!r}")
    if config.execution.entry.lower() not in {"market", "as_stated"}:
        errors.append("execution.entry must be 'market' or 'as_stated'")
    if config.execution.tp_mode.lower() not in {"first", "last", "split"}:
        errors.append("execution.tp_mode must be 'first', 'last' or 'split'")
    if not 0 <= config.execution.max_entry_slippage_pct_of_stop <= 500:
        errors.append("execution.max_entry_slippage_pct_of_stop must be between 0 and 500")
    if not 0 < config.risk.risk_per_trade_pct <= 20:
        errors.append("risk.risk_per_trade_pct must be between 0 and 20")
    if config.risk.fixed_lot is not None and config.risk.fixed_lot <= 0:
        errors.append("risk.fixed_lot must be positive when set")
    if config.risk.max_open_trades < 1:
        errors.append("risk.max_open_trades must be at least 1")
    if not 0 < config.risk.partial_close_default <= 1:
        errors.append("risk.partial_close_default must be between 0 and 1")
    limit = config.telegram.max_groups
    if not 1 <= limit <= 10:
        errors.append(f"telegram.max_groups must be between 1 and 10, got {limit}")
    else:
        enabled = config.telegram.enabled_groups
        if len(enabled) > limit:
            listed = ", ".join(group.title or group.key for group in enabled)
            errors.append(
                f"{len(enabled)} groups are enabled but the limit is {limit}. "
                f"Set `enabled: false` on the ones you are not trading right now "
                f"(they stay in config.yaml, ready to switch back on). "
                f"Currently enabled: {listed}"
            )
    keys: set[str] = set()
    for group in config.telegram.groups:
        if group.key in keys:
            errors.append(f"group {group.key} is listed twice")
        keys.add(group.key)
        if group.id is None and not group.username:
            errors.append(f"group {group.title or '<unnamed>'} needs an id or username")
    if errors:
        raise ValueError("invalid configuration:\n  - " + "\n  - ".join(errors))
