"""Trailing stops and the hard loss cap.

Both are backstops for a stop loss that did not hold, which is a thing
that happened on the live account.
"""

from fmsbot.broker.base import Position

from .helpers import FakeBroker, make_bot, settings

ENTRY, ATR, PER = 1.16600, 0.00040, 1000.0


def _trail_bot(**over):
    s = settings(SYMBOLS="EURUSDm", TIMEFRAME="M5", FIXED_LOT=0.01,
                 ATR_PERIOD=14, TRAIL_ATR_MULT=1.5, TRAIL_START_MONEY=0.10,
                 **over)
    b = FakeBroker(price=ENTRY, per_price=PER, atr=ATR)
    return (*make_bot(s, b, ["EURUSDm"]), b)


def test_trailing_stop_ratchets_and_never_retreats():
    bot, session, _, b = _trail_bot()
    p = Position(1, "EURUSDm", "buy", 0.01, ENTRY, ENTRY - 0.0006,
                 ENTRY + 0.0015, 0.0)
    highest = p.sl
    for price in (ENTRY + 0.0005, ENTRY + 0.0010, ENTRY + 0.0020,
                  ENTRY + 0.0015, ENTRY + 0.0010):
        b.price = price
        p.profit = (price - ENTRY) * PER
        bot._trail_stops(session, [p])
        if 1 in b.modified:
            p.sl = b.modified[1][0]
        assert p.sl >= highest - 1e-12, "the stop moved backwards"
        highest = max(highest, p.sl)
    assert p.sl > ENTRY, "a trade that ran 20 pips should be locked in profit"


def test_trailing_waits_for_trail_start_money():
    bot, session, _, b = _trail_bot()
    p = Position(1, "EURUSDm", "buy", 0.01, ENTRY, ENTRY - 0.0006,
                 ENTRY + 0.0015, 0.05)
    b.price = ENTRY + 0.00005
    bot._trail_stops(session, [p])
    assert 1 not in b.modified, "trailed before TRAIL_START_MONEY was reached"


def test_trailing_respects_the_broker_minimum_stop():
    """A stop closer than the broker allows is rejected (10011) and lost."""
    bot, session, _, b = _trail_bot()
    b._min_stop = 0.00080
    b.price = ENTRY + 0.0020
    p = Position(1, "EURUSDm", "buy", 0.01, ENTRY, ENTRY - 0.0006,
                 ENTRY + 0.0015, 2.0)
    bot._trail_stops(session, [p])
    gap = b.price - b.modified[1][0]
    assert gap >= b._min_stop - 1e-9, f"stop only {gap} from price, would be rejected"


def test_trailing_shorts_ratchet_downward():
    bot, session, _, b = _trail_bot()
    p = Position(2, "EURUSDm", "sell", 0.01, ENTRY, ENTRY + 0.0006,
                 ENTRY - 0.0015, 0.0)
    lowest = p.sl
    for price in (ENTRY - 0.0005, ENTRY - 0.0010, ENTRY - 0.0020, ENTRY - 0.0010):
        b.price = price
        p.profit = (ENTRY - price) * PER
        bot._trail_stops(session, [p])
        if 2 in b.modified:
            p.sl = b.modified[2][0]
        assert p.sl <= lowest + 1e-12, "the short's stop moved backwards"
        lowest = min(lowest, p.sl)
    assert p.sl < ENTRY, "a short that ran should be locked in profit"


def _cap_bot(cap="1.0", **over):
    s = settings(SYMBOLS="GBPUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
                 MAX_LOSS_PER_TRADE=cap, **over)
    b = FakeBroker(price=1.34, per_price=PER)
    return (*make_bot(s, b, ["GBPUSDm"]), b)


def _losers():
    return [Position(1, "GBPUSDm", "buy", 0.01, 1.34, 1.339, 1.345, 2000.00),
            Position(2, "GBPUSDm", "buy", 0.01, 1.34, 1.339, 1.345, -0.40),
            Position(3, "GBPUSDm", "buy", 0.01, 1.34, 1.339, 1.345, -3.10)]


def test_loss_cap_closes_only_what_is_past_it():
    bot, session, _, b = _cap_bot()
    left = bot._enforce_loss_cap(session, _losers())
    assert b.closed == [3], f"closed {b.closed}, expected only the -3.10"
    assert [p.ticket for p in left] == [1, 2]


def test_loss_cap_is_off_by_default():
    bot, session, _, b = _cap_bot(cap="0")
    assert len(bot._enforce_loss_cap(session, _losers())) == 3
    assert not b.closed


def test_loss_cap_honours_a_per_symbol_override():
    bot, session, _, b = _cap_bot(cap="10", SYM_GBPUSDM_MAX_LOSS_PER_TRADE="1.0")
    bot._enforce_loss_cap(session, _losers())
    assert b.closed == [3], b.closed


def test_a_refused_close_is_reported_not_swallowed():
    from fmsbot.broker.base import BrokerError
    bot, session, msgs, b = _cap_bot()

    def refuse(ticket):
        raise BrokerError("market closed")
    b.close_position = refuse
    left = bot._enforce_loss_cap(session, _losers())
    assert len(left) == 3
    assert any("refused to close" in m for m in msgs), \
        "a position past the cap that will not close must be shouted about"
