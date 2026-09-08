"""Solving an instrument's real measurements into settings that fit it.

Shared by `tune_symbols.py`, which writes the result to .env, and by the
bot's own review, which re-derives them while trading is paused. Both must
agree: a stop the tuner considers correct and the bot considers too tight
would block every trade with no explanation.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Settings


#: Fallbacks used only when the configuration leaves the gate switched off.
DEFAULT_SPREAD_SHARE = 0.15
DEFAULT_REWARD_COST = 3.0
#: Sit this far clear of the broker's minimum stop, which moves with spread.
STOP_FLOOR_MARGIN = 1.2
#: Above this, the spread eats so much of a normal move that the instrument
#: needs an implausibly wide stop to be worth trading.
UNTRADEABLE_SPREAD_ATR = 0.5


@dataclass
class Row:
    """One instrument, measured and solved."""
    symbol: str
    spread: float
    atr: float
    floor: float
    per_price: float
    stop_distance: float
    target_distance: float

    @property
    def stop_money(self) -> float:
        return self.stop_distance * self.per_price

    @property
    def target_money(self) -> float:
        return self.target_distance * self.per_price

    @property
    def cost(self) -> float:
        return self.spread * self.per_price

    @property
    def spread_atr(self) -> float:
        return self.spread / self.atr if self.atr > 0 else 0.0

    @property
    def untradeable(self) -> bool:
        return self.spread_atr > UNTRADEABLE_SPREAD_ATR


def solve(settings: Settings, symbol: str, spread: float, atr_value: float,
          floor: float, per_price: float) -> Row:
    """Turn one instrument's measurements into stop and target distances.

    The stop is the widest of three requirements: the strategy's own
    ATR distance, the distance that keeps the spread within the bot's
    spread gate, and the broker's minimum stop. The target keeps the
    configured reward:risk unless that would fail the cost gate, in which
    case it is raised to clear the round trip.
    """
    share = settings.max_spread_ratio if settings.max_spread_ratio > 0 else DEFAULT_SPREAD_SHARE
    reward_cost = (settings.min_reward_cost_ratio
                   if settings.min_reward_cost_ratio > 0 else DEFAULT_REWARD_COST)

    stop = atr_value * settings.atr_sl_mult
    if spread > 0:
        stop = max(stop, spread / share)
    if floor > 0:
        stop = max(stop, floor * STOP_FLOOR_MARGIN)

    ratio = (settings.atr_tp_mult / settings.atr_sl_mult
             if settings.atr_sl_mult > 0 else 1.5)
    target = stop * ratio
    if spread > 0:
        # Clear the round trip with a little headroom, since the spread at
        # the moment of the trade will not be exactly the spread now. The
        # gate compares cash, but value-per-price cancels from both sides,
        # so the requirement is purely a distance.
        target = max(target, spread * reward_cost * 1.05)
    return Row(symbol, spread, atr_value, floor, per_price, stop, target)
