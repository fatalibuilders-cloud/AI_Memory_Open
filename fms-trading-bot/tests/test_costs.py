"""What a backtested trade is charged to enter.

A 120-day test started on a Sunday priced AUDUSD at 9.2 pips and GBPUSD
at 3.8 — four to ten times their weekday spreads — because the cost came
from info.spread, the quote at the instant the test ran. Every strategy
in that run lost. The bars themselves record what was really quoted.
"""

from backtest import bar_count, typical_spread
from fmsbot.broker.base import Bar


class Info:
    """The fields typical_spread reads off an MT5 symbol_info."""

    def __init__(self, spread=0, point=0.00001):
        self.spread, self.point = spread, point


def series(spreads):
    return [Bar(i * 60, 1.0, 1.0, 1.0, 1.0, s) for i, s in enumerate(spreads)]


def test_the_history_prices_the_trade_not_the_moment_of_the_run():
    """Sunday's 92-point quote does not decide what weekday trades cost."""
    import io
    from contextlib import redirect_stdout
    bars = series([10] * 500)
    with redirect_stdout(io.StringIO()):       # the note has its own test
        got = typical_spread(bars, "AUDUSDm", Info(spread=92))
    assert got == 10 * 0.00001


def test_an_outlier_hour_does_not_set_the_price():
    """The median, not the mean: a news spike is not the usual cost."""
    bars = series([10] * 99 + [900])
    assert typical_spread(bars, "EURUSDm", Info(spread=10)) == 10 * 0.00001


def test_a_genuinely_wide_instrument_is_charged_what_it_costs():
    bars = series([260] * 200)
    got = typical_spread(bars, "XAUUSDm", Info(spread=260, point=0.001))
    assert abs(got - 0.26) < 1e-12, got


def test_a_feed_without_spreads_falls_back_to_the_live_quote():
    bars = [Bar(i * 60, 1.0, 1.0, 1.0, 1.0) for i in range(100)]
    assert typical_spread(bars, "EURUSDm", Info(spread=20)) == 20 * 0.00001


def test_nothing_known_at_all_returns_none_for_the_caller_to_handle():
    bars = [Bar(i * 60, 1.0, 1.0, 1.0, 1.0) for i in range(10)]
    assert typical_spread(bars, "EURUSDm", Info(spread=0)) is None


def test_a_closed_market_is_called_out():
    """The warning is the point: a losing backtest priced at weekend
    spreads is not evidence about weekday trading."""
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        typical_spread(series([10] * 100), "AUDUSDm", Info(spread=92))
    assert "closed or thin" in buf.getvalue()

    quiet = io.StringIO()
    with redirect_stdout(quiet):
        typical_spread(series([10] * 100), "AUDUSDm", Info(spread=11))
    assert quiet.getvalue() == ""


def test_days_are_bars_not_dates():
    """60 days of M1 is 86,400 bars, which spans far more than 60 days."""
    assert bar_count("M1", 60) == 86_400
    assert bar_count("M5", 60) == 17_280
    # a higher timeframe covers more calendar time for the same bar count
    assert bar_count("M15", 120) < bar_count("M1", 30)
