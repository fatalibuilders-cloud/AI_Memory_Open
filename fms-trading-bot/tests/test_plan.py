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


def test_the_scalp1000_preset_matches_what_plan_solved():
    """The preset is the plan. If they drift apart, one of them is a lie."""
    import preset
    p = preset.PRESETS["scalp1000"]
    assert "scalp1000" in preset.NOTES

    balance = BALANCE
    risk = balance * float(p["RISK_PCT"]) / 100
    rr = float(p["MIN_REWARD_RISK"])
    budget = balance * float(p["DAILY_LOSS_LIMIT_PCT"]) / 100

    # ~$1 a trade: the number that makes 1000 trades possible at all
    assert 0.8 < risk < 1.5, risk
    # the day's budget must absorb far more than the planned trade count
    assert budget / risk > int(p["MAX_TRADES_PER_DAY"]), \
        "the daily cap still ends the day before the trade count is reached"
    # and the goal must close at that size
    need = required_win_rate(150, 1000, risk, rr, cost_ratio=0.15)
    assert need < PLAUSIBLE and need > 100.0 * 1.15 / (rr + 1), need

    # exits consistent with the reward floor
    assert float(p["ATR_TP_MULT"]) / float(p["ATR_SL_MULT"]) >= rr - 1e-9
    # and no dollar-denominated ladder, which is what capped every winner
    assert p["PROFIT_STAGES"] == "" and p["TP_MONEY"] == "0"


def test_the_preset_ladder_cannot_pay_less_than_a_loss():
    """A rung locking under 1R makes every protected win smaller than a loss."""
    import preset
    from fmsbot.config import parse_stages
    p = preset.PRESETS["scalp1000"]
    rungs = parse_stages(p["PROFIT_STAGES_PCT"])
    rr = float(p["MIN_REWARD_RISK"])
    for trigger, lock in rungs:
        locked_r = lock / 100.0 * rr        # lock is a % of the target
        assert locked_r == 0.0 or locked_r >= 1.0, (
            f"rung locks {locked_r:.2f}R — less than a full loss")
