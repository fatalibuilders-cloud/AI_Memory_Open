# AITrader — Staging Master Context

**Project Name:** AITrader
**Category:** Software (Full Retail Trading Platform)
**Owner:** Founder (fatalibuilders@gmail.com)
**Stage:** Staging (Ideation & Preparation)
**Last Updated:** 2026-07-14

---

## Project Vision

AITrader is a fully autonomous AI-driven trading platform for retail investors. Users fund or connect a brokerage account, and AITrader's AI strategies analyze markets and execute trades on their behalf without requiring per-trade approval — giving individual investors access to systematic, emotion-free trading strategies historically reserved for institutions.

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

### Document 2: Architecture/Design
**Status:** [ ] Not Started [x] In Progress [ ] Complete
**Description:** System design, technology stack, operational model, compliance model

### Document 3: Release Plan
**Status:** [x] Not Started [ ] In Progress [ ] Complete
**Description:** Phased roadmap with version milestones, epics, and acceptance criteria — deferred until the regulatory path (Document 1/2 gating item) is resolved

---

## Key Commands During Staging

- **Continue staging from Document N:** "Continue with Document {1|2|3}"
- **Review current progress:** "Where are we in staging?"
- **Save and close session:** "Close staging session"
- **Promote to full project:** "Initialize AITrader via PROJECT_MEMORY_INIT.md"

---

## Institutional Dependencies

- **Legal:** CRITICAL. Fully autonomous trading of retail client funds is discretionary investment advice under the Investment Advisers Act of 1940 — see `decisions-learnings/` for the regulatory gating decision.
- **Finance:** Fee/revenue model, capital requirements, custody structure, financial controls.
- **Security:** Brokerage API credentials, funds-movement security, encryption, SOC 2 posture.
- **Marketing:** Highly regulated under the SEC Marketing Rule for investment advisers (performance advertising restrictions).
- **Operations:** Near-continuous uptime during market hours, incident response for trading outages.
- **Executive:** Go/no-go decisions on regulatory path, funding strategy.

---

## Available Agents

| Domain | Department Folder | Agent Files | Expertise |
|---|---|---|---|
| Finance & Investment | `Finance/agents/` | Finance-AGENT.md, Finance-advisor.md, Investment-AGENT.md, Investment-advisor.md | Financial modeling, budgeting, cash flow, investment strategy |
| Marketing & Growth | `Marketing/agents/` | Marketing-AGENT.md, Marketing-advisor.md, Sales-AGENT.md, Sales-advisor.md | Campaigns, content, GTM, sales |
| Legal | `Legal/agents/` | Legal-AGENT.md, Legal-advisor.md | Contracts, compliance, IP, regulatory (RIA/broker-dealer registration) |
| Security & Infrastructure | `Security/agents/` | Infrastructure-AGENT.md, Infrastructure-advisor.md | Security architecture, infrastructure design, cloud |
| Executive & Strategy | `Executive/agents/` | Strategy-AGENT.md, Strategy-advisor.md, PMO-AGENT.md, PMO-advisor.md, Growth-n-Revenue-AGENT.md, Growth-n-Revenue-advisor.md | Strategic planning, program management, revenue |
| Operations | `Operations/agents/` | Operations-AGENT.md, Operations-advisor.md, Automation-AGENT.md, Automation-advisor.md | Process design, runbooks, infrastructure ops, automation |
| Product Development | `Product_Development/agents/` | Product-Development-AGENT.md, Product-Development-advisor.md, Software-Development-AGENT.md, Software-Development-advisor.md | Product strategy, specs, software architecture |
| Tech Support | `TechSupport/agents/` | Tech-Support-AGENT.md, Tech-Support-advisor.md | Ticket triage, escalation, KB articles |
| People & Culture | `People-n-Culture/agents/` | People-n-Culture-AGENT.md, People-n-Culture-advisor.md | Hiring (e.g. Chief Compliance Officer), org design |

**How to use:** When your task touches any of these domains, read the relevant AGENT.md for operational workflows or the advisor.md for strategic guidance before proceeding.

**Source:** All agents originate from `AI_Memory_Open/Memory_Agents/`. If project-local copies are outdated, refresh from the source.

---

## Document 1: Project Context

### Vision & Goals
- **Vision Statement:** AITrader is a fully autonomous AI-driven trading platform for retail investors. Users fund or connect a brokerage account, and AITrader's AI strategies analyze markets and execute trades on their behalf without requiring per-trade approval.
- **Primary Goal:** Prove a compliant, reliable path to autonomous algorithmic trading of retail client capital that outperforms relevant benchmarks net of fees and regulatory overhead.
- **Secondary Goals:** Build trust/transparency tooling (performance reporting, risk disclosures) that differentiates from black-box competitors; establish a defensible strategy-research pipeline.

### Target Audience / Users
- **Who:** Retail / individual investors — people who currently either build their own trading bots/scripts, use static robo-advisors (passive index allocation only), or trade manually and are prone to behavioral mistakes (panic-selling, chasing momentum).
- **Problem solved:** Removes manual effort and emotional bias from trading while giving access to systematic strategies previously reserved for institutions or sophisticated DIY quants.
- **Usage model:** User completes onboarding/KYC, links or funds a brokerage account, selects or is assigned a strategy/risk profile, and the platform trades autonomously going forward. User monitors performance via dashboard; does not approve individual trades.

