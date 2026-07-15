"""
Monte Carlo risk-of-ruin simulation for FatalibuildersTrader Scalper 1's
Aggressive Mode (2026-07-14y).

THIS IS NOT A REAL BACKTEST. No historical price data, no MQL5 code, and no
MT5 Strategy Tester are involved. This is a pure mathematical simulation
answering one question: "if Aggressive Mode risks a fixed PERCENTAGE of
current equity on every trade with a 1:1 reward, what's the probability of
the account falling to near-zero, at various assumed real win rates?"

Origin: founder asked for a "very very aggressive bot" with "20% of blowing
a $100 [account] with an 80% equity winning rate." Two questions bundled
into one request, so this simulation separates them:
  1. At the HOPED-FOR 80% win rate, is ~20% ruin probability realistic?
  2. If not, what combination of (win rate, risk-per-trade) DOES produce
     something close to a 20% ruin probability, so the number can be
     understood honestly instead of just asserted?

RUIN is defined here as equity falling to $10 or below (90% of a $100
starting balance lost) at any point within N trades -- a stand-in for
"blowing the account," not literally $0 (a broker would stop the account
from actually reaching $0 well before that via margin calls anyway).
"""
import random

random.seed(42)

STARTING_EQUITY = 100.0
RUIN_THRESHOLD = 10.0
N_SIMULATIONS = 20000
TRADE_COUNTS = [50, 100, 200]


def simulate_ruin_probability(risk_pct, reward_pct, win_rate, n_trades, n_sims):
    ruin_count = 0
    for _ in range(n_sims):
        equity = STARTING_EQUITY
        for _ in range(n_trades):
            if equity <= RUIN_THRESHOLD:
                break
            risk_dollars = equity * (risk_pct / 100.0)
            reward_dollars = equity * (reward_pct / 100.0)
            win = random.random() < win_rate
            equity += reward_dollars if win else -risk_dollars
        if equity <= RUIN_THRESHOLD:
            ruin_count += 1
    return ruin_count / n_sims * 100.0


print("=" * 95)
print("PART 1 -- At the HOPED-FOR 80% win rate, across a range of risk-per-trade sizes,")
print("is ~20% ruin probability realistic?")
print("=" * 95)
for risk_pct in [3, 5, 10, 15, 20]:
    for n in TRADE_COUNTS:
        p = simulate_ruin_probability(risk_pct, risk_pct, 0.80, n, N_SIMULATIONS)
        print(f"  risk/reward={risk_pct:>2}% of equity, win_rate=80%, trades={n:>3}  ->  ruin probability = {p:5.2f}%")

print()
print("=" * 95)
print("PART 2 -- At more REALISTIC (unproven-strategy) win rates, what risk-per-trade")
print("produces something close to a 20% ruin probability?")
print("=" * 95)
for win_rate in [0.50, 0.55, 0.60]:
    for risk_pct in [10, 15, 20]:
        for n in [50, 100]:
            p = simulate_ruin_probability(risk_pct, risk_pct, win_rate, n, N_SIMULATIONS)
            print(f"  win_rate={win_rate*100:>4.0f}%  risk/reward={risk_pct:>2}% of equity  trades={n:>3}  ->  ruin probability = {p:5.2f}%")

print()
print("=" * 95)
print("CHOSEN DEFAULT: 15% risk-per-trade, 15% reward-per-trade (1:1), $100 start")
print("=" * 95)
for win_rate in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
    p50 = simulate_ruin_probability(15, 15, win_rate, 50, N_SIMULATIONS)
    p100 = simulate_ruin_probability(15, 15, win_rate, 100, N_SIMULATIONS)
    print(f"  win_rate={win_rate*100:>4.0f}%  ->  ruin probability @ 50 trades = {p50:5.2f}%   @ 100 trades = {p100:5.2f}%")
