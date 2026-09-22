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


# -- refusing a symbol changes the answer for the others ---------------

LIVE = {   # measured on the account, 2000 M1 bars
    "EURUSDm": dict(sigma=0.00006, spread=0.00008, value=1000.0, floor=0.0),
    "GBPUSDm": dict(sigma=0.00009, spread=0.00010, value=1000.0, floor=0.0),
    "USDJPYm": dict(sigma=0.01779, spread=0.02600, value=6.4, floor=0.0),
    "AUDUSDm": dict(sigma=0.00004, spread=0.00009, value=1000.0, floor=0.0),
    "USDCADm": dict(sigma=0.00006, spread=0.00016, value=720.0, floor=0.0),
    "XAUUSDm": dict(sigma=1.22166, spread=0.26000, value=1.0, floor=0.0),
}


def _solve(symbols=None, target=1000.0, per_symbol=4, ceiling=24, rr=2.0,
           max_cost=0.25):
    from rate import solve
    data = {k: v for k, v in LIVE.items() if symbols is None or k in symbols}
    return solve(data, target, per_symbol, ceiling, 1.0, rr, max_cost, 24.0)


def test_the_live_run_keeps_only_gold():
    """Five pairs spend 27-65% of the risk on spread at this rate."""
    got = _solve()
    assert got["keep"] == ["XAUUSDm"], got["keep"]
    assert len(got["dropped"]) == 5


def test_dropping_symbols_shortens_every_remaining_trade():
    """The bug this replaced: exits were solved once for 24 slots, five
    symbols were refused, and the survivor was reported at settings that
    assumed the other five were still there."""
    all_six = _solve()
    gold_only = _solve(symbols=["XAUUSDm"])
    assert gold_only["slots"] < 24
    assert gold_only["hold"] < all_six["hold"] or all_six["keep"] == ["XAUUSDm"]
    # and gold's stop is re-solved for the slots it actually has
    assert all_six["rows"]["XAUUSDm"]["stop"] == gold_only["rows"]["XAUUSDm"]["stop"]


def test_gold_survives_on_its_own_because_it_moves_more_than_it_costs():
    """1.22 of movement a bar against a 0.26 spread — the ratio that
    matters is movement per unit of spread, not the spread alone."""
    got = _solve(symbols=["XAUUSDm"])
    row = got["rows"]["XAUUSDm"]
    assert row["cost"] < 0.15
    assert 35.0 < row["win_rate"] < 40.0
    assert abs(row["sl_money"] - 2.07) < 0.05


def test_a_refusal_can_cascade_into_another():
    """Fewer symbols means fewer slots means shorter trades means a
    larger spread share — so one refusal can cause the next."""
    got = _solve(symbols=["EURUSDm", "GBPUSDm"], max_cost=0.45)
    assert got["keep"] == [], got["keep"]
    assert len(got["dropped"]) == 2


def test_nothing_survivable_is_reported_as_nothing_not_as_a_default():
    got = _solve(max_cost=0.01)
    assert got["keep"] == [] and got["rows"] == {}


def test_more_positions_per_symbol_buy_a_longer_trade():
    tight = _solve(symbols=["XAUUSDm"], per_symbol=4, ceiling=24)
    roomy = _solve(symbols=["XAUUSDm"], per_symbol=12, ceiling=24)
    assert roomy["hold"] > tight["hold"]
    assert roomy["rows"]["XAUUSDm"]["cost"] < tight["rows"]["XAUUSDm"]["cost"]


def test_the_ceiling_binds_when_it_is_lower_than_the_per_symbol_total():
    from rate import slots_for
    assert slots_for(6, 4, 24) == 24
    assert slots_for(6, 4, 8) == 8
    assert slots_for(1, 4, 24) == 4


def test_a_lower_target_makes_more_symbols_workable():
    fast = _solve(target=1000.0)
    slow = _solve(target=200.0)
    assert len(slow["keep"]) > len(fast["keep"])


# -- the rate and the risk budget have to agree ------------------------

def test_the_live_account_cannot_carry_a_thousand_trades():
    """$917 with a 2% daily limit loses $18.35 before it halts. At $4.10
    a trade that is four trades, not a thousand — and the limit then
    refuses everything for the rest of the day, which reads on the phone
    as a broken bot."""
    from rate import trades_the_budget_allows
    got = trades_the_budget_allows(917.27, 2.0, 4.10)
    assert 4 <= got <= 5, got


def test_the_same_exits_are_fine_on_the_account_they_were_solved_for():
    from rate import trades_the_budget_allows
    assert trades_the_budget_allows(92929.45, 2.0, 4.10) > 450


def test_a_wider_daily_limit_buys_proportionally_more_trades():
    from rate import trades_the_budget_allows
    assert (trades_the_budget_allows(1000.0, 4.0, 2.0)
            == 2 * trades_the_budget_allows(1000.0, 2.0, 2.0))


def test_nothing_configured_is_not_an_infinite_budget():
    from rate import trades_the_budget_allows
    assert trades_the_budget_allows(0.0, 2.0, 4.0) == 0.0
    assert trades_the_budget_allows(917.0, 0.0, 4.0) == 0.0
    assert trades_the_budget_allows(917.0, 2.0, 0.0) == 0.0
