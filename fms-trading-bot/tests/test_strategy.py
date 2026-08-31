"""The liquidity-sweep strategy: it must fire on the pattern, and only on it."""

from fmsbot.broker.base import Bar
from fmsbot.vecstrategy import VEC_STRATEGIES

from .helpers import settings


def _bars(prices, spread=0.3):
    """Bars whose high/low bracket each close, unless stated per-bar."""
    out = []
    for i, p in enumerate(prices):
        if isinstance(p, tuple):
            o, h, l, c = p
        else:
            o = h = l = c = p
            h, l = p + spread, p - spread
        out.append(Bar(i * 300, o, h, l, c))
    return out


def _strategy(**over):
    env = dict(SYMBOLS="XAUUSDm", TIMEFRAME="M5", EMA_FAST=3, EMA_SLOW=6,
               ATR_PERIOD=14, HTF_RATIO=4, SESSION_BARS=20,
               STRUCTURE_WINDOW=8, SWEEP_REJECT=0.5, RR_TARGET=2.0)
    env.update(over)
    return VEC_STRATEGIES["liquidity_sweep"](settings(**env))


def test_it_is_registered_and_searchable():
    import optimize as opt
    assert "liquidity_sweep" in VEC_STRATEGIES
    assert "liquidity_sweep" in opt.GRIDS
    assert opt.combos(opt.GRIDS["liquidity_sweep"]), "grid produced no combinations"


def test_a_close_beyond_the_level_is_a_breakout_not_a_sweep():
    """The test that separates the two. A breakout must be refused."""
    st = _strategy()
    # a bar that pokes above the level AND closes above it
    a = {"prev_high": [100.0] * 3, "prev_low": [90.0] * 3,
         "high": [0, 103.0, 0], "low": [0, 99.0, 0], "close": [0, 102.5, 0]}
    assert st._swept(a, 2, "sell") is None, "a close beyond the level is not a sweep"


def test_a_poke_that_closes_back_inside_is_a_sweep():
    st = _strategy()
    a = {"prev_high": [100.0] * 3, "prev_low": [90.0] * 3,
         "high": [0, 103.0, 0], "low": [0, 99.0, 0], "close": [0, 99.5, 0]}
    got = st._swept(a, 2, "sell")
    assert got is not None and got[1] == 103.0, got


def test_a_shallow_rejection_is_refused():
    """Giving back less than SWEEP_REJECT of the poke is not a rejection."""
    st = _strategy(SWEEP_REJECT=0.8)
    a = {"prev_high": [100.0] * 3, "prev_low": [90.0] * 3,
         "high": [0, 103.0, 0], "low": [0, 99.0, 0], "close": [0, 99.9, 0]}
    assert st._swept(a, 2, "sell") is None


def test_the_stop_sits_beyond_the_sweep_extreme():
    """Risk must be measured to the invalidation point, not a fixed size."""
    st = _strategy()
    n = 20
    prices = [100.0] * (2 * n)
    prices += [(100.0, 100.3, 96.0, 99.8)]        # sweep of the low
    prices += [101.0, 102.0, 103.0]               # structure break upward
    bars = _bars(prices)
    a = st.precompute(bars)
    a["trend"] = [1] * len(bars)                  # force an uptrend
    for i in range(2 * n + 1, len(bars)):
        sig = st.at(i, a)
        if sig:
            assert sig.side == "buy"
            # stop below the 96.0 sweep low
            assert bars[i].close - sig.sl_distance <= 96.0 + 1e-9, sig.sl_distance
            assert abs(sig.tp_distance / sig.sl_distance - 2.0) < 1e-9
            return
    raise AssertionError("no signal produced on a textbook sweep-and-break")


def test_counter_trend_setups_are_discarded():
    st = _strategy()
    n = 20
    prices = [100.0] * (2 * n) + [(100.0, 100.3, 96.0, 99.8), 101.0, 102.0, 103.0]
    bars = _bars(prices)
    a = st.precompute(bars)
    a["trend"] = [-1] * len(bars)     # downtrend: the bullish setup must not fire
    assert all(st.at(i, a) is None or st.at(i, a).side == "sell"
               for i in range(2 * n + 1, len(bars)))


def test_it_runs_over_a_full_series_without_error():
    import random
    from fmsbot.sim import simulate
    st = _strategy()
    rnd = random.Random(5)
    px, prices = 3400.0, []
    for _ in range(1500):
        px += rnd.gauss(0, 1.5)
        prices.append(px)
    bars = _bars(prices, spread=0.8)
    r = simulate(bars, st, st.s, 1000.0, 1.0, 0.26)
    assert r.bars == len(bars)
