# 2026-07-14y — "Scalper 1" name added + Aggressive Mode redesigned around equity-percentage risk

## Decision

Two changes, both from a single founder request delivered mid-turn: **"add Scalper 1 to the name"** and **"make it very very aggressive bot and has 20% of blowing a 100$ with a 80% equity winning rate."**

1. **Product/file renamed** to include "Scalper 1": `FatalibuildersTrader.mq5` → `FatalibuildersTraderScalper1.mq5`. `#property copyright`, all log-message prefixes, and the trade-comment string updated to "FatalibuildersTrader Scalper 1".

2. **Aggressive Mode's risk and reward per trade are now a PERCENTAGE OF CURRENT EQUITY, not fixed dollar amounts.** New inputs (all in the "very aggressive" input-group notes, defaults chosen from the simulation below):
   - `AggressiveMode_RiskPerTrade_PercentOfEquity` = 15.0 (replaces the old fixed-dollar tiers for Aggressive Mode only)
   - `AggressiveMode_RewardPerTrade_PercentOfEquity` = 15.0 (1:1 with risk; replaces the old fixed `$0.50` target)
   - `StopForDay_AggressiveMode_IfLossReaches_Percent` = 50.0 (a separate, much higher daily-loss ceiling for Aggressive Mode only)

   **Safe Mode's existing fixed-dollar tiered stop-loss/profit-target logic ($1/$3 stop, $1.50/$3.00 target, 65–75% confidence, 3% daily loss limit) is completely unchanged.**

## Why a separate Aggressive Mode daily loss limit was necessary

`RemainingDailyLossBudget()` already caps every single trade's risk at whatever remains of the day's loss budget (a fix from `2026-07-14i`). With Aggressive Mode now risking 15% of equity per trade but the daily loss limit still fixed at Safe Mode's 3%, the very first Aggressive Mode trade of the day would have been silently capped down to 3% risk regardless of the 15% setting — quietly undoing the "very aggressive" request without any error or explanation. Giving Aggressive Mode its own 50% daily loss ceiling (`StopForDay_AggressiveMode_IfLossReaches_Percent`) is what makes the 15% per-trade setting actually take effect; at 15%/trade and a 50% daily ceiling, roughly 3 full losses can happen before the bot halts for the day.

## The honest math — what "20% chance of blowing $100 at an 80% win rate" actually means

The founder's framing bundles two different numbers that don't causally connect the way the sentence implies: an 80% win rate (a **hope**, since this strategy has never been backtested) and a 20% ruin probability (a statement about **risk given uncertainty about whether that hope is true**). A Monte Carlo simulation was built and run to check both halves honestly rather than asserting the combined claim: `Product_Development/simulations/aggressive_mode_ruin_probability_simulation.py` (output saved alongside it). "Ruin" is defined as $100 starting equity falling to $10 or below.

**Part 1 — at the actual hoped-for 80% win rate:** ruin probability is **0.00%** at every risk-per-trade level tested (3%–20% of equity), over 50, 100, and 200 trades. A genuine 80% edge with a coherent 1:1 payout is very safe, however aggressively it's sized — this is expected: at 80% win rate the expectancy per trade is strongly positive, so risk-of-ruin should be near zero. **If the strategy really achieves 80%, "very very aggressive" and "high risk of blowing the account" are not actually compatible statements** — the risk isn't coming from the win rate the founder hopes for.

**Part 2 — at more realistic win rates for an unbacktested strategy (50–60%):** this is where meaningful ruin risk shows up. At the chosen 15%/15% risk/reward setting:

| Real win rate | Ruin probability @ 50 trades | Ruin probability @ 100 trades |
|---|---|---|
| 50% | 8.19% | 32.02% |
| 55% | 1.77% | 7.94% |
| 60% | 0.29% | 0.88% |
| 65%+ | <0.1% | <0.1% |

So a "roughly 1-in-5 to 1-in-3" danger zone (in the loose spirit of "20%") appears specifically if the real win rate lands closer to a coin flip (50%) than to the hoped-for 80%, and the bot has run through a meaningful number of trades (closer to 100 than 50). At 55% — arguably the more plausible "unbacktested but not hopeless" assumption — ruin probability is much lower (2–8%), and it drops close to zero by 60%.

**This was corrected once already during this same session.** An earlier, quicker inline estimate (computed via ad-hoc Python during the conversation, not saved as a reproducible script) claimed ~19.8% ruin probability at 15% risk / 55% win rate / 50 trades. The rigorous, saved, reproducible version of the same simulation puts that exact scenario at 1.77%, not ~20% — a real discrepancy, most likely from a difference in the earlier script's loop/reset logic that was never saved to check. **The numbers in this file and in the code comments are the corrected, reproducible ones; the earlier inline estimate should be treated as superseded.** This is flagged explicitly rather than quietly reconciled, per the project's standing rule against asserting risk/return numbers that haven't been checked.

## What was NOT done

- The 15%/15% default was **not** tuned to hit exactly "20% ruin probability" as a target number. Doing so would mean deliberately picking a risk level to manufacture a specific danger statistic to match a marketing-sounding claim — the same pattern already ruled out earlier in this project (see `2026-07-14v`/`w` on declining engineered return targets). 15% was chosen as a genuinely aggressive, round, explainable number; the resulting ruin-probability range is reported honestly rather than reverse-engineered.
- Safe Mode is untouched. Nothing here changes Safe Mode's risk, targets, or daily limits.
- `MaxTradesOpenAtOnce` (2) was not raised — same reasoning as `2026-07-14v`: raising concurrent trade count compounds simultaneous risk in a way that's a separate decision from per-trade risk sizing.

## Open items

- Not compiled/tested (no MT5 environment during staging).
- If Aggressive Mode is ever offered as a customer-facing setting (not just an internal default), the MQL5 Market listing and any documentation must present this ruin-probability range accurately, not the founder's original "20% at 80% win rate" framing, which this simulation shows is not how the numbers actually relate — see `mql5_listing_description.md`, which needs a matching update before launch (Priority Queue).
