"""Configuration loaded from environment variables.

Every knob the bot has is here. Nothing is read from the environment outside
this module, so a Config instance is the complete description of a bot run.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

# Deriv's market identifier for cryptocurrency. The bot refuses to trade any
# symbol whose `market` field is not exactly this value.
CRYPTO_MARKET = "cryptocurrency"

DEFAULT_ENDPOINT = "wss://ws.derivws.com/websockets/v3"


class ConfigError(Exception):
    """Raised when the environment does not describe a runnable bot."""


def _str(name: str, default: str | None = None, *, required: bool = False) -> str:
    raw = os.environ.get(name, "")
    value = raw.strip()
    if not value:
        if required:
            raise ConfigError(f"{name} is required but not set")
        return default or ""
    return value


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


def _list(name: str) -> tuple[str, ...]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return ()
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Config:
    """Immutable bot configuration."""

    # --- Connection -----------------------------------------------------
    app_id: str
    api_token: str
    endpoint: str = DEFAULT_ENDPOINT

    # --- Safety ---------------------------------------------------------
    # The bot runs against a virtual (demo) account unless this is explicitly
    # enabled AND the authorized account is a real-money account.
    allow_real_money: bool = False
    dry_run: bool = False
    kill_switch_file: str = "KILL_SWITCH"

    # --- Universe -------------------------------------------------------
    # Empty means "every open cryptocurrency symbol Deriv offers". Any symbol
    # listed here is still verified to be a cryptocurrency before it is traded.
    symbols: tuple[str, ...] = ()
    max_symbols: int = 6

    # --- Strategy -------------------------------------------------------
    # Name from strategies.REGISTRY. Run `python -m deriv_bot.backtest
    # --list-strategies` to see them.
    strategy: str = "ema_cross"
    candle_granularity: int = 60  # seconds per candle
    candle_count: int = 200
    ema_fast: int = 9
    ema_slow: int = 21
    rsi_period: int = 14
    rsi_upper: float = 70.0
    rsi_lower: float = 30.0
    atr_period: int = 14
    # Minimum EMA separation as a multiple of ATR. Filters out flat, choppy
    # markets where a crossover carries no information.
    min_separation_atr: float = 0.15

    # --- Trade sizing ---------------------------------------------------
    stake: float = 1.0
    currency: str = ""  # empty => use the account currency
    trade_duration: int = 5
    trade_duration_unit: str = "m"

    # --- Risk limits ----------------------------------------------------
    max_open_trades: int = 2
    max_trades_per_day: int = 40
    daily_loss_limit: float = 20.0
    daily_profit_target: float = 0.0  # 0 disables the target
    max_stake_fraction: float = 0.02  # cap stake at 2% of balance
    symbol_cooldown: int = 300  # seconds between trades on the same symbol

    # --- Loop timing ----------------------------------------------------
    poll_interval: int = 30
    reconnect_max_delay: int = 120
    request_timeout: int = 30

    # --- Bookkeeping ----------------------------------------------------
    state_file: str = "state/bot-state.json"
    journal_file: str = "state/trades.jsonl"
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if self.ema_fast >= self.ema_slow:
            raise ConfigError(
                f"EMA_FAST ({self.ema_fast}) must be smaller than EMA_SLOW ({self.ema_slow})"
            )
        if self.stake <= 0:
            raise ConfigError("STAKE must be greater than zero")
        if self.daily_loss_limit <= 0:
            raise ConfigError("DAILY_LOSS_LIMIT must be greater than zero")
        if self.max_open_trades < 1:
            raise ConfigError("MAX_OPEN_TRADES must be at least 1")
        if self.candle_count <= self.ema_slow + self.rsi_period:
            raise ConfigError(
                "CANDLE_COUNT must exceed EMA_SLOW + RSI_PERIOD to warm up the indicators"
            )
        if self.trade_duration_unit not in {"t", "s", "m", "h", "d"}:
            raise ConfigError(
                f"TRADE_DURATION_UNIT must be one of t/s/m/h/d, got {self.trade_duration_unit!r}"
            )
        if not 0 < self.max_stake_fraction <= 1:
            raise ConfigError("MAX_STAKE_FRACTION must be in (0, 1]")
        # Imported lazily: strategies.py imports this module, so a top-level
        # import here would be circular.
        from .strategies import REGISTRY

        if self.strategy not in REGISTRY:
            raise ConfigError(
                f"STRATEGY must be one of: {', '.join(sorted(REGISTRY))} "
                f"(got {self.strategy!r})"
            )

    @classmethod
    def from_env(cls) -> "Config":
        """Build a Config from environment variables."""
        return cls(
            app_id=_str("DERIV_APP_ID", required=True),
            api_token=_str("DERIV_API_TOKEN", required=True),
            endpoint=_str("DERIV_ENDPOINT", DEFAULT_ENDPOINT),
            allow_real_money=_bool("DERIV_ALLOW_REAL_MONEY", False),
            dry_run=_bool("DERIV_DRY_RUN", False),
            kill_switch_file=_str("KILL_SWITCH_FILE", "KILL_SWITCH"),
            symbols=_list("DERIV_SYMBOLS"),
            max_symbols=_int("MAX_SYMBOLS", 6),
            strategy=_str("STRATEGY", "ema_cross"),
            candle_granularity=_int("CANDLE_GRANULARITY", 60),
            candle_count=_int("CANDLE_COUNT", 200),
            ema_fast=_int("EMA_FAST", 9),
            ema_slow=_int("EMA_SLOW", 21),
            rsi_period=_int("RSI_PERIOD", 14),
            rsi_upper=_float("RSI_UPPER", 70.0),
            rsi_lower=_float("RSI_LOWER", 30.0),
            atr_period=_int("ATR_PERIOD", 14),
            min_separation_atr=_float("MIN_SEPARATION_ATR", 0.15),
            stake=_float("STAKE", 1.0),
            currency=_str("CURRENCY", ""),
            trade_duration=_int("TRADE_DURATION", 5),
            trade_duration_unit=_str("TRADE_DURATION_UNIT", "m"),
            max_open_trades=_int("MAX_OPEN_TRADES", 2),
            max_trades_per_day=_int("MAX_TRADES_PER_DAY", 40),
            daily_loss_limit=_float("DAILY_LOSS_LIMIT", 20.0),
            daily_profit_target=_float("DAILY_PROFIT_TARGET", 0.0),
            max_stake_fraction=_float("MAX_STAKE_FRACTION", 0.02),
            symbol_cooldown=_int("SYMBOL_COOLDOWN", 300),
            poll_interval=_int("POLL_INTERVAL", 30),
            reconnect_max_delay=_int("RECONNECT_MAX_DELAY", 120),
            request_timeout=_int("REQUEST_TIMEOUT", 30),
            state_file=_str("STATE_FILE", "state/bot-state.json"),
            journal_file=_str("JOURNAL_FILE", "state/trades.jsonl"),
            log_level=_str("LOG_LEVEL", "INFO"),
        )

    def redacted(self) -> dict:
        """Config as a dict safe to log — the API token is never included."""
        data = {
            key: getattr(self, key)
            for key in self.__dataclass_fields__  # type: ignore[attr-defined]
            if key != "api_token"
        }
        data["api_token"] = "***redacted***"
        return data
