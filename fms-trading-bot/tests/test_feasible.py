"""Whether a risk cap and a broker's smallest lot can both be obeyed.

A live account refused nearly every signal for a day:

    XAUUSDm order refused — it would risk 29.12, over the 1.02 that
    0.0011% allows, and 0.01 is the smallest size the broker takes

Nothing was broken. "One trade may lose about a dollar" and "the stop
goes beyond the sweep" are both reasonable, and on gold at the smallest
lot the broker takes they contradict each other. The bot chose the risk
limit, which is the right choice and looks exactly like a fault.
"""

from feasible import assess, stop_wanted
from fmsbot.broker.base import Bar
from tests.helpers import settings

BALANCE = 92929.45
CAP = 1.02              # 0.0011% of the live balance


def test_the_live_gold_refusal_is_reproduced():
    """0.01 lot of gold is 1 oz, so a 29.12 stop risks 29.12."""
    got = assess(CAP, 1.0, 29.12)
    assert not got["fits"]
    assert abs(got["cost"] - 29.12) < 0.01
    assert abs(got["over"] - 28.5) < 0.5           # 28x over the cap
    assert abs(got["afford"] - 1.02) < 0.01        # a 10-pip stop on gold


def test_it_names_the_cap_that_would_let_the_trade_through():
    got = assess(CAP, 1.0, 29.12)
    assert abs(got["needed"] - 29.12) < 0.01
    # which is this much of the account, and the number the user must choose
    assert abs(100 * got["needed"] / BALANCE - 0.0313) < 0.001


def test_a_symbol_whose_stop_fits_is_allowed():
    """EURUSD at 0.01 lot: 0.1 per pip, so a 30-pip stop costs 0.30."""
    got = assess(CAP, 1000.0, 0.0003)
    assert got["fits"]
    assert abs(got["cost"] - 0.30) < 0.001


def test_a_stop_exactly_at_the_cap_is_allowed_not_refused():
    got = assess(CAP, 1000.0, CAP / 1000.0)
    assert got["fits"], "the boundary must not be a refusal"


def test_raising_the_cap_is_the_only_thing_that_widens_the_stop():
    tight = assess(1.0, 1.0, 5.0)
    loose = assess(10.0, 1.0, 5.0)
    assert not tight["fits"] and loose["fits"]
    assert loose["afford"] == 10 * tight["afford"]


def test_a_worthless_price_unit_does_not_divide_by_zero():
    got = assess(CAP, 0.0, 1.0)
    assert got["afford"] == 0.0 and not got["fits"]


def _bars(atr_units: float, count: int = 400):
    """A series whose every bar has the same range."""
    out = []
    for i in range(count):
        px = 1.1000
        out.append(Bar(i * 60, px, px + atr_units / 2, px - atr_units / 2, px))
    return out


def test_the_sweep_strategy_is_priced_on_a_wider_stop_than_one_atr():
    """Its stop is structural, and measured about three ATR on this
    account — pricing it at one ATR would call gold feasible when the
    live bot refuses it every time."""
    sweep = settings(STRATEGY="liquidity_sweep", ATR_PERIOD=14,
                     ATR_SL_MULT=1.0)
    plain = settings(STRATEGY="ema_cross", ATR_PERIOD=14, ATR_SL_MULT=1.0)
    bars = _bars(0.0010)
    assert stop_wanted(bars, sweep) > stop_wanted(bars, plain)


def test_a_cash_stop_needs_no_room_because_it_is_the_cap():
    s = settings(STRATEGY="liquidity_sweep", SL_MONEY=1.0)
    assert stop_wanted(_bars(0.0010), s) == 0.0


def test_a_series_with_no_range_reports_no_stop_rather_than_guessing():
    s = settings(STRATEGY="ema_cross", ATR_PERIOD=14)
    flat = [Bar(i * 60, 1.1, 1.1, 1.1, 1.1) for i in range(400)]
    assert stop_wanted(flat, s) == 0.0
