#!/usr/bin/env python3
r"""Apply a tuning preset to .env.

    .\.venv\Scripts\python.exe preset.py aggressive
    .\.venv\Scripts\python.exe preset.py balanced
    .\.venv\Scripts\python.exe preset.py conservative
    .\.venv\Scripts\python.exe preset.py show

Only the keys the preset owns are rewritten; credentials and everything
else in .env are left untouched. A backup is written to .env.bak first.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PRESETS: dict[str, dict[str, str]] = {
    # Selective. Few, higher-quality trades. Survives bad weeks.
    "conservative": {
        "ENTRY_MODE": "signal",
        "TIMEFRAME": "M15",
        "EMA_FAST": "20", "EMA_SLOW": "50",
        "RSI_FLOOR": "45", "RSI_CEILING": "55",
        "ATR_SL_MULT": "1.5", "ATR_TP_MULT": "2.5",
        "FIXED_LOT": "0.01",
        "MAX_OPEN_POSITIONS": "2", "MAX_POSITIONS_PER_SYMBOL": "1",
        "MAX_TRADES_PER_DAY": "6",
        "DAILY_LOSS_LIMIT_PCT": "3",
        "COOLDOWN_SECONDS": "900",
    },
    # The shipped default.
    "balanced": {
        "ENTRY_MODE": "signal",
        "TIMEFRAME": "M5",
        "EMA_FAST": "20", "EMA_SLOW": "50",
        "RSI_FLOOR": "45", "RSI_CEILING": "55",
        "ATR_SL_MULT": "1.5", "ATR_TP_MULT": "2.0",
        "FIXED_LOT": "0.01",
        "MAX_OPEN_POSITIONS": "3", "MAX_POSITIONS_PER_SYMBOL": "1",
        "MAX_TRADES_PER_DAY": "20",
        "DAILY_LOSS_LIMIT_PCT": "5",
        "COOLDOWN_SECONDS": "300",
    },
    # Maximum realistic aggression: fast signals, more symbols, more
    # concurrent positions, tighter stops with a wider target (better
    # reward:risk), and a much looser daily stop. Still 0.01 lots, still
    # no martingale — those two are what keep a bad run survivable.
    "aggressive": {
        "ENTRY_MODE": "signal",
        "TIMEFRAME": "M1",
        "EMA_FAST": "9", "EMA_SLOW": "21",
        "RSI_FLOOR": "40", "RSI_CEILING": "60",
        "ATR_SL_MULT": "1.0", "ATR_TP_MULT": "2.5",
        "FIXED_LOT": "0.01",
        "MAX_OPEN_POSITIONS": "6", "MAX_POSITIONS_PER_SYMBOL": "2",
        "MAX_TRADES_PER_DAY": "60",
        "DAILY_LOSS_LIMIT_PCT": "15",
        "COOLDOWN_SECONDS": "60",
    },
}

PRESETS["highfreq"] = {
    # Targets ~100 trades/day across two symbols. M1 bars with very fast
    # EMAs, a wide RSI band, tight stops against a modest target, short
    # cooldown and room for several concurrent positions.
    "ENTRY_MODE": "signal",
    "TIMEFRAME": "M1",
    "EMA_FAST": "5", "EMA_SLOW": "13",
    "RSI_FLOOR": "35", "RSI_CEILING": "65",
    "ATR_SL_MULT": "1.0", "ATR_TP_MULT": "1.5",
    "FIXED_LOT": "0.01",
    "MAX_OPEN_POSITIONS": "10", "MAX_POSITIONS_PER_SYMBOL": "3",
    "MAX_TRADES_PER_DAY": "100",
    "DAILY_LOSS_LIMIT_PCT": "20",
    "COOLDOWN_SECONDS": "30",
}

PRESETS["riskfirst"] = {
    # Capital preservation > frequency > profit target.
    # The 1,000/day ceiling is a cap, never a quota: the gates below decide
    # how many trades actually happen, and most days will be far fewer.
    "ENTRY_MODE": "signal",
    "TIMEFRAME": "M5",
    "EMA_FAST": "20", "EMA_SLOW": "50",
    "RSI_FLOOR": "45", "RSI_CEILING": "55",
    "ATR_SL_MULT": "1.5", "ATR_TP_MULT": "2.0",
    "FIXED_LOT": "0.01",
    "RISK_PCT": "0.25",
    "TP_MONEY": "0.50",
    "PROFIT_STAGES": "0.10:0,0.25:0.10",
    "MAX_OPEN_POSITIONS": "5", "MAX_POSITIONS_PER_SYMBOL": "1",
    "MAX_TRADES_PER_DAY": "1000",
    "ROLLING_TRADE_WINDOW_HOURS": "24",
    "DAILY_LOSS_LIMIT_PCT": "1",
    "MAX_CONSECUTIVE_LOSSES": "3",
    "LOSS_PAUSE_MINUTES": "60",
    "MAX_SPREAD_RATIO": "0.25",
    "SPREAD_SPIKE_FACTOR": "3.0",
    "MAX_SLIPPAGE_RATIO": "0.5",
    "MIN_REWARD_COST_RATIO": "2.0",
    "COOLDOWN_SECONDS": "60",
}

NOTES = {
    "conservative": "A handful of trades a day. Slowest growth, smallest drawdowns.",
    "balanced": "The shipped default: a few trades a day per symbol.",
    "aggressive": (
        "Expect roughly 10-40 trades/day. More trades means more spread paid and\n"
        "  bigger swings BOTH ways — a bad day can now cost 15% before the daily\n"
        "  stop trips. This is the realistic ceiling; anything beyond it is\n"
        "  gambling, not aggression."
    ),
    "riskfirst": (
        "Capital preservation first: 0.25% risk, 1% daily stop, 5 positions,\n"
        "  pause after 3 losses in a row, a two-stage protective stop\n"
        "  (break-even at +$0.10, then locking +$0.10 at +$0.25), and every\n"
        "  entry gated on spread, spread stability, slippage and reward vs cost.\n"
        "  1,000 trades/day is a CEILING, not a target — expect far fewer, and\n"
        "  days with none at all when conditions do not qualify."
    ),
    "highfreq": (
        "Targets ~100 trades/day. DEMO ONLY.\n"
        "  At 0.01 lots the spread costs roughly $12-30/day: negligible on a\n"
        "  100k demo, but it would consume a $50 live account in 2-3 days before\n"
        "  the market moves at all. The daily stop is set to -20%, so a bad day\n"
        "  runs much further before the bot stops itself.\n"
        "  Measure it rather than assume: backtest.py --preset highfreq"
    ),
}


def read_env(path: Path) -> list[str]:
    if not path.is_file():
        sys.exit(f"{path} not found — run this from the fms-trading-bot folder.")
    return path.read_text(encoding="utf-8").splitlines()


def current_values(lines: list[str], keys) -> dict[str, str]:
    out = {}
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k = k.strip()
        if k in keys:
            out[k] = v.split("#")[0].strip()
    return out


def apply(lines: list[str], preset: dict[str, str]) -> tuple[list[str], list[str]]:
    """Rewrite owned keys in place; append any that are missing."""
    seen, out, changes = set(), [], []
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            key = s.partition("=")[0].strip()
            if key in preset:
                old = s.partition("=")[2].split("#")[0].strip()
                new = preset[key]
                if old != new:
                    changes.append(f"{key}: {old or '(empty)'} -> {new}")
                seen.add(key)
                out.append(f"{key}={new}")
                continue
        out.append(line)
    missing = [k for k in preset if k not in seen]
    if missing:
        out.append("")
        out.append("# --- added by preset.py ---")
        for k in missing:
            out.append(f"{k}={preset[k]}")
            changes.append(f"{k}: (not set) -> {preset[k]}")
    return out, changes


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in (*PRESETS, "show"):
        print(__doc__)
        print("Presets:", ", ".join(PRESETS))
        return 2

    env_path = Path(".env")
    lines = read_env(env_path)
    name = sys.argv[1]

    if name == "show":
        keys = set().union(*(p.keys() for p in PRESETS.values()))
        current = current_values(lines, keys)
        print("Current tuning values in .env:\n")
        for k in sorted(keys):
            print(f"  {k:26} = {current.get(k, '(not set)')}")
        matches = [n for n, p in PRESETS.items()
                   if all(current.get(k) == v for k, v in p.items())]
        print(f"\nMatches preset: {matches[0] if matches else 'none (custom)'}")
        return 0

    preset = PRESETS[name]
    new_lines, changes = apply(lines, preset)

    if not changes:
        print(f"Already on the '{name}' preset — nothing to change.")
        return 0

    shutil.copyfile(env_path, Path(".env.bak"))
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    print(f"Applied preset '{name}' ({len(changes)} change(s)); backup in .env.bak\n")
    for c in changes:
        print(f"  {c}")
    print(f"\n{NOTES[name]}")
    print("\nRestart the bot for it to take effect:")
    print("  Stop-ScheduledTask -TaskName FMSTradingBot; "
          "Start-ScheduledTask -TaskName FMSTradingBot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
