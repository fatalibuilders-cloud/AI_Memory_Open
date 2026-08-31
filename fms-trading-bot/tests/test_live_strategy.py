"""Trading a searchable strategy live, alone or in combination."""

import random

from fmsbot.broker.base import Bar
from fmsbot.live import Combined, VecAdapter, build_strategy, strategy_name
from fmsbot.strategy import Signal

from .helpers import settings


def _bars(n=1200, seed=4, start=3400.0, step=1.5):
    rnd = random.Random(seed)
    px, out = start, []
    for i in range(n):
        o = px
        px = o + rnd.gauss(0, step)
        out.append(Bar(i * 300, o, max(o, px) + 0.4, min(o, px) - 0.4, px))
    return out


def test_default_is_still_the_ema_crossover():
    s = settings(SYMBOLS="EURUSDm")
    st = build_strategy(s)
    assert type(st).__name__ == "EmaCrossStrategy"


def test_any_searchable_strategy_can_be_traded_live():
    for name in ("liquidity_sweep", "breakout", "momentum", "rsi_reversion"):
        s = settings(SYMBOLS="XAUUSDm", TIMEFRAME="M5", STRATEGY=name)
        st = build_strategy(s)
        assert isinstance(st, VecAdapter) and st.name == name
        assert st.min_bars() > 0
        # and it must answer without raising on a real-length series
        st.signal(_bars(max(st.min_bars() + 50, 400)))


def test_an_unknown_name_is_refused_with_the_list():
    s = settings(SYMBOLS="EURUSDm", STRATEGY="martingale_recovery")
    try:
        build_strategy(s)
    except ValueError as exc:
        assert "unknown strategy" in str(exc) and "ema_cross" in str(exc)
    else:
        raise AssertionError("a typo must not silently fall back to something")


def test_plus_requires_agreement_and_comma_does_not():
    s = settings(SYMBOLS="XAUUSDm", STRATEGY="ema_cross+liquidity_sweep")
    both = build_strategy(s)
    assert isinstance(both, Combined) and both.require_all

    s2 = settings(SYMBOLS="XAUUSDm", STRATEGY="ema_cross,liquidity_sweep")
    either = build_strategy(s2)
    assert isinstance(either, Combined) and not either.require_all


class _Fixed:
    """A stand-in that always returns the same signal."""

    def __init__(self, name, signal):
        self.name, self._signal = name, signal

    def min_bars(self):
        return 3

    def signal(self, bars):
        return self._signal

    trend_signal = signal


def test_disagreement_produces_no_trade():
    a = _Fixed("a", Signal("buy", 1.0, 2.0, "a"))
    b = _Fixed("b", Signal("sell", 1.0, 2.0, "b"))
    assert Combined([a, b], require_all=True).signal([]) is None


def test_silence_from_one_member_blocks_a_required_combination():
    a = _Fixed("a", Signal("buy", 1.0, 2.0, "a"))
    b = _Fixed("b", None)
    assert Combined([a, b], require_all=True).signal([]) is None
    # but "either may fire" still takes it
    assert Combined([a, b], require_all=False).signal([]) is not None


def test_a_combined_signal_takes_the_widest_stop():
    """Combining must never place a stop inside a member's invalidation."""
    a = _Fixed("a", Signal("buy", 1.0, 3.0, "a"))     # 3R off a tight stop
    b = _Fixed("b", Signal("buy", 4.0, 8.0, "b"))     # 2R off a wide one
    got = Combined([a, b], require_all=True).signal([])
    assert got.sl_distance == 4.0, "took a stop inside a member's invalidation"
    assert got.tp_distance == 8.0, "must keep the most conservative reward:risk"
    assert got.side == "buy"


def test_the_strategy_name_reaches_the_evidence_fingerprint():
    """Switching strategy must start the trade record again."""
    from fmsbot.evidence import fingerprint
    s = settings(SYMBOLS="XAUUSDm", STRATEGY="liquidity_sweep")
    one = fingerprint(s, strategy_name(build_strategy(s)))
    s2 = settings(SYMBOLS="XAUUSDm", STRATEGY="breakout")
    two = fingerprint(s2, strategy_name(build_strategy(s2)))
    assert one != two, "two strategies must not share one record"


def test_every_preset_has_a_note_and_valid_keys():
    """A preset without a note crashed preset.py after writing .env."""
    import preset
    from fmsbot.config import Settings
    known = set(vars(Settings()))
    for name, values in preset.PRESETS.items():
        assert name in preset.NOTES, f"preset '{name}' has no NOTES entry"
        for key in values:
            attr = key.lower()
            assert attr in known or key in (
                "PROFIT_STAGES", "PROFIT_STAGES_PCT", "ACTIVE_BROKERS"), \
                f"preset '{name}' sets unknown key {key}"
