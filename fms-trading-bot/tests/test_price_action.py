"""Pin bar and inside bar false breakout.

Both come from the price-action literature, and both have one test that
is the whole pattern. For the fakeout it is the CLOSE: a bar that breaks
the mother bar's high and closes above it is a breakout, and trading that
as a reversal is how the pattern loses money. For the pin bar it is the
LEVEL: a rejection wick in open space is just a bar with a wick.
"""

from fmsbot.broker.base import Bar
from fmsbot.vecstrategy import VEC_STRATEGIES

from .helpers import settings


def _bars(rows):
    return [Bar(i * 300, o, h, l, c) for i, (o, h, l, c) in enumerate(rows)]


def _pin(**over):
    env = dict(SYMBOLS="EURUSDm", TIMEFRAME="M5", ATR_PERIOD=14,
               PIN_MA_PERIOD=5, PIN_WICK_RATIO=0.66, PIN_BODY_MAX=0.33,
               PIN_LEVEL_ATR=0.5, RR_TARGET=2.0)
    env.update(over)
    return VEC_STRATEGIES["pin_bar"](settings(**env))


def _fake(**over):
    env = dict(SYMBOLS="EURUSDm", TIMEFRAME="M5", ATR_PERIOD=14, RR_TARGET=2.0)
    env.update(over)
    return VEC_STRATEGIES["inside_bar_fakeout"](settings(**env))


def test_both_are_registered_and_searchable():
    import optimize as opt
    for name in ("pin_bar", "inside_bar_fakeout"):
        assert name in VEC_STRATEGIES
        assert name in opt.GRIDS
        assert opt.combos(opt.GRIDS[name])


# ---------------------------------------------------------------- pin bar

def _pin_series(wick_top=True, trend_down=True, n=40):
    """A trend, then a bar that pokes at the average and is rejected."""
    rows = []
    px = 1.2000 if trend_down else 1.1000
    step = -0.0010 if trend_down else 0.0010
    for _ in range(n):
        o = px
        px = o + step
        rows.append((o, max(o, px) + 0.0002, min(o, px) - 0.0002, px))
    # the pin: a long wick back toward the average, tiny body
    o = px
    if wick_top:
        rows.append((o, o + 0.0030, o - 0.0002, o - 0.0001))
    else:
        rows.append((o, o + 0.0002, o - 0.0030, o + 0.0001))
    return _bars(rows)


def test_a_rejection_with_the_trend_signals():
    st = _pin()
    bars = _pin_series(wick_top=True, trend_down=True)
    a = st.precompute(bars)
    got = st.at(len(bars) - 1, a)
    assert got is not None and got.side == "sell", got
    # stop beyond the wick tip
    tip, close = bars[-1].high, bars[-1].close
    assert got.sl_distance >= tip - close
    assert abs(got.tp_distance / got.sl_distance - 2.0) < 1e-9


def test_a_rejection_against_the_trend_is_ignored():
    """A bullish rejection in a downtrend is somebody else's trade."""
    st = _pin()
    bars = _pin_series(wick_top=False, trend_down=True)
    a = st.precompute(bars)
    assert st.at(len(bars) - 1, a) is None


def test_a_big_body_is_not_a_rejection():
    st = _pin()
    bars = _pin_series(wick_top=True, trend_down=True)
    last = bars[-1]
    # same wick, but a large body: a directional bar with a tail
    bars[-1] = Bar(last.time, last.open, last.high, last.low,
                   last.open - 0.0015)
    a = st.precompute(bars)
    assert st.at(len(bars) - 1, a) is None


def test_a_rejection_far_from_the_level_is_ignored():
    """A wick in open space is just a bar with a wick."""
    st = _pin(PIN_LEVEL_ATR=0.01)
    bars = _pin_series(wick_top=True, trend_down=True)
    # push the bar far from the average
    last = bars[-1]
    off = 0.05
    bars[-1] = Bar(last.time, last.open - off, last.high - off,
                   last.low - off, last.close - off)
    a = st.precompute(bars)
    assert st.at(len(bars) - 1, a) is None


