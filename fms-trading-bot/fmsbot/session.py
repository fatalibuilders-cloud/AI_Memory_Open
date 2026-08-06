"""One trading account: its broker, symbols, risk state and progress.

The bot holds a list of these so several accounts (e.g. an Exness forex
account and a Deriv crypto account) can trade at the same time. Each keeps
its own RiskManager, because balances and daily loss limits are per-account
— sharing them across brokers would let a loss on one stop the other.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from .broker.base import Broker, BrokerError
from .config import BrokerConfig, Settings
from .risk import RiskManager

log = logging.getLogger("fmsbot.session")

RECONNECT_DELAYS = [10, 20, 40, 60]


@dataclass
class BrokerSession:
    name: str
    cfg: BrokerConfig
    broker: Broker
    risk: RiskManager
    symbols: list[str]
    connected: bool = False
    last_bar: dict[str, int] = field(default_factory=dict)
    symbol_warned: dict[str, float] = field(default_factory=dict)
    last_entry_attempt: dict[str, float] = field(default_factory=dict)
    known_tickets: set[int] = field(default_factory=set)
    reconnect_attempt: int = 0
    last_block: str = ""          # why the most recent signal was refused

    @property
    def label(self) -> str:
        return f"{self.name}/{self.cfg.kind}" if self.name != self.cfg.kind else self.name

    def connect(self) -> bool:
        try:
            self.broker.connect()
            self.connected = True
            self.reconnect_attempt = 0
            return True
        except BrokerError as exc:
            self.connected = False
            log.warning("[%s] connect failed: %s", self.name, exc)
            return False

    def disconnect(self) -> None:
        try:
            self.broker.disconnect()
        except Exception:
            pass
        self.connected = False

    def warn_symbol(self, symbol: str, exc: Exception) -> None:
        """Warn about a broken symbol at most once every 15 minutes."""
        now = time.time()
        if now - self.symbol_warned.get(symbol, 0.0) < 900:
            return
        self.symbol_warned[symbol] = now
        log.warning("[%s] %s unavailable, skipping it: %s", self.name, symbol, exc)


class MultiTerminalError(RuntimeError):
    """More than one MetaTrader 5 account was requested in one process."""


def check_mt5_conflict(configs) -> None:
    """Reject two MT5 accounts in one process.

    The MetaTrader5 python package drives ONE terminal, and initialising it
    with a second login switches that terminal's account rather than opening
    a parallel connection. Both sessions then read and trade the same
    account while reporting different names — silently wrong, so refuse it.
    """
    from .config import MT5_BACKENDS
    mt5_accounts = [c for c in configs if c.kind in MT5_BACKENDS]
    if len(mt5_accounts) > 1:
        names = ", ".join(c.name for c in mt5_accounts)
        raise MultiTerminalError(
            f"{len(mt5_accounts)} MetaTrader 5 accounts requested ({names}), but one "
            f"process can only drive one MT5 terminal — the second login switches "
            f"the terminal instead of adding a connection, so both would trade the "
            f"SAME account.\n"
            f"  Pick one:  python profile.py use {mt5_accounts[0].name}\n"
            f"  To trade several MT5 brokers at once, run a second copy of the bot "
            f"in its own folder, with its own portable MT5 terminal and its own "
            f"Telegram token.\n"
            f"  An MT5 account CAN run alongside oanda or binance accounts, since "
            f"those use their own APIs.")


def build_sessions(settings: Settings) -> list[BrokerSession]:
    from .broker import build_broker_from_config
    configs = settings.broker_configs()
    check_mt5_conflict(configs)
    sessions = []
    for cfg in configs:
        sessions.append(BrokerSession(
            name=cfg.name, cfg=cfg,
            broker=build_broker_from_config(cfg),
            risk=RiskManager(settings),
            symbols=list(cfg.symbols),
        ))
    return sessions
