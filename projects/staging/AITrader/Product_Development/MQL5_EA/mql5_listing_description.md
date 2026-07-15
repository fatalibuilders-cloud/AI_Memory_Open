# FatalibuildersTrader — MQL5 Market Listing Description (Draft)

**Status:** Draft text, ready to use once the EA itself is compiled, backtested, and has a real verified track record. Do not publish this description while any placeholder logic (see `README.md`) is still in the product — MQL5's rules require descriptions to accurately reflect the product, and this text currently describes the *intended* final product, not the current placeholder-signal state.

**Formatting note:** MQL5's service rules require clean text — no icons/emojis, don't overuse bold/italic. This draft follows that.

---

## Short Description (for listing summary / search results)

FatalibuildersTrader is a short-timeframe scalping Expert Advisor for MetaTrader 5, trading forex and metals only, with two trading modes — a selective Safe Mode and an opportunistic Aggressive Mode — built around tiered risk management, daily loss and profit limits, and configurable entry filters.

## Full Description

### Overview

FatalibuildersTrader is a scalping Expert Advisor for MetaTrader 5, designed for short timeframes (M1-M5) on forex and metals instruments only — it will not run on indices, crypto, or stock CFDs. It looks for short-term mean-reversion setups (price extending to a statistical extreme and turning back) and offers two operating modes so you can choose the risk profile that fits your account:

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

FatalibuildersTrader evaluates multiple conditions before entering a trade, including recent trading volume, current volatility relative to its recent average, and current trend strength — designed to avoid illiquid periods, abnormal volatility spikes, and strongly trending conditions that don't suit a mean-reversion approach.

### Recommended Setup

- **Symbol(s):** Forex pairs and metals (gold, silver) only — the EA will not initialize on other instrument types
- **Timeframe:** M1 or M5 (short-timeframe scalping)
- **Minimum recommended balance:** [fill in once backtested — depends heavily on account leverage and traded symbol; the EA includes a pre-trade margin check (2026-07-14w) so a too-small account gets a clear log message rather than silently failing, but that's not a substitute for testing a realistic minimum]
- **Recommended broker:** compatible with any MT5 broker; developed and tested with Exness. Spread settings should be reviewed per symbol — metals typically require a wider allowed-spread setting than forex majors.

### Important Risk Disclosure

Trading forex and CFDs carries a substantial risk of loss and is not suitable for all investors. Past performance, including any backtest or historical results shown, does not guarantee future results. You should only trade with capital you can afford to lose. FatalibuildersTrader does not guarantee profits, and no trading strategy can eliminate the risk of loss.

---

## Fields Still Needing Real Data Before This Can Be Published

- [ ] Confirm final symbol list once backtested (which specific forex pairs and metals performed acceptably)
- [ ] Minimum recommended balance
- [ ] Any performance figures — **only add these once backed by a real, verifiable backtest/forward-test.** Do not add illustrative or hoped-for numbers (see the marketing red-flag checklist in `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md`).
- [ ] Confirm [N] for max concurrent trades matches the shipped build (currently 2 in the code)
- [ ] Decide if Safe Mode and Aggressive Mode ship as one product with an input toggle (as currently coded) or as two separate MQL5 Market listings — affects how this description should be structured
