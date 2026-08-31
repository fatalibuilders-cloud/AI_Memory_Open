"""Shared scaffolding: a broker that answers without a terminal."""

from __future__ import annotations

import os
import threading

from fmsbot.broker.base import Bar, Broker, OrderReceipt


#: Every key any call to settings() has ever set. Cleared on the next call
#: so one test cannot configure the next: a leaked LIVE_REQUIRES_EVIDENCE
#: once let a "live account" test place an order and pass by accident.
_SET_BY_US: set[str] = set()


def settings(**env):
    """Load Settings from a clean environment plus these overrides."""
    for key in list(os.environ):
        if key in _SET_BY_US or key.startswith(
                ("SYM_", "PROFIT_STAGES", "TRAIL_", "MAX_", "MIN_", "ENTRY_",
                 "ATR_", "TP_", "SL_", "BREAKEVEN_", "EVIDENCE_", "LIVE_",
                 "HALT_", "RISK_", "DAILY_", "COOLDOWN_")):
            del os.environ[key]
    _SET_BY_US.update(env)
    os.environ.update({"BROKER": "mt5", "TG_BOT_TOKEN": "x",
                       "TG_PASSWORD": "secret123"})
    os.environ.update({k: str(v) for k, v in env.items()})
    from fmsbot.config import Settings
    return Settings.load()


class FakeBroker(Broker):
    """Deterministic prices, and a record of everything asked of it."""

    def __init__(self, price=1.0, per_price=1000.0, spread=0.0001,
                 min_stop=0.0, atr=0.0004, demo=True, balance=1000.0):
        self.price, self.per = price, per_price
        self._spread, self._min_stop, self._atr = spread, min_stop, atr
        self._demo, self._balance = demo, balance
        self.orders, self.closed, self.modified = [], [], {}

    def connect(self): pass
    def disconnect(self): pass
    def balance(self): return self._balance
    def equity(self): return self._balance
    def positions(self): return []
    def spread(self, symbol): return self._spread
    def min_stop_distance(self, symbol): return self._min_stop
    def value_per_price(self, symbol, volume): return self.per * (volume / 0.01)
    def current_price(self, symbol, side): return self.price
    def is_demo(self): return self._demo
    def account_currency(self): return "USD"
    def volume_from_lots(self, symbol, lots): return lots
    def volume_for_risk(self, symbol, distance, amount): return 0.01

    def bars(self, symbol, timeframe, count):
        px = self.price
        return [Bar(i * 60, px, px + self._atr / 2, px - self._atr / 2, px)
                for i in range(count)]

    def close_position(self, ticket):
        self.closed.append(ticket)
        return 0.0

    def modify_position(self, ticket, sl, tp):
        self.modified[ticket] = (sl, tp)

    def market_order(self, symbol, side, volume, sl, tp, comment=""):
        self.orders.append((symbol, side, volume, sl, tp))
        return OrderReceipt(len(self.orders), symbol, side, volume,
                            self.price, sl, tp)


def make_bot(s, broker, symbols, **session_kw):
    """A TradingBot wired to a fake broker, without touching Telegram."""
    from fmsbot import bot as botmod
    from fmsbot.risk import RiskManager
    from fmsbot.session import BrokerSession

    messages = []
    session = BrokerSession(name="test", cfg=s.broker_configs()[0],
                            broker=broker, risk=RiskManager(s),
                            symbols=list(symbols), **session_kw)
    bot = object.__new__(botmod.TradingBot)
    bot.s = s
    bot._trade_lock = threading.Lock()
    bot.remote = type("R", (), {"broadcast": lambda self, m: messages.append(m)})()
    return bot, session, messages
