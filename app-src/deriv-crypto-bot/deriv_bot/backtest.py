"""Backtesting: replay historical candles through the live strategy and risk code.

    python -m deriv_bot.backtest --symbol cryBTCUSD --days 30
    python -m deriv_bot.backtest --from-file candles.json --symbol cryBTCUSD

The point of this module is to drive the *same* `strategy.evaluate` and
`risk.RiskManager` the live bot uses, over a trailing window of exactly
`CANDLE_COUNT` candles — which is what the live bot fetches each cycle. A
result here therefore reflects the bot's real decision path, not a
reimplementation of it.

READ THIS BEFORE TRUSTING A NUMBER IT PRINTS
--------------------------------------------
The simulation has one large, unavoidable assumption: **the payout ratio**.
Deriv prices each contract at purchase time from the symbol's live volatility,
and that price is not recoverable from historical candles. The backtest
therefore applies one fixed ratio to every trade (`--payout-ratio`, default
0.85). Real payouts vary trade to trade, so results are indicative of the
*strategy's directional edge*, not a forecast of account balance.

Three further gaps, all in the optimistic direction:
  * no spread or slippage is modelled,
  * a contract is settled from the candle close at expiry, ignoring intra-candle
    movement,
  * an exact tie (exit equals entry) is scored as a loss, which matches Deriv's
    Rise/Fall rules but is applied against candle closes rather than ticks.

Treat a backtest that barely clears breakeven as a losing strategy.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .config import Config, ConfigError
from .indicators import Candle
from .market import duration_seconds, parse_duration
from .risk import RiskManager
from .state import StateStore
from .strategy import evaluate

log = logging.getLogger(__name__)


@dataclass
class SimulatedTrade:
    symbol: str
    direction: str
    entry_epoch: int
    exit_epoch: int
    entry_price: float
    exit_price: float
    stake: float
    profit: float
    reason: str

    @property
    def won(self) -> bool:
        return self.profit > 0


@dataclass
class BacktestResult:
    symbol: str
    candles: int
    starting_balance: float
    payout_ratio: float
    trades: list[SimulatedTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    halted_days: int = 0
    signals_suppressed: int = 0

    # -- derived statistics ------------------------------------------------

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.won)

    @property
    def losses(self) -> int:
        return len(self.trades) - self.wins

    @property
    def win_rate(self) -> float:
        return (self.wins / len(self.trades) * 100) if self.trades else 0.0

    @property
    def breakeven_win_rate(self) -> float:
        """The win rate below which this payout ratio guarantees a loss."""
        return 100.0 / (1.0 + self.payout_ratio)

    @property
    def total_pnl(self) -> float:
        return sum(t.profit for t in self.trades)

    @property
    def ending_balance(self) -> float:
        return self.starting_balance + self.total_pnl

    @property
    def return_pct(self) -> float:
        if self.starting_balance <= 0:
            return 0.0
        return self.total_pnl / self.starting_balance * 100

    @property
    def gross_profit(self) -> float:
        return sum(t.profit for t in self.trades if t.profit > 0)

    @property
    def gross_loss(self) -> float:
        return abs(sum(t.profit for t in self.trades if t.profit < 0))

    @property
    def profit_factor(self) -> float:
        """Gross profit divided by gross loss. Below 1.0 loses money."""
        return self.gross_profit / self.gross_loss if self.gross_loss else float("inf")

    @property
    def max_drawdown(self) -> float:
        """Largest peak-to-trough fall in account equity, in currency."""
        peak = self.starting_balance
        worst = 0.0
        for value in self.equity_curve:
            peak = max(peak, value)
            worst = max(worst, peak - value)
        return worst

    @property
    def max_drawdown_pct(self) -> float:
        return (self.max_drawdown / self.starting_balance * 100) if self.starting_balance else 0.0

    @property
    def longest_losing_streak(self) -> int:
        longest = current = 0
        for trade in self.trades:
            current = 0 if trade.won else current + 1
            longest = max(longest, current)
        return longest

    @property
    def span_days(self) -> float:
        if len(self.trades) < 2:
            return 0.0
        return (self.trades[-1].exit_epoch - self.trades[0].entry_epoch) / 86400


def _candles_per_contract(config: Config) -> int:
    """How many candles a contract spans. Tick durations cannot be simulated."""
    if config.trade_duration_unit == "t":
        raise ConfigError(
            "backtesting requires a time-based TRADE_DURATION_UNIT (s/m/h/d); "
            "tick durations cannot be mapped onto candles"
        )
    seconds = duration_seconds(config.trade_duration, config.trade_duration_unit)
    assert seconds is not None
    if seconds < config.candle_granularity:
        raise ConfigError(
            f"TRADE_DURATION ({seconds}s) is shorter than one candle "
            f"({config.candle_granularity}s) — cannot resolve the outcome"
        )
    return max(1, seconds // config.candle_granularity)


def simulate(
    symbol: str,
    candles: list[Candle],
    config: Config,
    *,
    starting_balance: float = 1000.0,
    payout_ratio: float = 0.85,
) -> BacktestResult:
    """Replay `candles` through the live strategy and risk code."""
    span = _candles_per_contract(config)
    result = BacktestResult(
        symbol=symbol,
        candles=len(candles),
        starting_balance=starting_balance,
        payout_ratio=payout_ratio,
    )

    store = StateStore("", "", persist=False)
    risk = RiskManager(config, store)
    balance = starting_balance
    # exit index -> (trade-in-progress fields)
    pending: dict[int, dict] = {}
    seen_halts: set[str] = set()

    warmup = config.ema_slow + max(config.rsi_period, config.atr_period) + 2
    for i in range(warmup, len(candles)):
        candle = candles[i]
        moment = datetime.fromtimestamp(candle.epoch, tz=timezone.utc)

        # --- settle anything expiring on this candle ----------------------
        if i in pending:
            position = pending.pop(i)
            exit_price = candle.close
            entry_price = position["entry_price"]
            if position["direction"] == "CALL":
                won = exit_price > entry_price
            else:
                won = exit_price < entry_price
            profit = position["stake"] * payout_ratio if won else -position["stake"]

            balance += profit
            store.record_settlement(profit, {})
            result.equity_curve.append(balance)
            result.trades.append(
                SimulatedTrade(
                    symbol=symbol,
                    direction=position["direction"],
                    entry_epoch=position["entry_epoch"],
                    exit_epoch=candle.epoch,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    stake=position["stake"],
                    profit=profit,
                    reason=position["reason"],
                )
            )

        # --- limits, evaluated on simulated time --------------------------
        risk.refresh_daily_limits(moment)
        if store.daily.halted:
            if store.daily.day not in seen_halts:
                seen_halts.add(store.daily.day)
                result.halted_days += 1
            continue

        # --- signal, over the same trailing window the live bot fetches ----
        window = candles[max(0, i + 1 - config.candle_count) : i + 1]
        signal = evaluate(symbol, window, config)
        if not signal.is_trade:
            continue

        open_symbols = {p["symbol"] for p in pending.values()}
        decision = risk.check(
            symbol,
            balance=balance,
            open_trades=len(pending),
            open_symbols=open_symbols,
            now=float(candle.epoch),
        )
        if not decision.allowed:
            result.signals_suppressed += 1
            continue

        exit_index = i + span
        if exit_index >= len(candles):
            break  # not enough history left to resolve this contract

        pending[exit_index] = {
            "symbol": symbol,
            "direction": signal.direction,
            "entry_epoch": candle.epoch,
            "entry_price": candle.close,
            "stake": decision.stake,
            "reason": signal.reason,
        }
        risk.note_trade(symbol, now=float(candle.epoch))
        store.record_open({})

    return result


def format_report(result: BacktestResult, config: Config) -> str:
    """A plain-text summary, written to be read rather than parsed."""
    lines: list[str] = []
    add = lines.append

    add("=" * 62)
    add(f"  BACKTEST — {result.symbol}")
    add("=" * 62)
    add("")
    add(f"  Candles replayed     {result.candles:,} @ {config.candle_granularity}s")
    if result.span_days:
        add(f"  Period covered       {result.span_days:.1f} days")
    add(
        f"  Strategy             EMA {config.ema_fast}/{config.ema_slow}, "
        f"RSI {config.rsi_period} ({config.rsi_lower:g}-{config.rsi_upper:g}), "
        f"ATR sep {config.min_separation_atr:g}x"
    )
    add(f"  Contract             {config.trade_duration}{config.trade_duration_unit}")
    add(f"  Assumed payout       {result.payout_ratio:.2f}x stake on a win")
    add("")

    if not result.trades:
        add("  No trades were taken.")
        add("")
        add("  The filters may be too strict for this data, or the sample is")
        add("  too short. Try more candles, or lower MIN_SEPARATION_ATR.")
        add("=" * 62)
        return "\n".join(lines)

    add("-" * 62)
    add("  RESULTS")
    add("-" * 62)
    add(f"  Trades               {len(result.trades)}  ({result.wins}W / {result.losses}L)")
    add(f"  Win rate             {result.win_rate:.1f}%")
    add(f"  Breakeven win rate   {result.breakeven_win_rate:.1f}%   <-- must beat this")
    add("")
    add(f"  Starting balance     {result.starting_balance:,.2f}")
    add(f"  Ending balance       {result.ending_balance:,.2f}")
    add(f"  Net P&L              {result.total_pnl:+,.2f}  ({result.return_pct:+.1f}%)")
    add("")
    add(f"  Profit factor        {result.profit_factor:.2f}")
    add(f"  Max drawdown         {result.max_drawdown:,.2f} ({result.max_drawdown_pct:.1f}%)")
    add(f"  Longest losing run   {result.longest_losing_streak}")
    if result.span_days >= 1:
        add(f"  Trades per day       {len(result.trades) / result.span_days:.1f}")
    add("")
    add(f"  Signals suppressed   {result.signals_suppressed} (by risk limits)")
    add(f"  Days halted early    {result.halted_days} (daily loss limit)")
    add("")

    add("-" * 62)
    add("  VERDICT")
    add("-" * 62)
    margin = result.win_rate - result.breakeven_win_rate
    if result.total_pnl <= 0:
        add("  LOSS. This configuration lost money over this period.")
    elif margin < 2.0:
        add("  MARGINAL. Profitable here, but within noise of breakeven —")
        add("  a small change in real payouts would erase it.")
    else:
        add(f"  PROFITABLE over this period, {margin:.1f} points above breakeven.")
    add("")
    add("  One period is not evidence. Re-run across different months and")
    add("  symbols before drawing any conclusion, and remember the payout")
    add("  ratio above is an assumption, not a measurement.")
    add("=" * 62)
    return "\n".join(lines)


# -- data loading ---------------------------------------------------------


def load_candles(path: str) -> list[Candle]:
    """Load candles from a JSON array or a JSON-Lines file."""
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read().strip()
    if not text:
        return []
    if text[0] == "[":
        raw = json.loads(text)
    else:
        raw = [json.loads(line) for line in text.splitlines() if line.strip()]
    candles = [Candle.from_api(entry) for entry in raw]
    candles.sort(key=lambda c: c.epoch)
    return candles


async def fetch_candles(config: Config, symbol: str, wanted: int) -> list[Candle]:
    """Download candles from Deriv, paginating backwards from now.

    Deriv caps a single ticks_history response, so longer histories are
    assembled by walking `end` backwards until enough candles are collected.
    """
    from .api import DerivAPI

    api = DerivAPI(config)
    collected: dict[int, Candle] = {}
    try:
        await api.connect()
        end: int | str = "latest"
        while len(collected) < wanted:
            batch = await api.send(
                {
                    "ticks_history": symbol,
                    "style": "candles",
                    "granularity": config.candle_granularity,
                    "count": min(5000, wanted - len(collected)),
                    "end": end,
                }
            )
            rows = batch.get("candles", [])
            if not rows:
                break
            before = len(collected)
            for entry in rows:
                candle = Candle.from_api(entry)
                collected[candle.epoch] = candle
            if len(collected) == before:
                break  # Deriv returned only candles we already had
            end = min(collected) - config.candle_granularity
            log.info("fetched %d/%d candles", len(collected), wanted)
    finally:
        await api.close()

    return [collected[epoch] for epoch in sorted(collected)]


# -- CLI ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m deriv_bot.backtest",
        description="Replay historical candles through the bot's strategy and risk rules.",
        epilog="Results are indicative only — see the module docstring for the assumptions.",
    )
    parser.add_argument("--symbol", default="cryBTCUSD", help="crypto symbol (default: cryBTCUSD)")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--from-file", help="load candles from a JSON or JSONL file")
    source.add_argument("--days", type=float, help="fetch this many days of history from Deriv")
    parser.add_argument("--balance", type=float, default=1000.0, help="starting balance")
    parser.add_argument(
        "--payout-ratio",
        type=float,
        default=0.85,
        help="assumed profit per unit staked on a win (default: 0.85)",
    )
    parser.add_argument("--save-candles", help="write fetched candles to this file for reuse")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def _as_json(result: BacktestResult) -> str:
    return json.dumps(
        {
            "symbol": result.symbol,
            "candles": result.candles,
            "trades": len(result.trades),
            "wins": result.wins,
            "losses": result.losses,
            "win_rate": round(result.win_rate, 2),
            "breakeven_win_rate": round(result.breakeven_win_rate, 2),
            "starting_balance": result.starting_balance,
            "ending_balance": round(result.ending_balance, 2),
            "total_pnl": round(result.total_pnl, 2),
            "return_pct": round(result.return_pct, 2),
            "profit_factor": None
            if result.profit_factor == float("inf")
            else round(result.profit_factor, 3),
            "max_drawdown": round(result.max_drawdown, 2),
            "max_drawdown_pct": round(result.max_drawdown_pct, 2),
            "longest_losing_streak": result.longest_losing_streak,
            "signals_suppressed": result.signals_suppressed,
            "halted_days": result.halted_days,
            "payout_ratio": result.payout_ratio,
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)-7s %(message)s", stream=sys.stderr
    )

    try:
        if args.from_file:
            config = _config_for_backtest()
            candles = load_candles(args.from_file)
        elif args.days:
            config = Config.from_env()
            wanted = int(args.days * 86400 / config.candle_granularity)
            candles = asyncio.run(fetch_candles(config, args.symbol, wanted))
            if args.save_candles:
                with open(args.save_candles, "w", encoding="utf-8") as handle:
                    json.dump(
                        [
                            {
                                "epoch": c.epoch,
                                "open": c.open,
                                "high": c.high,
                                "low": c.low,
                                "close": c.close,
                            }
                            for c in candles
                        ],
                        handle,
                    )
                log.info("saved %d candles to %s", len(candles), args.save_candles)
        else:
            build_parser().print_help()
            print("\nGive it data: --from-file candles.json, or --days 30 to fetch.")
            return 2
    except ConfigError as exc:
        log.error("configuration error: %s", exc)
        return 2
    except FileNotFoundError as exc:
        log.error("no such file: %s", exc.filename)
        return 2

    if not candles:
        log.error("no candles to replay")
        return 1

    try:
        result = simulate(
            args.symbol,
            candles,
            config,
            starting_balance=args.balance,
            payout_ratio=args.payout_ratio,
        )
    except ConfigError as exc:
        log.error("%s", exc)
        return 2

    print(_as_json(result) if args.json else format_report(result, config))
    return 0


def _config_for_backtest() -> Config:
    """Config for a file-based backtest, which needs no live credentials."""
    os.environ.setdefault("DERIV_APP_ID", "0")
    os.environ.setdefault("DERIV_API_TOKEN", "backtest")
    return Config.from_env()


if __name__ == "__main__":
    raise SystemExit(main())