# ------------------------------------------------- inside bar false breakout

def _fakeout_series(close_inside=True, upside=True, n=30):
    rows = [(1.1000, 1.1005, 1.0995, 1.1000) for _ in range(n)]
    rows.append((1.1000, 1.1040, 1.0960, 1.1000))          # mother bar
    rows.append((1.1005, 1.1020, 1.0985, 1.1000))          # inside bar
    if upside:
        close = 1.1010 if close_inside else 1.1050
        rows.append((1.1010, 1.1060, 1.1000, close))       # breaks the high
    else:
        close = 1.0990 if close_inside else 1.0950
        rows.append((1.0990, 1.1000, 1.0940, close))       # breaks the low
    return _bars(rows)


def test_a_break_that_closes_back_inside_signals_the_other_way():
    st = _fake()
    bars = _fakeout_series(close_inside=True, upside=True)
    a = st.precompute(bars)
    got = st.at(len(bars) - 1, a)
    assert got is not None and got.side == "sell", got
    assert got.sl_distance >= bars[-1].high - bars[-1].close


def test_a_break_that_closes_beyond_is_a_breakout_and_is_refused():
    """The one test that separates the pattern from its opposite."""
    st = _fake()
    bars = _fakeout_series(close_inside=False, upside=True)
    a = st.precompute(bars)
    assert st.at(len(bars) - 1, a) is None, \
        "a close beyond the mother bar is a breakout, not a failed one"


def test_the_downside_case_signals_a_buy():
    st = _fake()
    bars = _fakeout_series(close_inside=True, upside=False)
    a = st.precompute(bars)
    got = st.at(len(bars) - 1, a)
    assert got is not None and got.side == "buy", got


def test_without_an_inside_bar_there_is_no_pattern():
    st = _fake()
    bars = _fakeout_series(close_inside=True, upside=True)
    # widen the middle bar so it is no longer contained
    m = bars[-2]
    bars[-2] = Bar(m.time, m.open, 1.1100, 1.0900, m.close)
    a = st.precompute(bars)
    assert st.at(len(bars) - 1, a) is None


def test_both_run_over_a_full_series_without_error():
    import random
    from fmsbot.sim import simulate
    rnd = random.Random(9)
    px, rows = 1.1000, []
    for _ in range(1500):
        o = px
        px = o + rnd.gauss(0, 0.0003)
        rows.append((o, max(o, px) + 0.0001, min(o, px) - 0.0001, px))
    bars = _bars(rows)
    for st in (_pin(), _fake()):
        r = simulate(bars, st, st.s, 1000.0, 1000.0, 0.00008)
        assert r.bars == len(bars)


# ------------------------------------------------------- engulfing bar

def _eng(**over):
    env = dict(SYMBOLS="EURUSDm", TIMEFRAME="M5", ATR_PERIOD=14,
               PIN_MA_PERIOD=5, PIN_LEVEL_ATR=0.5, RR_TARGET=2.0)
    env.update(over)
    return VEC_STRATEGIES["engulfing"](settings(**env))


def _eng_series(bullish=True, engulfs=True, n=40):
    rows = []
    px = 1.1000 if bullish else 1.2000
    step = 0.0010 if bullish else -0.0010
    for _ in range(n):
        o = px
        px = o + step
        rows.append((o, max(o, px) + 0.0002, min(o, px) - 0.0002, px))
    if bullish:
        rows.append((px, px + 0.0002, px - 0.0012, px - 0.0010))     # small down
        prev_c = px - 0.0010
        body = 0.0020 if engulfs else 0.0004
        o2 = prev_c - 0.0001
        c2 = o2 + body
        rows.append((o2, c2 + 0.0002, o2 - 0.0004, c2))
    else:
        rows.append((px, px + 0.0012, px - 0.0002, px + 0.0010))     # small up
        prev_c = px + 0.0010
        body = 0.0020 if engulfs else 0.0004
        o2 = prev_c + 0.0001
        c2 = o2 - body
        rows.append((o2, o2 + 0.0004, c2 - 0.0002, c2))
    return _bars(rows)


