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
**Open item:** Confirm exact profit-lock mechanics (see Open Questions below) before marking complete.

### Document 2: Architecture/Design
**Status:** [ ] Not Started [x] In Progress [ ] Complete
**Description:** EA architecture (MQL5), licensing/anti-piracy system, broker integration, profit-lock logic

### Document 3: Release Plan
**Status:** [ ] Not Started [x] In Progress [ ] Complete
**Description:** Phased roadmap — drafted below; the legal/marketing-compliance review is a milestone within it rather than a hard pre-draft blocker (this model's legal review is much lighter than the original RIA path)

---

## Open Questions (from founder, not yet resolved — transcription was unclear on these points)

A few points from the last session came through garbled in voice transcription and need to be re-confirmed before Documents 1-2 are finalized:

1. **"Text tag / who's the key"** — unclear what this referred to (possibly a UI label, a license-key mechanism, or something else). Needs clarification.
2. **"Piece of tape onto the..."** — unclear, possibly related to trailing stop / stop-loss mechanics. Needs clarification.
3. **"What happens if you put a starfish? The AI trade is successful."** — unclear; possibly garbled speech-to-text for a stop-loss or trade-outcome question. Needs clarification.
4. **Profit-lock exact mechanics** — confirmed target is $0.50–$1 secured profit per trade, but not yet confirmed: is this a fixed take-profit order, or a trailing/breakeven-lock mechanism (open the position, then once floating profit hits the threshold, move stop-loss to lock in at least that amount)? Also unconfirmed: is $0.50/$1 a flat dollar amount regardless of lot size, or does it scale with position size?

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
- **Security:** License-key/anti-piracy system to protect the EA from cracking and unauthorized redistribution (a known, persistent problem in the MT5 EA market).
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
- **Secondary Goals:** Build a licensing/anti-piracy system that meaningfully reduces unauthorized redistribution; establish an Exness IB/affiliate relationship as a secondary revenue stream.

### Target Audience / Users
- **Who:** Retail forex/CFD traders in Exness's served markets (Exness does not accept US clients) — individuals already trading or interested in automated/algorithmic trading but who don't want to code their own EA.
- **Problem solved:** Removes the need to manually watch charts and execute trades; offers a scalping-style strategy that takes small, frequent, locked-in profits rather than risking large drawdowns from letting trades run.
- **Usage model:** Customer buys the license, installs the EA on their MT5 terminal (or a VPS for 24/5 uptime), enters their license key, connects it to their funded Exness account, and the EA trades automatically from then on.

### Success Metrics
- License sales volume / revenue
- License activation → active-usage retention (are buyers still running it 30/60/90 days later?)
- Live-track-record performance (win rate, average profit-per-trade vs. the $0.50–$1 target, max drawdown)
- Piracy/unauthorized-copy rate (proxy: activations per license sold)
- Refund/chargeback rate
- Exness IB commission revenue (if pursued)

### Institutional Dependencies
See "Institutional Dependencies" section above.

### Assumptions & Constraints
- Target market is international (Exness's footprint), not the US.
- No custody of customer funds at any point — customers trade on their own account, under their own control, and can stop the EA at any time.
- Legal review needed on marketing/disclaimer language before public launch, but this is a much shorter runway than RIA registration.
- Several mechanics are still unconfirmed pending founder clarification — see "Open Questions" above. Do not finalize Document 1/2 or begin marketing-copy drafting until these are resolved.

---

## Document 2: Architecture/Design

### System Architecture
- **EA core (MQL5):** The trading algorithm itself, written in MQL5 for MetaTrader 5. Includes signal/entry logic, position sizing, and the profit-lock exit logic (mechanics TBD — see Open Questions).
- **Licensing system:** License-key generation, validation on EA startup, and anti-tamper/anti-crack measures (e.g., account-number binding, periodic online validation, obfuscation). This is a first-order design concern given how common EA piracy is.
- **Broker integration:** MT5's standard broker-agnostic API is used for order execution; Exness is the primary target/tested broker, but the EA should ideally work with any MT5-compatible broker to widen the addressable market — confirm with founder whether multi-broker support is in scope for v1 or Exness-only.
- **Backtesting/validation pipeline:** Historical tick-data backtesting in MT5's Strategy Tester, plus a live/demo forward-test track record to support (non-guaranteed) marketing performance claims.
- **Distribution & delivery:** Either a self-hosted site with license-key checkout, or listing on the official MQL5 Market (which has its own licensing/delivery infrastructure built in) — decision pending (see NextSteps).
- **Customer support tooling:** Installation guides, license activation/deactivation flow, VPS setup guidance for 24/5 uptime.

### Technology Stack
- **EA/strategy logic:** MQL5 (native MetaTrader 5 language)
- **Licensing backend (if self-hosted):** Not yet decided — needs a lightweight service for key generation/validation
- **Distribution:** Not yet decided — self-hosted vs. MQL5 Market vs. both

### Security Model
- License-key validation and anti-piracy measures (see above) — the primary "security" concern here, distinct from the funds-custody security model in the earlier draft (no longer applicable since AITrader never touches customer funds).
- Standard software-delivery security (secure download/checkout, no plaintext key storage).

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
- Finalize entry/exit logic, including the exact profit-lock mechanism (blocked on founder clarification)
- Build and run MT5 Strategy Tester backtests across representative historical periods
- Start a live/demo forward-test to build a verifiable track record ahead of launch marketing

**Epic 2: Licensing & Anti-Piracy System**
- Design license-key generation/validation flow
- Decide self-hosted vs. MQL5 Market distribution (affects this epic's scope significantly)
- Implement anti-tamper measures appropriate to the chosen distribution channel

**Epic 3: Legal & Marketing Compliance Review**
- IP/commercial counsel review of ToS, licensing terms, and disclaimer language
- Confirm no CTA/investment-adviser registration trigger in target jurisdictions
- Draft marketing copy using only verified backtest/forward-test data, with required risk disclosures

**Epic 4: Purchase & Support Flow**
- Checkout/payment flow (confirm a payment processor that accepts trading-software/EA merchants)
- Installation and setup documentation (including VPS guidance)
- Support process for license activation issues

**Epic 5 (optional, secondary revenue): Exness IB/Affiliate Setup**
- Apply for Exness introducing-broker/affiliate program
- Decide whether to disclose this revenue relationship to customers (recommended for trust/transparency)

### Milestones
- **M1 — Strategy Locked:** Profit-lock mechanics confirmed and coded; backtest results in hand
- **M2 — Legal Clear:** Marketing/ToS language reviewed and approved
- **M3 — Licensing Ready:** License-key system functional, distribution channel chosen
- **M4 — Public Launch:** First paid licenses sold

### Risks & Mitigation
- **Risk:** Marketing claims read as a profit guarantee → regulatory/reputational exposure.
  - **Mitigation:** Legal review (Epic 3) before any public marketing copy ships; always pair performance claims with risk disclosures.
- **Risk:** EA piracy undermines license revenue.
  - **Mitigation:** Anti-tamper licensing system (Epic 2); consider MQL5 Market's built-in protections as an alternative to building this in-house.
- **Risk:** Profit-lock strategy performs differently in live markets than backtests (a common failure mode for scalping-style EAs — spread/slippage can eat small fixed-dollar profit targets).
  - **Mitigation:** Require a live/demo forward-test period (Epic 1) before relying on backtest numbers alone; the exact profit-lock mechanism needs to explicitly account for spread and commission per trade, not just price movement.

---

## How to Use This File

1. **Reference During Sessions:** This file is your master reference while staging. Return to it frequently.
2. **Update Incrementally:** As you develop each document, update the "Status" fields in the Staging Roadmap section.
3. **Link to Decisions:** When decisions are made during staging, log them in `decisions-learnings/` and index them in `Key-Decisions.md`.
4. **Promote to Project:** Once all three documents are complete and signed off, execute `PROJECT_MEMORY_INIT.md` to create the full project memory.
