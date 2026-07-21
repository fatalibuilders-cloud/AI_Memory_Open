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

**Management features — CONFIRMED IN SCOPE (owner, 2026-07-16):** job tracking, crew scheduling, and daily site logs stay in the product (delivered as Release 4, after the core results-generator).

**Release 1 construction scope — CONFIRMED (owner, 2026-07-16, per AI recommendation):** residential buildings — houses/villas, ground floor plus a few storeys. Other construction types follow in later releases.

**Market — CONFIRMED (owner, 2026-07-16):** launch from Kenya; product built for the worldwide market from day one.

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
**Status:** [ ] Not Started [ ] In Progress [x] **COMPLETE (2026-07-16)**
**Description:** Vision, goals, target market, success metrics, key assumptions, institutional dependencies
**Note:** All key elements owner-confirmed: public product, 7 outputs, $30 lifetime, worldwide market launching from Kenya, residential-first, management features in scope.

### Document 2: Architecture/Design
**Status:** [ ] Not Started [ ] In Progress [x] **DRAFT COMPLETE (2026-07-16) — pending owner sign-off**
**Description:** System design, technology stack, data model, security model, deployment strategy
**Note:** Code-profile standards architecture owner-confirmed; platform/stack AI-proposed (see Document 2 section) — owner may approve as-is.

### Document 3: Release Plan
**Status:** [ ] Not Started [ ] In Progress [x] **DRAFT COMPLETE (2026-07-16) — pending owner sign-off**
**Description:** Phased roadmap (R1-R4) with epics and acceptance criteria (see Document 3 section)

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

## Document 2: Architecture/Design [DRAFT COMPLETE — pending owner sign-off]

> Standards, market, integrations, auth, and payments are owner-confirmed. Platform/stack items marked *(AI-proposed)* follow from those decisions; the owner may approve as-is or adjust.

### For Software Projects
- **Design codes & standards — CONFIRMED (owner, 2026-07-16).** The app's calculations, drawings, and engineering outputs follow recognized codes, selectable per project as a **code profile**:
  - **Eurocodes (primary baseline):** EN 1990 (basis of design), EN 1991 (actions/loading), EN 1992 (concrete), EN 1993 (steel), EN 1995 (timber), EN 1996 (masonry), **EN 1997 (geotechnical — governs the geotech report)**, EN 1998 (seismic); supporting: EN 206 (concrete spec), EN 13670, EN 10025, EN 1090
  - **British Standards (legacy support, still widely used):** BS 8110 (concrete), BS 5950 (steel), BS 5268 (timber), BS 6399 (loading), **BS 8004 (foundations)**, BS 5628 (masonry), BS 8000 (workmanship), BS 8204 (screeds), BS 7671 (wiring), BS 5839 (fire alarms)
  - **US codes:** IBC/IRC (building), ACI 318 (concrete), AISC 360 (steel), ASCE 7 (loads), TMS 402/602 (masonry), NDS (wood), NFPA 70/13/101 (electrical/fire)
  - **Kenya profile:** Eurocodes + BS as commonly adopted, **KEBS KS standards** (Kenyan adaptations of ISO/BS/EN), FIDIC contract conditions where relevant
  - **Implementation rule:** every generated output states which code profile produced it. Release 1 calculators use code-consistent quantity/measurement conventions; Release 3 structural/geotech rule-sets implement Eurocode + BS first (Kenya-aligned), US codes later.
