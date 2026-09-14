"""The multi-timeframe blueprint's rules, as code that can be measured.

Every item here was asserted by a document, not by a measurement. They
are implemented so they can be TESTED — the same treatment the six
candlestick patterns got, five of which then failed on every symbol.
"""

import calendar

from fmsbot.sessions import Sessions
from fmsbot.sim import SimResult, SimTrade
from fmsbot.vecstrategy import VEC_STRATEGIES
from tests.helpers import settings
from find_edge import folds_of


def at(hour, day=14):
    return calendar.timegm((2026, 9, day, hour, 0, 0, 0, 0, 0))


# -- session filter ----------------------------------------------------

def test_hours_outside_the_window_are_refused():
    s = Sessions("7-16")
    assert not s.allows(at(6))
    assert s.allows(at(7)) and s.allows(at(15))
    assert not s.allows(at(16)), "the end hour is exclusive"


def test_two_windows_in_one_day():
    s = Sessions("7-11,13-17")
    assert s.allows(at(8)) and s.allows(at(14))
    assert not s.allows(at(12)), "the gap between them is not tradable"


def test_a_window_across_midnight_covers_both_ends():
    s = Sessions("22-3")
    assert s.allows(at(23)) and s.allows(at(1))
    assert not s.allows(at(12))


def test_no_setting_means_every_hour():
    assert Sessions("").allows(at(3))
    assert not Sessions("").enabled


