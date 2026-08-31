"""Rate control, and naming the gate that is actually throttling.

The live bot reported "spreads are wide right now; this one is protecting
you" when the real cause was a stop too tight to clear the spread — a
permanent property of the settings that refuses every trade. Sending
someone to wait out a quiet market when their configuration is broken is
worse than saying nothing.
"""

import time

from fmsbot.pace import Pace, classify


def _times(n, span=3600):
    now = time.time()
    return [now - span * i / max(n, 1) for i in range(n)]


def test_the_interval_that_exactly_meets_the_target():
    p = Pace(target_per_hour=100, floor_seconds=5)
    assert p.effective_interval(600, 6, _times(100)) == 216


def test_behind_pace_speeds_up_and_ahead_does_not_slow_down():
    p = Pace(target_per_hour=100, floor_seconds=5)
    assert p.effective_interval(600, 6, _times(50)) < 216
    assert p.effective_interval(600, 6, _times(150)) == 216


def test_the_floor_and_the_configured_interval_both_hold():
    assert Pace(target_per_hour=100000, floor_seconds=5
                ).effective_interval(600, 1, []) == 5
    assert Pace(target_per_hour=1, floor_seconds=5
                ).effective_interval(30, 6, []) == 30


def test_disabled_when_no_target_is_set():
    p = Pace()
    assert p.effective_interval(30, 6, []) == 30
    assert p.shortfall_report([], 6) is None


def test_the_two_spread_refusals_are_told_apart():
    """They need opposite responses, so they must not share a label."""
    spike = classify("spread 0.00040 is 4.2x its typical 0.00009 "
                     "— abnormal conditions")
    tight = classify("spread 0.00008 is 40% of the 0.00020 stop (limit 25%)")
    assert spike == "spread spike", spike
    assert tight == "stop too tight for the spread", tight
    assert spike != tight


def test_every_refusal_maps_to_the_setting_it_belongs_to():
    cases = {
        "EURUSDm cooldown (120s left)": "cooldown",
        "already positioned in XAUUSDm": "one position per symbol",
        "max open positions (5)": "open-position limit",
        "trade cap (2400) reached for the rolling 24h window": "trade cap",
        "daily loss limit hit (-1.20%)": "daily loss limit",
        "paused after 3 consecutive losses (12 min left)": "loss-streak pause",
        "target $0.30 is below 1.5x the $0.26 cost of the trade":
            "target too small for the spread",
        "the record over 40 trades says this configuration loses":
            "evidence halt",
        "something new entirely": "other",
    }
    for reason, want in cases.items():
        assert classify(reason) == want, (reason, classify(reason), want)


def test_a_settings_problem_is_named_as_one():
    p = Pace(target_per_hour=83)
    for _ in range(250):
        p.record_block("spread 0.00008 is 40% of the 0.00020 stop (limit 25%)")
    for _ in range(50):
        p.record_block("target $0.30 is below 1.5x the $0.26 cost of the trade")
    report = p.shortfall_report([time.time() - 7200], symbols=6)
    assert "stop too tight" in report, report
    assert "SETTINGS problem" in report, report
    assert "tune_symbols.py" in report, report
    assert "protecting you" not in report, "the misleading advice is back"


def test_a_temporary_cause_is_not_called_a_settings_problem():
    p = Pace(target_per_hour=83)
    for _ in range(80):
        p.record_block("spread 0.00040 is 4.2x its typical 0.00009 "
                       "— abnormal conditions")
    report = p.shortfall_report([time.time() - 7200], symbols=6)
    assert "worth waiting out" in report, report
    assert "SETTINGS problem" not in report, report


def test_the_binding_gate_is_named_with_its_fix():
    p = Pace(target_per_hour=100)
    for _ in range(60):
        p.record_block("already positioned in EURUSDm")
    for _ in range(12):
        p.record_block("EURUSDm cooldown (30s left)")
    report = p.shortfall_report([time.time() - 7200], symbols=6)
    assert "one position per symbol" in report
    assert "MAX_POSITIONS_PER_SYMBOL" in report


def test_it_stays_quiet_for_the_first_hour_and_repeats_at_most_hourly():
    now = time.time()
    assert Pace(target_per_hour=100).shortfall_report([now - 60], 6) is None
    p = Pace(target_per_hour=100)
    assert p.shortfall_report([now - 7200], 6) is not None
    assert p.shortfall_report([now - 7200], 6) is None
