"""Position sizing and the guards that decide whether to trade at all.

Deliberately free of I/O: every input arrives as a plain value, so the rules
that protect your account are cheap to unit-test and easy to reason about.
The bot copies someone else's opinion — these limits are the only thing
standing between a bad night in a signal group and your balance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .config import Config
from .models import Action, Side, Signal, SymbolInfo


@dataclass
class RiskState:
    """Everything the guards need to know about the world right now."""

    now: datetime
    open_total: int = 0
    open_for_symbol: int = 0
    signals_last_hour: int = 0
    equity: float = 0.0
    day_start_balance: float = 0.0
    duplicate_of: Optional[str] = None  # fingerprint seen inside the dedupe window

    @property
    def day_drawdown_pct(self) -> float:
        if self.day_start_balance <= 0:
            return 0.0
        return (self.day_start_balance - self.equity) / self.day_start_balance * 100.0


@dataclass
class GateResult:
    ok: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.ok


ALLOW = GateResult(True)


def _deny(reason: str) -> GateResult:
    return GateResult(False, reason)


def check_guards(
    signal: Signal,
    info: Optional[SymbolInfo],
    state: RiskState,
    config: Config,
) -> GateResult:
    """Run every pre-trade guard. The first failure wins."""
    risk = config.risk

    if state.duplicate_of:
        return _deny(
            f"duplicate of a signal already acted on in the last "
            f"{risk.dedupe_window_minutes} min"
        )

    # Management messages skip the entry guards below — closing a trade or
    # moving a stop must keep working even when we have stopped opening new ones.
    if signal.action is not Action.OPEN:
        return ALLOW

    symbol = signal.symbol.upper()
    if risk.block_symbols and symbol in {item.upper() for item in risk.block_symbols}:
        return _deny(f"{symbol} is in risk.block_symbols")
    if risk.allow_symbols and symbol not in {item.upper() for item in risk.allow_symbols}:
        return _deny(f"{symbol} is not in risk.allow_symbols")

    start, end, days = risk.hours.parsed()
    if days and state.now.weekday() not in days:
        return _deny(f"{state.now:%A} is outside risk.hours.days")
    current = state.now.time()
    inside = start <= current <= end if start <= end else (current >= start or current <= end)
    if not inside:
        return _deny(f"{current:%H:%M} is outside trading hours {risk.hours.start}-{risk.hours.end}")

    if risk.max_daily_loss_pct > 0 and state.day_drawdown_pct >= risk.max_daily_loss_pct:
        return _deny(
            f"daily loss halt: down {state.day_drawdown_pct:.2f}% today "
            f"(limit {risk.max_daily_loss_pct}%)"
        )
    if state.open_total >= risk.max_open_trades:
        return _deny(f"already {state.open_total} positions open (max {risk.max_open_trades})")
    if state.open_for_symbol >= risk.max_open_per_symbol:
        return _deny(
            f"already {state.open_for_symbol} {symbol} positions open "
            f"(max {risk.max_open_per_symbol} per symbol)"
        )
    if state.signals_last_hour >= risk.max_signals_per_hour:
        return _deny(
            f"{state.signals_last_hour} signals acted on in the last hour "
            f"(max {risk.max_signals_per_hour})"
        )

    if info is not None:
        # Point-denominated limits mean different amounts per instrument, so
        # take whatever this symbol was configured with.
        min_stop_points, max_spread_points = risk.limits_for(symbol)
        if max_spread_points > 0 and info.spread_points > max_spread_points:
            return _deny(
                f"spread {info.spread_points:.0f} points is above the "
                f"{max_spread_points:.0f} point limit for {symbol}"
            )
        stop = signal.stop_loss
        reference = signal.entry or info.mid
        if stop is not None and reference and info.point > 0:
            distance_points = abs(reference - stop) / info.point
            if min_stop_points > 0 and distance_points < min_stop_points:
                return _deny(
                    f"stop is only {distance_points:.0f} points away "
                    f"(min {min_stop_points:.0f} for {symbol})"
                )
            if info.stops_level_points and distance_points < info.stops_level_points:
                return _deny(
                    f"stop {distance_points:.0f} points is inside the broker's minimum "
                    f"of {info.stops_level_points} points"
                )
    return ALLOW


@dataclass
class Sizing:
    """The result of turning a risk budget into a lot size."""

    volume: float
    stop_loss: Optional[float]
    risk_amount: float
    actual_risk: float
    notes: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error and self.volume > 0


def round_to_step(volume: float, step: float, *, down: bool = True) -> float:
    """Snap a volume onto the broker's lot step.

    Rounds down by default: overshooting the step is how a "1% risk" trade
    quietly becomes 1.4%.
    """
    if step <= 0:
        return round(volume, 2)
    steps = volume / step
    steps = math.floor(steps + 1e-9) if down else round(steps)
    # Lot steps are decimal (0.01, 0.1, 1.0); 8 places kills float dust.
    return round(steps * step, 8)


def resolve_stop(
    signal: Signal,
    info: SymbolInfo,
    config: Config,
    reference_price: float,
) -> tuple[Optional[float], list[str]]:
    """Work out the absolute stop price, converting pips or applying a fallback."""
    notes: list[str] = []
    if signal.stop_loss is not None:
        return signal.stop_loss, notes
    if signal.side is None:
        return None, notes

    # "SL 30 pips" — a pip is 10 points on 5-digit FX and 3-digit JPY quotes.
    if signal.sl_pips is not None:
        pip = info.point * (10 if info.digits in (3, 5) else 1)
        stop = reference_price - signal.side.sign * signal.sl_pips * pip
        notes.append(f"converted SL {signal.sl_pips} pips to {stop:.{info.digits}f}")
        return round(stop, info.digits), notes

    if config.risk.fallback_stop_points > 0:
        stop = reference_price - signal.side.sign * config.risk.fallback_stop_points * info.point
        notes.append(
            f"no stop in message; applied fallback of "
            f"{config.risk.fallback_stop_points:.0f} points"
        )
        return round(stop, info.digits), notes
    return None, notes


def size_position(
    signal: Signal,
    info: SymbolInfo,
    balance: float,
    config: Config,
    *,
    reference_price: Optional[float] = None,
    group_multiplier: float = 1.0,
    legs: int = 1,
) -> Sizing:
    """Convert a risk budget into a lot size for one leg of a signal.

    Percentage sizing needs a stop: risk % of balance divided by the distance to
    the stop, in account currency. With `risk.fixed_lot` set, that arithmetic is
    skipped entirely and the fixed size is used.
    """
    notes: list[str] = []
    reference = reference_price or signal.entry or info.mid
    if not reference:
        return Sizing(0.0, None, 0.0, 0.0, error="no reference price to size against")

    stop, stop_notes = resolve_stop(signal, info, config, reference)
    notes.extend(stop_notes)

    budget = balance * config.risk.risk_per_trade_pct / 100.0 * group_multiplier
    legs = max(1, legs)

    if config.risk.fixed_lot is not None:
        volume = config.risk.fixed_lot / legs
        notes.append(f"fixed lot {config.risk.fixed_lot} split across {legs} leg(s)")
    else:
        if stop is None:
            return Sizing(
                0.0,
                None,
                budget,
                0.0,
                error="cannot size by risk percentage without a stop loss "
                "(set risk.fixed_lot or risk.fallback_stop_points)",
            )
        distance = abs(reference - stop)
        value_per_unit = info.value_per_price_unit()
        if distance <= 0 or value_per_unit <= 0:
            return Sizing(0.0, stop, budget, 0.0, error="stop distance or tick value is zero")
        volume = budget / (distance * value_per_unit) / legs

    volume = min(volume, config.risk.max_lot, info.volume_max)
    volume = round_to_step(volume, info.volume_step, down=True)

    if volume < info.volume_min:
        # The smallest tradable size would risk more than the budget allows.
        floor_volume = info.volume_min
        if stop is not None:
            implied = abs(reference - stop) * info.value_per_price_unit() * floor_volume
            if implied > budget * 1.5:
                return Sizing(
                    0.0,
                    stop,
                    budget,
                    implied,
                    error=(
                        f"minimum lot {floor_volume} would risk {implied:.2f} "
                        f"vs a budget of {budget:.2f} — stop is too wide for this account"
                    ),
                )
            notes.append(
                f"rounded up to the broker minimum lot {floor_volume} "
                f"(risking {implied:.2f} instead of {budget:.2f})"
            )
        volume = floor_volume

    actual = 0.0
    if stop is not None:
        actual = abs(reference - stop) * info.value_per_price_unit() * volume
    return Sizing(
        volume=volume,
        stop_loss=stop,
        risk_amount=budget,
        actual_risk=actual,
        notes=notes,
    )


def select_take_profits(signal: Signal, config: Config) -> list[Optional[float]]:
    """Decide which take-profit levels become positions.

    Returns one entry per leg to open; None means "no TP, let the stop and the
    admin's follow-up messages manage it".
    """
    tps = signal.take_profits[: max(1, config.execution.max_tps)]
    if not tps:
        return [None]
    mode = config.execution.tp_mode.lower()
    if mode == "split":
        return list(tps)
    if mode == "last":
        return [tps[-1]]
    return [tps[0]]


def breakeven_price(
    open_price: float, side: Side, info: SymbolInfo, offset_points: float
) -> float:
    """Stop at entry, nudged into profit by offset_points to cover costs."""
    return round(open_price + side.sign * offset_points * info.point, info.digits)
