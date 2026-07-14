# AITrader — Staging Master Context

**Project Name:** AITrader
**Category:** Software (MetaTrader 5 Expert Advisor — licensed trading bot)
**Owner:** Founder (fatalibuilders@gmail.com)
**Stage:** Staging (Ideation & Preparation)
**Last Updated:** 2026-07-14

---

## Project Vision

AITrader is an AI-driven trading bot (Expert Advisor) for MetaTrader 5. Customers open and fund their own account with a supported broker (Exness is the primary target broker), purchase a one-time license (~$300), and run the EA on their own MT5 terminal/VPS. The EA trades automatically, using a profit-lock strategy that closes each position once a small target profit (roughly $0.50–$1) is secured, rather than letting positions run and risk giving profit back.

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

**Still open, newly surfaced:**
1. **Lot-scaling schedule** — "scale lot size once equity reaches target" is directional, not yet quantified. Need exact equity thresholds and lot-size increments.
2. **News/TradingView integration scope** — a simple economic-calendar news filter (standard, low-complexity) vs. a full TradingView signal bridge (requires an external relay service and has MQL5-Market `WebRequest` policy implications) are very different builds. See decision file for details — needs founder input on which is actually wanted.
3. **Volatility-adaptive logic design** — "must work in high and low volatility markets" is a requirement, not yet a design (e.g., ATR-based dynamic stop/target sizing is the standard approach — needs to be specified).
4. **Exit-mode default** — once both exit modes are backtested, which becomes the default vs. a user-configurable setting in the listing?

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
- **Security:** Licensing/anti-piracy is now largely delegated to MQL5 Market's built-in protections rather than custom-built. If a TradingView bridge is built (Epic 2, Option B), that external service becomes its own security surface.
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
- **Vision Statement:** AITrader is an AI-driven MetaTrader 5 Expert Advisor. Customers fund their own Exness (or other supported) broker account, buy a one-time license (~$300), and run the EA, which trades automatically and locks in a small target profit (~$0.50–$1) per trade.
- **Primary Goal:** Sell a reliable, transparent EA with a defensible (backtested + live-verified) track record, at a licensing volume that sustains the business without relying on exaggerated marketing claims.
- **Secondary Goals:** Ship a strategy that's robust across volatility regimes (not tuned to one market condition); establish an Exness IB/affiliate relationship as a secondary revenue stream.

### Target Audience / Users
- **Who:** Retail forex/CFD traders in Exness's served markets (Exness does not accept US clients) — individuals already trading or interested in automated/algorithmic trading but who don't want to code their own EA.
- **Problem solved:** Removes the need to manually watch charts and execute trades; offers a scalping-style strategy that takes frequent, locked-in profits across varying market conditions rather than risking large drawdowns from letting trades run or relying on one volatility regime.
- **Usage model:** Customer buys the license via MQL5 Market, installs the EA on their MT5 terminal (or a VPS for 24/5 uptime), activates it, connects it to their funded Exness account, and the EA trades automatically from then on — trading as frequently as suitable setups appear.

### Success Metrics
- License sales volume / revenue (via MQL5 Market)
- License activation → active-usage retention (are buyers still running it 30/60/90 days later?)
- Live-track-record performance (win rate, average net profit-per-trade vs. the $0.50–$1 target after spread/commission, max drawdown), tracked separately across high- and low-volatility periods
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
  - Signal/entry logic, designed to trade opportunistically (as many setups as the market presents, no artificial trade cap)
  - Volatility-adaptive filters (e.g., ATR-based dynamic adjustment of entry criteria, stop distance, and/or target sizing) so the strategy remains viable in both high- and low-volatility conditions — design TBD, see Open Questions
  - Dual-mode profit-lock exit logic: (a) outright close at $0.50–$1 profit, or (b) move stop to breakeven and let the position run. Both modes configurable/testable.
  - Money-management module: default lot size 0.01, with equity-based lot scaling (exact thresholds/increments TBD, see Open Questions)
- **News/analysis integration:** Requirement to incorporate news and TradingView-referenced analysis. Two very different implementation paths under consideration — see `decisions-learnings/2026-07-14c_strategy-and-distribution-details.md` for the news-filter-only vs. full-TradingView-bridge tradeoff. This is an open scope decision, not yet designed.
- **Licensing & distribution:** Listed on the **official MQL5 Market**, which provides its own licensing/delivery infrastructure — no separate license-key system needs to be built.
- **Broker integration:** MT5's standard broker-agnostic API for order execution; Exness is the primary target/tested broker. Confirm with founder whether broader MT5-compatible broker support is in scope for v1 or Exness-only.
- **Backtesting/validation pipeline:** Historical tick-data backtesting in MT5's Strategy Tester across both high- and low-volatility historical periods (to validate the volatility-adaptive design), plus a live/demo forward-test track record to support (non-guaranteed) marketing performance claims.
- **Customer support tooling:** Installation guides, MQL5 Market activation flow, VPS setup guidance for 24/5 uptime (important given the "as many trades as suitable" design implies near-continuous market monitoring).

