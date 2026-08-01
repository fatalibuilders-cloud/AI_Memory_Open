"""Trade simulation engine shared by backtest.py and optimize.py.

Deliberately pessimistic, so a strategy that looks good here has cleared a
realistic bar rather than an optimistic one:

  * entries fill at the NEXT bar's open (never the signal bar's close)
  * the spread is charged on every entry
  * when a bar's range covers both stop and target, the STOP is taken
  * no position is opened while `max_open_positions` are already running
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .broker.base import Bar
from .vecstrategy import VecStrategy


@dataclass
class SimTrade:
    opened: int
    side: str
    entry: float
    sl: float
    tp: float
    lots: float
    closed: Optional[int] = None
    exit: Optional[float] = None
    pnl: float = 0.0
    reason: str = ""


@dataclass
class SimResult:
    trades: list[SimTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    start_balance: float = 0.0
    end_balance: float = 0.0
    bars: int = 0
    span_days: float = 0.0

    @property
    def wins(self):
        return [t for t in self.trades if t.pnl > 0]

    @property
    def losses(self):
        return [t for t in self.trades if t.pnl <= 0]

    @property
    def win_rate(self) -> float:
        return 100.0 * len(self.wins) / len(self.trades) if self.trades else 0.0

    @property
    def profit_factor(self) -> float:
        gross_win = sum(t.pnl for t in self.wins)
        gross_loss = -sum(t.pnl for t in self.losses)
        if gross_loss <= 0:
            return float("inf") if gross_win > 0 else 0.0
        return gross_win / gross_loss

    @property
    def max_drawdown_pct(self) -> float:
        peak, worst = self.start_balance, 0.0
        for eq in self.equity_curve:
            peak = max(peak, eq)
            if peak > 0:
                worst = max(worst, (peak - eq) / peak * 100.0)
        return worst

    @property
    def return_pct(self) -> float:
        if self.start_balance <= 0:
            return 0.0
        return (self.end_balance - self.start_balance) / self.start_balance * 100.0

    @property
    def per_day_pct(self) -> float:
        return self.return_pct / self.span_days if self.span_days > 0 else 0.0


def simulate(bars: list[Bar], strategy: VecStrategy, settings,
             balance: float, point_value: float, spread: float) -> SimResult:
    res = SimResult(start_balance=balance, bars=len(bars))
    if len(bars) > 1:
        res.span_days = (bars[-1].time - bars[0].time) / 86400.0

    arrays = strategy.precompute(bars)
    warmup = max(strategy.warmup(), 2)
    open_trades: list[SimTrade] = []
    equity = balance

    for i in range(warmup, len(bars) - 1):
        bar, nxt = bars[i], bars[i + 1]

        still_open = []
        for t in open_trades:
            hit_sl = bar.low <= t.sl if t.side == "buy" else bar.high >= t.sl
            hit_tp = bar.high >= t.tp if t.side == "buy" else bar.low <= t.tp
            if hit_sl:
                exit_price, why = t.sl, "SL"
            elif hit_tp:
                exit_price, why = t.tp, "TP"
            else:
                still_open.append(t)
                continue
            move = (exit_price - t.entry) if t.side == "buy" else (t.entry - exit_price)
            t.pnl = move * t.lots * point_value
            t.exit, t.closed, t.reason = exit_price, bar.time, why
            equity += t.pnl
            res.trades.append(t)
        open_trades = still_open
        res.equity_curve.append(equity)

        if len(open_trades) >= settings.max_open_positions:
            continue
        signal = strategy.at(i, arrays)
        if signal is None:
            continue

        entry = nxt.open + (spread if signal.side == "buy" else -spread)
        if settings.fixed_lot > 0:
            lots = settings.fixed_lot
        else:
            denom = signal.sl_distance * point_value
            lots = max(round(equity * settings.risk_pct / 100.0 / denom, 2), 0.01) \
                if denom > 0 else 0.01
        if signal.side == "buy":
            sl, tp = entry - signal.sl_distance, entry + signal.tp_distance
        else:
            sl, tp = entry + signal.sl_distance, entry - signal.tp_distance
        open_trades.append(SimTrade(nxt.time, signal.side, entry, sl, tp, lots))

    res.end_balance = equity
    return res
