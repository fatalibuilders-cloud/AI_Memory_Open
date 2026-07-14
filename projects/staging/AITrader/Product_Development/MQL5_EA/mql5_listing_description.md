# AITrader — MQL5 Market Listing Description (Draft)

**Status:** Draft text, ready to use once the EA itself is compiled, backtested, and has a real verified track record. Do not publish this description while any placeholder logic (see `README.md`) is still in the product — MQL5's rules require descriptions to accurately reflect the product, and this text currently describes the *intended* final product, not the current placeholder-signal state.

**Formatting note:** MQL5's service rules require clean text — no icons/emojis, don't overuse bold/italic. This draft follows that.

---

## Short Description (for listing summary / search results)

AITrader is a MetaTrader 5 Expert Advisor with two trading modes — a selective Safe Mode and an opportunistic Aggressive Mode — built around tiered risk management, daily loss and profit limits, and configurable entry filters.

## Full Description

### Overview

AITrader is an Expert Advisor for MetaTrader 5 designed around risk management first. It offers two operating modes so you can choose the risk profile that fits your account:

- **Safe Mode** — trades only setups that clear an internal confidence filter, prioritizing selectivity over frequency.
- **Aggressive Mode** — trades more opportunistically, with no selectivity filter, accepting more trades and more risk in exchange for higher potential activity.

### Risk Management

- Stop-loss is set per trade based on your account equity tier, keeping risk proportional rather than fixed regardless of account size.
- Each mode has its own profit-lock target, calibrated to that mode's risk profile.
- A configurable daily profit target halts trading for the day once reached.
- A daily loss limit halts trading for the day if losses reach the configured threshold, protecting the account from a single bad session.
- No more than [N] positions are held concurrently.
- Weekend protection closes open positions ahead of the weekend and blocks new entries near the Friday close and Monday open, avoiding gap risk from a closed market.
- An economic-calendar check avoids opening new trades immediately ahead of high-impact news events.

### Entry Filters

AITrader evaluates multiple conditions before entering a trade, including recent trading volume, current volatility relative to its recent average, and trend strength — designed to avoid illiquid periods, abnormal volatility spikes, and choppy, range-bound conditions that don't suit the underlying strategy.

### Recommended Setup

- **Symbol(s):** [fill in once backtested — e.g. specific forex pairs/instruments the strategy was validated on]
- **Timeframe:** [fill in]
- **Minimum recommended balance:** [fill in]
- **Recommended broker:** compatible with any MT5 broker; developed and tested with Exness

### Important Risk Disclosure

Trading forex and CFDs carries a substantial risk of loss and is not suitable for all investors. Past performance, including any backtest or historical results shown, does not guarantee future results. You should only trade with capital you can afford to lose. AITrader does not guarantee profits, and no trading strategy can eliminate the risk of loss.

---

## Fields Still Needing Real Data Before This Can Be Published

- [ ] Recommended symbol(s)/timeframe — depends on what the real (non-placeholder) signal is actually validated on
- [ ] Minimum recommended balance
- [ ] Any performance figures — **only add these once backed by a real, verifiable backtest/forward-test.** Do not add illustrative or hoped-for numbers (see the marketing red-flag checklist in `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md`).
- [ ] Confirm [N] for max concurrent trades matches the shipped build (currently 2 in the code)
- [ ] Decide if Safe Mode and Aggressive Mode ship as one product with an input toggle (as currently coded) or as two separate MQL5 Market listings — affects how this description should be structured
