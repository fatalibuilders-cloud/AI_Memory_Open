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


# Known MT5 brokers and the symbol-naming convention they use, so the
# right names can be suggested instead of guessed. Suffixes vary by
# ACCOUNT TYPE too — symbols.py always reports the truth for your account.
# Deriv's synthetic indices are simulated instruments that run 24/7,
# including weekends when every real market is shut. Names contain spaces
# and are used verbatim in SYMBOLS.
DERIV_SYNTHETICS = [
    "Volatility 10 Index", "Volatility 25 Index", "Volatility 50 Index",
    "Volatility 75 Index", "Volatility 100 Index",
    "Boom 1000 Index", "Crash 1000 Index",
    "Step Index", "Jump 100 Index",
]

KNOWN_BROKERS = {
    "exness":     {"suffix": "m", "crypto": True,
                   "note": "CMA-licensed in Kenya, KES accounts, M-Pesa. 9 crypto pairs."},
    "hfm":        {"suffix": "", "crypto": True,
                   "note": "CMA-licensed in Kenya, KES accounts. 75+ crypto pairs."},
    "pepperstone": {"suffix": "", "crypto": True,
                    "note": "CMA-licensed, M-Pesa. BTCUSD spread from ~$15, no KES accounts."},
    "icmarkets":  {"suffix": "", "crypto": True, "note": "Tight spreads, offshore regulation."},
    "xm":         {"suffix": "", "crypto": True, "note": "Widely available, offshore regulation."},
    "roboforex":  {"suffix": "", "crypto": True, "note": "Wide instrument range."},
    "fbs":        {"suffix": "", "crypto": True, "note": "Widely available in Africa/Asia."},
    "deriv":      {"suffix": "", "crypto": True,
                   "symbols": ["Volatility 75 Index", "Volatility 100 Index", "Step Index"],
                   "note": ("Popular in Kenya, M-Pesa. Synthetic indices trade 24/7 "
                            "including weekends — but they are simulated instruments, "
                            "not real markets (see README)."),
                   },
}


def _profile_value(profile: str, key: str, fallback_env: str) -> str:
    """Read BROKER_<PROFILE>_<KEY>, else the plain MT5_* variable."""
    if profile:
        value = os.environ.get(f"BROKER_{profile.upper()}_{key}", "").strip()
        if value:
            return value
    return os.environ.get(fallback_env, "").strip()