def test_an_engulfing_body_with_the_trend_signals():
    st = _eng(PIN_LEVEL_ATR=50.0)          # take the level out of the question
    for bullish, side in ((True, "buy"), (False, "sell")):
        bars = _eng_series(bullish=bullish, engulfs=True)
        a = st.precompute(bars)
        got = st.at(len(bars) - 1, a)
        assert got is not None and got.side == side, (bullish, got)


def test_a_body_that_does_not_engulf_is_refused():
    st = _eng(PIN_LEVEL_ATR=50.0)
    bars = _eng_series(bullish=True, engulfs=False)
    a = st.precompute(bars)
    assert st.at(len(bars) - 1, a) is None


def test_an_engulfing_bar_far_from_the_level_is_refused():
    """Engulfing bodies happen constantly in open space."""
    st = _eng(PIN_LEVEL_ATR=0.01)
    bars = _eng_series(bullish=True, engulfs=True)
    last = bars[-1]
    off = 0.05
    bars[-1] = Bar(last.time, last.open + off, last.high + off,
                   last.low + off, last.close + off)
    a = st.precompute(bars)
    assert st.at(len(bars) - 1, a) is None


# --------------------------------------------- inside bar as continuation

def _cont(**over):
    env = dict(SYMBOLS="EURUSDm", TIMEFRAME="M5", ATR_PERIOD=14,
               PIN_MA_PERIOD=5, RR_TARGET=2.0)
    env.update(over)
    return VEC_STRATEGIES["inside_bar_breakout"](settings(**env))


def _cont_series(up=True, beyond=True, n=40):
    rows = []
    px = 1.1000 if up else 1.2000
    step = 0.0010 if up else -0.0010
    for _ in range(n):
        o = px
        px = o + step
        rows.append((o, max(o, px) + 0.0002, min(o, px) - 0.0002, px))
    mh, ml = px + 0.0020, px - 0.0020
    rows.append((px, mh, ml, px))                       # mother bar
    rows.append((px, px + 0.0010, px - 0.0010, px))     # inside bar
    if up:
        close = mh + 0.0010 if beyond else px
        rows.append((px, close + 0.0002, px - 0.0002, close))
    else:
        close = ml - 0.0010 if beyond else px
        rows.append((px, px + 0.0002, close - 0.0002, close))
    return _bars(rows)


def test_a_close_beyond_the_mother_with_the_trend_is_a_continuation():
    st = _cont()
    for up, side in ((True, "buy"), (False, "sell")):
        bars = _cont_series(up=up, beyond=True)
        a = st.precompute(bars)
        got = st.at(len(bars) - 1, a)
        assert got is not None and got.side == side, (up, got)
        # the stop sits on the far side of the mother bar
        mother_low, mother_high = bars[-3].low, bars[-3].high
        close = bars[-1].close
        if side == "buy":
            assert close - got.sl_distance <= mother_low
        else:
            assert close + got.sl_distance >= mother_high


def test_a_close_still_inside_the_mother_is_not_a_breakout():
    st = _cont()
    bars = _cont_series(up=True, beyond=False)
    a = st.precompute(bars)
    assert st.at(len(bars) - 1, a) is None


def test_continuation_and_fakeout_are_opposite_trades():
    """The difference is only where the bar closes, and it must be."""
    cont, fake = _cont(), _fake()
    beyond = _cont_series(up=True, beyond=True)
    got = cont.at(len(beyond) - 1, cont.precompute(beyond))
    assert got is not None and got.side == "buy"
    assert fake.at(len(beyond) - 1, fake.precompute(beyond)) is None, \
        "a close beyond the mother bar must not read as a failed break"
