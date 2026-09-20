"""A shut market is not a broken symbol.

At 01:00 the broker rejected a gold order with "(10017): session closed".
10017 was on the permanent list, so the bot retired gold for the rest of
the session — the only instrument on this account whose movement beats
its own spread, taken out by its own daily break, while five symbols that
cannot pay their spread kept trading.
"""

import time

from fmsbot.bot import (SESSION_RETRY_SECONDS, _is_closed_market,
                        _is_permanent_symbol_error)
from fmsbot.broker.base import BrokerError
from tests.helpers import FakeBroker, make_bot, settings

LIVE = BrokerError("Order rejected (10017): session closed")


def test_the_live_rejection_is_read_as_temporary():
    assert _is_closed_market(LIVE)
    assert not _is_permanent_symbol_error(LIVE)


def test_a_symbol_the_account_may_never_trade_is_still_permanent():
    for text in ("Order rejected (10017): Trading is disabled for this SYMBOL",
                 "Symbol XAUUSD247m does not exist on this account",
                 "trade disabled on this account type"):
        assert _is_permanent_symbol_error(BrokerError(text)), text


def test_every_wording_a_broker_uses_for_shut_is_recognised():
    for text in ("session closed", "Market closed", "the market is closed",
                 "Order rejected (10018)"):
        assert _is_closed_market(BrokerError(text)), text


def _session():
    s = settings(SYMBOLS="XAUUSDm,EURUSDm")
    bot, session, messages = make_bot(s, FakeBroker(), ["XAUUSDm", "EURUSDm"])
    return bot, session, messages


def test_a_paused_symbol_leaves_the_active_list_and_comes_back():
    _, session, _ = _session()
    session.retry_symbol_at["XAUUSDm"] = time.time() + 60
    assert session.active_symbols() == ["EURUSDm"]

    session.retry_symbol_at["XAUUSDm"] = time.time() - 1
    assert session.active_symbols() == ["XAUUSDm", "EURUSDm"]
    assert "XAUUSDm" not in session.retry_symbol_at, "the pause must clear"


def test_a_permanently_disabled_symbol_does_not_come_back_on_its_own():
    _, session, _ = _session()
    session.disabled_symbols["XAUUSDm"] = "trade disabled"
    assert session.active_symbols() == ["EURUSDm"]
    assert session.active_symbols() == ["EURUSDm"], "it must stay gone"


def test_the_pause_is_long_enough_to_be_worth_taking():
    """Retrying every two seconds through a nine-hour weekend gap is how
    a phone gets three thousand identical messages."""
    assert SESSION_RETRY_SECONDS >= 600


def test_the_two_states_are_reported_differently():
    """One says "fix your symbol list", the other says "wait" — telling
    them apart is the difference between editing settings at 1am and
    going to bed."""
    from fmsbot import bot as botmod
    assert botmod._is_closed_market(LIVE)
    permanent = BrokerError("Trading is disabled for this SYMBOL")
    assert botmod._is_permanent_symbol_error(permanent)
    assert not botmod._is_closed_market(permanent)


# -- writing the symbol list to the key that actually supplies it ------

def test_a_profile_overrules_the_plain_symbol_list():
    """With ACTIVE_BROKER=exness the list comes from BROKER_EXNESS_SYMBOLS.
    A tool writing SYMBOLS would be silently overruled: the change looks
    made, the bot keeps trading the old list, nothing says so."""
    import os
    from fmsbot.config import symbols_env_key

    os.environ.pop("BROKER_EXNESS_SYMBOLS", None)
    assert symbols_env_key("exness") == "SYMBOLS"
    os.environ["BROKER_EXNESS_SYMBOLS"] = "EURUSDm,XAUUSDm"
    try:
        assert symbols_env_key("exness") == "BROKER_EXNESS_SYMBOLS"
        assert symbols_env_key("") == "SYMBOLS", "no profile, no override"
    finally:
        del os.environ["BROKER_EXNESS_SYMBOLS"]


def test_an_empty_profile_list_falls_back_rather_than_pointing_nowhere():
    import os
    from fmsbot.config import symbols_env_key
    os.environ["BROKER_EXNESS_SYMBOLS"] = "   "
    try:
        assert symbols_env_key("exness") == "SYMBOLS"
    finally:
        del os.environ["BROKER_EXNESS_SYMBOLS"]
