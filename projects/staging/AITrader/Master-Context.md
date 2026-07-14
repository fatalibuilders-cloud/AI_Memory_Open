# AITrader — Staging Master Context

**Project Name:** AITrader
**Category:** Software (MetaTrader 5 Expert Advisor — licensed trading bot)
**Owner:** Founder (fatalibuilders@gmail.com)
**Stage:** Staging (Ideation & Preparation)
**Last Updated:** 2026-07-14

---

## Project Vision

AITrader is an AI-driven trading bot (Expert Advisor) for MetaTrader 5. Customers open and fund their own account with a supported broker (Exness is the primary target broker), purchase a one-time license (~$300), and run the EA on their own MT5 terminal/VPS. The EA trades automatically, using a profit-lock strategy that closes each position once a target profit (roughly $0.50) is secured, rather than letting positions run and risk giving profit back. It offers two modes — a selective **Safe Mode** (only trades high-confidence setups) and an opportunistic **Aggressive Mode** — plus a configurable daily profit target that halts trading once reached, and a max of 2 concurrent open trades.

> **Business model note (2026-07-14):** This supersedes an earlier draft that assumed AITrader would hold discretionary trading authority over pooled client funds via an RIA + custodian structure. See `decisions-learnings/2026-07-14b_ea-license-business-model.md` for the full rationale. AITrader never holds or trades customer funds directly — customers keep their own broker account at all times.

---

## Staging Phase Objectives

During staging, we will collaboratively develop three foundation documents:

1. **Project Context Document** — Vision, goals, success metrics, target audience, and institutional dependencies
2. **Architecture/Design Document** — System design, technology stack, operational model
3. **Release Plan Document** — Phased delivery roadmap with milestones, epics, and acceptance criteria

Once these three documents are complete and approved, this project will be promoted to a full AI Memory project via `PROJECT_MEMORY_INIT.md`.

---

## Staging Roadmap

### Document 1: Project Context
**Status:** [ ] Not Started [x] In Progress [ ] Complete
**Description:** Vision, goals, target market, success metrics, key assumptions, institutional dependencies
**Open item:** Quantify lot-scaling thresholds and decide news/TradingView integration scope (see Open Questions below) before marking complete.

### Document 2: Architecture/Design
**Status:** [ ] Not Started [x] In Progress [ ] Complete
**Description:** EA architecture (MQL5), MQL5 Market distribution, broker integration, dual-mode exit logic, volatility-adaptive design, news/analysis integration

