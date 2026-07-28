"""Broker adapters."""

from .base import Broker, BrokerError
from .paper import PaperBroker

__all__ = ["Broker", "BrokerError", "PaperBroker", "build_broker"]


def build_broker(config: object) -> Broker:
    """Instantiate the broker named in config, honouring the live kill switch.

    Imported lazily so a machine without the MetaTrader5 package (any Linux or
    macOS box) can still run the parser, the risk engine and paper mode.
    """
    from ..config import Config  # local import avoids a cycle

    assert isinstance(config, Config)

    if not config.execution.live_enabled:
        return PaperBroker(
            starting_balance=config.execution.paper_balance,
            reason=config.execution.live_block_reason,
        )

    provider = config.broker.provider.lower()
    if provider in {"mt5", "metatrader5", "metatrader"}:
        from .mt5 import MT5Broker

        return MT5Broker(config.broker)
    if provider in {"paper", "demo", "none"}:
        return PaperBroker(starting_balance=config.execution.paper_balance)
    raise BrokerError(f"unknown broker provider: {config.broker.provider!r}")
