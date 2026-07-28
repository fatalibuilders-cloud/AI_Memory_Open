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


def build_sessions(settings: Settings) -> list[BrokerSession]:
    from .broker import build_broker_from_config
    sessions = []
    for cfg in settings.broker_configs():
        sessions.append(BrokerSession(
            name=cfg.name, cfg=cfg,
            broker=build_broker_from_config(cfg),
            risk=RiskManager(settings),
            symbols=list(cfg.symbols),
        ))
    return sessions
