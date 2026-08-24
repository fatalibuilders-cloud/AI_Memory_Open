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


def _stages(name: str) -> list[tuple[float, float]]:
    """Parse 'trigger:lock,trigger:lock' into sorted (trigger, lock) pairs."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    out = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        trigger, _, lock = part.partition(":")
        try:
            out.append((float(trigger), float(lock or 0)))
        except ValueError:
            continue
    return sorted(out)


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
                   # Deriv MT5 offers real crypto (BTCUSD, ETHUSD) alongside
                   # its synthetic indices — both trade 24/7.
                   "symbols": ["BTCUSD", "ETHUSD", "Volatility 75 Index"],
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


#: Backends that speak MetaTrader 5 and therefore share MT5 credentials.
MT5_BACKENDS = ("mt5", "exness", "deriv", "vantage")


@dataclass
class BrokerConfig:
    """One account the bot trades. Several can run at once."""
    name: str                 # profile name, e.g. "exness"
    kind: str                 # backend: mt5 | exness | deriv | vantage | oanda | binance
    symbols: list[str] = field(default_factory=list)
    login: int = 0
    password: str = ""
    server: str = ""
    path: str = ""
    oanda_token: str = ""
    oanda_account: str = ""
    oanda_env: str = "practice"
    binance_key: str = ""
    binance_secret: str = ""
    binance_testnet: bool = True

    def problems(self) -> list[str]:
        p = f"BROKER_{self.name.upper()}_"
        if self.kind in MT5_BACKENDS:
            if not (self.login and self.password and self.server):
                return [f"{self.name}: {p}LOGIN / {p}PASSWORD / {p}SERVER incomplete"]
        elif self.kind == "oanda":
            if not (self.oanda_token and self.oanda_account):
                return [f"{self.name}: OANDA_API_TOKEN / OANDA_ACCOUNT_ID missing"]
        elif self.kind == "binance":
            if not (self.binance_key and self.binance_secret):
                return [f"{self.name}: BINANCE_API_KEY / BINANCE_API_SECRET missing"]
        else:
            return [f"{self.name}: unknown backend '{self.kind}'"]
        if not self.symbols:
            return [f"{self.name}: no symbols ({p}SYMBOLS or SYMBOLS)"]
        return []


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

    # --- Binance USDⓈ-M Futures ----------------------------------------------
    binance_key: str = ""
    binance_secret: str = ""
    binance_testnet: bool = True      # testnet.binancefuture.com = free demo

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

    # --- Safety controls --------------------------------------------------
    # Pause after this many losses in a row. The point is to stop while a
    # market regime is clearly against the strategy rather than keep paying
    # to find out. 0 disables.
    max_consecutive_losses: int = 3
    # How long the pause lasts before trading may resume.
    loss_pause_minutes: int = 60
    # Count trades over a rolling window rather than a calendar day, so a
    # burst just before midnight cannot be followed by another at 00:01.
    rolling_trade_window_hours: int = 24
    # Move the stop to break-even once a position is this far in profit
    # (account currency). 0 disables.
    breakeven_at_money: float = 0.0
    # How much profit the moved stop should LOCK IN. 0 means pure break-even
    # (the trade can no longer lose). A positive value guarantees that much
    # instead, and must stay below breakeven_at_money — a stop placed at the
    # current price is rejected by the broker as too close.
    breakeven_lock_money: float = 0.0
    #: Staged profit protection, tightening the stop as a trade advances.
    #: Each stage is (profit trigger, profit locked in), lowest first, e.g.
    #: PROFIT_STAGES=0.10:0,0.25:0.10 means "at +$0.10 move to break-even,
    #: at +$0.25 move up to guarantee +$0.10". Overrides the single
    #: BREAKEVEN_AT_MONEY / BREAKEVEN_LOCK_MONEY pair when set.
    profit_stages: list[tuple[float, float]] = field(default_factory=list)

    def stages(self) -> list[tuple[float, float]]:
        """Protection ladder, lowest trigger first."""
        if self.profit_stages:
            return sorted(self.profit_stages)
        if self.breakeven_at_money > 0:
            return [(self.breakeven_at_money, self.breakeven_lock_money)]
        return []
    # Refuse a fill that slipped further than this from the expected price,
    # as a fraction of the stop distance.
    max_slippage_ratio: float = 0.5
    # Treat the spread as abnormal when it exceeds this multiple of its
    # recent typical value, which usually means news or thin liquidity.
    spread_spike_factor: float = 3.0
    # Require the target to beat the round-trip cost by this multiple.
    min_reward_cost_ratio: float = 2.0

    # --- Money-based exits (override the ATR multiples when > 0) ----------
    # Close at a fixed cash profit rather than a multiple of ATR. When
    # tp_runner_money is also set, reaching tp_money moves the stop to
    # break-even and extends the target to tp_runner_money, so a trade that
    # keeps going can pay more while no longer being able to lose.
    tp_money: float = 0.0            # e.g. 0.50 = close at +$0.50
    tp_runner_money: float = 0.0     # e.g. 2.00 = let a confirmed winner run
    sl_money: float = 0.0            # e.g. 0.30 = cap the loss at $0.30

    # Refuse a trade when the spread eats more than this share of the stop
    # distance. Paying 50% of your risk in spread makes a trade close to
    # unwinnable regardless of how good the signal is — silver on M1 is the
    # usual offender. 0 disables the check.
    max_spread_ratio: float = 0.25

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

    def broker_configs(self) -> list["BrokerConfig"]:
        """Every account to trade.

        ACTIVE_BROKERS=exness,deriv runs both at once. ACTIVE_BROKER (singular)
        and the plain MT5_*/OANDA_*/BINANCE_* variables still work and yield a
        single account, so existing setups are unaffected.
        """
        names = [n.strip().lower()
                 for n in os.environ.get("ACTIVE_BROKERS", "").split(",") if n.strip()]
        if not names:
            names = [self.active_broker] if self.active_broker else []

        if not names:
            # no profiles: one account from the plain variables
            return [BrokerConfig(
                name=self.broker, kind=self.broker, symbols=list(self.symbols),
                login=self.mt5_login, password=self.mt5_password,
                server=self.mt5_server, path=self.mt5_path,
                oanda_token=self.oanda_token, oanda_account=self.oanda_account,
                oanda_env=self.oanda_env, binance_key=self.binance_key,
                binance_secret=self.binance_secret,
                binance_testnet=self.binance_testnet)]

        out = []
        for name in names:
            # a profile named after a known backend uses that backend, so
            # BROKER_DERIV_* automatically gets Deriv's FOK filling
            kind = os.environ.get(f"BROKER_{name.upper()}_KIND", "").strip().lower()
            if not kind:
                kind = name if name in (*MT5_BACKENDS, "oanda", "binance") else self.broker
            raw_symbols = _profile_value(name, "SYMBOLS", "SYMBOLS")
            out.append(BrokerConfig(
                name=name, kind=kind,
                symbols=[s.strip() for s in raw_symbols.split(",") if s.strip()],
                login=int(_profile_value(name, "LOGIN", "MT5_LOGIN") or 0),
                password=_profile_value(name, "PASSWORD", "MT5_PASSWORD"),
                server=_profile_value(name, "SERVER", "MT5_SERVER"),
                path=self.mt5_path,
                oanda_token=_profile_value(name, "OANDA_TOKEN", "OANDA_API_TOKEN"),
                oanda_account=_profile_value(name, "OANDA_ACCOUNT", "OANDA_ACCOUNT_ID"),
                oanda_env=self.oanda_env,
                binance_key=_profile_value(name, "BINANCE_KEY", "BINANCE_API_KEY"),
                binance_secret=_profile_value(name, "BINANCE_SECRET", "BINANCE_API_SECRET"),
                binance_testnet=self.binance_testnet,
            ))
        return out

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
            binance_key=os.environ.get("BINANCE_API_KEY", "").strip(),
            binance_secret=os.environ.get("BINANCE_API_SECRET", "").strip(),
            binance_testnet=_b("BINANCE_TESTNET", True),
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
            max_consecutive_losses=_i("MAX_CONSECUTIVE_LOSSES", 3),
            loss_pause_minutes=_i("LOSS_PAUSE_MINUTES", 60),
            rolling_trade_window_hours=_i("ROLLING_TRADE_WINDOW_HOURS", 24),
            breakeven_at_money=_f("BREAKEVEN_AT_MONEY", 0.0),
            breakeven_lock_money=_f("BREAKEVEN_LOCK_MONEY", 0.0),
            profit_stages=_stages("PROFIT_STAGES"),
            max_slippage_ratio=_f("MAX_SLIPPAGE_RATIO", 0.5),
            spread_spike_factor=_f("SPREAD_SPIKE_FACTOR", 3.0),
            min_reward_cost_ratio=_f("MIN_REWARD_COST_RATIO", 2.0),
            tp_money=_f("TP_MONEY", 0.0),
            tp_runner_money=_f("TP_RUNNER_MONEY", 0.0),
            sl_money=_f("SL_MONEY", 0.0),
            max_spread_ratio=_f("MAX_SPREAD_RATIO", 0.25),
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
        # Multi-account mode validates each account instead of the single set.
        if os.environ.get("ACTIVE_BROKERS", "").strip():
            configs = self.broker_configs()
            for cfg in configs:
                problems.extend(cfg.problems())
            if not self.tg_token:
                problems.append("TG_BOT_TOKEN missing — create a bot with @BotFather.")
            if not self.tg_password or len(self.tg_password) < 6:
                problems.append("TG_PASSWORD missing/too short (min 6 chars).")
            if self.fixed_lot < 0:
                problems.append("FIXED_LOT cannot be negative.")
            return problems
        if not self.tg_token:
            problems.append("TG_BOT_TOKEN missing — create a bot with @BotFather and paste its token.")
        if not self.tg_password or len(self.tg_password) < 6:
            problems.append("TG_PASSWORD missing/too short (min 6 chars) — this is your phone login password.")
        if self.broker == "binance":
            if not self.binance_key or not self.binance_secret:
                problems.append("BINANCE_API_KEY / BINANCE_API_SECRET missing — "
                                "create them at testnet.binancefuture.com (demo) "
                                "with Futures trading enabled and withdrawals OFF.")
        elif self.broker in ("mt5", "exness", "deriv", "vantage"):
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
        elif self.broker != "oanda":
            problems.append(
                f"BROKER must be one of mt5, exness, deriv, vantage, oanda, "
                f"binance — got '{self.broker}'.")
        if not self.symbols:
            problems.append("SYMBOLS is empty.")
        if self.fixed_lot < 0:
            problems.append("FIXED_LOT cannot be negative (use 0 to size by RISK_PCT).")
        if (self.breakeven_lock_money and self.breakeven_at_money
                and self.breakeven_lock_money >= self.breakeven_at_money):
            problems.append(
                f"BREAKEVEN_LOCK_MONEY ({self.breakeven_lock_money}) must be below "
                f"BREAKEVEN_AT_MONEY ({self.breakeven_at_money}) — a stop at or past "
                f"the current price is rejected by the broker.")
        previous_lock = None
        for trigger, lock in self.stages():
            if lock >= trigger:
                problems.append(
                    f"PROFIT_STAGES: stage {trigger}:{lock} locks {lock} at a "
                    f"{trigger} trigger — the lock must be below the trigger, or "
                    f"the stop sits at the current price and is rejected.")
            if previous_lock is not None and lock < previous_lock:
                problems.append(
                    f"PROFIT_STAGES: stage {trigger}:{lock} locks less than the "
                    f"stage before it ({previous_lock}) — stops must only tighten.")
            previous_lock = lock
        if self.fixed_lot == 0 and (self.risk_pct <= 0 or self.risk_pct > 5):
            problems.append("RISK_PCT must be between 0 and 5 (risking >5%/trade is reckless).")
        if self.entry_mode not in ("signal", "interval"):
            problems.append(f"ENTRY_MODE must be 'signal' or 'interval', got '{self.entry_mode}'.")
        if self.entry_mode == "interval" and self.entry_interval_seconds < 5:
            problems.append("ENTRY_INTERVAL_SECONDS must be >= 5.")
        return problems
