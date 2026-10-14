"""Limits that move with the balance.

Every configuration failure in this project had one shape: the broker's
smallest trade is 0.01 lot, what it costs is fixed, and the balance is
not. On $100 a 21-pip EURUSD stop is 2.1% of everything; on $10,000 the
same trade is 0.02%. One set of percentages cannot be right at both ends
— a 0.5% rule refused every order on a hundred-dollar account, because a
percentage cannot buy a fraction of the minimum lot.
"""

from fmsbot.evidence import fingerprint
from fmsbot.scaling import FIELDS, TIERS, apply, changes, describe, tier_for
from tests.helpers import FakeBroker, make_bot, settings

#: 0.01 lot of a USD-quoted pair, per pip.
PIP = 0.10


def test_the_hundred_dollar_account_lands_on_micro():
    assert tier_for(100.0).name == "micro"
    assert tier_for(0.0).name == "micro"


def test_every_balance_has_a_tier():
    for balance in (0.0, 1.0, 499.0, 500.0, 1999.0, 2000.0, 9999.0, 1e7):
        assert tier_for(balance) is not None


def test_the_tiers_are_ordered_and_do_not_overlap():
    floors = [t.floor for t in TIERS]
    assert floors == sorted(floors, reverse=True), floors
    assert len(set(floors)) == len(floors)


def test_risk_per_trade_falls_as_the_account_grows():
    """The minimum lot stops binding, so the percentage can come down."""
    def share(balance):
        t = tier_for(balance)
        money = (t.max_loss_per_trade if t.fixed_lot > 0
                 else balance * t.risk_pct / 100)
        return money / balance
    shares = [share(b) for b in (100, 900, 2500, 15000)]
    assert shares == sorted(shares, reverse=True), shares


def test_the_small_tiers_bound_the_trade_in_money_not_percent():
    """A percentage cannot buy a fraction of 0.01 lot, so below a certain
    size the only meaningful cap is a cash one."""
    for balance in (100.0, 900.0):
        t = tier_for(balance)
        assert t.fixed_lot > 0
        assert t.max_loss_per_trade > 0


def test_the_large_tiers_size_from_risk_instead():
    for balance in (2500.0, 50_000.0):
        t = tier_for(balance)
        assert t.fixed_lot == 0
        assert t.max_loss_per_trade == 0, "a cash cap would fight the sizing"


def test_every_tier_can_afford_the_broker_minimum_on_an_fx_pair():
    """The failure this exists to prevent: a cap below what the smallest
    possible trade costs refuses every order forever."""
    worst_stop = 52 * PIP          # the widest stop seen live, $5.20
    ordinary = 21 * PIP            # the typical one, $2.10
    for balance in (100.0, 900.0, 2500.0, 15_000.0):
        t = tier_for(balance)
        cap = (t.max_loss_per_trade if t.fixed_lot > 0
               else balance * t.risk_pct / 100)
        assert cap >= ordinary, (balance, cap)
        assert cap <= worst_stop or t.fixed_lot == 0, (balance, cap)


def test_every_tier_lets_the_day_hold_more_than_one_trade():
    """2% of $100 is $2 — less than one trade, so the day's first entry
    would be refused. That is how a daily limit becomes a dead bot."""
    for balance in (100.0, 900.0, 2500.0, 15_000.0):
        t = tier_for(balance)
        per_trade = (t.max_loss_per_trade if t.fixed_lot > 0
                     else balance * t.risk_pct / 100)
        budget = balance * t.daily_loss_limit_pct / 100
        assert budget >= 2 * per_trade, (balance, budget, per_trade)


def test_the_trade_cap_fits_the_daily_budget_in_every_tier():
    """A cap far above what the day's budget can pay for is decoration:
    the loss limit ends the day first, while the phone shows 9/1200 and
    nothing says which number is binding. Allowing 2.5x the loss count
    leaves room for the winners and scratches in between."""
    for balance in (100.0, 900.0, 2500.0, 15_000.0):
        t = tier_for(balance)
        per_trade = (t.max_loss_per_trade if t.fixed_lot > 0
                     else balance * t.risk_pct / 100)
        budget = balance * t.daily_loss_limit_pct / 100
        losses = budget / per_trade
        assert t.max_trades_per_day <= losses * 2.5, (
            balance, t.max_trades_per_day, losses)


