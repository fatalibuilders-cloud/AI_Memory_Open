"""Solving a daily profit goal against the risk rules.

The live account was risking $465 a trade while asking for 1000 trades a
day. The daily loss cap allows 4 losses at that size, so the plan ends
after the fourth losing trade of the day, not the thousandth.
"""

from plan import PLAUSIBLE, max_risk, required_win_rate

BALANCE = 93148.0


def test_cost_scales_with_size_not_as_a_fixed_sum():
    """A smaller position pays proportionally less spread, not the same."""
    small = required_win_rate(150, 1000, risk=1.0, rr=3.0, cost_ratio=0.15)
    large = required_win_rate(150, 1000, risk=100.0, rr=3.0, cost_ratio=0.15)
    # both need roughly the same win rate; only the profit term differs
    assert abs(small - large) < 5.0, (small, large)
    assert 28.0 < large < 30.0, large


def test_break_even_is_the_floor_no_target_can_beat():
    """With no profit asked for, the answer is exactly break-even."""
    for rr in (1.0, 2.0, 3.0):
        got = required_win_rate(0.0, 1000, risk=1.0, rr=rr, cost_ratio=0.0)
        assert abs(got - 100.0 / (rr + 1)) < 1e-9, (rr, got)


def test_costs_raise_the_required_win_rate():
    free = required_win_rate(150, 1000, 1.0, 3.0, cost_ratio=0.0)
    paid = required_win_rate(150, 1000, 1.0, 3.0, cost_ratio=0.15)
    assert paid > free


def test_a_higher_reward_to_risk_lowers_the_win_rate_needed():
    two = required_win_rate(150, 1000, 1.0, 2.0, 0.15)
    three = required_win_rate(150, 1000, 1.0, 3.0, 0.15)
    assert three < two, (two, three)


def test_the_daily_cap_fixes_the_size_once_the_count_is_chosen():
    """1000 trades at 40% wins is 600 losses. They must fit in the budget."""
    r = max_risk(BALANCE, daily_loss_pct=2.0, trades=1000, win_rate=40.0)
    assert 3.0 < r < 3.2, r
    budget = BALANCE * 0.02
    assert abs(600 * r - budget) < 1.0


def test_the_live_size_allows_four_losses_not_a_thousand():
    """$465 a trade against a 2% cap on $93,148."""
    budget = BALANCE * 0.02
    assert int(budget / 465.74) == 4


def test_the_users_goal_is_consistent_at_the_right_size():
    """1000 trades, $150 a day, 3R — the win rate must be reachable."""
    risk = max_risk(BALANCE, 2.0, trades=1000, win_rate=32.5)
    need = required_win_rate(150, 1000, risk=min(risk, 1.0), rr=3.0,
                             cost_ratio=0.15)
    after_costs = 100.0 * 1.15 / 4.0
    assert need < PLAUSIBLE, f"needs {need:.1f}% wins"
    assert need > after_costs, "a plan below break-even is not a plan"
    assert 30.0 < need < 35.0, need


def test_the_goal_at_the_live_size_is_not_consistent():
    """The same goal at $465 a trade breaches the cap long before 1000."""
    risk = 465.74
    losses_allowed = BALANCE * 0.02 / risk
    expected_losses = 1000 * (1 - 0.325)
    assert expected_losses > losses_allowed * 100