### Success Metrics
- Assets under algorithmic management (AUM)
- Active account count / retention rate
- Strategy risk-adjusted performance (Sharpe ratio) vs. relevant benchmark, net of fees
- Regulatory audit / exam pass rate (once registered)
- Trading system uptime and execution reliability during market hours
- Customer complaint / dispute rate

### Institutional Dependencies
- **Legal (highest priority, gating):** Autonomous discretionary trading of client funds = investment advisory activity under the Investment Advisers Act of 1940. Likely requires state or SEC Registered Investment Adviser (RIA) registration (threshold depends on AUM), a written compliance program, and Form ADV filings. If AITrader itself routes orders to exchanges (rather than via a licensed broker-dealer), broker-dealer registration may also be triggered — the recommended path is to integrate with an existing regulated broker-dealer/custodian (e.g., Alpaca Securities, Interactive Brokers, Tradier) as an introducing/API relationship rather than becoming a broker-dealer. **A securities attorney should be engaged before further build investment.**
- **Finance:** Fee model (AUM-based advisory fee vs. subscription vs. performance fee — performance fees have their own regulatory restrictions for retail/non-qualified clients), custody structure (funds must sit with a qualified custodian, not AITrader directly), startup capital for registration/compliance/insurance.
- **Security:** Brokerage API credentials and any funds-movement flows are high-value attack targets; needs encryption at rest/in transit, least-privilege credential storage, SOC 2-track controls, and an incident response plan.
- **Marketing:** SEC Marketing Rule (2020, effective for advisers) tightly restricts performance advertising, testimonials, and hypothetical results — marketing copy must be compliance-reviewed.
- **Operations:** Trading infrastructure needs high uptime during market hours, monitoring/alerting for execution failures, and a documented incident response runbook (a stalled/failed autonomous trading system is a direct financial-harm risk to users).

### Assumptions & Constraints
- Assumed early-stage/bootstrapped team; funding strategy not yet defined (flagged for Executive/Finance).
- Assumed U.S. retail market as the initial target (regulatory specifics above are U.S.-centric — cross-border expansion would add jurisdiction-specific requirements).
- Regulatory registration is assumed to be the critical path item that gates any handling of real user funds — engineering can proceed on paper-trading/backtesting infrastructure in parallel, but must not onboard real capital pre-registration.
- Technology stack not yet decided (Document 2, open item).

---

## Document 2: Architecture/Design

### System Architecture
- **Client app:** Web (and later mobile) app for onboarding/KYC, account linking or funding, risk-profile selection, and a performance/holdings dashboard.
- **Brokerage/custody integration layer:** Integrate with an existing regulated broker-dealer/custodian via API (e.g., Alpaca Broker API, Interactive Brokers, Tradier) rather than building order routing/exchange connectivity in-house. This keeps AITrader out of broker-dealer registration and keeps client funds with a qualified custodian.
- **AI/strategy engine:**
  - Signal generation / model layer (the "AI" — could range from classical quant models to ML-based signal generation; needs its own explainability and validation strategy given fiduciary/compliance requirements)
  - Backtesting engine (survivorship-bias-free historical data, realistic slippage/fee modeling)
  - Risk management layer (position sizing, max drawdown limits, circuit breakers)
  - Execution engine (order submission to broker API, execution monitoring, retry/failure handling)
- **Compliance & audit layer:** Immutable trade/decision logging, best-execution recordkeeping, client suitability and risk-tolerance capture, support for Form ADV and exam recordkeeping requirements.
- **Data layer:** Real-time and historical market data feeds; separate from the custodian's data.

### Technology Stack
- Not yet decided — open item for Product_Development / Software-Development agent to advise on in a follow-up session.

### Security Model
- Brokerage credentials/API tokens: encrypted at rest, never logged, least-privilege scoping.
- AITrader should never directly custody client funds — funds remain at the qualified custodian; AITrader only has trading authorization (limited power of attorney), not withdrawal rights.
- Target SOC 2 Type II readiness ahead of scaling past early users.
- Documented incident response plan for both security incidents and trading-system failures (the latter is a direct-financial-harm scenario unique to this domain).

### Deployment & Operations
- Cloud-hosted (AWS/GCP), designed for high availability during market hours at minimum; 24/7 monitoring recommended given crypto/extended-hours markets may be in scope later.
- CI/CD strategy and dev conventions: not yet decided — open item.

### Compliance Model (Business/Regulatory — carries into Architecture because it constrains system design)
- Recommended structure: register as an RIA (state or SEC depending on AUM), operate trading authorization via limited power of attorney over accounts held at a third-party qualified custodian, and avoid broker-dealer registration by using an existing broker-dealer's API.
- Compliance program required: written policies & procedures, a designated Chief Compliance Officer (People & Culture dependency), annual compliance review, Form ADV Part 2 disclosure to clients (fees, conflicts of interest, strategy risks).

---

## Document 3: Release Plan

> Deferred. Recommend resolving the Legal/regulatory path (RIA registration approach, broker-dealer/custodian partner selection) before finalizing a release plan, since the phasing (e.g., "paper trading only" phase vs. "live trading" phase) depends directly on registration timeline.

---

## How to Use This File

1. **Reference During Sessions:** This file is your master reference while staging. Return to it frequently.
2. **Update Incrementally:** As you develop each document, update the "Status" fields in the Staging Roadmap section.
3. **Link to Decisions:** When decisions are made during staging, log them in `decisions-learnings/` and index them in `Key-Decisions.md`.
4. **Promote to Project:** Once all three documents are complete and signed off, execute `PROJECT_MEMORY_INIT.md` to create the full project memory.
