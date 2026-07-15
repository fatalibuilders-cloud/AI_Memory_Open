# FatalibuildersTrader Scalper 1 — MQL5 Market Listing Description (Draft)

**Status:** Draft text, ready to use once the EA itself is compiled, backtested, and has a real verified track record. Do not publish this description while any placeholder logic (see `README.md`) is still in the product — MQL5's rules require descriptions to accurately reflect the product, and this text currently describes the *intended* final product, not the current placeholder-signal state.

**Formatting note:** MQL5's service rules require clean text — no icons/emojis, don't overuse bold/italic. This draft follows that.

---

## Short Description (for listing summary / search results)

FatalibuildersTrader Scalper 1 is a short-timeframe scalping Expert Advisor for MetaTrader 5, trading forex and metals only, with two trading modes — a selective Safe Mode and a high-risk, high-activity Aggressive Mode — built around tiered/percentage risk management, daily loss and profit limits, configurable entry filters, and a choice between full automation and manual (signal-only) operation.

## Full Description

### Overview

FatalibuildersTrader Scalper 1 is a scalping Expert Advisor for MetaTrader 5, designed for short timeframes (M1-M5) on forex and metals instruments only — it will not run on indices, crypto, or stock CFDs. It looks for short-term mean-reversion setups (price extending to a statistical extreme and turning back) and offers two operating modes so you can choose the risk profile that fits your account:

- **Safe Mode** — trades only setups that clear a higher internal confidence filter, risks a small fixed dollar amount per trade based on your account size, and prioritizes selectivity over frequency.
- **Aggressive Mode** — trades more opportunistically (a lower, but still present, confidence filter applies) and risks a configurable **percentage of current account equity per trade** rather than a small fixed dollar amount. This is a deliberately high-risk setting: with realistic default settings, simulation shows a meaningful probability of substantial account loss if the underlying signal's real win rate turns out to be mediocre, versus very low risk if the signal performs as intended. See "Important Risk Disclosure" below — this is not a low-risk setting and should not be marketed as one.

Every mode can additionally be run in one of two operation modes:

- **Auto-Trade** — the EA places trades itself the moment a qualifying setup appears, no action needed from the user.
- **Signals-Only** — the EA never places a trade. Instead it alerts the user (on-chart popup, on-chart note, and an optional phone push notification) with a suggested direction, position size, stop-loss, and take-profit, and leaves the decision to place the trade entirely to the user.

### Risk Management

- Safe Mode: stop-loss and profit-lock target are fixed dollar amounts set per your account's equity tier, keeping risk proportional rather than fixed regardless of account size.
- Aggressive Mode: stop-loss and profit-lock target are both a configurable percentage of current account equity (1:1 by default) — a substantially higher and more volatile risk profile than Safe Mode, by design.
- A configurable daily profit target halts trading for the day once reached, independently for each mode.
- A daily loss limit halts trading for the day if losses reach the configured threshold — Safe Mode and Aggressive Mode use separate, independently configurable daily loss limits, since Aggressive Mode's larger per-trade risk requires a larger daily ceiling to remain meaningful.
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

Trading forex and CFDs carries a substantial risk of loss and is not suitable for all investors. Past performance, including any backtest or historical results shown, does not guarantee future results. You should only trade with capital you can afford to lose. FatalibuildersTrader Scalper 1 does not guarantee profits, and no trading strategy can eliminate the risk of loss.

**Aggressive Mode specifically carries substantially higher risk than Safe Mode.** It risks a configurable percentage of current account equity on every trade (15% by default) rather than a small fixed dollar amount. Internal simulation (not a guarantee of future results) shows this setting can be safe if the underlying strategy performs at its intended win rate, but can risk a significant portion of the account if the real win rate turns out lower than hoped — which is unknown until the strategy has a verified track record. Aggressive Mode is not recommended for funds you cannot afford to lose a large portion of.

---

## Fields Still Needing Real Data Before This Can Be Published

- [ ] Confirm final symbol list once backtested (which specific forex pairs and metals performed acceptably)
- [ ] Minimum recommended balance
- [ ] Any performance figures — **only add these once backed by a real, verifiable backtest/forward-test.** Do not add illustrative or hoped-for numbers (see the marketing red-flag checklist in `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md`).
- [ ] Confirm [N] for max concurrent trades matches the shipped build (currently 2 in the code)
- [ ] Decide if Safe Mode and Aggressive Mode ship as one product with an input toggle (as currently coded) or as two separate MQL5 Market listings — affects how this description should be structured
