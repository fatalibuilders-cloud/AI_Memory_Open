"""A daily profit target, and dropping instruments that lose.

The live record was the argument for the second: metals were 8% of the
trades and 77% of the losses. Halting the whole account is too blunt;
waiting for the whole account to be convicted is too slow.
"""

import tempfile
from pathlib import Path

from fmsbot.evidence import FAILED, PROVING, Evidence
from fmsbot.risk import RiskManager

from .helpers import FakeBroker, make_bot, settings

TMP = Path(tempfile.mkdtemp())


def test_trading_stops_once_the_daily_target_is_banked():
    s = settings(SYMBOLS="EURUSDm", DAILY_PROFIT_TARGET=1000,
                 DAILY_LOSS_LIMIT_PCT=2)
    r = RiskManager(s)
    start = 100000.0
    ok, _ = r.can_enter("EURUSDm", start, start, 0, 0)
    assert ok, "should trade at the start of the day"

    ok, why = r.can_enter("EURUSDm", start, start + 999.0, 0, 0)
    assert ok, f"999 of a 1000 target should still trade: {why}"

    ok, why = r.can_enter("EURUSDm", start, start + 1000.0, 0, 0)
    assert not ok and "target reached" in why, why


def test_the_target_is_off_by_default():
    s = settings(SYMBOLS="EURUSDm")
    r = RiskManager(s)
    ok, _ = r.can_enter("EURUSDm", 100000.0, 1_000_000.0, 0, 0)
    assert ok, "no target set means no ceiling on the day"


def test_the_daily_floor_is_reported_never_enforced():
    """No setting can make the market pay. A floor is a report, not a gate."""
    s = settings(SYMBOLS="EURUSDm", DAILY_PROFIT_FLOOR=100)
    r = RiskManager(s)
    start = 100000.0
    ok, _ = r.can_enter("EURUSDm", start, start - 50.0, 0, 0)
    assert ok, "being below the floor must never block trading"
    lines = r.explain(start, start - 50.0, 0, ["EURUSDm"])
    assert any("floor 100" in line for line in lines)


def _ev(name):
    return Evidence.load(TMP / f"{name}.json", "fp", min_trades=30, alpha=0.01)


def test_a_losing_instrument_is_convicted_on_its_own_record():
    e = _ev("split")
    for _ in range(40):
        e.record(0.50, "EURUSDm")      # a steady winner
        e.record(-0.90, "XAGUSDm")     # a steady loser
    assert e.symbol_verdict("XAGUSDm") == FAILED
    assert e.symbol_verdict("EURUSDm") != FAILED


def test_an_instrument_with_too_few_trades_is_left_alone():
    e = _ev("young")
    for _ in range(10):
        e.record(-0.90, "XAGUSDm")
    assert e.symbol_verdict("XAGUSDm") == PROVING, "10 trades is not a verdict"


def test_the_summary_is_ordered_worst_first():
    e = _ev("summary")
    for _ in range(40):
        e.record(0.50, "EURUSDm")
        e.record(-0.90, "XAGUSDm")
        e.record(0.01, "GBPUSDm")
    rows = e.symbol_summary()
    assert [r[0] for r in rows][0] == "XAGUSDm", rows
    assert rows[0][4] == FAILED


def test_a_retired_symbol_stops_trading_and_the_rest_carry_on():
    s = settings(SYMBOLS="EURUSDm,XAGUSDm", TIMEFRAME="M5", FIXED_LOT=0.01)
    b = FakeBroker(price=1.166, per_price=1000.0)
    ev = _ev("retire")
    for _ in range(40):
        ev.record(0.50, "EURUSDm")
        ev.record(-0.90, "XAGUSDm")
    bot, session, msgs = make_bot(s, b, ["EURUSDm", "XAGUSDm"], evidence=ev)

    bot._retire_losing_symbol(session, "XAGUSDm")
    assert "XAGUSDm" in session.disabled_symbols
    assert any("RETIRED" in m for m in msgs)
    assert session.active_symbols() == ["EURUSDm"], session.active_symbols()

    bot._retire_losing_symbol(session, "EURUSDm")
    assert "EURUSDm" not in session.disabled_symbols, "retired a winner"


def test_retiring_is_announced_once_not_every_loop():
    s = settings(SYMBOLS="XAGUSDm", TIMEFRAME="M5", FIXED_LOT=0.01)
    ev = _ev("once")
    for _ in range(40):
        ev.record(-0.90, "XAGUSDm")
    bot, session, msgs = make_bot(s, FakeBroker(), ["XAGUSDm"], evidence=ev)
    for _ in range(5):
        bot._retire_losing_symbol(session, "XAGUSDm")
    assert sum("RETIRED" in m for m in msgs) == 1, msgs


def test_the_per_symbol_record_survives_a_restart():
    e = _ev("persist")
    for _ in range(5):
        e.record(-1.0, "XAUUSDm")
    again = Evidence.load(TMP / "persist.json", "fp")
    assert again.by_symbol.get("XAUUSDm") == [-1.0] * 5
