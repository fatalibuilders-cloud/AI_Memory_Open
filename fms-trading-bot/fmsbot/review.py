"""Re-examine the configuration while trading is paused.

A pause after consecutive losses is dead time that can be spent asking
whether the settings still fit the market. This does three things, and
the boundary between them is the whole design:

  * **Re-measures** each instrument's spread, volatility and minimum stop,
    and re-derives the exits from them. This is measurement, not fitting:
    there is no way for it to talk itself into a bad answer, so it is
    applied automatically.

  * **Re-tests** the CURRENT configuration over recent history and reports
    what it would have done. One configuration on one window, not a search
    over thousands -- searching and adopting the winner is how noise gets
    promoted to a strategy, which is what `find_edge.py` exists to prevent.

  * **Recommends** everything else. Dropping a symbol, changing a
    timeframe or adopting new parameters increases or redirects risk, and
    those stay decisions for a person.

The asymmetry is deliberate: an action that can only reduce exposure is
safe to take unattended; one that could increase it is not.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .config import Settings, symbol_key
from .indicators import atr
from .sim import simulate
from .tuning import solve
from .vecstrategy import VEC_STRATEGIES

log = logging.getLogger("fmsbot.review")

#: Below this many simulated trades a symbol's result is not evidence.
MIN_TRADES = 20


@dataclass
class SymbolReview:
    symbol: str
    bars: int = 0
    days: float = 0.0
    trades: int = 0
    profit_factor: float = 0.0
    net: float = 0.0
    win_rate: float = 0.0
    note: str = ""
    retune: dict[str, float] = field(default_factory=dict)


def _bar_seconds(timeframe: str) -> int:
    return {"M1": 60, "M5": 300, "M15": 900, "M30": 1800,
            "H1": 3600, "H4": 14400, "D1": 86400}.get(timeframe, 300)


def review_symbol(settings: Settings, broker, symbol: str, strategy_name: str,
                  days: int, balance: float) -> SymbolReview:
    """Measure one instrument, then replay the current settings over it."""
    out = SymbolReview(symbol=symbol)
    per_bar = _bar_seconds(settings.timeframe)
    want = min(int(days * 86400 / per_bar), 200_000)
    try:
        bars = broker.bars(symbol, settings.timeframe, want)
    except Exception as exc:
        out.note = f"no history ({str(exc)[:40]})"
        return out
    if len(bars) < 500:
        out.note = f"only {len(bars)} bars"
        return out
    out.bars = len(bars)
    out.days = (bars[-1].time - bars[0].time) / 86400.0

    # --- measurement: what does this instrument cost right now? ---------
    try:
        spread = broker.spread(symbol)
        per_price = broker.value_per_price(symbol, settings.fixed_lot or 0.01)
        floor = broker.min_stop_distance(symbol)
    except Exception:
        spread = per_price = floor = 0.0
    value = atr([b.high for b in bars], [b.low for b in bars],
                [b.close for b in bars], settings.atr_period)
    if value and value > 0 and per_price > 0 and spread > 0:
        row = solve(settings, symbol, spread, value, floor, per_price)
        cfg = settings.for_symbol(symbol)
        # Only worth changing when it is materially different.
        if cfg.atr_sl_mult > 0 and abs(row.stop_distance / value
                                       - cfg.atr_sl_mult) > cfg.atr_sl_mult * 0.2:
            out.retune["atr_sl_mult"] = round(row.stop_distance / value, 2)
            out.retune["atr_tp_mult"] = round(row.target_distance / value, 2)
        if cfg.tp_money > 0 and abs(row.target_money - cfg.tp_money) > cfg.tp_money * 0.2:
            out.retune["tp_money"] = round(row.target_money, 2)
            if cfg.sl_money > 0:
                out.retune["sl_money"] = round(row.stop_money, 2)

    # --- replay: what would these settings have done? -------------------
    cls = VEC_STRATEGIES.get(strategy_name)
    if cls is None:
        out.note = f"{strategy_name} cannot be replayed"
        return out
    try:
        result = simulate(bars, cls(settings), settings, balance,
                          per_price / (settings.fixed_lot or 0.01) if per_price else 0.0,
                          spread)
    except Exception as exc:
        out.note = f"replay failed ({str(exc)[:40]})"
        return out
    out.trades = len(result.trades)
    out.profit_factor = result.profit_factor
    out.net = result.end_balance - result.start_balance
    out.win_rate = result.win_rate
    if out.trades < MIN_TRADES:
        out.note = "too few trades to judge"
    elif out.profit_factor < 1.0:
        out.note = "LOSING over this window"
    return out


def run_review(settings: Settings, broker, symbols: list[str],
               strategy_name: str, days: int, balance: float
               ) -> tuple[list[SymbolReview], dict[str, dict[str, float]]]:
    """Review every symbol. Returns the rows and the overrides to apply."""
    rows, applied = [], {}
    for symbol in symbols:
        row = review_symbol(settings, broker, symbol, strategy_name,
                            days, balance)
        rows.append(row)
        if row.retune:
            applied[symbol_key(symbol)] = row.retune
    return rows, applied


def format_review(rows: list[SymbolReview], days: int,
                  timeframe: str, applied: dict) -> str:
    """The message sent to the phone."""
    lines = [f"🔬 Review — {timeframe}, last {days} days",
             ""]
    losing = []
    for row in sorted(rows, key=lambda r: r.profit_factor):
        if not row.bars:
            lines.append(f"{row.symbol}: {row.note}")
            continue
        pf = "inf" if row.profit_factor == float("inf") else f"{row.profit_factor:.2f}"
        lines.append(f"{row.symbol}: {row.trades} trades, PF {pf}, "
                     f"{row.win_rate:.0f}% wins, net {row.net:+.2f}")
        if row.note:
            lines.append(f"   {row.note}")
        if row.profit_factor < 1.0 and row.trades >= MIN_TRADES:
            losing.append(row.symbol)

    if applied:
        lines.append("")
        lines.append("Re-measured and applied (spreads move, so exits must):")
        for symbol, over in applied.items():
            bits = ", ".join(f"{k}={v}" for k, v in over.items())
            lines.append(f"   {symbol}: {bits}")

    lines.append("")
    if losing:
        lines.append(f"LOSING on this window: {', '.join(losing)}.")
        lines.append("I have not dropped them — a backtest is not a reason to "
                     "change what you trade, only a reason to look. Retirement "
                     "happens on REAL results (/evidence).")
    else:
        lines.append("Nothing is clearly losing on this window.")
    lines.append("")
    lines.append("Not searched for better parameters on purpose: adopting the "
                 "winner of a search is how noise becomes a strategy. "
                 "find_edge.py does that properly, with a null to beat.")
    return "\n".join(lines)
