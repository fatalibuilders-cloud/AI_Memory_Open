"""Position size must match the stop the order is actually sent with.

Live, on a $99,146 account configured for 0.5% risk (~$496 a trade), two
positions closed at exactly -3000.00 within a minute of each other -- six
times the intended risk, and together three times the 2% daily limit.

The cause: size was computed from the strategy's stop, then the stop was
widened to the broker's minimum and the size was never recomputed. A stop
widened 6x loses 6x.
"""

from fmsbot.strategy import Signal

from .helpers import FakeBroker, make_bot, settings

BALANCE = 99146.50


class SizingBroker(FakeBroker):
    """Sizes by risk the way a real broker does, and has a minimum stop."""

    def __init__(self, min_stop, per_lot=100000.0, **kw):
        super().__init__(**kw)
        self._min_stop = min_stop
        self.per_lot = per_lot
        self._balance = BALANCE

    def value_per_price(self, symbol, volume):
        return self.per_lot * volume

    def volume_for_risk(self, symbol, distance, amount):
        if distance <= 0:
            return 0.01
        raw = amount / (distance * self.per_lot)
        return max(0.01, round(raw, 2))

    def volume_from_lots(self, symbol, lots):
        return max(0.01, lots)


def _bot(min_stop, **over):
    env = dict(SYMBOLS="EURUSDm", TIMEFRAME="M5", FIXED_LOT=0,
               RISK_PCT=0.5, DAILY_LOSS_LIMIT_PCT=2,
               MAX_SPREAD_RATIO=0, MIN_REWARD_COST_RATIO=0,
               LIVE_REQUIRES_EVIDENCE="false")
    env.update(over)
    s = settings(**env)
    b = SizingBroker(min_stop, price=1.16600, spread=0.00008)
    return (*make_bot(s, b, ["EURUSDm"]), b, s)


def _risk_taken(broker):
    """What the sent order actually puts at risk."""
    symbol, side, volume, sl, tp = broker.orders[0]
    return abs(broker.price - sl) * broker.value_per_price(symbol, volume)


def test_size_is_recomputed_when_the_broker_widens_the_stop():
    """The exact live failure: a 6x widening must not become a 6x loss."""
    bot, session, _, b, s = _bot(min_stop=0.0060)      # 6x the strategy stop
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0020, "t"), 1.16600)
    assert b.orders, f"no order placed: {session.last_block}"
    allowed = BALANCE * 0.5 / 100
    taken = _risk_taken(b)
    assert taken <= allowed * 1.1, (
        f"risked {taken:.2f} against an allowance of {allowed:.2f} "
        f"— this is the -3000 bug")


def test_size_is_recomputed_when_a_cash_stop_replaces_the_atr_stop():
    bot, session, _, b, s = _bot(min_stop=0.0, SL_MONEY=200.0)
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0020, "t"), 1.16600)
    assert b.orders, session.last_block
    allowed = BALANCE * 0.5 / 100
    assert _risk_taken(b) <= allowed * 1.1, _risk_taken(b)


def test_an_order_that_cannot_be_sized_small_enough_is_refused():
    """The smallest lot is not always small enough. Then you do not trade."""
    bot, session, msgs, b, s = _bot(min_stop=0.0060)
    b.per_lot = 100_000_000.0            # 0.01 lot alone blows the budget
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0020, "t"), 1.16600)
    assert not b.orders, "sent an order it could not size safely"
    assert "refused" in session.last_block, session.last_block
    assert any("refused" in m for m in msgs)


def test_no_single_trade_may_spend_the_whole_daily_budget():
    """Two of these took 6% of the account against a 2% daily limit."""
    bot, session, _, b, s = _bot(min_stop=0.0, FIXED_LOT=5.0, RISK_PCT=0.5)
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0100, 0.0200, "t"), 1.16600)
    if b.orders:
        budget = BALANCE * 2 / 100
        assert _risk_taken(b) <= budget, (
            f"one trade risks {_risk_taken(b):.2f} of a {budget:.2f} daily "
            f"budget, which makes the daily limit decorative")


def test_the_per_trade_cap_is_an_absolute_ceiling():
    bot, session, _, b, s = _bot(min_stop=0.0, FIXED_LOT=1.0,
                                 MAX_LOSS_PER_TRADE=50.0)
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0020, "t"), 1.16600)
    assert not b.orders, "ignored MAX_LOSS_PER_TRADE when sizing by fixed lot"
    assert "MAX_LOSS_PER_TRADE" in session.last_block


def test_a_normal_trade_still_goes_through():
    """The guard must not refuse everything."""
    bot, session, _, b, s = _bot(min_stop=0.0)
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0020, "t"), 1.16600)
    assert b.orders, f"a well-sized trade was refused: {session.last_block}"
    allowed = BALANCE * 0.5 / 100
    assert abs(_risk_taken(b) - allowed) < allowed * 0.15, _risk_taken(b)