def test_a_malformed_window_is_refused_loudly():
    """Silently trading round the clock because of a typo is the failure
    this project has been bitten by most."""
    for bad in ("7", "7-", "25-26", "abc"):
        try:
            Sessions(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted")


def test_gold_can_keep_different_hours_from_eurusd():
    """Per-instrument configuration, which the blueprint asks for twice."""
    s = settings(SESSION_HOURS="0-24", SYM_XAUUSDM_SESSION_HOURS="7-16")
    assert s.for_symbol("XAUUSDm").session_hours == "7-16"
    assert s.for_symbol("EURUSDm").session_hours == "0-24"


def test_the_session_filter_never_adds_trades():
    from fmsbot.broker.base import Bar
    from fmsbot.sim import simulate

    # M5 bars from the epoch, so the series runs through every hour of
    # the day and a window can actually cut some of it away.
    bars = []
    for i in range(900):
        px = 1.0 + (i % 60) * 0.0002
        bars.append(Bar(i * 300, px, px + 0.0008, px - 0.0008, px + 0.0004))
    base = settings(STRATEGY="liquidity_sweep", SESSION_BARS=20,
                    STRUCTURE_WINDOW=8, FIXED_LOT=0.01)
    gated = settings(STRATEGY="liquidity_sweep", SESSION_BARS=20,
                     STRUCTURE_WINDOW=8, FIXED_LOT=0.01, SESSION_HOURS="7-9")
    cls = VEC_STRATEGIES["liquidity_sweep"]
    wide = simulate(bars, cls(base), base, 1000.0, 1000.0, 0.0001)
    narrow = simulate(bars, cls(gated), gated, 1000.0, 1000.0, 0.0001)
    assert len(narrow.trades) <= len(wide.trades)


# -- multi-timeframe stack ---------------------------------------------

def test_one_ratio_is_exactly_the_old_single_timeframe_filter():
    s = settings(STRATEGY="liquidity_sweep", HTF_RATIO=12)
    assert VEC_STRATEGIES["liquidity_sweep"](s)._ratios() == [12]


def test_a_stack_is_read_smallest_to_largest():
    s = settings(STRATEGY="liquidity_sweep", HTF_RATIOS="288,12,48")
    assert VEC_STRATEGIES["liquidity_sweep"](s)._ratios() == [12, 48, 288]


def test_one_dissenting_timeframe_vetoes_the_trade():
    s = settings(STRATEGY="liquidity_sweep", HTF_RATIOS="2,4")
    sweep = VEC_STRATEGIES["liquidity_sweep"](s)
    sweep._trend_at = lambda closes, total, ratio: (
        [1] * total if ratio == 2 else [-1] * total)
    assert sweep._trend_stack([1.0] * 40, 40) == [None] * 40


def test_agreement_passes_the_side_through():
    s = settings(STRATEGY="liquidity_sweep", HTF_RATIOS="2,4")
    sweep = VEC_STRATEGIES["liquidity_sweep"](s)
    sweep._trend_at = lambda closes, total, ratio: [-1] * total
    assert sweep._trend_stack([1.0] * 20, 20) == [-1] * 20


def test_an_undecided_timeframe_is_not_agreement():
    """None means "not enough history yet", which is not a vote."""
    s = settings(STRATEGY="liquidity_sweep", HTF_RATIOS="2,4")
    sweep = VEC_STRATEGIES["liquidity_sweep"](s)
    sweep._trend_at = lambda closes, total, ratio: (
        [1] * total if ratio == 2 else [None] * total)
    assert sweep._trend_stack([1.0] * 20, 20) == [None] * 20


def test_the_slowest_timeframe_sets_the_warmup():
    s = settings(STRATEGY="liquidity_sweep", HTF_RATIOS="12,288",
                 EMA_SLOW=50, SESSION_BARS=10)
    assert VEC_STRATEGIES["liquidity_sweep"](s).warmup() >= 288 * 50


# -- momentum confirmation ---------------------------------------------

def test_a_doji_cannot_confirm_a_setup():
    s = settings(STRATEGY="liquidity_sweep", MOMENTUM_BODY_ATR=0.5)
    sweep = VEC_STRATEGIES["liquidity_sweep"](s)
    a = {"conf": {"efficiency": [1.0] * 5, "body": [0.0] * 5,
                  "direction": [0] * 5}}
    assert sweep._checked(a, 2, "buy", 1.0, 0.001, 0.001, "x") is None


def test_a_strong_bar_in_the_right_direction_confirms():
    s = settings(STRATEGY="liquidity_sweep", MOMENTUM_BODY_ATR=0.5)
    sweep = VEC_STRATEGIES["liquidity_sweep"](s)
    a = {"conf": {"efficiency": [1.0] * 5, "body": [0.002] * 5,
                  "direction": [1] * 5}}
    assert sweep._checked(a, 2, "buy", 1.0, 0.001, 0.001, "x") is not None


def test_a_strong_bar_the_wrong_way_does_not_confirm():
    s = settings(STRATEGY="liquidity_sweep", MOMENTUM_BODY_ATR=0.5)
    sweep = VEC_STRATEGIES["liquidity_sweep"](s)
    a = {"conf": {"efficiency": [1.0] * 5, "body": [0.002] * 5,
                  "direction": [-1] * 5}}
    assert sweep._checked(a, 2, "buy", 1.0, 0.001, 0.001, "x") is None


def test_it_is_off_by_default():
    s = settings(STRATEGY="liquidity_sweep")
    assert s.momentum_body_atr == 0.0
    sweep = VEC_STRATEGIES["liquidity_sweep"](s)
    a = {"conf": {"efficiency": [1.0] * 5, "body": [0.0] * 5,
                  "direction": [0] * 5}}
    assert sweep._checked(a, 2, "buy", 1.0, 0.001, 0.001, "x") is not None


# -- walk-forward ------------------------------------------------------

def test_one_fold_is_the_original_split_untouched():
    assert folds_of(900, 1) == [(600, 600, 900)]


def test_folds_never_score_a_bar_they_were_fitted_on():
    for folds in (2, 3, 5):
        for train_end, start, end in folds_of(1200, folds):
            assert start >= train_end, (folds, train_end, start)


def test_the_folds_cover_the_series_without_gaps_or_overlap():
    spans = folds_of(1200, 4)
    assert spans[0][1] > 0, "the first fold must have something to fit on"
    for (_, _, end), (_, nxt, _) in zip(spans, spans[1:]):
        assert end == nxt, (end, nxt)
    assert spans[-1][2] == 1200, "the last fold runs to the end of the data"


def test_each_fold_is_fitted_on_more_history_than_the_last():
    ends = [train_end for train_end, _, _ in folds_of(1200, 4)]
    assert ends == sorted(ends) and len(set(ends)) == len(ends)


def test_a_series_too_short_to_split_falls_back_to_one_split():
    assert len(folds_of(4, 9)) == 1


# -- Monte Carlo drawdown ----------------------------------------------

def _result(pnls):
    res = SimResult(start_balance=1000.0)
    for i, pnl in enumerate(pnls):
        t = SimTrade(side="buy", entry=1.0, sl=0.9, tp=1.1, lots=0.01,
                     opened=i)
        t.pnl = pnl
        res.trades.append(t)
    return res


def test_the_order_of_the_same_trades_changes_the_worst_moment():
    """The drawdown a backtest reports is one draw, not the risk."""
    res = _result([10.0] * 20 + [-10.0] * 20)
    mc = res.drawdown_percentiles(runs=200)
    assert mc[95] > mc[50] > 0


def test_a_run_with_no_losses_has_no_drawdown_in_any_order():
    assert _result([5.0] * 30).drawdown_percentiles(runs=50)[95] == 0.0


def test_it_is_deterministic_so_two_readings_agree():
    res = _result([3.0, -1.0] * 25)
    assert res.drawdown_percentiles(runs=100) == res.drawdown_percentiles(runs=100)


def test_no_trades_is_not_a_crash():
    assert SimResult(start_balance=1000.0).drawdown_percentiles()[95] == 0.0


# -- what the filters cost in trades -----------------------------------

def _sweep_trades(**over):
    """Trades liquidity_sweep takes over one synthetic series."""
    import random
    from fmsbot.broker.base import Bar
    from fmsbot.sim import simulate

    rnd = random.Random(12)
    bars, price, step = [], 1.10, 0.0
    for i in range(9000):
        step = rnd.gauss(0, 0.0004) + 0.000015 + step * 0.25
        opened, price = price, price + step
        bars.append(Bar(i * 300, opened,
                        max(opened, price) + abs(rnd.gauss(0, 0.0002)),
                        min(opened, price) - abs(rnd.gauss(0, 0.0002)),
                        price))
    s = settings(STRATEGY="liquidity_sweep", FIXED_LOT=0.01,
                 SESSION_BARS=288, STRUCTURE_WINDOW=12, **over)
    cls = VEC_STRATEGIES["liquidity_sweep"]
    return len(simulate(bars, cls(s), s, 100.0, 1000.0, 0.00008).trades)


def test_every_blueprint_filter_costs_trades_and_none_adds_any():
    """Each filter is a veto. Stacking them multiplies the vetoes, and
    a setup that never fires cannot be measured, however sound it reads."""
    baseline = _sweep_trades()
    assert baseline > 0, "the baseline must trade or this proves nothing"
    for over in ({"HTF_RATIOS": "12,48"},
                 {"SESSION_HOURS": "7-16"},
                 {"MOMENTUM_BODY_ATR": 0.5},
                 {"HTF_RATIOS": "12,48", "SESSION_HOURS": "7-16",
                  "MOMENTUM_BODY_ATR": 0.5}):
        assert _sweep_trades(**over) <= baseline, over


def test_a_three_deep_stack_can_silence_the_strategy_completely():
    """Measured, not feared: 1H+4H+daily unanimity leaves nothing to
    judge on this series, and find_edge needs 30 out-of-sample trades."""
    assert _sweep_trades(HTF_RATIOS="12,48,288") == 0
