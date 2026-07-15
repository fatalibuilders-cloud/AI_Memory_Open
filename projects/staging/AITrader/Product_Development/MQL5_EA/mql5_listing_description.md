# FatalibuildersTrader Super Scalpers — MQL5 Market Listing Description (Draft)

**Status:** Draft text, ready to use once the EA itself is compiled, backtested, and has a real verified track record. Do not publish this description while any placeholder logic (see `README.md`) is still in the product — MQL5's rules require descriptions to accurately reflect the product, and this text currently describes the *intended* final product, not the current placeholder-signal state.

**Formatting note:** MQL5's service rules require clean text — no icons/emojis, don't overuse bold/italic. This draft follows that.

---

## Short Description (for listing summary / search results)

FatalibuildersTrader Super Scalpers is a 1-minute scalping Expert Advisor for MetaTrader 5, trading gold (XAUUSD) and GBPUSD only, with two trading modes — a selective Safe Mode and a high-risk, high-activity Aggressive Mode — built around tiered/percentage risk management, daily loss and profit limits, configurable entry filters (including a session-open timing filter), and a choice between full automation and manual (signal-only) operation.

## Full Description

### Overview

FatalibuildersTrader Super Scalpers is a scalping Expert Advisor for MetaTrader 5, designed specifically for the M1 (1-minute) chart on **gold (XAUUSD) and GBPUSD only** — it will not run on any other instrument or any other timeframe. It looks for short-term mean-reversion setups (price extending to a statistical extreme and turning back) and offers two operating modes so you can choose the risk profile that fits your account:

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
- No more than 20 positions are held concurrently (raised from an original 2, 2026-07-14zzz) — this is a genuinely high-concurrency setting; see "Important Risk Disclosure" below.
- Weekend protection closes open positions ahead of the weekend and blocks new entries near the Friday close and Monday open, avoiding gap risk from a closed market.
- An economic-calendar check avoids opening new trades immediately ahead of high-impact news events.
- A session-open delay filter blocks new trades for a set number of minutes (60 by default) after each of the 3 major trading sessions opens (Asia, London, New York), letting spreads and volatility settle before the EA acts on a signal.

### Entry Filters

FatalibuildersTrader Super Scalpers evaluates multiple conditions before entering a trade, including recent trading volume, current volatility relative to its recent average, current trend strength, and proximity to a session open — designed to avoid illiquid periods, abnormal volatility spikes, session-open whipsaws, and strongly trending conditions that don't suit a mean-reversion approach.

### Recommended Setup

- **Symbol(s):** Gold (XAUUSD) and GBPUSD only — the EA will not initialize on any other instrument
- **Timeframe:** M1 (1-minute chart) — required, the EA will not initialize on any other timeframe
- **Minimum recommended balance:** [fill in once backtested — depends heavily on account leverage; the EA includes a pre-trade margin check (2026-07-14w) so a too-small account gets a clear log message rather than silently failing, but that's not a substitute for testing a realistic minimum]
- **Recommended broker:** compatible with any MT5 broker; developed and tested with Exness. XAUUSD's normal spread is typically wider than GBPUSD's — the allowed-spread setting should be reviewed per symbol.

### Important Risk Disclosure

Trading forex and CFDs carries a substantial risk of loss and is not suitable for all investors. Past performance, including any backtest or historical results shown, does not guarantee future results. You should only trade with capital you can afford to lose. FatalibuildersTrader Super Scalpers does not guarantee profits, and no trading strategy can eliminate the risk of loss.

**Aggressive Mode specifically carries substantially higher risk than Safe Mode.** It risks a configurable percentage of current account equity on every trade (15% by default) rather than a small fixed dollar amount. Internal simulation (not a guarantee of future results) shows this setting can be safe if the underlying strategy performs at its intended win rate, but can risk a significant portion of the account if the real win rate turns out lower than hoped — which is unknown until the strategy has a verified track record. Aggressive Mode is not recommended for funds you cannot afford to lose a large portion of.

**The EA can hold up to 20 positions at once, and can open more than one trade off a single 1-minute candle's signal.** This is a substantial increase in simultaneous market exposure compared to a typical low-frequency EA, and at high trade frequency, spread and commission costs on each individual trade become a larger share of the small profit targets used here. This has not yet been validated against real trading costs at this concurrency level.

---

## Fields Still Needing Real Data Before This Can Be Published

- [ ] Confirm XAUUSD and GBPUSD both perform acceptably once backtested (symbol list itself is fixed per founder decision, 2026-07-14z)
- [ ] Minimum recommended balance
- [ ] Any performance figures — **only add these once backed by a real, verifiable backtest/forward-test.** Do not add illustrative or hoped-for numbers (see the marketing red-flag checklist in `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md`).
- [ ] Confirm 20 concurrent trades (raised from 2, 2026-07-14zzz) is still the intended shipped setting once real backtesting/cost analysis exists
- [ ] Decide if Safe Mode and Aggressive Mode ship as one product with an input toggle (as currently coded) or as two separate MQL5 Market listings — affects how this description should be structured
