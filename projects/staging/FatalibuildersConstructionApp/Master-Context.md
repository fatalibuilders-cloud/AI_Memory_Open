# FatalibuildersConstructionApp — Staging Master Context

**Project Name:** FatalibuildersConstructionApp
**Category:** Software (web/mobile construction management app)
**Owner:** Eng Ali Ahmed (fatalibuilders@gmail.com) — Owner, Fatali Builders
**Stage:** Staging (Ideation & Preparation)
**Last Updated:** 2026-07-16 (session 2 — integration strategy confirmed by owner)

---

## Project Vision

> **STATUS: OWNER-DIRECTED (2026-07-16), core feature definition still open.** The owner redefined the product: it is NOT an internal tool — it is a public Fatalibuilders product.

The Fatalibuilders Construction App is a **Fatalibuilders-branded product open to the public**. Anyone can create an account and log in. Users **insert their construction project data and the app gives out results**. Access is sold as a **one-time payment of $30 for lifetime access**. Results export to Excel and share via WhatsApp; contact screens support tap-to-call.

**Core tool outputs — CONFIRMED (owner, 2026-07-16):** from the user's project data the app produces:
1. **Material quantities** — cement, blocks, steel, sand, paint, etc.
2. **Cost estimate** — itemized, client-ready
3. **Labor/time estimate** — crew size and duration
4. **2D drawings** — plans generated from the entered dimensions
5. **Renders** — visualizations of the project
6. **Structural drawings** — preliminary structural layouts
7. **Geotechnical report** — generated once the user enters the soil type

> **⚠️ ENGINEERING RESPONSIBILITY (recorded 2026-07-16, must be reflected in Legal + product design):** Structural drawings and geotechnical reports are professional engineering deliverables. In most jurisdictions they legally require review and stamping by a licensed engineer before use in construction. The app MUST label outputs 4-7 as **preliminary/indicative — for guidance only, not for construction without licensed engineer review**, with clear disclaimers at generation and on every exported document. This protects users' safety and Fatali Builders' liability.

> **KEY OPEN QUESTION 2 (still open):** Are the earlier-drafted management features (job tracking, crew scheduling, daily site logs) also wanted in this product (Epic 6), or is the product the focused results-generator above?

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
- **Vision Statement (owner-directed, 2026-07-16):** A public Fatalibuilders product: users log in, insert construction data, get results — $30 one-time for lifetime access.
- **Primary Goal:** *(draft)* Paying users — the product generates revenue for Fatali Builders as a product line, not just internal savings.
- **Secondary Goals:** *(draft)* Brand visibility for Fatali Builders; the company itself uses the app for its own estimates.

### Target Audience / Users
- **CONFIRMED (owner, 2026-07-16):** Anyone can use it after logging in — a public product, not an internal tool. Likely users: contractors, builders, site engineers, and possibly homeowners planning projects.
- *(open)* Primary market/geography and language(s)?

### Business Model
- **CONFIRMED (owner, 2026-07-16):** One-time payment, **$30 for lifetime access**.
- **Advisor note (Growth-n-Revenue advisor, consulted 2026-07-16):** Lifetime pricing caps revenue per customer at $30 while hosting/support costs continue for the customer's lifetime — unit economics must be watched (LTV is fixed; keep infrastructure cost per user very low). Recommendations to revisit before launch: (a) treat $30 lifetime as a launch offer that can later become a tier; (b) leave room for future expansion revenue (e.g., a pro tier with advanced features); (c) validate willingness-to-pay with the first real users. The owner's $30 lifetime directive stands for release 1.

### Success Metrics
- *(draft — aligned to the business model)* Paid signups, revenue, activation rate (% of signups who run their first calculation), retention/usage (results generated per user per month), refund rate

### Institutional Dependencies
- **Updated for public product (2026-07-16):**
  - **Marketing** — now essential: go-to-market for a paid public product (app store/web presence, launch messaging)
  - **Legal** — terms of service, privacy policy, refund policy for the $30 purchase, consumer protection compliance in target markets; **professional-liability disclaimers for engineering outputs (structural drawings, geotechnical reports) — mandatory before Release 3**
  - **Finance** — payment processing, revenue tracking, tax on digital sales
  - **Security** — user accounts and credentials, payment security, personal data protection
  - **Operations/Tech Support** — support channel for paying customers

### Assumptions & Constraints
- **CONFIRMED (owner, 2026-07-16):** The app must **integrate with all kinds of tools** — it should be built integration-first rather than as a closed system.
- **CONFIRMED (owner, 2026-07-16, revised same day):** Accounting tool is **Microsoft Excel only** — the owner explicitly dropped QuickBooks ("use just Microsoft Excel, leave QuickBooks"). The app must import/export Excel files and can act as the primary job-costing/invoicing system itself, with Excel as the reporting/migration format.
- **CONFIRMED (owner, 2026-07-16):** Communication with clients and crews happens via **WhatsApp and phone calls** — the app should integrate WhatsApp messaging and make calling easy (tap-to-call, call notes). Remaining tool inventory (client contact storage, photo storage, scheduling/calendar) still to be collected.
- *(open — owner input needed)* Budget, timeline, offline access requirements for job sites, language(s) required

