"""Configuration from environment variables / .env file."""

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
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), _clean_value(value))


def _f(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return float(raw) if raw else default


def _i(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


def _b(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    # --- Telegram remote control ---------------------------------------
    tg_token: str = ""                # bot token from @BotFather
    tg_password: str = ""             # password you type as /login <password>
    tg_state_file: str = "tg_state.json"  # persisted authorized chat ids

    # --- Broker selection -------------------------------------------------
    broker: str = "mt5"               # "mt5" (Windows; forex+metals+stocks)
                                      # or "oanda" (any OS; forex+metals)

    # --- MetaTrader 5 ----------------------------------------------------
    mt5_login: int = 0
    mt5_password: str = ""
    mt5_server: str = ""
    mt5_path: str = ""                # optional path to terminal64.exe

    # --- OANDA -------------------------------------------------------------
    oanda_token: str = ""
    oanda_account: str = ""
    oanda_env: str = "practice"       # practice | live

    # --- Trading -----------------------------------------------------------
    symbols: list[str] = field(default_factory=lambda: ["EURUSD", "XAUUSD"])
    timeframe: str = "M5"             # M1 M5 M15 M30 H1 H4 D1
    history_bars: int = 300

    # --- Strategy ------------------------------------------------------------
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_period: int = 14
    rsi_floor: float = 45.0           # long only if RSI > floor
    rsi_ceiling: float = 55.0         # short only if RSI < ceiling
    atr_period: int = 14
    atr_sl_mult: float = 1.5          # stop-loss  = ATR * mult
    atr_tp_mult: float = 2.0          # take-profit = ATR * mult

    # --- Risk ------------------------------------------------------------------
    risk_pct: float = 0.5             # % of balance risked per trade
    max_open_positions: int = 3
    max_positions_per_symbol: int = 1
    max_trades_per_day: int = 10
    daily_loss_limit_pct: float = 3.0 # stop for the day at -3% of day-start balance
    cooldown_seconds: int = 300       # per-symbol pause between entries
    start_paused: bool = True         # trade only after /resume from your phone

    log_level: str = "INFO"

    @classmethod
    def load(cls, dotenv_path: str | Path = ".env") -> "Settings":
        _load_dotenv(dotenv_path)
        # NOTE: broker symbol names are case-sensitive (Exness uses EURUSDm,
        # not EURUSDM) — never normalize the case here.
        symbols = [s.strip() for s in os.environ.get("SYMBOLS", "EURUSD,XAUUSD").split(",") if s.strip()]
        return cls(
            tg_token=os.environ.get("TG_BOT_TOKEN", "").strip(),
            tg_password=os.environ.get("TG_PASSWORD", "").strip(),
            tg_state_file=os.environ.get("TG_STATE_FILE", "tg_state.json").strip(),
            broker=os.environ.get("BROKER", "mt5").strip().lower(),
            mt5_login=_i("MT5_LOGIN", 0),
            mt5_password=os.environ.get("MT5_PASSWORD", ""),
            mt5_server=os.environ.get("MT5_SERVER", "").strip(),
            mt5_path=os.environ.get("MT5_PATH", "").strip(),
            oanda_token=os.environ.get("OANDA_API_TOKEN", "").strip(),
            oanda_account=os.environ.get("OANDA_ACCOUNT_ID", "").strip(),
            oanda_env=os.environ.get("OANDA_ENV", "practice").strip().lower(),
            symbols=symbols,
            timeframe=os.environ.get("TIMEFRAME", "M5").strip().upper(),
            history_bars=_i("HISTORY_BARS", 300),
            ema_fast=_i("EMA_FAST", 20),
            ema_slow=_i("EMA_SLOW", 50),
            rsi_period=_i("RSI_PERIOD", 14),
            rsi_floor=_f("RSI_FLOOR", 45.0),
            rsi_ceiling=_f("RSI_CEILING", 55.0),
            atr_period=_i("ATR_PERIOD", 14),
            atr_sl_mult=_f("ATR_SL_MULT", 1.5),
            atr_tp_mult=_f("ATR_TP_MULT", 2.0),
            risk_pct=_f("RISK_PCT", 0.5),
            max_open_positions=_i("MAX_OPEN_POSITIONS", 3),
            max_positions_per_symbol=_i("MAX_POSITIONS_PER_SYMBOL", 1),
            max_trades_per_day=_i("MAX_TRADES_PER_DAY", 10),
            daily_loss_limit_pct=_f("DAILY_LOSS_LIMIT_PCT", 3.0),
            cooldown_seconds=_i("COOLDOWN_SECONDS", 300),
            start_paused=_b("START_PAUSED", True),
            log_level=os.environ.get("LOG_LEVEL", "INFO").strip().upper(),
        )

    def validate(self) -> list[str]:
        problems = []
        if not self.tg_token:
            problems.append("TG_BOT_TOKEN missing — create a bot with @BotFather and paste its token.")
        if not self.tg_password or len(self.tg_password) < 6:
            problems.append("TG_PASSWORD missing/too short (min 6 chars) — this is your phone login password.")
        if self.broker == "mt5":
            if not self.mt5_login or not self.mt5_password or not self.mt5_server:
                problems.append("MT5_LOGIN / MT5_PASSWORD / MT5_SERVER missing — use your MT5 account credentials.")
        elif self.broker == "oanda":
            if not self.oanda_token or not self.oanda_account:
                problems.append("OANDA_API_TOKEN / OANDA_ACCOUNT_ID missing — generate them in the OANDA portal.")
            if self.oanda_env not in ("practice", "live"):
                problems.append("OANDA_ENV must be 'practice' or 'live'.")
        else:
            problems.append(f"BROKER must be 'mt5' or 'oanda', got '{self.broker}'.")
        if not self.symbols:
            problems.append("SYMBOLS is empty.")
        if self.risk_pct <= 0 or self.risk_pct > 5:
            problems.append("RISK_PCT must be between 0 and 5 (risking >5%/trade is reckless).")
        return problems
