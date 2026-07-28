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


def _mt5_class(kind: str):
    if kind == "exness":
        from .exness import ExnessBroker
        return ExnessBroker
    if kind == "deriv":
        from .deriv import DerivBroker
        return DerivBroker
    if kind == "vantage":
        from .vantage import VantageBroker
        return VantageBroker
    from .mt5 import MT5Broker
    return MT5Broker


def build_broker_from_config(cfg) -> Broker:
    """Instantiate one account from a BrokerConfig."""
    kind = (cfg.kind or "mt5").lower()
    if kind == "oanda":
        from .oanda import OandaBroker
        return OandaBroker(cfg.oanda_token, cfg.oanda_account, cfg.oanda_env)
    if kind == "binance":
        from .binance import BinanceBroker
        return BinanceBroker(cfg.binance_key, cfg.binance_secret, cfg.binance_testnet)
    return _mt5_class(kind)(cfg.login, cfg.password, cfg.server, cfg.path)


def build_broker(settings) -> Broker:
    """Instantiate the FIRST configured account.

    Kept for the single-account tools (doctor, backtest, symbols). The bot
    itself uses build_broker_from_config once per account so it can run
    several at the same time.
    """
    return build_broker_from_config(settings.broker_configs()[0])
