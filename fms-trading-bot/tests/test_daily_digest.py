"""One message a day, whether or not anything happened.

"The bot has been idle some days yet connected" is the hardest thing to
diagnose after the fact: the hourly pace report only exists when a trade
rate is configured, and the preset for a small account sets that to zero
— so a quiet day produced no record at all, and the question could only
be answered by guessing.
"""

from datetime import date, timedelta

from fmsbot.evidence import Evidence
from fmsbot.pace import Pace
from fmsbot.risk import RiskManager
from tests.helpers import FakeBroker, make_bot, settings

BALANCE = 100.0


def _bot(**over):
    env = {"SYMBOLS": "EURUSDm", "DAILY_LOSS_LIMIT_PCT": 10.0,
           "MIN_TRADES_PER_HOUR": 0}
    env.update(over)
    s = settings(**env)
    bot, session, messages = make_bot(
        s, FakeBroker(balance=BALANCE), ["EURUSDm"],
        # The real session always has both; only their reporting is
        # switched off by a zero trade-rate target.
        pace=Pace(target_per_hour=0),
        evidence=Evidence(fingerprint="test"))
    bot.remote = type("R", (), {"broadcast": lambda self, m: messages.append(m)})()
    return bot, session, messages


def _end_the_day(session, equity=BALANCE, trades=0):
    """Roll the clock so the risk manager finishes yesterday."""
    session.risk.can_enter("EURUSDm", BALANCE, BALANCE, 0, 0)
    session.risk.stats.trades = trades
    session.risk.stats.day = date.today() - timedelta(days=1)
    session.risk.can_enter("EURUSDm", BALANCE, equity, 0, 0)


def test_a_day_with_trades_is_reported_with_its_result():
    bot, session, messages = _bot()
    _end_the_day(session, equity=BALANCE - 3.0, trades=4)
    bot._report_finished_day(session)
    assert messages, "nothing was said about the day"
    assert "4 trade(s)" in messages[0]
    assert "-3.00" in messages[0]


def test_a_quiet_day_says_what_refused_the_trades():
    bot, session, messages = _bot()
    for _ in range(12):
        session.pace.record_block("daily loss limit hit (-10.2%)")
    _end_the_day(session, trades=0)
    bot._report_finished_day(session)
    assert "No trades" in messages[0]
    assert "daily loss limit" in messages[0]


def test_a_quiet_day_with_nothing_refused_says_the_setup_never_came():
    """The answer that was impossible to get before: not broken, not
    blocked — no setup. On M15 that is an ordinary day."""
    bot, session, messages = _bot()
    _end_the_day(session, trades=0)
    bot._report_finished_day(session)
    assert "nothing refused any" in messages[0]
    assert "ordinary day" in messages[0]


def test_it_is_said_once_not_every_tick():
    bot, session, messages = _bot()
    _end_the_day(session, trades=2)
    bot._report_finished_day(session)
    bot._report_finished_day(session)
    bot._report_finished_day(session)
    assert len(messages) == 1, messages


def test_nothing_is_said_on_a_day_that_has_not_ended():
    bot, session, messages = _bot()
    session.risk.can_enter("EURUSDm", BALANCE, BALANCE, 0, 0)
    bot._report_finished_day(session)
    assert not messages


def test_the_blocks_are_cleared_so_tomorrow_starts_clean():
    """Yesterday's refusals explaining today's silence would be worse
    than saying nothing."""
    bot, session, messages = _bot()
    for _ in range(5):
        session.pace.record_block("EURUSDm cooldown (120s left)")
    _end_the_day(session, trades=0)
    bot._report_finished_day(session)
    assert not session.pace.blocks


def test_the_record_so_far_rides_along_with_the_day():
    bot, session, messages = _bot()
    session.evidence.record(+4.0)
    session.evidence.record(-2.0)
    _end_the_day(session, trades=2)
    bot._report_finished_day(session)
    assert "Record so far: 2 trades" in messages[0]
    assert "profit factor 2.00" in messages[0]


def test_a_first_day_with_no_history_is_not_announced_as_a_finished_one():
    """A fresh risk file has no previous day to report."""
    r = RiskManager(settings(SYMBOLS="EURUSDm"))
    assert r.finished_day is None
    r.can_enter("EURUSDm", BALANCE, BALANCE, 0, 0)
    assert r.finished_day is None
