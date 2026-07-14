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
| profit-lock, take-profit, risk:reward, target | Profit-lock target raised to $2–$3 (from $0.50–$1) to fix the risk:reward ratio flagged above; worst-case break-even win rate drops from ~86% to ~50% — **later reverted, see next entry** | `decisions-learnings/2026-07-14g_profit-target-raised.md` | 2026-07-14 |
| profit-lock, target reverted, safe mode, aggressive mode, daily target, daily loss limit, max concurrent trades, risk management research | Profit target reverted to $0.50; added Safe/Aggressive trading modes, max 2 concurrent trades, configurable daily profit target; web-researched risk-per-trade and daily-loss-limit best practice; "$50→$1,000/day" confirmed as internal-only framing | `decisions-learnings/2026-07-14h_dual-mode-daily-controls-target-reverted.md` | 2026-07-14 |
| daily loss limit, 3%, risk management | Daily loss limit set to 3% of daily starting equity, symmetric to the daily profit target — surfaced a new tier-boundary interaction with the $3 stop-loss at $50 equity | `decisions-learnings/2026-07-14i_daily-loss-limit-set.md` | 2026-07-14 |
| MQL5 Market, launch readiness, marketing red flags, realistic returns, daily target | Researched realistic daily-return norms (professional traders: 1-2%/day is a very good day) and MQL5 Market's actual submission/review requirements; confirmed $50→$1,000 and $10→$100 per day are both internal-only framing, never marketing claims | `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md` | 2026-07-14 |
| aggressive mode, daily target, 20%, default | Aggressive Mode's internal daily profit-target default set to 20% (top of the researched 5-20% range), replacing the retired multiplier narrative; Safe Mode's own default still unset | `decisions-learnings/2026-07-14k_aggressive-mode-daily-target-set-20pct.md` | 2026-07-14 |

---

## Latest Decisions Summary

**2026-07-14 (session 11):** Founder adopted the research recommendation from session 10: Aggressive Mode's internal daily profit target is now a concrete **20%** (the top of the 5-20% recommended range), replacing the retired "$50→$1,000/day" narrative. This becomes the default for the EA's daily-profit-target setting in Aggressive Mode. Still open: Safe Mode needs its own, lower default (recommend 1-5%/day, not yet decided), and 20% needs backtest validation before being trusted rather than treated as a guarantee.

**2026-07-14 (session 10):** Founder asked whether $10→$100/day is more realistic than $50→$1,000/day, and asked for the product to be made launch-ready for MQL5 Market with safe, red-flag-free marketing. Researched both: (1) realistic daily-return norms — professional day traders consider 1-2% a very good day, so both $10→$100 (+900%) and $50→$1,000 (+1,900%) are far outside realistic territory; recommended 5-20%/day as the outer ceiling if an internal aggressive-mode number is ever needed. (2) MQL5 Market's actual submission process — Seller registration (~10 business days), logo size requirements, description content/formatting rules, and the automated Strategy Tester + manual programming-error review. Compiled a concrete pre-launch marketing checklist (no multiplier claims, no guarantee language, required risk disclosures, accurate mode descriptions) as the deliverable for the Legal & Marketing epic.

**2026-07-14 (session 9):** Daily loss limit set to **3% of the day's starting equity**, closing the last gap flagged in session 8 (the daily profit target now has a symmetric loss-side counterpart). This also resolves the "Aggressive Mode has no safety margin" risk from session 8's risk register. However, it surfaces a new interaction worth fixing before build: at exactly $50 equity, 3% is only $1.50, but the ≥$50 stop-loss tier is $3 — meaning a single losing trade at that boundary can exceed the entire day's loss budget in one shot. Flagged as a new priority item; not yet resolved.

**2026-07-14 (session 8):** Multiple decisions from founder's latest instructions, cross-checked against web research on professional risk management:
- Profit-lock target **reverted to $0.50** (the session-7 change to $2–$3 is superseded).
- **Max 2 concurrent open trades**, and a **configurable daily profit target** that halts trading for the day once reached.
- **Two trading modes:** Safe Mode (80–100% win-probability filter) and Aggressive Mode (opportunistic, no filter, "turn $50 into $1,000/day" as an internal stretch goal only — founder confirmed this must not be engineered toward or marketed).
- **Web research** (FTMO, professional trading education sources) confirms 1–2% risk-per-trade as standard, daily loss limits of 3–5% as common practice, and flags that our $3 stop-loss at exactly $50 equity (6% risk) exceeds professional norms.
- Reverting to $0.50 reintroduces the risk:reward math from session 6 — Safe Mode's win-rate filter is meant to cover this, but the ≥$50 tier's 85.7% break-even requirement may exceed Safe Mode's stated 80% floor. Flagged for backtest validation, not yet resolved.
- **Daily loss limit is recommended but not yet a founder decision** — the strongest remaining gap in the risk framework.

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
| `2026-07-14g_profit-target-raised.md` | 2026-07-14 | Session 7 — profit-lock target raised to $2–$3, risk:reward resolved (later reverted) |
| `2026-07-14h_dual-mode-daily-controls-target-reverted.md` | 2026-07-14 | Session 8 — target reverted to $0.50; Safe/Aggressive modes, daily controls, web research |
| `2026-07-14i_daily-loss-limit-set.md` | 2026-07-14 | Session 9 — daily loss limit set to 3%; tier-boundary interaction surfaced |
| `2026-07-14j_realistic-targets-launch-readiness.md` | 2026-07-14 | Session 10 — realistic daily-return research; MQL5 Market launch-readiness checklist |
| `2026-07-14k_aggressive-mode-daily-target-set-20pct.md` | 2026-07-14 | Session 11 — Aggressive Mode daily target set to 20% |
