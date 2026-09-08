"""The pause-time review, and announcing when the pause ends.

The live log showed a pause at 19:12 and nothing until a restart at
20:19. The pause really was 15 minutes; the silence after it was
indistinguishable from a fault, which is its own problem.
"""

import time

from fmsbot import review
from fmsbot.broker.base import Bar

from .helpers import FakeBroker, make_bot, settings


class HistoryBroker(FakeBroker):
    """Serves as much history as asked for."""

    def __init__(self, n=8000, **kw):
        super().__init__(**kw)
        self.n = n
        self.asked = []

    def bars(self, symbol, timeframe, count):
        self.asked.append((symbol, timeframe, count))
        import random
        rnd = random.Random(hash(symbol) % 1000)
        px, out = self.price, []
        for i in range(min(count, self.n)):
            o = px
            px = o + rnd.gauss(0, self.price * 0.0002)
            out.append(Bar(i * 60, o, max(o, px) * 1.0001,
                           min(o, px) * 0.9999, px))
        return out


def _s(**over):
    env = dict(SYMBOLS="EURUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
               ATR_SL_MULT=1.5, ATR_TP_MULT=2.0, REVIEW_DAYS=90,
               MAX_CONSECUTIVE_LOSSES=3, LOSS_PAUSE_MINUTES=10)
    env.update(over)
    return settings(**env)


def test_it_asks_for_three_months_at_the_entry_timeframe():
    s = _s(TIMEFRAME="M1", REVIEW_DAYS=90)
    b = HistoryBroker(price=1.166, per_price=1000.0)
    review.review_symbol(s, b, "EURUSDm", "ema_cross", 90, 1000.0)
    symbol, timeframe, count = b.asked[0]
    assert timeframe == "M1"
    assert count == 90 * 24 * 60, count      # 129,600 M1 bars


def test_a_replay_produces_a_verdict_not_an_exception():
    s = _s()
    b = HistoryBroker(price=1.166, per_price=1000.0)
    row = review.review_symbol(s, b, "EURUSDm", "ema_cross", 90, 1000.0)
    assert row.bars > 0 and row.days > 0
    assert isinstance(row.profit_factor, float)


def test_a_symbol_without_history_is_reported_not_crashed():
    s = _s()
    b = HistoryBroker(n=10, price=1.166, per_price=1000.0)
    row = review.review_symbol(s, b, "EURUSDm", "ema_cross", 90, 1000.0)
    assert row.bars == 0 and "only" in row.note


def test_the_report_never_claims_to_have_dropped_a_symbol():
    """A backtest is a reason to look, never a reason to change what trades."""
    rows = [review.SymbolReview(symbol="XAGUSDm", bars=9000, days=90,
                                trades=60, profit_factor=0.4, net=-300.0,
                                win_rate=25.0, note="LOSING over this window")]
    text = review.format_review(rows, 90, "M1", {})
    assert "LOSING on this window: XAGUSDm" in text
    assert "have not dropped" in text
    assert "REAL results" in text


def test_the_report_says_it_did_not_search_for_parameters():
    text = review.format_review([], 90, "M1", {})
    assert "find_edge.py" in text
    assert "noise becomes a strategy" in text


def test_re_measured_exits_are_applied_to_the_live_settings():
    s = _s(TIMEFRAME="M1", ATR_SL_MULT=0.2)      # far too tight for the spread
    b = HistoryBroker(price=1.166, per_price=1000.0, spread=0.00030)
    bot, session, msgs = make_bot(s, b, ["EURUSDm"])
    bot._start_review(session)
    for _ in range(200):
        if not session.reviewing:
            break
        time.sleep(0.05)
    assert not session.reviewing, "review never finished"
    over = s.symbol_overrides.get("EURUSDM", {})
    assert over, "a stop far too tight for the spread should have been re-measured"
    assert over["atr_sl_mult"] > 0.2, over
    assert any("Review" in m for m in msgs)


def test_only_one_review_runs_at_a_time():
    s = _s()
    b = HistoryBroker(price=1.166, per_price=1000.0)
    bot, session, _ = make_bot(s, b, ["EURUSDm"])
    session.reviewing = True
    bot._start_review(session)          # must not start a second
    assert session.reviewing


def test_the_end_of_a_pause_is_announced_exactly_once():
    s = _s()
    b = FakeBroker()
    bot, session, msgs = make_bot(s, b, ["EURUSDm"])

    session.risk.stats.paused_until = time.time() + 600
    bot._announce_pause_end(session)
    assert not msgs, "announced the end while still paused"

    session.risk.stats.paused_until = time.time() - 1
    bot._announce_pause_end(session)
    assert sum("resume" in m for m in msgs) == 1, msgs
    bot._announce_pause_end(session)
    bot._announce_pause_end(session)
    assert sum("resume" in m for m in msgs) == 1, "announced more than once"


def test_a_pause_that_never_happened_is_not_announced():
    s = _s()
    bot, session, msgs = make_bot(s, FakeBroker(), ["EURUSDm"])
    session.risk.stats.paused_until = 0.0
    bot._announce_pause_end(session)
    assert not msgs