---

## Document 2: Architecture/Design [TEMPLATE]

> Not started. To be developed collaboratively. This is a **Software** project — use the software sections below.

### For Software Projects
- **Design codes & standards — CONFIRMED (owner, 2026-07-16).** The app's calculations, drawings, and engineering outputs follow recognized codes, selectable per project as a **code profile**:
  - **Eurocodes (primary baseline):** EN 1990 (basis of design), EN 1991 (actions/loading), EN 1992 (concrete), EN 1993 (steel), EN 1995 (timber), EN 1996 (masonry), **EN 1997 (geotechnical — governs the geotech report)**, EN 1998 (seismic); supporting: EN 206 (concrete spec), EN 13670, EN 10025, EN 1090
  - **British Standards (legacy support, still widely used):** BS 8110 (concrete), BS 5950 (steel), BS 5268 (timber), BS 6399 (loading), **BS 8004 (foundations)**, BS 5628 (masonry), BS 8000 (workmanship), BS 8204 (screeds), BS 7671 (wiring), BS 5839 (fire alarms)
  - **US codes:** IBC/IRC (building), ACI 318 (concrete), AISC 360 (steel), ASCE 7 (loads), TMS 402/602 (masonry), NDS (wood), NFPA 70/13/101 (electrical/fire)
  - **Kenya profile:** Eurocodes + BS as commonly adopted, **KEBS KS standards** (Kenyan adaptations of ISO/BS/EN), FIDIC contract conditions where relevant
  - **Implementation rule:** every generated output states which code profile produced it. Release 1 calculators use code-consistent quantity/measurement conventions; Release 3 structural/geotech rule-sets implement Eurocode + BS first (Kenya-aligned), US codes later.
- **Market signal (to confirm with owner):** the Kenya-specific standards guidance suggests **Kenya is the primary market**. If confirmed: payment provider must support **M-Pesa** alongside cards (e.g., Pesapal, Flutterwave, DPO, or Paystack as local gateways — Stripe is not directly available to Kenyan merchants), pricing shown in KES alongside USD, and KEBS/NCA (National Construction Authority) considerations noted for credibility.
- System architecture (services, layers, boundaries) — **owner directive (2026-07-16): integration-first architecture.** The app must be able to connect to all kinds of tools: design around an API-first core with webhooks and connector modules (MCP-style connectors, like the system's `zoho-mcp-server/` reference implementation).
- **User accounts & authentication (NEW, owner 2026-07-16):** public product — signup/login required. Email + password baseline; social login (Google) optional later. Payment status gates access.
- **Payments (NEW, owner 2026-07-16):** one-time $30 checkout for lifetime access → requires a payment provider (Stripe, Paddle, or Lemon Squeezy — Paddle/Lemon Squeezy act as merchant-of-record and handle sales tax globally, worth considering for a first-time seller). Provider account + keys needed at build/launch of the payment step.
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
*(revised 2026-07-16 after full core-tool definition — sequenced by feasibility)*

**Epic 1: Accounts & Access** — signup, login, password reset; $30 lifetime-access checkout (payment provider); access gating
**Epic 2: Project Data Input** — structured entry of project data (dimensions, floors, rooms, materials preferences, location, soil type when known) — the single input flow that feeds ALL outputs
**Epic 3: Calculators** — material quantities, itemized cost estimate, labor/time estimate
**Epic 4: Results Output & Sharing** — Excel export, WhatsApp share (wa.me), printable/PDF result sheets with disclaimers
**Epic 5: Drawings & Visuals** — 2D plan drawings generated from entered dimensions; renders (visualizations)
**Epic 6: Engineering Outputs** — preliminary structural drawings; geotechnical report generated from soil type input — **both watermarked "preliminary — requires licensed engineer review"**
**Epic 7: Product Site & Onboarding** — landing page, pricing page, first-run guidance
**Epic 8 (pending Open Question 2):** Job tracking / scheduling / site-log management features

**Suggested release phasing (to get to market fast and de-risk the hard parts):**
- **Release 1 (MVP):** Epics 1, 2, 3, 4, 7 — accounts, payment, calculators, exports, site. Sellable on day one.
- **Release 2:** Epic 5 — 2D drawings, then renders.
- **Release 3:** Epic 6 — structural drawings + geotechnical report (needs engineering rule-sets and legal review first).
- **Release 4 (if wanted):** Epic 8 — management features.

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
