"""The ladder must never cap a winner at a trivial fraction of its target.

Live, on a real account: XAUUSDm reached +2.20 and closed at +0.10, over
and over, because stage 2/2 locked $0.10 and the stop then never moved
again. With a $9.28 gold stop that structure needs a 98.9% win rate to
break even. This is the regression guard.
"""

from fmsbot.broker.base import Position

from .helpers import FakeBroker, make_bot, settings

ENTRY, TP, STOP = 3400.00, 3403.00, 3390.72     # $3.00 target, $9.28 stop


def _position(ticket, profit):
    return Position(ticket, "XAUUSDm", "buy", 0.01, ENTRY, STOP, TP, profit)


def test_absolute_rungs_cap_the_winner_and_are_reported():
    s = settings(SYMBOLS="XAUUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
                 PROFIT_STAGES="0.10:0,0.25:0.10")
    b = FakeBroker(price=ENTRY, per_price=1.0)
    bot, session, msgs = make_bot(s, b, ["XAUUSDm"])

    bot._protect_profits(session, [_position(1, 2.20)])
    locked = b.modified[1][0] - ENTRY
    assert abs(locked - 0.10) < 1e-9, f"expected the observed +0.10 cap, got {locked}"

    assert any("CAPPING EVERY WINNER" in m for m in msgs), \
        "a ladder that keeps 3% of the target must be reported, not left silent"


def test_percentage_rungs_scale_to_the_trade_and_do_not_cap():
    s = settings(SYMBOLS="XAUUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
                 PROFIT_STAGES_PCT="50:0,75:50")
    b = FakeBroker(price=ENTRY, per_price=1.0)
    bot, session, msgs = make_bot(s, b, ["XAUUSDm"])

    # +2.20 against a 3.00 target clears the 50% rung (1.50) only:
    # break-even, and the trade keeps running to its target.
    bot._protect_profits(session, [_position(1, 2.20)])
    assert b.modified[1][0] == ENTRY, "50% rung should move the stop to break-even"

    # 75% of 3.00 is 2.25, locking half the target.
    bot2, session2, _ = make_bot(s, FakeBroker(price=ENTRY, per_price=1.0),
                                 ["XAUUSDm"])
    b2 = session2.broker
    bot2._protect_profits(session2, [_position(2, 2.40)])
    locked = b2.modified[2][0] - ENTRY
    assert abs(locked - 1.50) < 1e-6, f"expected +1.50 locked, got {locked}"

    assert not any("CAPPING" in m for m in msgs), \
        "rungs measured against the target must not trigger the warning"


def test_percentage_rungs_fit_every_instrument_untuned():
    """The whole point: one setting, correct on instruments 4000x apart."""
    s = settings(SYMBOLS="EURUSDm,XAUUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
                 PROFIT_STAGES_PCT="50:0,75:50")
    for symbol, entry, tp, per, want_target in (
            ("EURUSDm", 1.16600, 1.16707, 1000.0, 1.07),
            ("XAUUSDm", 3400.00, 3403.00, 1.0, 3.00)):
        b = FakeBroker(price=entry, per_price=per)
        bot, session, _ = make_bot(s, b, [symbol])
        p = Position(9, symbol, "buy", 0.01, entry, entry - 0.001, tp, 0.0)
        ladder = bot._ladder_for(session, s, p)
        assert abs(ladder[0][0] - want_target * 0.5) < 0.01, (symbol, ladder)
        assert abs(ladder[1][1] - want_target * 0.5) < 0.01, (symbol, ladder)


def test_stop_is_never_loosened():
    """A rung may only ever tighten. Widening one would be catastrophic."""
    s = settings(SYMBOLS="XAUUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
                 PROFIT_STAGES_PCT="50:0,75:50")
    b = FakeBroker(price=ENTRY, per_price=1.0)
    bot, session, _ = make_bot(s, b, ["XAUUSDm"])
    # already protected well above where the 75% rung would put it
    p = Position(3, "XAUUSDm", "buy", 0.01, ENTRY, ENTRY + 2.90, TP, 2.40)
    bot._protect_profits(session, [p])
    if 3 in b.modified:
        assert b.modified[3][0] >= ENTRY + 2.90, "stop was moved backwards"
