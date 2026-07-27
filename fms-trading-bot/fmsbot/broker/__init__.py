"""Broker adapters.

Two kinds live here:

  * MetaTrader 5 brokers — Exness, Deriv, Vantage and any other MT5 broker.
    They share one API, so `mt5.MT5Broker` holds the implementation and the
    per-broker modules carry only what genuinely differs (symbol naming,
    order-filling mode, weekend availability).
  * Native-API brokers — `oanda.OandaBroker` and `binance.BinanceBroker`
    each speak their own REST API and implement `base.Broker` directly.

`build_broker(settings)` picks the right one from BROKER in .env.
Imports are deferred so a missing optional dependency (MetaTrader5 is
Windows-only) never breaks the others.
"""

from __future__ import annotations

from .base import Bar, Broker, BrokerError, OrderReceipt, Position  # noqa: F401

#: BROKER= values accepted in .env
BROKER_CHOICES = ("mt5", "exness", "deriv", "vantage", "oanda", "binance")

#: Which .env credentials each backend needs, for error messages.
BROKER_CREDENTIALS = {
    "mt5": ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"),
    "exness": ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"),
    "deriv": ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"),
    "vantage": ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"),
    "oanda": ("OANDA_API_TOKEN", "OANDA_ACCOUNT_ID"),
    "binance": ("BINANCE_API_KEY", "BINANCE_API_SECRET"),
}


def build_broker(settings) -> Broker:
    """Instantiate the broker named by settings.broker."""
    name = (settings.broker or "mt5").lower()

    if name == "oanda":
        from .oanda import OandaBroker
        return OandaBroker(settings.oanda_token, settings.oanda_account,
                           settings.oanda_env)

    if name == "binance":
        from .binance import BinanceBroker
        return BinanceBroker(settings.binance_key, settings.binance_secret,
                             settings.binance_testnet)

    mt5_classes = {}
    if name == "exness":
        from .exness import ExnessBroker
        mt5_classes["exness"] = ExnessBroker
    elif name == "deriv":
        from .deriv import DerivBroker
        mt5_classes["deriv"] = DerivBroker
    elif name == "vantage":
        from .vantage import VantageBroker
        mt5_classes["vantage"] = VantageBroker

    if name in mt5_classes:
        cls = mt5_classes[name]
    else:
        from .mt5 import MT5Broker
        cls = MT5Broker
    return cls(settings.mt5_login, settings.mt5_password,
               settings.mt5_server, settings.mt5_path)
