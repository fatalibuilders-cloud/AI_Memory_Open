"""Turning "I want 1000 trades a day" into exits that deliver it.

The target was set four times and never solved. It is not a setting:

    trades/day = open positions x minutes in the day / minutes per trade

and the minutes per trade are decided by where the stop and target sit.
Demanding more trades pushes the exits together; the spread does not move
with them. That is the whole tension, and it has an arithmetic answer.
"""

from rate import (exits_for_hold, hold_minutes, per_bar_move,
                  required_win_rate)
from fmsbot.broker.base import Bar


def test_the_live_configuration_cannot_reach_a_thousand():
    """6 symbols, one position each, 24h: 8.6 minutes per trade."""
    assert abs(hold_minutes(1000, 6) - 8.64) < 0.01


def test_more_slots_buy_longer_trades_proportionally():
    assert hold_minutes(1000, 24) == 4 * hold_minutes(1000, 6)


def test_a_shorter_session_squeezes_every_trade():
    """Trading only the London/New York overlap is 9 hours, not 24."""
    assert hold_minutes(1000, 24, hours_open=9) < hold_minutes(1000, 24)


def test_an_impossible_target_returns_a_hold_no_trade_can_survive():
    assert hold_minutes(100_000, 6) < 1.0


def test_no_target_is_not_a_division_by_zero():
    assert hold_minutes(0, 6) == 0.0
    assert hold_minutes(1000, 0) == 0.0


# -- exits that produce a given hold ----------------------------------

def test_a_shorter_hold_demands_a_tighter_stop():
    long_stop, _ = exits_for_hold(300, 0.0001, 3.0)
    short_stop, _ = exits_for_hold(12, 0.0001, 3.0)
    assert short_stop < long_stop


def test_the_hold_scales_as_the_square_of_the_stop():
    """E[T] = stop x target / sigma^2, so four times the hold is twice
    the stop — which is why demanding ten times the trades does not cost
    ten times the room."""
    a, _ = exits_for_hold(100, 0.0001, 3.0)
    b, _ = exits_for_hold(400, 0.0001, 3.0)
    assert abs(b / a - 2.0) < 1e-9


def test_the_target_keeps_the_reward_to_risk_asked_for():
    for rr in (1.5, 2.0, 3.0):
        stop, target = exits_for_hold(50, 0.0001, rr)
        assert abs(target / stop - rr) < 1e-9


def test_a_market_that_does_not_move_produces_no_exits():
    assert exits_for_hold(50, 0.0, 3.0) == (0.0, 0.0)


# -- what those exits then need ---------------------------------------

def test_costs_are_what_make_a_fast_rate_expensive():
    """The same 3R needs 25% with no spread and 31% when the spread is
    a quarter of the risk — and the faster the rate, the larger that
    share becomes, because the stop shrinks and the spread does not."""
    assert abs(required_win_rate(3.0, 0.0) - 25.0) < 1e-9
    assert abs(required_win_rate(3.0, 0.24) - 31.0) < 0.001


def test_a_spread_as_large_as_the_risk_doubles_what_is_needed():
    assert required_win_rate(3.0, 1.0) == 2 * required_win_rate(3.0, 0.0)


def test_a_higher_reward_to_risk_always_asks_less_of_the_win_rate():
    rates = [required_win_rate(rr, 0.2) for rr in (1.0, 2.0, 3.0, 5.0)]
    assert rates == sorted(rates, reverse=True)


# -- measuring the market ---------------------------------------------

def _walk(steps):
    bars, px = [], 1.1000
    for i, step in enumerate(steps):
        px += step
        bars.append(Bar(i * 60, px, px, px, px))
    return bars


def test_the_per_bar_move_is_measured_not_assumed():
    got = per_bar_move(_walk([0.0001, -0.0001] * 200))
    assert abs(got - 0.0001 * 1.4826) < 1e-9


def test_one_news_spike_does_not_set_the_pace_of_every_trade():
    calm = _walk([0.0001, -0.0001] * 200)
    spiked = _walk([0.0001, -0.0001] * 199 + [0.05, -0.05])
    assert abs(per_bar_move(calm) - per_bar_move(spiked)) < 1e-9


def test_a_flat_series_reports_no_movement_rather_than_guessing():
    assert per_bar_move(_walk([0.0] * 100)) == 0.0
    assert per_bar_move([]) == 0.0


# -- the two together --------------------------------------------------

def test_a_thousand_trades_on_six_symbols_needs_a_stop_inside_the_spread():
    """The finding this tool exists to deliver: at the live configuration
    the solved stop on EURUSD is about a pip, and the spread is most of
    it, so the trade pays more to open than it stands to keep."""
    hold = hold_minutes(1000, 6)                    # 8.6 minutes
    stop, _ = exits_for_hold(hold, 0.0001, 3.0)     # M1: 8.6 bars
    assert stop < 0.0002, stop
    spread = 0.00008
    assert spread / stop > 0.4, "the spread should dominate here"
    assert required_win_rate(3.0, spread / stop) > 33.0


def test_the_same_target_becomes_reasonable_with_more_slots():
    """24 slots instead of 6 is the difference between a stop inside the
    spread and one four times it."""
    stop, _ = exits_for_hold(hold_minutes(1000, 24), 0.0001, 3.0)
    assert 0.00008 / stop < 0.25
