"""
Monte Carlo expectancy simulation for AITrader Safe Mode (revised design).

THIS IS NOT A REAL BACKTEST. No historical price data, no MQL5 code, and no
MT5 Strategy Tester are involved. This is a pure mathematical simulation
that checks whether the *stated* SL/TP parameters produce positive
expectancy under a range of *assumed* win rates. It validates the design's
internal math, not real market behavior. Real backtesting requires the EA
to actually be built (Epic 1) and run through MT5's Strategy Tester against
historical tick data.
"""
import random

random.seed(42)

# Revised Safe Mode parameters
TIER_LOW = {"sl": 1.0, "tp": 1.50}   # equity < $50
TIER_HIGH = {"sl": 3.0, "tp": 3.00}  # equity >= $50

# Old Safe Mode parameters (shared with Aggressive Mode) for comparison
OLD_TIER_LOW = {"sl": 1.0, "tp": 0.50}
OLD_TIER_HIGH = {"sl": 3.0, "tp": 0.50}

COST_PER_TRADE = 0.05  # assumed spread+commission per round-trip trade at 0.01 lot (ILLUSTRATIVE, not from real Exness spec data)

WIN_RATES = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]
TRADES_PER_DAY = 20
N_DAYS_SIM = 20000
DAILY_LOSS_LIMIT_PCT = 0.03
DAILY_PROFIT_TARGET_PCT = 0.05


def expectancy_per_trade(tier, win_rate):
    return win_rate * tier["tp"] - (1 - win_rate) * tier["sl"] - COST_PER_TRADE


def breakeven_win_rate(tier):
    return tier["sl"] / (tier["sl"] + tier["tp"])


def simulate_day(tier, win_rate, starting_equity, max_trades):
    equity = starting_equity
    trades_taken = 0
    for _ in range(max_trades):
        loss_limit_hit = (starting_equity - equity) >= starting_equity * DAILY_LOSS_LIMIT_PCT
        profit_target_hit = (equity - starting_equity) >= starting_equity * DAILY_PROFIT_TARGET_PCT
        if loss_limit_hit or profit_target_hit:
            break
        win = random.random() < win_rate
        pnl = (tier["tp"] if win else -tier["sl"]) - COST_PER_TRADE
        equity += pnl
        trades_taken += 1
    return equity - starting_equity, trades_taken


def run_tier(tier_name, tier, starting_equity):
    print(f"\n--- {tier_name} (equity=${starting_equity}, SL=${tier['sl']}, TP=${tier['tp']}) ---")
    be = breakeven_win_rate(tier)
    print(f"Break-even win rate: {be*100:.1f}%")
    for wr in WIN_RATES:
        ev = expectancy_per_trade(tier, wr)
        daily_pnls = []
        target_hits = 0
        loss_limit_hits = 0
        for _ in range(N_DAYS_SIM):
            pnl, _ = simulate_day(tier, wr, starting_equity, TRADES_PER_DAY)
            daily_pnls.append(pnl)
            if pnl >= starting_equity * DAILY_PROFIT_TARGET_PCT * 0.99:
                target_hits += 1
            if pnl <= -starting_equity * DAILY_LOSS_LIMIT_PCT * 0.99:
                loss_limit_hits += 1
        avg_daily = sum(daily_pnls) / len(daily_pnls)
        pct_profitable_days = sum(1 for p in daily_pnls if p > 0) / len(daily_pnls) * 100
        print(f"  win_rate={wr*100:>4.0f}%  EV/trade=${ev:+.3f}  avg_daily_pnl=${avg_daily:+.3f} "
              f"({avg_daily/starting_equity*100:+.2f}%/day)  profitable_days={pct_profitable_days:5.1f}%  "
              f"hit_5%_target={target_hits/N_DAYS_SIM*100:5.1f}%  hit_3%_loss_limit={loss_limit_hits/N_DAYS_SIM*100:5.1f}%")


print("=" * 90)
print("REVISED SAFE MODE (own TP, not sharing Aggressive Mode's $0.50 target)")
print("=" * 90)
run_tier("< $50 tier", TIER_LOW, 40)
run_tier(">= $50 tier", TIER_HIGH, 100)

print("\n" + "=" * 90)
print("OLD SAFE MODE (for comparison — shared Aggressive Mode's $0.50 TP)")
print("=" * 90)
run_tier("< $50 tier (OLD)", OLD_TIER_LOW, 40)
run_tier(">= $50 tier (OLD)", OLD_TIER_HIGH, 100)