# -- applying it -------------------------------------------------------

def test_apply_moves_only_the_fields_the_tier_owns():
    s = settings(SYMBOLS="EURUSDm", STRATEGY="liquidity_sweep",
                 TIMEFRAME="M15", RISK_PCT=0.5)
    before = (s.strategy, s.timeframe, s.rr_target, s.atr_sl_mult)
    apply(s, tier_for(100.0))
    assert (s.strategy, s.timeframe, s.rr_target, s.atr_sl_mult) == before


def test_applying_the_same_tier_twice_changes_nothing():
    s = settings(SYMBOLS="EURUSDm")
    apply(s, tier_for(100.0))
    assert apply(s, tier_for(100.0)) == []


def test_the_changes_are_reported_before_they_are_made():
    s = settings(SYMBOLS="EURUSDm", RISK_PCT=0.5)
    planned = changes(s, tier_for(100.0))
    assert any(f == "risk_pct" for f, _, _ in planned)
    apply(s, tier_for(100.0))
    assert changes(s, tier_for(100.0)) == []


def test_a_tier_change_does_not_throw_away_the_trade_record():
    """The strategy is identical in every tier — the same trades in a
    different size are still evidence about the same thing."""
    s = settings(SYMBOLS="EURUSDm", STRATEGY="liquidity_sweep",
                 TIMEFRAME="M15")
    before = fingerprint(s, "liquidity_sweep")
    apply(s, tier_for(15_000.0))
    assert fingerprint(s, "liquidity_sweep") == before


def test_describe_states_the_limits_in_money():
    text = describe(tier_for(100.0), 100.0)
    assert "micro" in text and "3.00" in text and "10.00" in text


# -- in the bot --------------------------------------------------------

def _bot(balance, **over):
    env = {"SYMBOLS": "EURUSDm", "AUTO_SCALE": "true"}
    env.update(over)
    s = settings(**env)
    bot, session, messages = make_bot(s, FakeBroker(balance=balance),
                                      ["EURUSDm"])
    bot.remote = type("R", (), {"broadcast": lambda self, m: messages.append(m)})()
    return bot, session, messages


def test_the_bot_sets_the_tier_and_says_so():
    bot, session, messages = _bot(100.0)
    bot._autoscale(session, announce=True)
    assert session.tier == "micro"
    assert bot.s.max_loss_per_trade == 3.00
    assert messages and "micro" in messages[0]


def test_nothing_moves_when_the_switch_is_off():
    bot, session, messages = _bot(100.0, AUTO_SCALE="false")
    before = bot.s.max_loss_per_trade
    bot._autoscale(session, announce=True)
    assert bot.s.max_loss_per_trade == before
    assert not messages


def test_a_quiet_recheck_on_the_same_tier_says_nothing():
    bot, session, messages = _bot(100.0)
    bot._autoscale(session, announce=True)
    messages.clear()
    bot._autoscale(session)
    assert not messages


def test_growing_past_a_boundary_is_announced_with_what_changed():
    bot, session, messages = _bot(100.0)
    bot._autoscale(session, announce=True)
    messages.clear()
    session.broker._balance = 3000.0
    bot._autoscale(session)
    assert session.tier == "standard"
    assert messages and "Changed:" in messages[0]
    assert "carries over" in messages[0]


def test_the_small_account_presets_turn_it_on():
    """The whole point: one configuration that works at $100 and at
    $100,000 without anyone re-running a preset."""
    import preset
    for name in ("micro", "small"):
        assert preset.PRESETS[name].get("AUTO_SCALE") == "true", name


def test_the_tiers_agree_with_the_preset_they_start_from():
    """A preset that contradicts the tier it lands on would be rewritten
    at startup, which is confusing even when it is right."""
    import preset
    from fmsbot.scaling import tier_for
    micro = tier_for(100.0)
    p = preset.PRESETS["micro"]
    assert float(p["FIXED_LOT"]) == micro.fixed_lot
    assert float(p["MAX_LOSS_PER_TRADE"]) == micro.max_loss_per_trade
    assert float(p["DAILY_LOSS_LIMIT_PCT"]) == micro.daily_loss_limit_pct
    assert int(p["MAX_TRADES_PER_DAY"]) == micro.max_trades_per_day