### Document 3: Release Plan
**Status:** [ ] Not Started [x] In Progress [ ] Complete
**Description:** Phased roadmap — drafted below; the legal/marketing-compliance review is a milestone within it rather than a hard pre-draft blocker (this model's legal review is much lighter than the original RIA path)

---

## Open Questions

Most items from the original voice-transcription session are now resolved (see `decisions-learnings/2026-07-14c_strategy-and-distribution-details.md`):

- ~~Profit-lock exact mechanics~~ — **RESOLVED:** dual-mode exit — outright close, or move stop to breakeven and let the trade run. Both modes to be built and tested.
- ~~"Piece of tape" / "starfish" fragments~~ — **RESOLVED**, both were garbled references to the breakeven/exit-mode question above.
- **"Text tag / who's the key"** — still unclear, but likely **moot**: now that distribution is via MQL5 Market (which handles licensing natively), a self-built license-key system is probably not needed. Revisit only if the founder confirms this was about something else.

- ~~News/analysis integration scope~~ — **RESOLVED (2026-07-14d):** economic-calendar-driven news awareness that adapts EA behavior around news-driven volatility (widen stops, reduce lot size, adjust profit-lock threshold, etc.), folded into the volatility-adaptive module. No external TradingView bridge. See `decisions-learnings/2026-07-14d_news-scope-resolved.md`.
- ~~Lot-sizing method~~ — **RESOLVED (2026-07-14e):** dynamic, risk-based sizing (the EA analyzes equity and runs risk management before scaling up) rather than a fixed manual threshold table. See `decisions-learnings/2026-07-14e_lot-sizing-method-resolved.md` — **this surfaced a new blocking gap, see item 1 below.**

- ~~Stop-loss / max-loss-per-trade rule~~ — **RESOLVED (2026-07-14f):** tiered fixed-dollar stop-loss — **$1 for accounts below $50 equity, $3 for accounts at/above $50 equity.**
- ~~Profit-lock target~~ — **RESOLVED (2026-07-14h), reverted:** founder confirmed the target is **$0.50** (the 2026-07-14g change to $2–$3 is superseded). This reintroduces the tough risk:reward math from 2026-07-14f — see the new "Trading Modes" section below for how Safe Mode's win-rate filter is meant to cover it, and the flagged gap at the ≥$50 tier.
- ~~Trading modes / daily controls~~ — **RESOLVED (2026-07-14h):** Safe Mode (80–100% win-probability filter) and Aggressive Mode (opportunistic, no filter); max 2 concurrent trades; configurable daily profit target that halts trading for the day once hit. See `decisions-learnings/2026-07-14h_dual-mode-daily-controls-target-reverted.md`.
- ~~"$50 → $1,000 in a day"~~ — **RESOLVED (2026-07-14h):** founder confirmed this is an **internal stretch-goal framing only** — not a literal spec to engineer toward (no compounding/martingale lot logic) and not to appear in any marketing copy. Flagged to the Legal & Marketing epic as a specific prohibited-claim example.

- ~~Daily loss limit~~ — **RESOLVED (2026-07-14i):** set to **3% of the day's starting equity**, symmetric to the daily profit target. Both daily controls are now fully specified. See `decisions-learnings/2026-07-14i_daily-loss-limit-set.md`.
- ~~Aggressive Mode's internal daily target~~ — **RESOLVED (2026-07-14k):** set to **20%**, adopting the top of the research-recommended 5–20% range. Replaces the retired "$50→$1,000/day" narrative framing with a concrete, defensible default for the daily-profit-target setting. See `decisions-learnings/2026-07-14k_aggressive-mode-daily-target-set-20pct.md`.

- ~~Safe Mode's own daily target default~~ — **RESOLVED (2026-07-14l):** set to **5%**, the top of the recommended 1–5% range. Both modes now have concrete defaults (Safe 5%, Aggressive 20%). See `decisions-learnings/2026-07-14l_safe-mode-daily-target-set-5pct.md`.

- ~~Safe Mode's win-rate floor not covering the ≥$50 tier~~ — **RESOLVED (2026-07-14m):** Safe Mode redesigned with its own profit-lock target ($1.50 / $3.00 by tier) instead of sharing Aggressive Mode's $0.50, and the win-probability filter lowered to a realistic 65–75% (the 80–100% premise was itself the flaw). Monte Carlo simulation confirms positive expectancy at realistic win rates. **⚠️ Still needs real backtest validation once Epic 1 produces actual code — the simulation checks the design's math, not real market behavior.** See `decisions-learnings/2026-07-14m_safe-mode-revised-and-simulated.md`.

**⚠️ Needs founder attention (research-backed, not yet resolved):**
- **Reconsider the $50 stop-loss breakpoint** — research confirms $3 stop-loss at exactly $50 equity is 6% risk, well outside the professional 1–2% norm (some data favors under 1%). Consider raising the breakpoint or smoothing the transition. Note: at 3% daily loss limit on a $50 account, that's $1.50/day — a single $3 stop-loss trade at the ≥$50 boundary would *by itself* exceed the entire daily loss limit for an account just above $50. Worth double-checking this interaction specifically.

**Still open:**
1. **Volatility/news adjustment to risk parameters** — should the $1/$3 stop-loss and $0.50 profit-lock be hard fixed figures in all conditions, or a *baseline* that the volatility/news-adaptive module widens during high-volatility/news windows? A fixed tight dollar stop is in tension with the "must work in high volatility" requirement (easily triggered by normal noise, and actual losses can exceed the stated amount due to slippage in fast markets).
2. **Risk-per-trade percentage** — now partially superseded by the fixed-dollar tiers above, but worth confirming: should risk scale continuously with equity (e.g., a %) once accounts grow well beyond $50, rather than staying flat at $3 forever?
3. **Risk-management gating rules** — what specifically blocks/allows a lot-size increase (losing-streak cooldown, news-window restriction, max lot size cap)? Also: should lot size scale back down on drawdown, not just up?
4. **Volatility/news-adaptive logic design** — the requirement (adapt to both volatility regimes and news events) is set; the specific rules (which parameters change, by how much, per condition) are not yet designed. See open items in `2026-07-14d_news-scope-resolved.md`.
5. **Exit-mode default** — once both exit modes are backtested, which becomes the default vs. a user-configurable setting in the listing?
6. **Economic calendar source** — MT5's built-in calendar vs. a third-party API.
7. **Does Safe Mode need its own risk parameters** distinct from Aggressive Mode (different target/stop), given the ≥$50 tier's win-rate gap flagged above, or do both modes share the same $0.50 target / tiered stop-loss and differ only in trade selectivity?
8. **Daily loss limit value** — if added (recommended), what percentage? Research suggests 3–5% of daily starting equity as a common professional default.

---

## Key Commands During Staging

- **Continue staging from Document N:** "Continue with Document {1|2|3}"
- **Review current progress:** "Where are we in staging?"
- **Save and close session:** "Close staging session"
- **Promote to full project:** "Initialize AITrader via PROJECT_MEMORY_INIT.md"

---

## Institutional Dependencies

- **Legal:** Lighter than originally scoped — no RIA/broker-dealer registration needed since AITrader never holds customer funds. Still need: IP/commercial counsel review of licensing terms, ToS, and marketing/disclaimer language (avoid profit-guarantee claims), and confirmation that this doesn't trigger CTA-style "trading advisor" registration in target jurisdictions.
- **Finance:** One-time $300 license pricing, payment processing (needs a processor that accepts trading-software sales — some standard processors restrict "forex signal/EA" merchants), possible secondary revenue via Exness IB/affiliate commissions.
- **Security:** Licensing/anti-piracy is now largely delegated to MQL5 Market's built-in protections rather than custom-built. No external TradingView bridge is planned, so there's no added external-service security surface for the news/volatility module.
- **Marketing:** Must avoid guaranteed-return language; performance claims should be backed by verifiable backtest/live-track-record data and clearly labeled as historical, not promised, results. Distribution channel decision (MQL5 Market vs. self-hosted) affects what marketing claims are even permitted.
- **Operations:** Customer support for installation/setup on customer-owned MT5 terminals/VPS; license activation/deactivation support.
- **Executive:** Distribution channel decision, IB/affiliate partnership decision with Exness.

---

## Available Agents

| Domain | Department Folder | Agent Files | Expertise |
|---|---|---|---|
| Finance & Investment | `Finance/agents/` | Finance-AGENT.md, Finance-advisor.md, Investment-AGENT.md, Investment-advisor.md | Financial modeling, budgeting, cash flow, investment strategy |
| Marketing & Growth | `Marketing/agents/` | Marketing-AGENT.md, Marketing-advisor.md, Sales-AGENT.md, Sales-advisor.md | Campaigns, content, GTM, sales |
| Legal | `Legal/agents/` | Legal-AGENT.md, Legal-advisor.md | Contracts, licensing, IP, marketing-compliance review |
| Security & Infrastructure | `Security/agents/` | Infrastructure-AGENT.md, Infrastructure-advisor.md | Licensing/anti-piracy architecture, infrastructure design |
| Executive & Strategy | `Executive/agents/` | Strategy-AGENT.md, Strategy-advisor.md, PMO-AGENT.md, PMO-advisor.md, Growth-n-Revenue-AGENT.md, Growth-n-Revenue-advisor.md | Strategic planning, program management, revenue |
| Operations | `Operations/agents/` | Operations-AGENT.md, Operations-advisor.md, Automation-AGENT.md, Automation-advisor.md | Process design, runbooks, automation |
| Product Development | `Product_Development/agents/` | Product-Development-AGENT.md, Product-Development-advisor.md, Software-Development-AGENT.md, Software-Development-advisor.md | Product strategy, specs, software architecture (MQL5) |
| Tech Support | `TechSupport/agents/` | Tech-Support-AGENT.md, Tech-Support-advisor.md | Installation support, license activation issues |
| People & Culture | `People-n-Culture/agents/` | People-n-Culture-AGENT.md, People-n-Culture-advisor.md | Hiring, org design |

**How to use:** When your task touches any of these domains, read the relevant AGENT.md for operational workflows or the advisor.md for strategic guidance before proceeding.

**Source:** All agents originate from `AI_Memory_Open/Memory_Agents/`. If project-local copies are outdated, refresh from the source.

---

## Document 1: Project Context

### Vision & Goals
- **Vision Statement:** AITrader is an AI-driven MetaTrader 5 Expert Advisor. Customers fund their own Exness (or other supported) broker account, buy a one-time license (~$300), and run the EA, which trades automatically and locks in a target profit (~$2–$3) per trade.
- **Primary Goal:** Sell a reliable, transparent EA with a defensible (backtested + live-verified) track record, at a licensing volume that sustains the business without relying on exaggerated marketing claims.
- **Secondary Goals:** Ship a strategy that's robust across volatility regimes (not tuned to one market condition); establish an Exness IB/affiliate relationship as a secondary revenue stream.

### Target Audience / Users
- **Who:** Retail forex/CFD traders in Exness's served markets (Exness does not accept US clients) — individuals already trading or interested in automated/algorithmic trading but who don't want to code their own EA.
- **Problem solved:** Removes the need to manually watch charts and execute trades; offers a scalping-style strategy that takes frequent, locked-in profits across varying market conditions rather than risking large drawdowns from letting trades run or relying on one volatility regime.
- **Usage model:** Customer buys the license via MQL5 Market, installs the EA on their MT5 terminal (or a VPS for 24/5 uptime), activates it, connects it to their funded Exness account, picks Safe or Aggressive Mode, optionally sets a daily profit target, and the EA trades automatically from then on — as many trades as suitable setups appear, capped at 2 concurrent positions, stopping for the day once the daily target is hit.

### Success Metrics
- License sales volume / revenue (via MQL5 Market)
- License activation → active-usage retention (are buyers still running it 30/60/90 days later?)
- Live-track-record performance **per mode** (win rate, average net profit-per-trade vs. the $0.50 target after spread/commission, max drawdown), tracked separately across high- and low-volatility periods and across the two stop-loss tiers
- Safe Mode's actual win rate vs. its revised 65–75% design target, and vs. the new break-even bars (40% at <$50 tier, 50% at ≥$50 tier)
- Trade frequency vs. profitability (guard against over-trading eroding net profit via transaction costs)
- Refund/chargeback and MQL5 Market review-rating trends
- Exness IB commission revenue (if pursued)

### Institutional Dependencies
See "Institutional Dependencies" section above.

### Assumptions & Constraints
- Target market is international (Exness's footprint), not the US.
- No custody of customer funds at any point — customers trade on their own account, under their own control, and can stop the EA at any time.
- Legal review needed on marketing/disclaimer language before public launch, but this is a much shorter runway than RIA registration.
- Distribution is via MQL5 Market — subject to their commission structure and product review policy (needs confirming, see NextSteps).
- Lot-scaling thresholds and news/TradingView integration scope are still unquantified — see Open Questions. Do not finalize Document 1/2 or begin marketing-copy drafting until these are resolved.

---

## Document 2: Architecture/Design

### System Architecture
- **EA core (MQL5):** The trading algorithm itself, written in MQL5 for MetaTrader 5. Includes:
  - Signal/entry logic, designed to trade opportunistically (as many setups as the market presents, no artificial cap on total trades — but see Trading Modes and Daily Risk Controls below for the actual gates on this)
  - Volatility/news-adaptive module (single coherent system, see below) so the strategy remains viable in both high- and low-volatility conditions and can respond to news-driven fluctuations — design TBD, see Open Questions
  - Dual-mode profit-lock exit logic: (a) outright close, or (b) move stop to breakeven and let the position run. Both exit modes configurable/testable. **Target dollar amount now differs by trading mode — see Trading Modes below** (Aggressive Mode: $0.50; Safe Mode: $1.50 / $3.00 by tier).
  - Money-management module (dynamic, risk-based): starting lot size 0.01. Stop-loss is a tiered fixed-dollar figure — **$1 max loss/trade below $50 equity, $3 max loss/trade at/above $50 equity** — shared by both modes. Lot size is derived from the stop-loss tier and current stop distance, and the EA continuously re-analyzes equity/risk before scaling lot size up.
- **Trading Modes:**
  - **Safe Mode (redesigned 2026-07-14m):** Own profit-lock target, distinct from Aggressive Mode — **$1.50 at the <$50 tier (1:1.5 R:R, 40% break-even), $3.00 at the ≥$50 tier (1:1 R:R, 50% break-even).** Win-probability filter lowered from the original 80–100% to a realistic **65–75%** — the old 80–100% bar was itself the design flaw, not just a validation gap; real conservative strategies get their edge from risk:reward at achievable win rates, not near-perfect win rates. A Monte Carlo simulation (`Product_Development/simulations/safe_mode_expectancy_simulation.py`) confirms positive expectancy across 50–75% assumed win rates at the <$50 tier, and ≥55% at the ≥$50 tier — **this is a mathematical sanity check of the design, not a real backtest; see the caveat in `decisions-learnings/2026-07-14m_safe-mode-revised-and-simulated.md`.** Internal daily target: **5%** (2026-07-14l).
  - **Aggressive Mode:** No win-probability filter; trades whenever conditions look suitable. Shares the tiered stop-loss but keeps the smaller **$0.50** profit-lock target (higher trade frequency, tougher win-rate requirement, by design). Internal daily target: **20%** (2026-07-14k — top of the research-recommended 5–20% range). "Turn $50 into $1,000/day" / "$10 into $100/day" framing is retired in favor of this concrete number — **not engineered toward via compounding/martingale lot-sizing, and never referenced in marketing or the MQL5 Market listing.**
  - Mode selection is user-configurable (a setting the customer picks, not something AITrader decides for them).
- **Daily Risk Controls:**
  - **Daily profit target (configurable):** user sets a daily profit goal; once equity gains reach it, the EA stops trading for the rest of the day. **Defaults: 5% in Safe Mode, 20% in Aggressive Mode** (2026-07-14k, 2026-07-14l) — both user-overridable.
  - **Max 2 concurrent open trades** at any time — applies regardless of mode.
  - **Daily loss limit: fixed at 3% of the day's starting equity.** Once daily realized + floating losses reach 3%, the EA stops trading until the next day. ⚠️ Flagged interaction: at exactly $50 equity, 3% = $1.50/day, but the ≥$50 stop-loss tier is $3/trade — meaning a **single** losing trade at that boundary exceeds the entire daily loss budget. Needs explicit handling (e.g., don't let a single trade's max loss exceed the remaining daily loss budget) rather than assuming the two limits compose cleanly.
- **Volatility/news-adaptive module:** Uses an economic calendar (MT5 built-in calendar data, or a third-party API — source TBD) to detect high-impact news events, and adapts EA parameters (stop distance, lot size, profit-lock threshold, and/or general volatility filters) so the EA can keep trading through news-driven and general volatility fluctuations rather than either ignoring them or standing aside entirely. Confirmed scope (2026-07-14d) — no external TradingView bridge needed; this is a self-contained MQL5 component.
- **Licensing & distribution:** Listed on the **official MQL5 Market**, which provides its own licensing/delivery infrastructure — no separate license-key system needs to be built.
- **Broker integration:** MT5's standard broker-agnostic API for order execution; Exness is the primary target/tested broker. Confirm with founder whether broader MT5-compatible broker support is in scope for v1 or Exness-only.
- **Backtesting/validation pipeline:** Historical tick-data backtesting in MT5's Strategy Tester across both high- and low-volatility historical periods, including major news events, and **specifically validating Safe Mode's actual win rate against its 40%/50% break-even bars** (revised 2026-07-14m; a preliminary Monte Carlo simulation checked the design math only — real backtesting against historical data is still required), plus a live/demo forward-test track record to support (non-guaranteed) marketing performance claims.
- **Customer support tooling:** Installation guides, MQL5 Market activation flow, VPS setup guidance for 24/5 uptime (important given the "as many trades as suitable" design implies near-continuous market monitoring).

### Technology Stack
- **EA/strategy logic:** MQL5 (native MetaTrader 5 language) — self-contained, no external services required
- **Distribution:** MQL5 Market (decided)

### Security Model
- Licensing/anti-piracy is handled by the MQL5 Market platform rather than custom-built — reduces this project's security-engineering scope compared to the self-hosted option.
- No external bridge/relay service is planned, so there's no added external-service attack surface.
- No funds-custody security model needed — AITrader never touches customer funds.

### Deployment & Operations
- Customers self-host the EA on their own MT5 terminal or VPS — AITrader doesn't operate the trading infrastructure directly, which significantly simplifies the operational burden compared to the original discretionary-management model.
- Support load is around installation, license issues, and strategy questions rather than trading-system uptime.

---

## Document 3: Release Plan

### Release Overview
- **Release Version:** 0.1 (initial paid launch)
- **Target Launch Date:** TBD — depends on resolving the Open Questions above and completing the legal/marketing review
- **Success Criteria:** EA is licensable, verified via backtest + forward-test track record, legal review passed on marketing/ToS language, first paying customers onboarded successfully

### Epics

**Epic 1: Core EA Strategy & Backtesting**
- Decide whether the $1/$3 stop-loss and $0.50 profit-lock are fixed in all conditions or a baseline the volatility/news-adaptive module can widen
- Build dual-mode exit logic (outright close vs. breakeven-and-run) and decide the default via backtest comparison
- Build the dynamic risk-based money-management module: 0.01 starting lot, tiered stop-loss ($1 below $50 equity / $3 at or above) paired with the $0.50 profit-lock target, equity-and-risk-driven scaling, gating rules, up/down scaling (some values still need defining, see Open Questions)
- Build Safe Mode's own exit logic ($1.50 / $3.00 profit-lock by tier) and win-probability signal filter (target 65–75%, revised 2026-07-14m), then **run real MT5 Strategy Tester backtests to confirm actual win rate clears the 40%/50% break-even bars** — the Monte Carlo simulation only validated the design's arithmetic, not real signal performance
- Build Aggressive Mode (no filter) — explicitly without any compounding/martingale lot-sizing logic aimed at a daily multiplier target
- Build daily risk controls: configurable daily profit target (halts trading once hit), max 2 concurrent open trades, and a **3% daily loss limit** — including explicit logic so a single trade's stop-loss can't blow past the remaining daily loss budget at tier boundaries (see flagged interaction in Document 2)
- Design and implement the volatility/news-adaptive module: economic-calendar-driven detection of high-impact events plus parameter adaptation (stop distance, lot size, profit-lock threshold) so the EA holds up across volatility regimes and news-driven fluctuations. Self-contained MQL5 component — no external services.
- Build and run MT5 Strategy Tester backtests across representative historical periods, explicitly including both high- and low-volatility windows and major news events, **per mode and per stop-loss tier**
- Start a live/demo forward-test to build a verifiable track record ahead of launch marketing

**Epic 2: MQL5 Market Listing**
- Confirm current MQL5 Market commission structure (not yet independently confirmed — see NextSteps)
- Apply for Seller registration (MQL5's own process — review typically takes up to 10 working days, apply early so it doesn't gate the launch timeline)
- Set correct Expert Advisor "Type" field (buyers filter by this)
- Prepare logo images in the three required sizes: **200×200, 140×140, 60×60**
- Write the listing description covering: trading strategy overview, risk management methods (stop-loss tiers, daily loss limit, max concurrent trades), and system parameters — per MQL5's own guidance, this is what they expect to see
- Description formatting: **no icons/emojis, clean text, don't overuse styles** — this is an MQL5 service rule, not just a style preference
- Consider multi-language descriptions (MQL5 notes this has a positive effect on sales)
- Attach verified backtest/forward-test performance history (feeds both the MQL5 automated Strategy Tester check and buyer trust)
- Submit for MQL5 Market review (automated Strategy Tester check + manual check for known programming errors)

**Epic 3: Legal & Marketing Compliance Review**
- IP/commercial counsel review of ToS, licensing terms, and disclaimer language
- Confirm no CTA/investment-adviser registration trigger in target jurisdictions
- Draft marketing copy using only verified backtest/forward-test data, with required risk disclosures
- **Concrete pre-launch checklist** (see `decisions-learnings/2026-07-14j_realistic-targets-launch-readiness.md` for the full list):
  - No "$50→$1,000," "$10→$100," or any multiplier/guarantee framing anywhere in the description, images, or product name
  - No "guaranteed profit," "risk-free," or "no losing trades" language
  - Performance claims sourced only from verified backtest/forward-test data, explicitly labeled historical/hypothetical
  - Explicit risk disclosure present (trading forex/CFDs carries substantial risk of loss; past performance ≠ future results)
  - Safe Mode and Aggressive Mode both described accurately, including Aggressive Mode's higher risk profile stated plainly, not minimized

**Epic 4: Support & Documentation**
- Installation and setup documentation (including VPS guidance for near-continuous uptime)
- Support process for MQL5 Market activation/licensing issues (checkout/payment itself is handled by MQL5 Market, not built in-house)

**Epic 5 (optional, secondary revenue): Exness IB/Affiliate Setup**
- Apply for Exness introducing-broker/affiliate program
- Decide whether to disclose this revenue relationship to customers (recommended for trust/transparency)

### Milestones
- **M1 — Strategy Locked:** Exit modes, lot-scaling, and volatility/news-adaptive logic designed and backtested (including net-of-cost performance)
- **M2 — Legal Clear:** Marketing/ToS language reviewed and approved
- **M3 — MQL5 Market Listed:** Product submitted and approved on MQL5 Market
- **M4 — Public Launch:** First paid licenses sold

### Risks & Mitigation
- **Risk:** Marketing claims read as a profit guarantee → regulatory/reputational exposure. This includes internal framing (e.g., Aggressive Mode's "$50 to $1,000 in a day" stretch goal) leaking into public-facing copy.
  - **Mitigation:** Legal review (Epic 3) before any public marketing copy ships, with an explicit prohibited-claim checklist; always pair performance claims with risk disclosures; keep internal stretch-goal language out of code comments/UI strings that could be screenshotted or extracted from the listing.
- ~~**Risk (high severity):** Safe Mode's 80% win-probability floor may not clear the ≥$50 tier's 85.7% break-even requirement.~~ — **RESOLVED (2026-07-14m):** Safe Mode redesigned with its own $1.50/$3.00 targets and a realistic 65–75% filter; break-even bars are now 40%/50%. Simulation shows solid positive expectancy across realistic win rates. **Remaining risk:** the simulation validates design math only — real backtesting (Epic 1) is still required to confirm the actual signal logic achieves the assumed win rates.
- **Risk:** Aggressive Mode has no win-rate filter and inherits the full 66.7%/85.7% break-even requirement with no safety margin — combined with uncapped trade frequency, a bad session could produce many small losses quickly.
  - **Mitigation:** **RESOLVED (2026-07-14i)** — 3% daily loss limit now caps the damage from a bad session. Still needs backtest validation that 3% is reached gracefully (not overshot mid-trade) given the tier-boundary interaction flagged in Document 2.
- **Risk:** EA piracy undermines license revenue.
  - **Mitigation:** Rely on MQL5 Market's built-in licensing/anti-piracy protections (Epic 2) rather than building a custom system.
- **Risk:** Profit-lock strategy performs differently in live markets than backtests (a common failure mode for scalping-style EAs — spread/slippage can eat small fixed-dollar profit targets, especially at high trade frequency).
  - **Mitigation:** Require a live/demo forward-test period (Epic 1) before relying on backtest numbers alone; both exit modes need to explicitly account for spread and commission per trade, not just price movement.
- **Risk:** "As many trades as possible" combined with small fixed-dollar profit targets could mean transaction costs (spread + commission) eat a large share of gross profit, especially at 0.01 lot size.
  - **Mitigation:** Backtest net-of-cost performance (not just gross), and validate that the volatility/news-adaptive logic (Epic 1) doesn't over-trade in low-volatility/choppy conditions where costs dominate.
- **Risk:** The volatility/news-adaptive module misjudges a genuine high-impact news event (e.g., stale/delayed calendar data) and trades into it with default parameters, risking outsized slippage.
  - **Mitigation:** Backtest specifically around major historical news events (Epic 1); consider a hard pause (not just adapted parameters) for the very highest-impact event tier as a fallback rule.
- **Risk:** Risk-based lot scaling compounds losses if not paired with downside gating (a losing streak could otherwise coincide with — or even be worsened by — an ill-timed size increase).
  - **Mitigation:** Require explicit losing-streak and drawdown gating rules before any size-up logic, and confirm whether lot size should scale back down on drawdown, not just up.
- ~~**Risk (high severity):** The ≥$50 equity tier's stop-loss/profit-lock combination required a 75–86% win rate just to break even.~~ — **RESOLVED (2026-07-14g):** profit-lock target raised to $2–$3, bringing worst-case break-even win rate down to ~50%. Still worth validating via backtest that actual win rate clears this bar, but the ratio itself is no longer structurally unfavorable.

---

## How to Use This File

1. **Reference During Sessions:** This file is your master reference while staging. Return to it frequently.
2. **Update Incrementally:** As you develop each document, update the "Status" fields in the Staging Roadmap section.
3. **Link to Decisions:** When decisions are made during staging, log them in `decisions-learnings/` and index them in `Key-Decisions.md`.
4. **Promote to Project:** Once all three documents are complete and signed off, execute `PROJECT_MEMORY_INIT.md` to create the full project memory.
