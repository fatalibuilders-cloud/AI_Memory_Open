# FatalibuildersConstructionApp — Staging Master Context

**Project Name:** FatalibuildersConstructionApp
**Category:** Software (web/mobile construction management app)
**Owner:** Eng Ali Ahmed (fatalibuilders@gmail.com) — Owner, Fatali Builders
**Stage:** Staging (Ideation & Preparation)
**Last Updated:** 2026-07-16 (session 2 — integration strategy confirmed by owner)

---

## Project Vision

> **STATUS: AI-DRAFTED — PENDING OWNER REVIEW.** This vision was drafted by the AI during autonomous staging initialization because the project was staged from the task name alone. The owner should confirm, correct, or replace it in the next session.

The Fatalibuilders Construction App is a construction management application for Fatali Builders that connects the field and the office in one system. It solves the fragmentation problem of running construction jobs across phone calls, paper, and spreadsheets by unifying job/project tracking, estimates and quotes, crew scheduling, daily site logs with photos, materials and expense tracking, and client communication/invoicing. It is built for the company's owner, office staff, site supervisors, and field crews — and gives clients a transparent window into their project's progress.

---

## Staging Phase Objectives

During staging, we will collaboratively develop three foundation documents:

1. **Project Context Document** — Vision, goals, success metrics, target audience, and institutional dependencies
2. **Architecture/Design Document** — System/business/product design, technology stack (if applicable), operational model
3. **Release Plan Document** — Phased delivery roadmap with milestones, epics, and acceptance criteria

Once these three documents are complete and approved, this project will be promoted to a full AI Memory project via PROJECT_MEMORY_INIT.md.

---

## Staging Roadmap

### Document 1: Project Context
**Status:** [ ] Not Started [x] In Progress [ ] Complete
**Description:** Vision, goals, target market, success metrics, key assumptions, institutional dependencies
**Note:** Vision drafted by AI; all sections require owner input and confirmation.

### Document 2: Architecture/Design
**Status:** [ ] Not Started [x] In Progress [ ] Complete
**Description:** System design, technology stack, data model, security model, deployment strategy
**Note:** Integration-first architecture confirmed by owner (2026-07-16); candidate integration list drafted, prioritization pending.

### Document 3: Release Plan
**Status:** [x] Not Started [ ] In Progress [ ] Complete
**Description:** Phased roadmap with version milestones, epics, and acceptance criteria

---

## Key Commands During Staging

- **Continue staging from Document N:** "Continue with Document {1|2|3}"
- **Review current progress:** "Where are we in staging?"
- **Save and close session:** "Close staging session"
- **Promote to full project:** "Initialize FatalibuildersConstructionApp via PROJECT_MEMORY_INIT.md"

---

## Institutional Dependencies

Every project — whether software, business, product, or service — has the following potential institutional dependencies. Identify which apply to this project:

- **Marketing:** Brand, messaging, go-to-market, customer acquisition *(likely internal-tool first; confirm whether the app is also a client-facing differentiator)*
- **Legal:** Contracts, compliance, intellectual property, regulatory requirements *(construction contracts, lien/permit documentation, data privacy for client records)*
- **Finance:** Funding, budgeting, revenue modeling, cash flow *(development budget; invoicing/estimating features touch financial controls)*
- **Security:** Data protection, encryption, access control, audit trail *(client PII, financial data, role-based access for crews vs. office)*
- **Executive:** Leadership alignment, board updates, strategic visibility
- **Operations:** Process design, resource allocation, vendor management *(field workflows must map to how crews actually work)*

These dependencies will be documented in the Architecture/Design document.

---

## Available Agents

The following domain-expert agents are available in this project's department folders. When your current task requires domain expertise, read the relevant agent files before proceeding.

