#!/usr/bin/env python3
r"""Measure each instrument and derive settings that suit it.

    .\.venv\Scripts\python.exe tune_symbols.py
    .\.venv\Scripts\python.exe tune_symbols.py --apply

Gold, Bitcoin and forex differ by two orders of magnitude in spread and
volatility, so one shared setting cannot fit them. A $0.50 target is four
times the spread on EURUSD, roughly the spread on gold, and a rounding
error on Bitcoin — which is why the live account lost far more per trade
on metals than on forex.

For each symbol this reads the real spread, ATR and minimum stop distance
from the terminal, then solves for values that pass the bot's own filters
by construction:

  * a stop wide enough that the spread is at most MAX_SPREAD_RATIO of it,
    and never below the broker's minimum stop distance
  * a target that clears the round-trip cost by MIN_REWARD_COST_RATIO
    while keeping the configured reward:risk
  * protective stages scaled to that instrument's money-per-point

It writes only the kinds of setting the configuration already uses: cash
targets if the bot is running on cash targets, ATR multiples if it is
running on ATR multiples. It never switches you between the two.

Stop the bot before running this: two processes sharing one MT5 terminal
interfere.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from fmsbot.config import Settings, symbol_key
from fmsbot.indicators import atr

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


def env_lines_for(settings: Settings, row: Row) -> dict[str, object]:
    """The settings to write for one instrument, in the mode already in use."""
    key = symbol_key(row.symbol)
    out: dict[str, object] = {}

    def put(name: str, value: float, places: int = 2) -> None:
        out[f"SYM_{key}_{name.upper()}"] = round(value, places)

    # Always safe: the ATR multiples describe the same distances, and are
    # what the strategy falls back to when no cash target is configured.
    if row.atr > 0:
        put("atr_sl_mult", row.stop_distance / row.atr)
        put("atr_tp_mult", row.target_distance / row.atr)

    # Cash targets only if the configuration is already using them —
    # switching a symbol from ATR stops to fixed cash stops behind the
    # user's back would change the strategy, not tune it.
    if row.per_price > 0:
        if settings.sl_money > 0:
            put("sl_money", row.stop_money)
        if settings.tp_money > 0:
            put("tp_money", row.target_money)
        if settings.tp_runner_money > 0:
            put("tp_runner_money", row.target_money * (
                settings.tp_runner_money / settings.tp_money
                if settings.tp_money > 0 else 4.0))

        # Break-even stages are cash by nature, so they always need scaling:
        # $0.25 is half a EURUSD target and rounding error on Bitcoin. The
        # ladder keeps its shape — each rung stays the same fraction of the
        # target it was — so the protection behaves the same way everywhere.
        stages = settings.stages()
        if stages:
            scale = ladder_scale(settings, row)
            scaled = [(round(t * scale, 3), round(l * scale, 3))
                      for t, l in stages]
            if len(scaled) > 1:
                out[f"SYM_{key}_PROFIT_STAGES"] = ",".join(
                    f"{t}:{l}" for t, l in scaled)
            else:
                out[f"SYM_{key}_BREAKEVEN_AT_MONEY"] = scaled[0][0]
                out[f"SYM_{key}_BREAKEVEN_LOCK_MONEY"] = scaled[0][1]
    return out


def ladder_scale(settings: Settings, row: Row) -> float:
    """How much to stretch the protection ladder for this instrument.

    Rungs are set relative to the target when there is one, so a rung that
    sat at half the target still sits at half the target. Without a cash
    target there is nothing to be relative to, so the stop distance stands
    in for it.
    """
    if settings.tp_money > 0:
        return row.target_money / settings.tp_money
    if settings.sl_money > 0:
        return row.stop_money / settings.sl_money
    return 1.0


def report_risk(settings: Settings, broker, rows: list[Row], lot: float) -> None:
    """Check the derived stops against the account that has to absorb them.

    Tuning an instrument to its own spread says nothing about whether you
    can afford to trade it. Lot sizes have a floor — 0.01 is usually the
    smallest — so on gold, where one bar routinely moves several dollars
    per 0.01 lot, the smallest possible position can still risk more in a
    single trade than the account is allowed to lose in a day. That is a
    property of the instrument and the balance, and no setting fixes it.
    """
    try:
        balance = broker.balance()
    except Exception:
        return
    if balance <= 0:
        return

    limit = settings.risk_pct if settings.risk_pct > 0 else 0.5
    daily = settings.daily_loss_limit_pct if settings.daily_loss_limit_pct > 0 else 3.0
    daily_budget = balance * daily / 100.0

    print("\n" + "=" * 78)
    print(f"RISK AT YOUR BALANCE — ${balance:,.2f}, {lot} lot, "
          f"{limit}% per trade, {daily}% daily cap")
    print("=" * 78)
    print(f"\n{'symbol':16} {'stop $':>9} {'% of bal':>9} {'stops/day':>10} "
          f"{'balance needed':>15}")
    print("-" * 78)

    unaffordable = []
    for row in rows:
        share = row.stop_money / balance * 100.0
        stops = daily_budget / row.stop_money if row.stop_money > 0 else 0.0
        needed = row.stop_money / (limit / 100.0)
        mark = ""
        if share > limit:
            mark = "  << over your limit"
            unaffordable.append((row, needed))
        print(f"{row.symbol:16} {row.stop_money:9.2f} {share:8.2f}% "
              f"{stops:10.1f} {needed:14,.0f}{mark}")

    if not unaffordable:
        print(f"\n  Every instrument fits inside {limit}% per trade at {lot} lot.")
        return

    print(f"\n  {len(unaffordable)} instrument(s) cannot obey your own "
          f"{limit}%-per-trade rule at")
    print(f"  {lot} lot, because that is the smallest position the broker "
          f"will accept.")
    for row, needed in unaffordable:
        stops = daily_budget / row.stop_money if row.stop_money > 0 else 0.0
        if stops < 1:
            print(f"    {row.symbol}: one stop is ${row.stop_money:.2f}, more than "
                  f"the ${daily_budget:.2f} you allow")
            print("      yourself to lose in a whole day. A single losing trade "
                  "ends the day.")
        else:
            print(f"    {row.symbol}: ${row.stop_money:.2f} per stop is "
                  f"{row.stop_money / balance * 100:.1f}% of the account; the rule "
                  f"needs ${needed:,.0f}.")
    print("\n  This is not a settings problem and tuning cannot solve it: the")
    print("  position is already as small as the broker allows. Either fund the")
    print("  account to the size the instrument requires, or remove it from")
    print("  SYMBOLS and trade what the balance can carry.")


def main() -> int:
    p = argparse.ArgumentParser(description="Derive per-symbol settings")
    p.add_argument("--account", help="which account, when several are configured")
    p.add_argument("--apply", action="store_true", help="write them into .env")
    p.add_argument("--bars", type=int, default=300)
    args = p.parse_args()

    settings = Settings.load()
    configs = settings.broker_configs()
    cfg = configs[0]
    if args.account:
        matches = [c for c in configs if c.name.lower() == args.account.lower()]
        if not matches:
            names = ", ".join(c.name for c in configs)
            print(f"No account '{args.account}'. Configured: {names}", file=sys.stderr)
            return 1
        cfg = matches[0]

    from fmsbot.broker import build_broker_from_config
    broker = build_broker_from_config(cfg)
    broker.connect()
    try:
        lot = settings.fixed_lot or 0.01
        print("=" * 78)
        print(f"PER-SYMBOL TUNING — {cfg.name}, {settings.timeframe}, {lot} lot")
        print("=" * 78)
        if not settings.fixed_lot:
            print("  FIXED_LOT is unset, so size follows risk and the cash figures")
            print(f"  below assume {lot} lot. They scale with whatever you trade.")
        print(f"\n{'symbol':16} {'spread':>10} {'ATR':>10} {'sprd/ATR':>9} "
              f"{'stop $':>9} {'target $':>9} {'cost $':>8}")
        print("-" * 78)

        rows: list[Row] = []
        for symbol in cfg.symbols:
            try:
                bars = broker.bars(symbol, settings.timeframe, args.bars)
                spread = broker.spread(symbol)
                per_price = broker.value_per_price(symbol, lot)
                floor = broker.min_stop_distance(symbol)
            except Exception as exc:
                print(f"{symbol:16} unavailable: {str(exc)[:44]}")
                continue
            a = atr([b.high for b in bars], [b.low for b in bars],
                    [b.close for b in bars], settings.atr_period)
            if not a or a <= 0:
                print(f"{symbol:16} no volatility reading — is the market open?")
                continue
            if per_price <= 0:
                print(f"{symbol:16} broker gave no tick value; cannot price it")
                continue
            row = solve(settings, symbol, spread, a, floor, per_price)
            rows.append(row)
            mark = "  << spread too wide" if row.untradeable else ""
            print(f"{symbol:16} {spread:10.5f} {a:10.5f} {row.spread_atr:8.2f}x "
                  f"{row.stop_money:9.2f} {row.target_money:9.2f} "
                  f"{row.cost:8.3f}{mark}")

        if not rows:
            print("\nNothing measurable — is the market open and MT5 logged in?")
            return 1

        print("\n" + "=" * 78)
        print("DERIVED SETTINGS")
        print("=" * 78)
        env_lines: list[str] = []
        for row in rows:
            derived = env_lines_for(settings, row)
            if not derived:
                continue
            print(f"\n  {row.symbol}")
            for var, value in derived.items():
                print(f"    {var}={value}")
                env_lines.append(f"{var}={value}")

        report_risk(settings, broker, rows, lot)

        worst = max(rows, key=lambda r: r.spread_atr)
        print(f"\n  Widest spread relative to movement: {worst.symbol} at "
              f"{worst.spread_atr:.2f}x ATR.")
        bad = [r.symbol for r in rows if r.untradeable]
        if bad:
            print(f"  Marked too wide: {', '.join(bad)}. The spread there is over "
                  f"{UNTRADEABLE_SPREAD_ATR:.0%} of")
            print( "  a normal bar's range, so a stop wide enough to survive it makes")
            print( "  each trade risk more than the move is worth. Drop these from")
            print( "  SYMBOLS, or trade them on a slower timeframe where ATR is larger.")
        else:
            print("  No instrument's spread is unreasonable at this timeframe.")

        if not env_lines:
            print("\nNothing to write: no cash targets or ATR multiples are in use.")
            return 0

        if not args.apply:
            print("\nRe-run with --apply to write these into .env.")
            return 0

        env_path = Path(".env")
        if not env_path.exists():
            print("\nNo .env in this directory — run this from the bot folder.",
                  file=sys.stderr)
            return 1
        existing = env_path.read_text(encoding="utf-8").splitlines()
        kept = [l for l in existing
                if not re.match(r"^\s*SYM_[A-Z0-9]+_", l.strip().upper())
                and l.strip() != "# --- per-symbol tuning (tune_symbols.py) ---"]
        while kept and not kept[-1].strip():
            kept.pop()
        shutil.copyfile(env_path, Path(".env.bak"))
        env_path.write_text(
            "\n".join(kept + ["", "# --- per-symbol tuning (tune_symbols.py) ---"]
                      + env_lines) + "\n", encoding="utf-8")
        print(f"\nWrote {len(env_lines)} per-symbol setting(s) to .env "
              f"(backup in .env.bak).")
        print("Restart the bot to apply:  .\\update.ps1")
        return 0
    finally:
        broker.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
