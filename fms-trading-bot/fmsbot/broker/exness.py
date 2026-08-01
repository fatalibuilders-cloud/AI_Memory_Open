"""Exness — MetaTrader 5 broker.

Exness speaks standard MT5, so this only carries what is genuinely
Exness-specific. Everything else is inherited from MT5Broker.

Traits:
  * Many account types suffix symbols with 'm' (EURUSDm, XAUUSDm, BTCUSDm).
    Suffixes vary by account type, so MT5Broker._resolve still confirms
    against the account's real symbol list rather than assuming.
  * IOC filling is accepted on the usual account types.
  * CMA-licensed in Kenya; KES accounts and M-Pesa funding.
"""

from __future__ import annotations

from .mt5 import MT5Broker


class ExnessBroker(MT5Broker):
    broker_name = "Exness"
    preferred_filling = "IOC"
    symbol_suffix = "m"
