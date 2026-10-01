"""What a $100 account can physically do.

Every order on the live $100 account was refused:

    GBPUSDm order refused — it would risk 0.96, over the 0.50 that 0.5%
    allows, and 0.01 is the smallest size the broker takes

0.5% of $100 is $0.50. The smallest trade the broker accepts is 0.01
lot, which is $0.10 a pip, so a ten-pip stop risks twice the cap. No
percentage can buy a fraction of the broker's minimum lot, and a
configuration that asks it to will refuse every trade forever.
"""

import preset
from tests.helpers import settings

BALANCE = 100.0
PIP_VALUE = 0.10          # 0.01 lot, USD-quoted pair, per pip
#: Stop distances the sweep actually produced, from the refusal messages.
LIVE_STOPS = (9.6, 15.5, 52.3)


def _micro(**over):
    env = {k: v for k, v in preset.PRESETS["micro"].items()}
    env.update(over)
    return settings(**env)


def test_the_live_refusal_is_reproduced_by_the_old_settings():
    """0.5% of $100 cannot pay for the broker's smallest trade."""
    allowed = BALANCE * 0.5 / 100
    assert allowed == 0.50
    for pips in LIVE_STOPS:
        assert pips * PIP_VALUE > allowed, pips


def test_the_micro_preset_turns_the_percentage_gate_off():
    """With a fixed lot the risk-percentage refusal cannot fire — the
    size is already the broker's floor, so there is nothing to shrink."""
    s = _micro()
    assert s.fixed_lot == 0.01


def test_the_cap_is_set_in_money_and_admits_the_ordinary_stops():
    s = _micro()
    cap = s.max_loss_per_trade
    assert cap > 0, "something must still bound one trade"
    assert 9.6 * PIP_VALUE <= cap and 15.5 * PIP_VALUE <= cap
    assert 52.3 * PIP_VALUE > cap, "the widest stop should still be refused"


def test_the_daily_limit_admits_at_least_two_trades():
    """2% of $100 is $2, and the smallest possible trade risks more than
    that — a 2% limit would refuse the day's first entry."""
    s = _micro()
    budget = BALANCE * s.daily_loss_limit_pct / 100
    assert budget >= 2 * s.max_loss_per_trade, budget


def test_the_trade_cap_fits_the_daily_budget():
    """The mismatch that showed 9/1200 on the phone for days."""
    s = _micro()
    budget = BALANCE * s.daily_loss_limit_pct / 100
    assert s.max_trades_per_day <= budget / s.max_loss_per_trade + 1


def test_a_month_produces_enough_trades_for_a_verdict():
    """Four a day over twenty trading days is eighty — above the
    evidence gate's minimum, which is the point of the month."""
    s = _micro()
    assert s.max_trades_per_day * 20 >= s.evidence_min_trades


def test_the_account_keeps_scoring_itself_and_stops_when_it_loses():
    s = _micro()
    assert s.halt_on_failed_evidence
    assert s.evidence_min_trades >= 30


def test_gold_is_not_in_a_hundred_dollar_account():
    """0.01 lot of gold is one ounce; a structural stop risks $5-15,
    which is a seventh of the account on one trade."""
    assert "XAUUSD" not in preset.PRESETS["micro"]["SYMBOLS"]


def test_the_note_says_demo_and_says_why_the_numbers_look_wrong():
    note = preset.NOTES["micro"]
    assert "DEMO" in note
    assert "0.01 lot" in note
    assert "no edge at all" in note, "the variance warning must be there"
