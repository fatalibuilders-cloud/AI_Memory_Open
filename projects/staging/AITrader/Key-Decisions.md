# Key Decisions — AITrader (Staging)

**Scope:** Decisions made during AITrader staging. Read this index before starting new staging work; drill into a detail file only when its keyword matches your current task.

---

## Keyword Index

| Keyword | Decision / Topic | Detail File | Date |
|---------|-----------------|-------------|------|
| regulatory, RIA, broker-dealer, custody, compliance | ~~Pursue RIA + third-party custodian structure~~ — **SUPERSEDED**, see EA license entry below | `decisions-learnings/2026-07-14_regulatory-path.md` | 2026-07-14 |
| business model, EA, expert advisor, MT5, MetaTrader, Exness, licensing, fee model | Pivot to selling AITrader as a licensed MT5 Expert Advisor (~$300 flat one-time fee); customers keep custody of their own funds at their own broker | `decisions-learnings/2026-07-14b_ea-license-business-model.md` | 2026-07-14 |
| distribution, MQL5 Market, exit logic, breakeven, take-profit, lot size, money management, volatility, news, TradingView | Distribution via MQL5 Market; dual-mode exit (outright close or breakeven-and-run); 0.01 default lot with equity-based scaling; uncapped trade frequency; must work across volatility regimes; news/TradingView integration scope raised as open question | `decisions-learnings/2026-07-14c_strategy-and-distribution-details.md` | 2026-07-14 |
| news, TradingView, economic calendar, volatility-adaptive | News/analysis integration scope resolved: economic-calendar-driven adaptation (not a TradingView bridge), folded into the volatility-adaptive module | `decisions-learnings/2026-07-14d_news-scope-resolved.md` | 2026-07-14 |
| lot size, money management, risk management, position sizing, stop-loss | Lot sizing uses dynamic, risk-based scaling (equity-and-risk-driven), not fixed thresholds — surfaced a blocking gap: stop-loss/max-loss-per-trade rule is undefined | `decisions-learnings/2026-07-14e_lot-sizing-method-resolved.md` | 2026-07-14 |
| stop-loss, risk:reward, tiered risk, win rate | Tiered fixed-dollar stop-loss ($1 below $50 equity, $3 at/above) — flagged a high-severity risk:reward concern at the $3 tier, resolved in the next entry | `decisions-learnings/2026-07-14f_tiered-stop-loss.md` | 2026-07-14 |
| profit-lock, take-profit, risk:reward, target | Profit-lock target raised to $2–$3 (from $0.50–$1) to fix the risk:reward ratio flagged above; worst-case break-even win rate drops from ~86% to ~50% | `decisions-learnings/2026-07-14g_profit-target-raised.md` | 2026-07-14 |

---

## Latest Decisions Summary

**2026-07-14 (session 7):** Resolved the risk:reward concern from session 6. Founder chose to keep the tiered stop-loss ($1/$3) as-is and raise the profit-lock target from $0.50–$1 to **$2–$3**. This brings the worst-case break-even win rate down from ~86% to ~50% at the ≥$50 tier, and to ~25–33% at the <$50 tier. All prior references to the $0.50–$1 target across Documents 1–3 have been updated. The high-severity risk flagged in session 6 is now marked resolved (pending backtest validation of actual win rate).

**2026-07-14 (session 6):** Stop-loss defined as a tiered fixed-dollar amount: $1 for accounts below $50 equity, $3 at/above. This unblocks risk-based lot sizing (session 5). **But it surfaces a high-severity concern:** combined with the existing $0.50–$1 profit-lock target, the ≥$50 tier risks $3 to make $0.50–$1 — a 3:1 to 6:1 risk:reward ratio against the trade, needing a 75–86% win rate just to break even before costs. Flagged as a hard blocker on building/backtesting that tier until the founder confirms intent or adjusts the profit-lock target to scale with the stop-loss tier. See detail file for the full risk:reward table and additional feasibility flags (tight-stop triggering, slippage in volatile conditions, discontinuity at the $50 boundary).

**2026-07-14 (session 5):** Lot sizing confirmed as dynamic, risk-based scaling — the EA analyzes account equity and runs its own risk-management check before increasing lot size, rather than following a fixed manual threshold table. This is the standard "fixed-fractional risk-based position sizing" approach. It surfaced a **blocking gap**: no stop-loss/max-loss-per-trade rule has been defined yet, and risk-based sizing can't be computed without one. This is now the top priority item.

**2026-07-14 (session 4):** Resolved the news/analysis integration scope: the EA will use an economic calendar to detect high-impact news and adapt its own parameters (stop distance, lot size, profit-lock threshold) around news-driven volatility — a self-contained MQL5 module, not a TradingView signal bridge. Folded into the existing volatility-adaptive module; Document 3's Epic 2 (TradingView-bridge option) was removed and epics renumbered.

**2026-07-14 (session 3):** Resolved distribution channel (MQL5 Market) and profit-lock exit mechanics (dual-mode: outright close or breakeven-and-run). Added new scope: equity-based lot scaling from a 0.01 base, uncapped trade frequency ("as many trades as suitable"), and a requirement to work across both high- and low-volatility markets. Also introduced a new open scope question — news/TradingView integration — that needs a decision between a simple news filter and a much more complex TradingView bridge. See detail file for the full tradeoff and remaining open items.

**2026-07-14 (session 2):** Pivoted from the RIA/discretionary-management model to selling AITrader as a licensed MetaTrader 5 Expert Advisor. Customers run the bot on their own funded Exness account; AITrader never holds customer funds. Fee is a flat one-time ~$300 license, not performance-contingent.

**2026-07-14 (session 1, superseded):** Originally selected RIA + third-party broker-dealer/custodian as the regulatory structure for autonomous retail trading of pooled client funds. Superseded by the EA-license pivot — kept in the record for context, not to be acted on.

---

## File Chronology

| File | Date | Session Focus |
|------|------|---------------|
| `2026-07-14_regulatory-path.md` | 2026-07-14 | Initial staging session — project intake, regulatory structure decision (superseded) |
| `2026-07-14b_ea-license-business-model.md` | 2026-07-14 | Session 2 — business model pivot to MT5 EA licensing |
| `2026-07-14c_strategy-and-distribution-details.md` | 2026-07-14 | Session 3 — distribution channel, exit logic, lot sizing, trading scope |
| `2026-07-14d_news-scope-resolved.md` | 2026-07-14 | Session 4 — news/analysis integration scope resolved |
| `2026-07-14e_lot-sizing-method-resolved.md` | 2026-07-14 | Session 5 — dynamic risk-based lot sizing; stop-loss gap surfaced |
| `2026-07-14f_tiered-stop-loss.md` | 2026-07-14 | Session 6 — tiered stop-loss defined; risk:reward concern flagged |
| `2026-07-14g_profit-target-raised.md` | 2026-07-14 | Session 7 — profit-lock target raised to $2–$3, risk:reward resolved |
