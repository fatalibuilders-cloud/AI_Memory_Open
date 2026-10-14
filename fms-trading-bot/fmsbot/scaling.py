"""Size the account's limits to the account's balance.

Every configuration problem in this project has had the same shape: the
broker's smallest trade is 0.01 lot, and what that costs is fixed while
the balance is not. On $100 a 21-pip EURUSD stop is 2.1% of everything;
on $10,000 the same trade is 0.02%. A single set of percentages cannot
be right at both ends, and a percentage can never buy a fraction of the
minimum lot — which is how a 0.5% rule came to refuse every order on a
hundred-dollar account.

So the limits move with the balance instead of the operator moving them.
What does NOT move is the strategy: the entries, exits and timeframe are
identical in every tier, which is why the evidence record survives a tier
change. The same trades, sized differently, are still evidence about the
same thing.

Risk per trade FALLS as the account grows, because the minimum lot stops
binding. It rises as the account shrinks, because below a certain size
there is no other way to place a trade at all — that is the honest cost
of trading a small account, and it is stated here rather than hidden.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    name: str
    #: Smallest balance this tier applies to.
    floor: float
    fixed_lot: float
    risk_pct: float
    max_loss_per_trade: float
    daily_loss_limit_pct: float
    max_trades_per_day: int
    note: str


#: Largest balance first; tier_for walks down until one fits.
TIERS = (
    Tier("full", 10_000.0, 0.0, 0.5, 0.0, 2.0, 8,
         "Risk sizing does the work: 0.5% a trade is many minimum lots, so "
         "the broker's floor no longer decides anything."),
    Tier("standard", 2_000.0, 0.0, 0.5, 0.0, 3.0, 10,
         "0.5% is about 10.00 a trade here — enough for the stop distance "
         "to choose the size rather than the other way round."),
    Tier("small", 500.0, 0.01, 1.0, 5.00, 6.0, 6,
         "Still on the broker's smallest lot, so the stop decides the risk "
         "and a cash cap bounds it. The widest stops are refused."),
    Tier("micro", 0.0, 0.01, 3.0, 3.00, 10.0, 4,
         "The minimum lot risks 1-5% of this balance whatever the settings "
         "say. These percentages are reckless on real capital and the only "
         "ones that let a demo of this size trade at all."),
)

#: The settings a tier owns. Everything else is left alone.
FIELDS = ("fixed_lot", "risk_pct", "max_loss_per_trade",
          "daily_loss_limit_pct", "max_trades_per_day")


def tier_for(balance: float) -> Tier:
    """The tier this balance belongs to."""
    for tier in TIERS:
        if balance >= tier.floor:
            return tier
    return TIERS[-1]


def changes(settings, tier: Tier) -> list[tuple[str, object, object]]:
    """(field, from, to) for each setting this tier would change."""
    out = []
    for field in FIELDS:
        old, new = getattr(settings, field), getattr(tier, field)
        if old != new:
            out.append((field, old, new))
    return out


def apply(settings, tier: Tier) -> list[tuple[str, object, object]]:
    """Move the settings onto this tier. Returns what changed."""
    moved = changes(settings, tier)
    for field, _, new in moved:
        setattr(settings, field, new)
    return moved


def describe(tier: Tier, balance: float) -> str:
    """What this tier means for this balance, in money."""
    per_trade = (tier.max_loss_per_trade if tier.fixed_lot > 0
                 else balance * tier.risk_pct / 100.0)
    budget = balance * tier.daily_loss_limit_pct / 100.0
    room = int(budget / per_trade) if per_trade > 0 else 0
    lines = [
        f"balance {balance:,.2f} — tier '{tier.name}'",
        (f"  {tier.fixed_lot:g} lot, at most {per_trade:.2f} a trade"
         if tier.fixed_lot > 0
         else f"  {tier.risk_pct:g}% a trade, about {per_trade:.2f}"),
        f"  {tier.daily_loss_limit_pct:g}% a day = {budget:.2f}, "
        f"about {room} losing trades",
        f"  up to {tier.max_trades_per_day} trades a day",
        f"  {tier.note}",
    ]
    return "\n".join(lines)
