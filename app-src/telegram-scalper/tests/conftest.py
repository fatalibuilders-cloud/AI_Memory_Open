from __future__ import annotations

import pytest

from tgscalper import config as config_module
from tgscalper.models import SymbolInfo


@pytest.fixture
def config():
    """Default configuration: no config.yaml, no environment secrets."""
    return config_module.load("does-not-exist.yaml", env={})


def gold_info(bid: float = 2350.0, ask: float = 2350.2, **overrides) -> SymbolInfo:
    """XAUUSD as a typical MT5 broker specifies it: 100 oz per lot, $100 per $1."""
    defaults = dict(
        name="XAUUSD",
        digits=2,
        point=0.01,
        tick_size=0.01,
        tick_value=1.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        bid=bid,
        ask=ask,
        stops_level_points=0,
    )
    defaults.update(overrides)
    return SymbolInfo(**defaults)


def eurusd_info(bid: float = 1.08500, ask: float = 1.08512, **overrides) -> SymbolInfo:
    defaults = dict(
        name="EURUSD",
        digits=5,
        point=0.00001,
        tick_size=0.00001,
        tick_value=1.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        bid=bid,
        ask=ask,
        stops_level_points=0,
    )
    defaults.update(overrides)
    return SymbolInfo(**defaults)