@dataclass
class Settings:
    # --- Telegram remote control ---------------------------------------
    tg_token: str = ""                # bot token from @BotFather
    tg_password: str = ""             # password you type as /login <password>
    tg_state_file: str = "tg_state.json"  # persisted authorized chat ids

    # --- Broker selection -------------------------------------------------
    broker: str = "mt5"               # "mt5" (Windows; forex+metals+stocks)
                                      # or "oanda" (any OS; forex+metals)

    # Name of the active broker profile (ACTIVE_BROKER in .env). Empty means
    # the plain MT5_LOGIN/PASSWORD/SERVER variables are used.
    active_broker: str = ""

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

    # --- Entry mode ------------------------------------------------------
    # "signal"   : trade only EMA-crossover signals (default, selective)
    # "interval" : attempt a trade every entry_interval_seconds in the
    #              current trend direction. Far more trades, and far more
    #              spread paid — see README "Interval mode" before using.
    entry_mode: str = "signal"
    entry_interval_seconds: int = 30

    # --- Strategy ------------------------------------------------------------
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_period: int = 14
    rsi_floor: float = 45.0           # long only if RSI > floor
    rsi_ceiling: float = 55.0         # short only if RSI < ceiling
    atr_period: int = 14
    atr_sl_mult: float = 1.5          # stop-loss  = ATR * mult
    atr_tp_mult: float = 2.0          # take-profit = ATR * mult

    # Used by the alternative strategies available to the backtester /
    # optimizer (mean_reversion, breakout). The live bot trades ema_cross.
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    bb_period: int = 20
    bb_std: float = 2.0
    donchian_period: int = 20

    # --- Risk ------------------------------------------------------------------
    # Fixed lot size per trade. When > 0 this OVERRIDES risk_pct sizing and
    # every trade uses exactly this many lots (0.01 = broker minimum on most
    # accounts). Safest way to cap exposure while testing.
    fixed_lot: float = 0.0
    risk_pct: float = 0.5             # % of balance risked per trade (when fixed_lot = 0)
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
        # An active profile supplies credentials and (optionally) its own
        # symbol list, since naming differs per broker.
        profile = os.environ.get("ACTIVE_BROKER", "").strip().lower()
        raw_symbols = (_profile_value(profile, "SYMBOLS", "SYMBOLS")
                       or "EURUSD,XAUUSD")
        symbols = [s.strip() for s in raw_symbols.split(",") if s.strip()]
        return cls(
            tg_token=os.environ.get("TG_BOT_TOKEN", "").strip(),
            tg_password=os.environ.get("TG_PASSWORD", "").strip(),
            tg_state_file=os.environ.get("TG_STATE_FILE", "tg_state.json").strip(),
            broker=os.environ.get("BROKER", "mt5").strip().lower(),
            active_broker=profile,
            mt5_login=int(_profile_value(profile, "LOGIN", "MT5_LOGIN") or 0),
            mt5_password=_profile_value(profile, "PASSWORD", "MT5_PASSWORD"),
            mt5_server=_profile_value(profile, "SERVER", "MT5_SERVER"),
            mt5_path=os.environ.get("MT5_PATH", "").strip(),
            oanda_token=os.environ.get("OANDA_API_TOKEN", "").strip(),
            oanda_account=os.environ.get("OANDA_ACCOUNT_ID", "").strip(),
            oanda_env=os.environ.get("OANDA_ENV", "practice").strip().lower(),
            symbols=symbols,
            timeframe=os.environ.get("TIMEFRAME", "M5").strip().upper(),
            history_bars=_i("HISTORY_BARS", 300),
            entry_mode=os.environ.get("ENTRY_MODE", "signal").strip().lower(),
            entry_interval_seconds=_i("ENTRY_INTERVAL_SECONDS", 30),
            ema_fast=_i("EMA_FAST", 20),
            ema_slow=_i("EMA_SLOW", 50),
            rsi_period=_i("RSI_PERIOD", 14),
            rsi_floor=_f("RSI_FLOOR", 45.0),
            rsi_ceiling=_f("RSI_CEILING", 55.0),
            atr_period=_i("ATR_PERIOD", 14),
            rsi_oversold=_f("RSI_OVERSOLD", 30.0),
            rsi_overbought=_f("RSI_OVERBOUGHT", 70.0),
            bb_period=_i("BB_PERIOD", 20),
            bb_std=_f("BB_STD", 2.0),
            donchian_period=_i("DONCHIAN_PERIOD", 20),
            atr_sl_mult=_f("ATR_SL_MULT", 1.5),
            atr_tp_mult=_f("ATR_TP_MULT", 2.0),
            fixed_lot=_f("FIXED_LOT", 0.0),
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
                if self.active_broker:
                    p = f"BROKER_{self.active_broker.upper()}_"
                    problems.append(
                        f"ACTIVE_BROKER={self.active_broker} but {p}LOGIN / {p}PASSWORD / "
                        f"{p}SERVER are not all set (and no MT5_* fallback). "
                        f"Run 'python profile.py list' to see configured profiles.")
                else:
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
        if self.fixed_lot < 0:
            problems.append("FIXED_LOT cannot be negative (use 0 to size by RISK_PCT).")
        if self.fixed_lot == 0 and (self.risk_pct <= 0 or self.risk_pct > 5):
            problems.append("RISK_PCT must be between 0 and 5 (risking >5%/trade is reckless).")
        if self.entry_mode not in ("signal", "interval"):
            problems.append(f"ENTRY_MODE must be 'signal' or 'interval', got '{self.entry_mode}'.")
        if self.entry_mode == "interval" and self.entry_interval_seconds < 5:
            problems.append("ENTRY_INTERVAL_SECONDS must be >= 5.")
        return problems
