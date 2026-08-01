"""Configuration loaded from environment variables / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _clean_value(raw: str) -> str:
    value = raw.strip()
    if value[:1] in ('"', "'"):
        return value.strip('"').strip("'")
    # unquoted: drop inline comments ("0.5   # percent" -> "0.5");
    # a '#' with no whitespace before it is kept (e.g. inside passwords)
    for i in range(1, len(value)):
        if value[i] == "#" and value[i - 1] in " \t":
            return value[:i].strip()
    return value


def _load_dotenv(path: str | Path = ".env") -> None:
    """Minimal .env loader (no external dependency)."""
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), _clean_value(value))


def _get_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _get_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return float(raw) if raw else default


def _get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


@dataclass
class Settings:
    # --- connection ---------------------------------------------------
    # Full auth frame copied from browser devtools, e.g.
    #   42["auth",{"session":"...","isDemo":1,"uid":12345678,"platform":2}]
    ssid: str = ""
    demo: bool = True

    # --- trading ------------------------------------------------------
    asset: str = "EURUSD_otc"
    expiry_seconds: int = 60          # option duration
    candle_seconds: int = 60          # candle timeframe fed to the strategy

    # --- money management ---------------------------------------------
    stake: float = 1.0                # fixed stake per trade (account currency)
    stake_pct: float = 0.0            # if > 0, stake = balance * pct (overrides fixed)
    max_stake: float = 50.0           # hard cap on any single stake
    max_trades_per_day: int = 20
    max_consecutive_losses: int = 3   # stop after N losses in a row
    daily_loss_limit: float = 20.0    # stop once net PnL for the day <= -limit
    daily_profit_target: float = 0.0  # stop once net PnL >= target (0 = disabled)
    cooldown_seconds: int = 120       # min seconds between trades

    # --- strategy -----------------------------------------------------
    strategy: str = "rsi_ema"
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    ema_period: int = 50
    min_candles: int = 60             # warm-up candles before trading starts

    # --- misc -----------------------------------------------------------
    log_level: str = "INFO"
    dry_run: bool = False             # analyse + log signals but never send orders

    @classmethod
    def load(cls, dotenv_path: str | Path = ".env") -> "Settings":
        _load_dotenv(dotenv_path)
        return cls(
            ssid=os.environ.get("PO_SSID", "").strip(),
            demo=_get_bool("PO_DEMO", True),
            asset=os.environ.get("PO_ASSET", "EURUSD_otc").strip(),
            expiry_seconds=_get_int("PO_EXPIRY_SECONDS", 60),
            candle_seconds=_get_int("PO_CANDLE_SECONDS", 60),
            stake=_get_float("PO_STAKE", 1.0),
            stake_pct=_get_float("PO_STAKE_PCT", 0.0),
            max_stake=_get_float("PO_MAX_STAKE", 50.0),
            max_trades_per_day=_get_int("PO_MAX_TRADES_PER_DAY", 20),
            max_consecutive_losses=_get_int("PO_MAX_CONSECUTIVE_LOSSES", 3),
            daily_loss_limit=_get_float("PO_DAILY_LOSS_LIMIT", 20.0),
            daily_profit_target=_get_float("PO_DAILY_PROFIT_TARGET", 0.0),
            cooldown_seconds=_get_int("PO_COOLDOWN_SECONDS", 120),
            strategy=os.environ.get("PO_STRATEGY", "rsi_ema").strip(),
            rsi_period=_get_int("PO_RSI_PERIOD", 14),
            rsi_oversold=_get_float("PO_RSI_OVERSOLD", 30.0),
            rsi_overbought=_get_float("PO_RSI_OVERBOUGHT", 70.0),
            ema_period=_get_int("PO_EMA_PERIOD", 50),
            min_candles=_get_int("PO_MIN_CANDLES", 60),
            log_level=os.environ.get("PO_LOG_LEVEL", "INFO").strip().upper(),
            dry_run=_get_bool("PO_DRY_RUN", False),
        )

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.ssid:
            problems.append("PO_SSID is empty — copy the auth frame from browser devtools (see README).")
        elif not self.ssid.startswith('42["auth"'):
            problems.append('PO_SSID should be the full auth frame starting with 42["auth",...].')
        if self.expiry_seconds < 5:
            problems.append("PO_EXPIRY_SECONDS must be >= 5.")
        if self.stake <= 0 and self.stake_pct <= 0:
            problems.append("Set PO_STAKE > 0 or PO_STAKE_PCT > 0.")
        if not self.demo and '"isDemo":1' in self.ssid.replace(" ", ""):
            problems.append("PO_DEMO=0 but the SSID was captured from a DEMO session (isDemo:1).")
        return problems
