"""A win must not be structurally smaller than a loss.

Eight live trades: 6 wins, 2 losses — a 75% win rate — and net +$0.56.
Average win $1.97, average loss $5.63. The break-even win rate at that
size ratio is 74%, so 75% bought $0.07 a trade. The win rate was carrying
the entire strategy, which is the definition of no margin.
"""

from fmsbot.broker.base import Position
from fmsbot.strategy import Signal

from .helpers import FakeBroker, make_bot, settings

PRICE, PER = 1.16600, 1000.0


def _bot(**over):
    env = dict(SYMBOLS="EURUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
               MAX_SPREAD_RATIO=0, MIN_REWARD_COST_RATIO=0,
               LIVE_REQUIRES_EVIDENCE="false")
    env.update(over)
    s = settings(**env)
    b = FakeBroker(price=PRICE, per_price=PER, spread=0.00008)
    return (*make_bot(s, b, ["EURUSDm"]), b, s)


def _sent(b):
    _, _, volume, sl, tp = b.orders[0]
    return abs(PRICE - sl), abs(tp - PRICE)


def test_a_target_smaller_than_the_stop_is_widened_not_sent():
    bot, session, _, b, s = _bot(MIN_REWARD_RISK=2.0)
    # the shape that produced the live result: reward half the risk
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0005, "t"), PRICE)
    assert b.orders, session.last_block
    risk, reward = _sent(b)
    assert reward / risk >= 2.0 - 1e-9, f"sent {reward/risk:.2f}R"


def test_a_target_already_good_enough_is_left_alone():
    bot, session, _, b, s = _bot(MIN_REWARD_RISK=2.0)
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0030, "t"), PRICE)
    risk, reward = _sent(b)
    assert abs(reward - 0.0030) < 1e-9, "widened a target that was already 3R"


def test_it_is_off_by_default():
    bot, session, _, b, s = _bot()
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0005, "t"), PRICE)
    risk, reward = _sent(b)
    assert abs(reward - 0.0005) < 1e-9, "changed the target with no floor set"


def test_widening_the_target_never_widens_the_stop():
    """Risk is set by the stop. Reward must be free to move; risk must not."""
    bot, session, _, b, s = _bot(MIN_REWARD_RISK=3.0)
    bot._maybe_trade(session, "EURUSDm",
                     Signal("buy", 0.0010, 0.0002, "t"), PRICE)
    risk, reward = _sent(b)
    assert abs(risk - 0.0010) < 1e-9, f"the stop moved to {risk}"
    assert reward / risk >= 3.0 - 1e-9


def test_a_ladder_locking_less_than_a_stop_is_reported():
    """The live shape: locked wins of ~1.50 against stops of ~5.63."""
    s = settings(SYMBOLS="EURUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
                 PROFIT_STAGES="0.75:1.50")
    b = FakeBroker(price=PRICE, per_price=PER)
    bot, session, msgs = make_bot(s, b, ["EURUSDm"])
    # stop 0.00563 away = $5.63 at 0.01 lot; target well beyond
    p = Position(1, "EURUSDm", "buy", 0.01, PRICE, PRICE - 0.00563,
                 PRICE + 0.0200, 2.00)
    bot._protect_profits(session, [p])
    assert any("SMALLER THAN A LOSS" in m for m in msgs), msgs
    warning = next(m for m in msgs if "SMALLER THAN A LOSS" in m)
    assert "0.27x" in warning, warning       # 1.50 / 5.63
    assert "79%" in warning, warning         # break-even win rate


def test_a_ladder_locking_more_than_a_stop_is_not_reported():
    s = settings(SYMBOLS="EURUSDm", TIMEFRAME="M1", FIXED_LOT=0.01,
                 PROFIT_STAGES="1.00:6.00")
    b = FakeBroker(price=PRICE, per_price=PER)
    bot, session, msgs = make_bot(s, b, ["EURUSDm"])
    p = Position(1, "EURUSDm", "buy", 0.01, PRICE, PRICE - 0.00563,
                 PRICE + 0.0200, 2.00)
    bot._protect_profits(session, [p])
    assert not any("SMALLER THAN A LOSS" in m for m in msgs), msgs


def test_the_live_eight_trades_would_have_cleared_the_floor():
    """With reward at 2x risk, the same 75% win rate is genuinely profitable."""
    wins, losses = 6, 2
    risk = 5.63
    old_win, new_win = 1.97, risk * 2.0
    old = (wins * old_win - losses * risk) / (wins + losses)
    new = (wins * new_win - losses * risk) / (wins + losses)
    assert old < 0.10, old
    assert new > 7.0, new
