"""Vantage Markets — MetaTrader 5 broker.

Traits:
  * Some account types suffix symbols with '+' (EURUSD+); others use plain
    names. MT5Broker._resolve confirms against the account's real list.
  * IOC filling is accepted on the usual account types.
  * Offers forex, metals, indices, share CFDs and crypto CFDs.
"""

from __future__ import annotations

from .mt5 import MT5Broker


class VantageBroker(MT5Broker):
    broker_name = "Vantage"
    preferred_filling = "IOC"
    symbol_suffix = "+"