| Domain | Department Folder | Agent Files | Expertise |
|---|---|---|---|
| Finance & Investment | `Finance/agents/` | Finance-AGENT.md, Finance-advisor.md, Investment-AGENT.md, Investment-advisor.md | Financial modeling, budgeting, cash flow, investment strategy |
| Marketing & Growth | `Marketing/agents/` | Marketing-AGENT.md, Marketing-advisor.md, Market-Development-AGENT.md, Market-Development-advisor.md, Sales-AGENT.md, Sales-advisor.md | Campaigns, content, GTM, market development, sales |
| Legal | `Legal/agents/` | Legal-AGENT.md, Legal-advisor.md | Contracts, compliance, IP, regulatory |
| Security & Infrastructure | `Security/agents/` | Infrastructure-AGENT.md, Infrastructure-advisor.md | Security architecture, infrastructure design, cloud |
| Executive & Strategy | `Executive/agents/` | Strategy-AGENT.md, Strategy-advisor.md, PMO-AGENT.md, PMO-advisor.md, Growth-n-Revenue-AGENT.md, Growth-n-Revenue-advisor.md, Human-Psychology-AGENT.md, Human-Psychology-advisor.md | Strategic planning, program management, revenue, stakeholder psychology |
| Operations | `Operations/agents/` | Operations-AGENT.md, Operations-advisor.md, Infrastructure-AGENT.md, Infrastructure-advisor.md, Automation-AGENT.md, Automation-advisor.md | Process design, runbooks, infrastructure ops, automation |
| Product Development | `Product_Development/agents/` | Product-Development-AGENT.md, Product-Development-advisor.md, Software-Development-AGENT.md, Software-Development-advisor.md | Product strategy, specs, software architecture, dev workflows |
| Tech Support | `TechSupport/agents/` | Tech-Support-AGENT.md, Tech-Support-advisor.md | Ticket triage, escalation, KB articles, customer support |
| People & Culture | `People-n-Culture/agents/` | People-n-Culture-AGENT.md, People-n-Culture-advisor.md | HR, hiring, onboarding, performance, org design |

**How to use:** When your task touches any of these domains, read the relevant AGENT.md for operational workflows or the advisor.md for strategic guidance before proceeding.

**Source:** All agents originate from `AI_Memory_Open/Memory_Agents/`. If project-local copies are outdated, refresh from the source.

---

## Document 1: Project Context [TEMPLATE — IN PROGRESS]

> Fill in this section collaboratively with the owner. Items marked *(draft)* were proposed by the AI and need confirmation.

### Vision & Goals
- **Vision Statement:** *(draft)* One system connecting Fatali Builders' field crews, office, and clients — replacing scattered calls, paper, and spreadsheets with unified job tracking, estimating, scheduling, and invoicing.
- **Primary Goal:** *(open — owner input needed)* What outcome defines success? (e.g., every active job tracked in the app within 3 months of launch)
- **Secondary Goals:** *(open — owner input needed)*

### Target Audience / Users
- *(draft)* Company owner, office/admin staff, site supervisors, field crews, and clients of Fatali Builders
- *(open)* Is this an internal tool only, or also a product to offer other contractors?
- *(open)* How many users/jobs are expected at launch?

### Success Metrics
- *(open — owner input needed)* Candidate KPIs: % of jobs managed in-app, estimate turnaround time, invoice collection time, daily-log compliance, client satisfaction

### Institutional Dependencies
- *(draft)* Legal (contracts, client data privacy), Finance (estimating/invoicing controls), Security (role-based access, client PII), Operations (field workflow design)

### Assumptions & Constraints
- **CONFIRMED (owner, 2026-07-16):** The app must **integrate with all kinds of tools** — it should be built integration-first rather than as a closed system.
- **CONFIRMED (owner, 2026-07-16, revised same day):** Accounting tool is **Microsoft Excel only** — the owner explicitly dropped QuickBooks ("use just Microsoft Excel, leave QuickBooks"). The app must import/export Excel files and can act as the primary job-costing/invoicing system itself, with Excel as the reporting/migration format.
- **CONFIRMED (owner, 2026-07-16):** Communication with clients and crews happens via **WhatsApp and phone calls** — the app should integrate WhatsApp messaging and make calling easy (tap-to-call, call notes). Remaining tool inventory (client contact storage, photo storage, scheduling/calendar) still to be collected.
- *(open — owner input needed)* Budget, timeline, offline access requirements for job sites, language(s) required