### Technology Stack
- **EA/strategy logic:** MQL5 (native MetaTrader 5 language)
- **News/TradingView bridge (if Option B is chosen):** Would require an external relay/webhook service — not yet designed, pending scope decision
- **Distribution:** MQL5 Market (decided)

### Security Model
- Licensing/anti-piracy is handled by the MQL5 Market platform rather than custom-built — reduces this project's security-engineering scope compared to the self-hosted option.
- If a news/TradingView bridge (Option B) is built, that external service becomes a new security surface (webhook authentication, no exposure of trading logic or account data) and a `WebRequest` URL that end users must explicitly whitelist per MQL5 Market policy.
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
- Build dual-mode exit logic (outright close vs. breakeven-and-run) and decide the default via backtest comparison
- Build money-management module: 0.01 default lot, equity-based scaling (needs thresholds defined — see Open Questions)
- Design and implement volatility-adaptive logic (e.g., ATR-based) so the strategy holds up in both high- and low-volatility regimes
- Build and run MT5 Strategy Tester backtests across representative historical periods, explicitly including both high- and low-volatility windows
- Start a live/demo forward-test to build a verifiable track record ahead of launch marketing

**Epic 2: News/Analysis Integration**
- Decide scope: news-event filter only (economic calendar, lower complexity) vs. full TradingView signal bridge (external relay service, higher complexity, MQL5-Market `WebRequest` policy implications)
- Build and backtest whichever scope is chosen
- If Option B (TradingView bridge): stand up and secure the external relay service

**Epic 3: MQL5 Market Listing**
- Confirm current MQL5 Market commission structure and product review/approval requirements
- Prepare listing assets (description, verified backtest/forward-test performance history, screenshots)
- Submit for MQL5 Market review

**Epic 4: Legal & Marketing Compliance Review**
- IP/commercial counsel review of ToS, licensing terms, and disclaimer language
- Confirm no CTA/investment-adviser registration trigger in target jurisdictions
- Draft marketing copy using only verified backtest/forward-test data, with required risk disclosures

**Epic 5: Support & Documentation**
- Installation and setup documentation (including VPS guidance for near-continuous uptime)
- Support process for MQL5 Market activation/licensing issues (checkout/payment itself is handled by MQL5 Market, not built in-house)

**Epic 6 (optional, secondary revenue): Exness IB/Affiliate Setup**
- Apply for Exness introducing-broker/affiliate program
- Decide whether to disclose this revenue relationship to customers (recommended for trust/transparency)

### Milestones
- **M1 — Strategy Locked:** Exit modes, lot-scaling, and volatility-adaptive logic designed and backtested
- **M2 — News/Analysis Scope Decided & Built:** Epic 2 scope chosen and implemented
- **M3 — Legal Clear:** Marketing/ToS language reviewed and approved
- **M4 — MQL5 Market Listed:** Product submitted and approved on MQL5 Market
- **M5 — Public Launch:** First paid licenses sold

### Risks & Mitigation
- **Risk:** Marketing claims read as a profit guarantee → regulatory/reputational exposure.
  - **Mitigation:** Legal review (Epic 4) before any public marketing copy ships; always pair performance claims with risk disclosures.
- **Risk:** EA piracy undermines license revenue.
  - **Mitigation:** Rely on MQL5 Market's built-in licensing/anti-piracy protections (Epic 3) rather than building a custom system.
- **Risk:** Profit-lock strategy performs differently in live markets than backtests (a common failure mode for scalping-style EAs — spread/slippage can eat small fixed-dollar profit targets, especially at high trade frequency).
  - **Mitigation:** Require a live/demo forward-test period (Epic 1) before relying on backtest numbers alone; both exit modes need to explicitly account for spread and commission per trade, not just price movement.
- **Risk:** "As many trades as possible" combined with small fixed-dollar profit targets could mean transaction costs (spread + commission) eat a large share of gross profit, especially at 0.01 lot size.
  - **Mitigation:** Backtest net-of-cost performance (not just gross), and validate that the volatility-adaptive logic (Epic 1) doesn't over-trade in low-volatility/choppy conditions where costs dominate.
- **Risk:** If the TradingView bridge (Epic 2, Option B) is chosen, its uptime/latency becomes a dependency for trade decisions, and MQL5 Market's review process may scrutinize or restrict the external `WebRequest` call.
  - **Mitigation:** Confirm MQL5 Market's current policy before committing to Option B; default to the simpler news-filter approach (Option A) if there's any doubt.

---

## How to Use This File

1. **Reference During Sessions:** This file is your master reference while staging. Return to it frequently.
2. **Update Incrementally:** As you develop each document, update the "Status" fields in the Staging Roadmap section.
3. **Link to Decisions:** When decisions are made during staging, log them in `decisions-learnings/` and index them in `Key-Decisions.md`.
4. **Promote to Project:** Once all three documents are complete and signed off, execute `PROJECT_MEMORY_INIT.md` to create the full project memory.