- **Market — CONFIRMED (owner, 2026-07-16):** **Launch from Kenya, built for the WORLD.** The product launches from Kenya but targets a worldwide market from day one — not only Kenya or Africa. Implications: dual payment stack (global card checkout via a merchant-of-record provider + M-Pesa via a Kenyan gateway for the home market), multi-currency display (USD primary, KES and others), English first with the interface built translation-ready, and the code-profile architecture (Eurocode/BS/US/KEBS) serving worldwide users from the start.
- System architecture (services, layers, boundaries) — **owner directive (2026-07-16): integration-first architecture.** The app must be able to connect to all kinds of tools: design around an API-first core with webhooks and connector modules (MCP-style connectors, like the system's `zoho-mcp-server/` reference implementation).
- **User accounts & authentication (NEW, owner 2026-07-16):** public product — signup/login required. Email + password baseline; social login (Google) optional later. Payment status gates access.
- **Payments (owner 2026-07-16; dual stack for worldwide + Kenya launch):** one-time $30 checkout for lifetime access via (a) a global **merchant-of-record** card provider (Paddle or Lemon Squeezy — handles worldwide sales tax/VAT) AND (b) **M-Pesa** through a Kenyan gateway (Pesapal/Flutterwave/DPO) for the home market. Provider accounts + keys needed at build/launch of the payment step.
- **Platform & technology stack *(AI-proposed 2026-07-16)*:**
  - **Platform:** mobile-first **Progressive Web App (PWA)** — runs on any phone/tablet/computer in the browser, installable to the home screen, one codebase, no app-store gatekeeping → worldwide reach on day one and fits mobile-heavy usage in the launch market. Native apps only later if demand justifies.
  - **Frontend:** Next.js (React) + TypeScript; responsive UI; calculators cached offline via PWA (weak connectivity on job sites)
  - **Backend:** Node.js/TypeScript (Next.js API routes); REST API + webhooks (integration-first)
  - **Database & storage:** managed PostgreSQL; S3-compatible object storage for generated files (drawings, PDFs, Excel) and uploads
  - **Output engines:** calculator rule-modules per code profile (pure TypeScript, unit-tested against worked examples validated by the owner-engineer); 2D drawings as SVG → PDF/DXF export; renders from the same geometry via three.js (R2); PDF report generator; .xlsx via spreadsheet library
  - **Hosting & CI/CD:** low-cost scalable platform (Vercel/Railway/Fly.io — final pick at build time); deploys from GitHub
  - **Unit economics guardrail (advisor):** serverless/low-fixed-cost hosting keeps per-user lifetime cost far below the $30 price
- **Multi-currency & languages:** prices in USD with KES and local equivalents; English first, interface built translation-ready
- **Free preview funnel *(AI-proposed)*:** visitors can run a sample calculation with limited output before paying; $30 unlocks full results, exports, and saved projects
- Data model and integrations — **broad integration surface, candidates to prioritize with owner:**
  - *Accounting/Finance:* **CONFIRMED (owner, 2026-07-16, revised): Microsoft Excel ONLY — QuickBooks dropped by owner decision.** → Priority integration 1: **Excel import/export** (.xlsx) for estimates, job-cost reports, invoices, and migration of existing spreadsheets. The app itself becomes the system of record for job finances, with Excel as the in/out format. ~~QuickBooks connector~~ (superseded 2026-07-16). Payment processing optional/later.
  - *Messaging:* **CONFIRMED (owner, 2026-07-16): WhatsApp + phone calls.** → Priority integration 2: **WhatsApp** (send job updates, quotes, and reminders to clients/crews — via WhatsApp Business API, or simple wa.me share links as a no-setup first step). **Calls:** tap-to-call from every contact/job screen + optional call notes. Slack/SMS/email deprioritized.
  - *CRM:* none in use today — the app's own contact management likely suffices; external CRM connectors deferred
  - *Productivity:* photo/document storage handled in-app (object storage); external Drive/365 sync deferred
  - *Field/Construction:* weather services, maps/geolocation, supplier catalogs, e-signature — later releases
- **Unified project-data input model (key design artifact):** one structured entry flow — location, construction type (R1: residential), dimensions/floors/rooms, material preferences, soil type when known — feeds ALL 7 outputs so users never re-enter data as new output types ship in R2/R3.
- **Security & compliance:** HTTPS everywhere; passwords hashed (argon2/bcrypt); secrets in environment variables, never in git; roles: user / admin (R4 adds per-project owner/supervisor/crew roles); data protection per Kenya Data Protection Act 2019 + GDPR-compatible practices (worldwide product); engineering outputs carry watermark + code-profile stamp + engineer-review disclaimer on every document.

---

## Document 3: Release Plan [DRAFT COMPLETE — pending owner sign-off]

> Owner-confirmed: R1 scope = residential buildings; management features stay (R4). Story-level detail is written at PROJECT_MEMORY_INIT time.

### Release Overview
- **Release 1 (MVP "Sellable Core"):** accounts + $30 dual-stack checkout (cards worldwide + M-Pesa) + unified project data input (residential) + all three calculators (Eurocode/BS profiles) + Excel/PDF/WhatsApp outputs + product site. **Success criteria:** a stranger can sign up, pay $30, enter a residential project, and download/share a correct materials + cost + labor estimate stamped with its code profile.
- **Release 2 ("See It"):** 2D plan drawings from entered dimensions (SVG → PDF/DXF), then renders (three.js). **Success criteria:** the same entered data produces a dimensioned 2D plan and a visual render without re-entry.
- **Release 3 ("Engineering"):** preliminary structural drawings + geotechnical report from soil type (EN 1997 / BS 8004 first). **Gate:** owner-engineer validates rule-sets; legal disclaimers reviewed BEFORE release. **Success criteria:** outputs carry watermark, code-profile stamp, and engineer-review disclaimer on every page.
- **Release 4 ("Run the Job"):** job tracking, crew scheduling, daily site logs with photos, per-project roles. **Success criteria:** a builder manages a real project end-to-end in the app.
- **Target dates:** set at PROJECT_MEMORY_INIT; R1 is sized to be the fastest possible path to revenue.

### Epics (Major Work Streams)
*(revised 2026-07-16 after full core-tool definition — sequenced by feasibility)*

**Epic 1: Accounts & Access** — signup, login, password reset; $30 lifetime-access checkout (payment provider); access gating
**Epic 2: Project Data Input** — structured entry of project data (dimensions, floors, rooms, materials preferences, location, soil type when known) — the single input flow that feeds ALL outputs
**Epic 3: Calculators** — material quantities, itemized cost estimate, labor/time estimate
**Epic 4: Results Output & Sharing** — Excel export, WhatsApp share (wa.me), printable/PDF result sheets with disclaimers
**Epic 5: Drawings & Visuals** — 2D plan drawings generated from entered dimensions; renders (visualizations)
**Epic 6: Engineering Outputs** — preliminary structural drawings; geotechnical report generated from soil type input — **both watermarked "preliminary — requires licensed engineer review"**
**Epic 7: Product Site & Onboarding** — landing page, pricing page, first-run guidance
**Epic 8 (CONFIRMED IN SCOPE, owner 2026-07-16):** Job tracking / crew scheduling / daily site-log management features → Release 4

### Epic → Release Mapping
| Release | Epics | Scope |
|---|---|---|
| R1 — Sellable Core | 1, 2, 3, 4, 7 | Accounts, payment (cards + M-Pesa), residential data input, calculators, Excel/PDF/WhatsApp outputs, product site |
| R2 — See It | 5 | 2D drawings, then renders |
| R3 — Engineering | 6 | Structural drawings + geotech report (Eurocode/BS rule-sets, legal gate) |
| R4 — Run the Job | 8 | Job tracking, scheduling, site logs, per-project roles |

### Risks & Mitigation
- **Risk:** Lifetime $30 pricing vs. ongoing hosting costs. → **Mitigation:** serverless/low-fixed-cost stack; advisor guardrails (launch-offer framing, future pro tier).
- **Risk:** Engineering outputs used without professional review. → **Mitigation:** watermarks, disclaimers, legal review gate before R3; owner-engineer validates rule-sets.
- **Risk:** Calculator accuracy damages brand trust. → **Mitigation:** rule modules unit-tested against worked examples the owner validates; code-profile stamping; residential-only scope in R1.
- **Risk:** Payment failures in launch market. → **Mitigation:** dual stack (M-Pesa + global cards); tested in provider sandbox before launch.
- **Risk:** Scope creep delaying revenue. → **Mitigation:** R1 fixed to Epics 1-4 + 7; everything else phased.

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