---

## Document 2: Architecture/Design [TEMPLATE]

> Not started. To be developed collaboratively. This is a **Software** project — use the software sections below.

### For Software Projects
- System architecture (services, layers, boundaries) — **owner directive (2026-07-16): integration-first architecture.** The app must be able to connect to all kinds of tools: design around an API-first core with webhooks and connector modules (MCP-style connectors, like the system's `zoho-mcp-server/` reference implementation).
- Technology stack (frontend, backend, databases, infrastructure) — *(open)* mobile-first (crews are in the field) vs. web-first; native vs. PWA
- Data model and integrations — **broad integration surface, candidates to prioritize with owner:**
  - *Accounting/Finance:* **CONFIRMED (owner, 2026-07-16, revised): Microsoft Excel ONLY — QuickBooks dropped by owner decision.** → Priority integration 1: **Excel import/export** (.xlsx) for estimates, job-cost reports, invoices, and migration of existing spreadsheets. The app itself becomes the system of record for job finances, with Excel as the in/out format. ~~QuickBooks connector~~ (superseded 2026-07-16). Payment processing optional/later.
  - *Messaging:* **CONFIRMED (owner, 2026-07-16): WhatsApp + phone calls.** → Priority integration 2: **WhatsApp** (send job updates, quotes, and reminders to clients/crews — via WhatsApp Business API, or simple wa.me share links as a no-setup first step). **Calls:** tap-to-call from every contact/job screen + optional call notes. Slack/SMS/email deprioritized.
  - *CRM:* none in use today — the app's own contact management likely suffices; external CRM connectors deferred
  - *Productivity:* Google Workspace / Microsoft 365 — pending owner answer on photo storage & calendar
  - *Field/Construction:* weather services, maps/geolocation, supplier catalogs, e-signature — later releases
- Security model and constraints — role-based access (owner/office/supervisor/crew/client); credential management for third-party integrations must follow the system rule: secrets never committed to git
- Deployment targets and CI/CD strategy
- Development conventions and standards

---

## Document 3: Release Plan [TEMPLATE]

> Not started. To be developed collaboratively after Documents 1 and 2.

### Release Overview
- **Release Version:** (e.g., 0.1, 1.0, Phase 1)
- **Codename:** (optional)
- **Target Launch Date:** *(open — owner input needed)*
- **Success Criteria:** *(open — owner input needed)*

### Epics (Major Work Streams)
*(draft candidates for discussion — refine with owner)*

**Epic 1: Jobs & Projects Core** — job records, status tracking, documents, photos
**Epic 2: Estimates & Quotes** — line-item estimating, quote generation, client approval
**Epic 3: Scheduling & Crews** — calendar, crew assignment, dispatch
**Epic 4: Field Logs** — daily site logs, photo capture, timesheets, offline support
**Epic 5: Invoicing & Payments** — invoices from estimates/actuals, payment tracking

### Milestones
*(to be defined)*

### Risks & Mitigation
*(to be defined)*

---

## How to Use This File

1. **Reference During Sessions:** This file is your master reference while staging. Return to it frequently.
2. **Update Incrementally:** As you develop each document, update the "Status" fields in the Staging Roadmap section.
3. **Link to Decisions:** When decisions are made during staging, log them in `decisions-learnings/` and index them in `Key-Decisions.md`.
4. **Promote to Project:** Once all three documents are complete and signed off, execute PROJECT_MEMORY_INIT.md to create the full project memory.

---

## Next Steps

**Now:** Owner reviews this Master-Context.md — especially the AI-drafted vision — and confirms or corrects it.

**Then:** Continue with Document 1 (Project Context) to lock vision, goals, users, and constraints.

When ready, say: "Start with Document {1|2|3}"
