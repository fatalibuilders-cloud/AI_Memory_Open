"""Requiring several reasons before a setup is taken.

The literature's rule is quality over quantity: a pin bar in open space
is noise, the same pin bar where a level, a moving average and a
Fibonacci retracement meet is a setup. Requiring confluence does not make
a pattern more likely to work — nobody has shown that — but it trades far
less, and pays the spread far less often, while that is being found out.
"""

from fmsbot import confluence
from fmsbot.broker.base import Bar
from fmsbot.vecstrategy import VEC_STRATEGIES

from .helpers import settings


def _bars(rows):
    return [Bar(i * 300, o, h, l, c) for i, (o, h, l, c) in enumerate(rows)]


def _s(**over):
    env = dict(SYMBOLS="EURUSDm", TIMEFRAME="M5", ATR_PERIOD=14,
               PIN_MA_PERIOD=21, MA_FAST_PERIOD=8, FIB_LOOKBACK=100,
               PIN_LEVEL_ATR=0.5, RR_TARGET=2.0)
    env.update(over)
    return settings(**env)


def _series(n=300, start=1.1000, step=0.0004):
    rows, px = [], start
    for _ in range(n):
        o = px
        px = o + step
        rows.append((o, max(o, px) + 0.0001, min(o, px) - 0.0001, px))
    return _bars(rows)


def test_it_is_off_by_default():
    s = _s()
    assert s.confluence_min == 0
    st = VEC_STRATEGIES["pin_bar"](s)
    bars = _series()
    a = st.precompute(bars)
    ok, found = st._confluence_ok(a, len(bars) - 1, "buy", bars[-1].close, 0.0004)
    assert ok and found == [], "the filter must not apply until asked for"


def test_trend_counts_only_for_the_side_it_favours():
    s = _s()
    bars = _series()                       # steadily rising
    a = confluence.arrays(bars, s)
    i = len(bars) - 1
    up = confluence.factors(a, i, "buy", s, bars[-1].close, 0.0004)
    down = confluence.factors(a, i, "sell", s, bars[-1].close, 0.0004)
    assert "trend" in up
    assert "trend" not in down


def test_a_moving_average_counts_when_price_is_at_it():
    s = _s(PIN_LEVEL_ATR=5.0)              # generous proximity
    bars = _series()
    a = confluence.arrays(bars, s)
    i = len(bars) - 1
    found = confluence.factors(a, i, "buy", s, a["ma_slow"][i], 0.0004)
    assert "ma21" in found


def test_a_price_far_from_everything_has_no_factors_but_trend():
    s = _s(PIN_LEVEL_ATR=0.001)
    bars = _series()
    a = confluence.arrays(bars, s)
    found = confluence.factors(a, len(bars) - 1, "buy", s, 99.0, 0.0004)
    assert found == ["trend"], found


def test_a_fibonacci_retracement_counts():
    """50% of the swing is a factor; a price between levels is not."""
    s = _s(PIN_LEVEL_ATR=0.5, FIB_LOOKBACK=50)
    rows, px = [], 1.1000
    for _ in range(60):                    # a clean run up: swing 1.1000->1.1200
        o = px
        px = o + 0.0040
        rows.append((o, px, o, px))
    bars = _bars(rows)
    a = confluence.arrays(bars, s)
    i = len(bars) - 1
    high, low = a["swing_high"][i - 1], a["swing_low"][i - 1]
    halfway = high - (high - low) * 0.5
    found = confluence.factors(a, i, "buy", s, halfway, 0.0040)
    assert "fib50" in found, found


def test_the_filter_blocks_a_setup_with_too_few_reasons():
    """Same bars, same pattern: only the requirement changes."""
    rows, px = [], 1.2000
    for _ in range(60):
        o = px
        px = o - 0.0010
        rows.append((o, max(o, px) + 0.0002, min(o, px) - 0.0002, px))
    o = px
    rows.append((o, o + 0.0030, o - 0.0002, o - 0.0001))   # bearish pin
    bars = _bars(rows)

    loose = VEC_STRATEGIES["pin_bar"](_s(PIN_MA_PERIOD=5, PIN_LEVEL_ATR=50.0))
    got = loose.at(len(bars) - 1, loose.precompute(bars))
    assert got is not None, "the pattern itself must still be found"

    strict = VEC_STRATEGIES["pin_bar"](
        _s(PIN_MA_PERIOD=5, PIN_LEVEL_ATR=0.0001, CONFLUENCE_MIN=3))
    assert strict.at(len(bars) - 1, strict.precompute(bars)) is None, \
        "three factors should not be found on a bar sitting at nothing"


def test_the_factors_are_named_in_the_reason():
    rows, px = [], 1.2000
    for _ in range(60):
        o = px
        px = o - 0.0010
        rows.append((o, max(o, px) + 0.0002, min(o, px) - 0.0002, px))
    o = px
    rows.append((o, o + 0.0030, o - 0.0002, o - 0.0001))
    bars = _bars(rows)
    st = VEC_STRATEGIES["pin_bar"](
        _s(PIN_MA_PERIOD=5, PIN_LEVEL_ATR=50.0, CONFLUENCE_MIN=1))
    got = st.at(len(bars) - 1, st.precompute(bars))
    assert got is not None and "[" in got.reason, got.reason


def test_every_price_action_strategy_carries_the_arrays():
    s = _s()
    bars = _series()
    for name in ("pin_bar", "engulfing", "inside_bar_breakout",
                 "inside_bar_fakeout", "liquidity_sweep"):
        assert "conf" in VEC_STRATEGIES[name](s).precompute(bars), name


def test_requiring_more_factors_never_produces_more_trades():
    """The filter must only ever subtract."""
    import random
    rnd = random.Random(11)
    px, rows = 1.1000, []
    for _ in range(3000):
        o = px
        px = o + rnd.gauss(0, 0.0003)
        rng = abs(px - o) + abs(rnd.gauss(0, 0.0003)) * rnd.choice([0.3, 1.0, 2.5])
        top, bot = max(o, px), min(o, px)
        spare = max(rng - (top - bot), 0.0)
        up = spare * rnd.random()
        rows.append((o, top + up, bot - (spare - up), px))
    bars = _bars(rows)
    counts = []
    for need in (0, 1, 2, 3):
        st = VEC_STRATEGIES["engulfing"](_s(CONFLUENCE_MIN=need))
        a = st.precompute(bars)
        start = max(st.warmup(), 2)
        counts.append(sum(1 for i in range(start, len(bars))
                          if st.at(i, a) is not None))
    assert counts == sorted(counts, reverse=True), counts
