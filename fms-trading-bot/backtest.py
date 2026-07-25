#!/usr/bin/env python3
r"""Backtest the strategy on real historical data — the only honest way to
find out what a configuration actually returns.

    .\.venv\Scripts\python.exe backtest.py --symbol EURUSDm --days 30
    .\.venv\Scripts\python.exe backtest.py --symbol EURUSDm --days 30 --preset aggressive
    .\.venv\Scripts\python.exe backtest.py --csv data.csv --balance 50

Reads bars from MetaTrader 5 (same terminal the bot uses) or a CSV with
columns time,open,high,low,close. Simulation rules, deliberately
pessimistic so results are not flattering:

  * entries fill at the NEXT bar's open (no looking into the future)
  * the spread is paid on every entry
  * if a bar's range covers both stop and target, the STOP is taken
  * position size is the bot's own FIXED_LOT / RISK_PCT logic
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from typing import Optional

from fmsbot.broker.base import Bar
from fmsbot.config import Settings
from fmsbot.series import atr_full, ema_full, rsi_full
from fmsbot.strategy import EmaCrossStrategy, Signal

# money per 1.0 of price movement, per 1.0 lot
DEFAULT_POINT_VALUE = {
    "XAU": 100.0,      # gold: 1 lot = 100 oz
    "XAG": 5000.0,     # silver: 1 lot = 5000 oz
    "BTC": 1.0,        # crypto: 1 lot = 1 coin
    "ETH": 1.0,
}
FX_POINT_VALUE = 100_000.0                            # 1 lot = 100k units
DEFAULT_SPREAD = {
    "XAU": 0.30,
    "XAG": 0.02,
    "BTC": 30.0,       # crypto spreads are wide — often $20-60
    "ETH": 2.0,
}
FX_SPREAD = 0.00012                                   # ~1.2 pips


@dataclass
class Trade:
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
class Result:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    start_balance: float = 0.0
    end_balance: float = 0.0
    bars: int = 0
    span_days: float = 0.0

    @property
    def wins(self) -> list[Trade]:
        return [t for t in self.trades if t.pnl > 0]

    @property
    def losses(self) -> list[Trade]:
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


def signal_at(s: Settings, i: int, fast, slow, rsis, atrs) -> Optional[Signal]:
    """Same logic as EmaCrossStrategy, evaluated from precomputed series."""
    f_now, f_prev = fast[i], fast[i - 1]
    s_now, s_prev = slow[i], slow[i - 1]
    r, a = rsis[i], atrs[i]
    if None in (f_now, f_prev, s_now, s_prev, r, a) or a <= 0:
        return None
    sl_d, tp_d = a * s.atr_sl_mult, a * s.atr_tp_mult

    if s.entry_mode == "interval":
        side = "buy" if f_now > s_now else "sell"
        return Signal(side, sl_d, tp_d, f"interval entry, trend {side}")

    if f_prev <= s_prev and f_now > s_now and r > s.rsi_floor:
        return Signal("buy", sl_d, tp_d, f"EMA{s.ema_fast}x{s.ema_slow} up, RSI {r:.0f}")
    if f_prev >= s_prev and f_now < s_now and r < s.rsi_ceiling:
        return Signal("sell", sl_d, tp_d, f"EMA{s.ema_fast}x{s.ema_slow} down, RSI {r:.0f}")
    return None


def point_value_for(symbol: str) -> float:
    for key, value in DEFAULT_POINT_VALUE.items():
        if symbol.upper().startswith(key):
            return value
    return FX_POINT_VALUE


def spread_for(symbol: str) -> float:
    for key, value in DEFAULT_SPREAD.items():
        if symbol.upper().startswith(key):
            return value
    return FX_SPREAD


def run_backtest(bars: list[Bar], settings: Settings, symbol: str,
                 balance: float, point_value: float, spread: float) -> Result:
    strategy = EmaCrossStrategy(settings)
    res = Result(start_balance=balance, bars=len(bars))
    if len(bars) > 1:
        res.span_days = (bars[-1].time - bars[0].time) / 86400.0

    # Precompute indicators once (single pass) — replaying them per bar is
    # O(n^2) and takes hours on a month of M1 data.
    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    fast = ema_full(closes, settings.ema_fast)
    slow = ema_full(closes, settings.ema_slow)
    rsis = rsi_full(closes, settings.rsi_period)
    atrs = atr_full(highs, lows, closes, settings.atr_period)

    open_trades: list[Trade] = []
    equity = balance
    min_bars = strategy.min_bars()

    for i in range(min_bars, len(bars) - 1):
        bar = bars[i]
        nxt = bars[i + 1]

        # --- manage open trades against THIS bar's range -----------------
        still_open = []
        for t in open_trades:
            hit_sl = bar.low <= t.sl if t.side == "buy" else bar.high >= t.sl
            hit_tp = bar.high >= t.tp if t.side == "buy" else bar.low <= t.tp
            if hit_sl:                      # pessimistic: stop wins ties
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

        # --- look for a new entry -----------------------------------------
        if len(open_trades) >= settings.max_open_positions:
            continue
        signal = signal_at(settings, i, fast, slow, rsis, atrs)
        if signal is None:
            continue

        entry = nxt.open + (spread if signal.side == "buy" else -spread)
        if settings.fixed_lot > 0:
            lots = settings.fixed_lot
        else:
            risk_money = equity * settings.risk_pct / 100.0
            denom = signal.sl_distance * point_value
            lots = round(risk_money / denom, 2) if denom > 0 else 0.0
            lots = max(lots, 0.01)
        if signal.side == "buy":
            sl, tp = entry - signal.sl_distance, entry + signal.tp_distance
        else:
            sl, tp = entry + signal.sl_distance, entry - signal.tp_distance
        open_trades.append(Trade(nxt.time, signal.side, entry, sl, tp, lots))

    res.end_balance = equity
    return res


def load_csv(path: str) -> list[Bar]:
    bars = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            bars.append(Bar(int(float(row["time"])), float(row["open"]),
                            float(row["high"]), float(row["low"]), float(row["close"])))
    return bars


def load_mt5(settings: Settings, symbol: str, timeframe: str, days: int):
    """Returns (bars, point_value, spread) straight from the terminal."""
    from fmsbot.broker.mt5 import MT5Broker
    broker = MT5Broker(settings.mt5_login, settings.mt5_password,
                       settings.mt5_server, settings.mt5_path)
    broker.connect()
    try:
        per_bar = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800,
                   "H1": 3600, "H4": 14400, "D1": 86400}[timeframe]
        count = min(int(days * 86400 / per_bar), 200_000)
        bars = broker.bars(symbol, timeframe, count)
        info = broker.mt5.symbol_info(broker._resolve(symbol))
        point_value = spread = None
        if info is not None and info.trade_tick_size:
            point_value = info.trade_tick_value / info.trade_tick_size
            spread = info.spread * info.point if info.point else None
        return (bars,
                point_value or point_value_for(symbol),
                spread or spread_for(symbol))
    finally:
        broker.disconnect()


def report(res: Result, settings: Settings, symbol: str, spread: float) -> None:
    print("=" * 68)
    print(f"BACKTEST  {symbol}  {settings.timeframe}  "
          f"{settings.ema_fast}/{settings.ema_slow} EMA, "
          f"{'fixed ' + str(settings.fixed_lot) + ' lot' if settings.fixed_lot else str(settings.risk_pct) + '% risk'}")
    print("=" * 68)
    print(f"  bars              : {res.bars} ({res.span_days:.1f} days)")
    print(f"  spread assumed    : {spread:g} price units per trade")
    print(f"  start balance     : {res.start_balance:.2f}")
    print(f"  end balance       : {res.end_balance:.2f}")
    print(f"  return            : {res.return_pct:+.2f}%")
    print()
    print(f"  trades            : {len(res.trades)}")
    if not res.trades:
        print("\n  No trades — the strategy found no signals in this window.")
        return
    print(f"  win rate          : {res.win_rate:.1f}%  "
          f"({len(res.wins)}W / {len(res.losses)}L)")
    avg_w = sum(t.pnl for t in res.wins) / len(res.wins) if res.wins else 0.0
    avg_l = sum(t.pnl for t in res.losses) / len(res.losses) if res.losses else 0.0
    print(f"  average win/loss  : {avg_w:+.2f} / {avg_l:+.2f}")
    pf = res.profit_factor
    print(f"  profit factor     : {'inf' if pf == float('inf') else f'{pf:.2f}'}"
          f"   (>1 = profitable, >1.5 = good)")
    print(f"  max drawdown      : {res.max_drawdown_pct:.1f}%")
    if res.span_days > 0:
        per_day = res.return_pct / res.span_days
        print(f"  average per day   : {per_day:+.2f}%")
        print()
        print("  PROJECTION (compounding this daily rate, if it persisted):")
        if per_day <= 0:
            print("     negative expectancy — this configuration loses money.")
        else:
            bal, days = res.start_balance, 0
            target = res.start_balance * 20
            while bal < target and days < 3650:
                bal *= (1 + per_day / 100.0)
                days += 1
            if days >= 3650:
                print(f"     20x would take over 10 years at {per_day:+.2f}%/day.")
            else:
                print(f"     20x ({res.start_balance:.0f} -> {target:.0f}) "
                      f"would take ~{days} days at {per_day:+.2f}%/day.")
            print("     Past results do NOT persist — treat this as a ceiling, not a plan.")


def main() -> int:
    p = argparse.ArgumentParser(description="Backtest the FMS strategy")
    p.add_argument("--symbol", default=None, help="e.g. EURUSDm (default: first in .env)")
    p.add_argument("--days", type=int, default=30, help="history window (default 30)")
    p.add_argument("--csv", help="use a CSV instead of MT5 (time,open,high,low,close)")
    p.add_argument("--balance", type=float, default=50.0, help="starting balance")
    p.add_argument("--preset", choices=("conservative", "balanced", "aggressive"),
                   help="test a preset without changing .env")
    p.add_argument("--timeframe", help="override timeframe")
    p.add_argument("--point-value", type=float, help="money per 1.0 price move per lot")
    p.add_argument("--spread", type=float, help="spread in price units")
    args = p.parse_args()

    settings = Settings.load()
    if args.preset:
        from preset import PRESETS
        for key, value in PRESETS[args.preset].items():
            attr = key.lower()
            if hasattr(settings, attr):
                current = getattr(settings, attr)
                setattr(settings, attr, type(current)(value)
                        if not isinstance(current, str) else value)
    if args.timeframe:
        settings.timeframe = args.timeframe
    symbol = args.symbol or (settings.symbols[0] if settings.symbols else "EURUSD")

    if args.csv:
        bars = load_csv(args.csv)
        point_value = args.point_value or point_value_for(symbol)
        spread = args.spread if args.spread is not None else spread_for(symbol)
    else:
        try:
            bars, point_value, spread = load_mt5(settings, symbol,
                                                 settings.timeframe, args.days)
        except Exception as exc:
            print(f"Could not load MT5 data: {exc}", file=sys.stderr)
            print("Tip: use --csv with columns time,open,high,low,close instead.",
                  file=sys.stderr)
            return 1
        if args.point_value:
            point_value = args.point_value
        if args.spread is not None:
            spread = args.spread

    if len(bars) < 100:
        print(f"Only {len(bars)} bars — not enough to backtest.", file=sys.stderr)
        return 1

    res = run_backtest(bars, settings, symbol, args.balance, point_value, spread)
    report(res, settings, symbol, spread)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
