"""Entry gates: per-symbol settings, the evidence gate, and the filters.

Includes the two faults that made every trade impossible or unprotected:
_maybe_trade reading `cfg` before assigning it, and a chained edit that
pulled the filters' return statements out of their guards.
"""

from fmsbot.strategy import Signal

from .helpers import FakeBroker, make_bot, settings

MARKET = {   # spread, min stop, $ per 1.0 price at 0.01 lot, price
    "EURUSDm": (0.00008, 0.0, 1000.0, 1.16600),
    "XAUUSDm": (0.26, 0.10, 1.0, 3400.00),
}


def _broker(symbol):
    spread, min_stop, per, price = MARKET[symbol]
    return FakeBroker(price=price, per_price=per, spread=spread,
                      min_stop=min_stop, balance=1000.0)


def test_a_trade_is_actually_placed():
    """Guards the NameError that made every entry raise."""
    s = settings(SYMBOLS="EURUSDm", TIMEFRAME="M5", FIXED_LOT=0.01,
                 ATR_SL_MULT=1.5, ATR_TP_MULT=2.0, LIVE_REQUIRES_EVIDENCE="false")
    b = _broker("EURUSDm")
    bot, session, _ = make_bot(s, b, ["EURUSDm"])
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0008, 0.00107, "t"), 1.16600)
    assert len(b.orders) == 1, f"no order was placed: {session.last_block}"


def test_per_symbol_settings_reach_the_order():
    s = settings(SYMBOLS="EURUSDm,XAUUSDm", TIMEFRAME="M5", FIXED_LOT=0.01,
                 ATR_SL_MULT=1.5, ATR_TP_MULT=2.0, SL_MONEY=0.50, TP_MONEY=0.50,
                 LIVE_REQUIRES_EVIDENCE="false",
                 SYM_EURUSDM_SL_MONEY=0.80, SYM_EURUSDM_TP_MONEY=1.07,
                 SYM_XAUUSDM_SL_MONEY=2.25, SYM_XAUUSDM_TP_MONEY=3.00)
    for symbol, want_risk in (("EURUSDm", 0.80), ("XAUUSDm", 2.25)):
        b = _broker(symbol)
        bot, session, _ = make_bot(s, b, [symbol])
        bot._maybe_trade(session, symbol,
                         Signal("buy", 0.001, 0.0015, "t"), MARKET[symbol][3])
        assert b.orders, f"{symbol}: {session.last_block}"
        _, _, _, sl, _ = b.orders[0]
        risk = abs(MARKET[symbol][3] - sl) * MARKET[symbol][2]
        assert abs(risk - want_risk) < 0.01, (symbol, risk, want_risk)


def test_symbol_names_match_regardless_of_suffix_or_spaces():
    from fmsbot.config import symbol_key
    assert symbol_key("EURUSDm") == "EURUSDM"
    assert symbol_key("Volatility 75 Index") == "VOLATILITY75INDEX"
    s = settings(SYMBOLS="Volatility 75 Index", SYM_VOLATILITY75INDEX_TP_MONEY=9.0)
    assert s.for_symbol("Volatility 75 Index").tp_money == 9.0


def test_the_spread_filter_blocks_only_when_it_should():
    """The return must sit inside its guard, not fire unconditionally."""
    s = settings(SYMBOLS="EURUSDm", TIMEFRAME="M5", FIXED_LOT=0.01,
                 MAX_SPREAD_RATIO=0.25, LIVE_REQUIRES_EVIDENCE="false")
    # a stop far wider than the spread must pass
    b = _broker("EURUSDm")
    bot, session, _ = make_bot(s, b, ["EURUSDm"])
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0015, "t"), 1.16600)
    assert b.orders, f"a 12x-spread stop was wrongly blocked: {session.last_block}"

    # a stop barely wider than the spread must not
    b2 = _broker("EURUSDm")
    bot2, session2, _ = make_bot(s, b2, ["EURUSDm"])
    bot2._maybe_trade(session2, "EURUSDm",
                      Signal("buy", 0.0001, 0.0002, "t"), 1.16600)
    assert not b2.orders, "a stop only 1.25x the spread should have been refused"


def test_the_reward_versus_cost_filter_blocks_only_when_it_should():
    s = settings(SYMBOLS="XAUUSDm", TIMEFRAME="M5", FIXED_LOT=0.01,
                 MIN_REWARD_COST_RATIO=1.5, MAX_SPREAD_RATIO=0,
                 LIVE_REQUIRES_EVIDENCE="false")
    b = _broker("XAUUSDm")
    bot, session, _ = make_bot(s, b, ["XAUUSDm"])
    bot._maybe_trade(session, "XAUUSDm", Signal("buy", 2.25, 3.0, "t"), 3400.0)
    assert b.orders, f"a 11x-cost target was wrongly blocked: {session.last_block}"

    b2 = _broker("XAUUSDm")
    bot2, session2, _ = make_bot(s, b2, ["XAUUSDm"])
    bot2._maybe_trade(session2, "XAUUSDm", Signal("buy", 2.25, 0.30, "t"), 3400.0)
    assert not b2.orders, "a target barely above the spread should be refused"


def test_real_money_needs_a_proven_configuration():
    s = settings(SYMBOLS="EURUSDm", TIMEFRAME="M5", FIXED_LOT=0.01)
    for demo, expect in ((True, True), (False, False), (None, False)):
        b = _broker("EURUSDm")
        b._demo = demo
        bot, session, _ = make_bot(s, b, ["EURUSDm"])
        bot._maybe_trade(session, "EURUSDm",
                         Signal("buy", 0.0008, 0.0012, "t"), 1.16600)
        assert bool(b.orders) is expect, (demo, session.last_block)


def test_the_evidence_gate_can_be_switched_off_deliberately():
    s = settings(SYMBOLS="EURUSDm", TIMEFRAME="M5", FIXED_LOT=0.01,
                 LIVE_REQUIRES_EVIDENCE="false")
    b = _broker("EURUSDm")
    b._demo = False
    bot, session, _ = make_bot(s, b, ["EURUSDm"])
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0008, 0.0012, "t"), 1.16600)
    assert b.orders, "an explicit override must be honoured"
