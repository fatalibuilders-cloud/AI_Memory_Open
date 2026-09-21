"""The daily loss limit, measured against the right number.

A live account went days without a trade. Every hour: "168 x daily loss
limit — the day's loss limit is doing its job". It was not: the limit
compared today's EQUITY against today's opening BALANCE. Balance excludes
the profit and loss of positions still open, so a float carried past
midnight was counted as a loss made today. An account holding a 2%
floating loss at midnight started every new day already over its limit,
refused every entry, and so never closed the positions that caused it.
"""

import json
from datetime import date, timedelta
from pathlib import Path
import tempfile

from fmsbot.risk import RiskManager
from tests.helpers import settings

BALANCE = 92929.45


def _risk(**over):
    env = {"DAILY_LOSS_LIMIT_PCT": 2.0, "MAX_TRADES_PER_DAY": 1200,
           "MAX_OPEN_POSITIONS": 24, "MAX_POSITIONS_PER_SYMBOL": 4,
           "COOLDOWN_SECONDS": 0, "MAX_CONSECUTIVE_LOSSES": 0}
    env.update(over)
    return RiskManager(settings(**env))


def test_a_float_carried_past_midnight_is_not_a_loss_made_today():
    """The bug, stated as the day it broke: 2% down on open positions at
    midnight, and the new day refuses its very first trade."""
    r = _risk()
    floating = -BALANCE * 0.021
    ok, why = r.can_enter("XAUUSDm", BALANCE, BALANCE + floating, 0, 0)
    assert ok, why


def test_the_day_still_stops_when_the_day_itself_loses_the_limit():
    """The limit must still do what it is for."""
    r = _risk()
    assert r.can_enter("XAUUSDm", BALANCE, BALANCE, 0, 0)[0]   # sets the base
    down = BALANCE * 0.979                                     # -2.1% today
    ok, why = r.can_enter("XAUUSDm", BALANCE, down, 0, 0)
    assert not ok and "daily loss limit" in why


def test_a_loss_taken_today_counts_whether_it_is_closed_or_floating():
    """Equity is the honest figure while positions are open: a trade
    going against you is a loss now, not when it closes."""
    r = _risk()
    r.can_enter("XAUUSDm", BALANCE, BALANCE, 0, 0)
    ok, why = r.can_enter("XAUUSDm", BALANCE, BALANCE * 0.975, 0, 0)
    assert not ok and "daily loss limit" in why


def test_the_next_day_starts_from_where_the_account_actually_is():
    """Yesterday's float is today's starting point, not today's loss."""
    r = _risk()
    floating = -BALANCE * 0.03
    r.can_enter("XAUUSDm", BALANCE, BALANCE + floating, 0, 0)
    r.stats.day = date.today() - timedelta(days=1)             # roll over

    # The same, unchanged float: a new day, and it may trade.
    ok, why = r.can_enter("XAUUSDm", BALANCE, BALANCE + floating, 0, 0)
    assert ok, why
    # And the new day's budget is measured from there.
    worse = BALANCE + floating - BALANCE * 0.021
    assert not r.can_enter("XAUUSDm", BALANCE, worse, 0, 0)[0]


def test_day_pnl_reports_against_the_same_base_the_gate_uses():
    """A figure on the phone that disagrees with the gate is worse than
    no figure: it sends the operator to fix the wrong thing."""
    r = _risk()
    r.can_enter("XAUUSDm", BALANCE, BALANCE, 0, 0)
    moved, pct = r.day_pnl(BALANCE * 0.99)
    assert abs(moved + BALANCE * 0.01) < 0.01
    assert abs(pct + 1.0) < 0.001


def test_why_always_names_the_loss_limit_not_only_when_a_target_is_set():
    """/why is the command for explaining silence, and it did not
    mention the gate that was causing it."""
    r = _risk(DAILY_PROFIT_TARGET=0, DAILY_PROFIT_FLOOR=0)
    r.can_enter("XAUUSDm", BALANCE, BALANCE, 0, 0)
    lines = r.explain(BALANCE, BALANCE * 0.975, 0, ["XAUUSDm"])
    text = "\n".join(lines)
    assert "loss limit" in text
    assert "HIT" in text


def test_why_separates_the_float_from_the_rest_of_the_day():
    """The operator needs to see that the number is open positions, not
    realised losses — those need opposite responses."""
    r = _risk()
    r.can_enter("XAUUSDm", BALANCE, BALANCE, 0, 0)
    lines = r.explain(BALANCE, BALANCE - 500.0, 0, ["XAUUSDm"])
    assert any("open positions are -500.00" in ln for ln in lines), lines


def test_a_state_file_written_before_this_field_existed_still_loads():
    """An upgrade must not read a missing start_equity as zero and
    re-open a budget the day already spent."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp, "risk.json")
        path.write_text(json.dumps({
            "day": date.today().isoformat(),
            "start_balance": BALANCE,
            "trades": 40,
        }), encoding="utf-8")
        s = settings(DAILY_LOSS_LIMIT_PCT=2.0)
        r = RiskManager(s, state_file=str(path))
        assert r.stats.start_equity == BALANCE
        assert r.stats.trades == 40
        assert not r.can_enter("XAUUSDm", BALANCE, BALANCE * 0.97, 0, 0)[0]
