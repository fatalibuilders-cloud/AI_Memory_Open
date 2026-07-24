# Master AI Context — FatalibuildersConstructionApp

**Document Purpose:** Primary operational context file for any AI assistant working on FatalibuildersConstructionApp. Project overview, tech stack, conventions, execution model, and progress. For full architectural design, see [FatalibuildersConstructionApp_architecture.md](./Product_Development/FatalibuildersApp/FatalibuildersConstructionApp_architecture.md).

**Memory Design Version:** 1.1
**Last Updated:** 2026-07-16
**Owner:** Eng Ali Ahmed (fatalibuilders@gmail.com) — Owner, Fatali Builders. **First-time app builder: communications must be jargon-free with explicit action lists** (see root `contacts/Eng-Ali-Ahmed.md`).

---

## 1. Project Overview

**FatalibuildersConstructionApp** is a public Fatalibuilders-branded product. Anyone can create an account and log in. Users insert their construction project data ONCE and the app produces **seven outputs**:

1. Material quantities (cement, blocks, steel, sand, paint, …)
2. Itemized cost estimate (client-ready)
3. Labor/time estimate (crew size and duration)
4. 2D drawings from entered dimensions *(Release 2)*
5. Renders / visualizations *(Release 2)*
6. Preliminary structural drawings *(Release 3, engineer-review watermark)*
7. Geotechnical report from soil type *(Release 3, engineer-review watermark)*

**Business model:** one-time **$30 for lifetime access** (advisor guardrails: treat as launch offer; keep per-user cost near zero; future pro tier possible). Free preview before purchase.
**Market:** worldwide, launched from Kenya. Payments: global cards (merchant-of-record) + M-Pesa. USD-primary, KES prominent.
**Release 1 scope:** residential buildings (houses/villas, ground + a few storeys).
**Standards:** per-project **code profiles** — Eurocodes (EN 1990-1999) + British Standards first, US codes later, KEBS/Kenya profile; every output stamps its profile. EN 1997 / BS 8004 govern the geotech report.
**Integrations:** Excel (.xlsx) export first-class; WhatsApp share (wa.me → Business API later); tap-to-call. Management features (job tracking, crew scheduling, site logs) confirmed → Release 4.

Full context trail: staging archive at `projects/staging/FatalibuildersConstructionApp/` (Documents 1-3 and the complete decision history).

---

## 2. Technical Stack

Mobile-first **PWA** · Next.js (React) + TypeScript + Tailwind · Next.js API routes (Node) · PostgreSQL · S3-compatible object storage · TypeScript calc rule modules per code profile · SVG→PDF/DXF drawings (R2) · three.js renders (R2) · PDF/xlsx document generation · Paddle-or-LemonSqueezy + M-Pesa gateway · Vercel/Railway/Fly.io hosting · GitHub CI/CD. Details: architecture doc §2.

---

## 3. Core Directory Structure

The app source code lives in its **own private repository**: **https://github.com/fatalibuilders-cloud/fatalibuilders-app** (migrated there 2026-07-23 — no longer under `app-src/` in this memory repo). Future sessions: clone the app repo (`add_repo` fatalibuilders-cloud/fatalibuilders-app), work there, push to its `main`. This memory repo holds context/planning only. Structure documented in [module-map.md](./Product_Development/FatalibuildersApp/module-map.md).

---

## 4. Key Commands

*To be documented at CORE-1.0 (scaffold) and maintained in module-map.md / production-instructions.md. Expected: `npm install`, `npm run dev`, `npm run build`, `npm run test`, `npm run lint`.*

---

## 5. Development Conventions & Rules

### 5.1 Secrets & Environment Variables
- **Never hardcode secrets.** Use `.env.local` (git-ignored) locally and the hosting platform's secret manager in production.
- AI assistants must NEVER read, store, echo, or log secret values. Use `__HUMAN_PROVIDED__` placeholders and give the owner plain-language instructions for where to paste values.

### 5.2 Code Generation Rules
- Complete, runnable code — no truncation. Exact file path at the top of every code block written into memory files.
- Silent error catching banned; log errors with context.
- Every calculator rule module ships with unit tests against owner-validated worked examples BEFORE its story is marked done.

### 5.3 Git Branching
- App repo: trunk-based; feature branches → PR → `main`; preview deploys per PR.
- Memory repo: commit and push per session closure protocol.

---

## 6. AI Execution Model

**Model D (mixed, direct execution):** AI executes code directly (Claude Code) using the `[AI]` / `[Human]` / `[AI+Human]` story labeling convention.

### Story Labels
- **`[AI]`** — AI executes directly: reads story, runs commands, writes files, reports results.
- **`[AI + Human]`** — AI performs all technical steps; the owner acts at explicit `[Human]` checkpoints (creating provider accounts, pasting keys into the hosting dashboard, validating engineering examples, approving legal text).
- **`[Human]`** — Owner-only actions (identity verification with payment providers, business decisions).

### Direct Execution Rules
1. Terminal commands run directly and sequentially; wait for completion.
2. Files are written directly to the workspace.
3. Errors are diagnosed and resolved autonomously before reporting.
4. Security boundary: never read or echo secrets; placeholders only.
5. Scope discipline: execute only the current story; no speculative execution of future stories.
6. Human checkpoints are written in plain language for a first-time app builder — say exactly where to click and what to paste, and why.

---

## 6a. Bug & Change Request Tracking

All changes outside a formal release story are logged in **`Product_Development/Releases/Bugs.md`** — naming `bug-[release]-[YYYY-MM-DD]-[HHMM]`, statuses Open → In Progress → Complete, metrics table maintained. Log BEFORE starting the work; complete the entry after. Not logged: normal story execution, pure Q&A, session protocols.

---

## 7. Memory Access Model — Lazy Loading

### Tier 1 — Always Read (Session Init)
| File | Purpose |
|------|---------|
| **This file** | Overview, progress, conventions, execution model |
| [FatalibuildersConstructionApp_architecture.md](./Product_Development/FatalibuildersApp/FatalibuildersConstructionApp_architecture.md) | Design philosophy, security, infrastructure constraints |
| [module-map.md](./Product_Development/FatalibuildersApp/module-map.md) | Physical structure of the app repo |
| [NextSteps.md](./NextSteps.md) | Roadmap, blockers, what to work on next |

### Tier 2 — Read Index Only, Drill Down on Match
| Index | Details | When |
|-------|---------|------|
| [Key-Decisions.md](./Key-Decisions.md) | `decisions-learnings/` | Keyword match with current task |
| [Sessions.md](./Sessions.md) | `session-summary/` | Possible prior work / troubleshooting |
| [Risk-Registry.md](./Risk-Registry.md) | `Security/` | Task touches a risk area; release planning |

### Tier 3 — Read Only When Relevant
Release files (`Product_Development/Releases/`), Bugs.md (metrics at init), production-instructions.md (before any build/deploy), plan-release.md (planning), api-key-store.md (integrations), assets/ (UI/design work).

---

## 8. Available Agents — Domain Expertise Index

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

**How to use:** when a task touches a domain, read the AGENT.md (operational) or advisor.md (strategic) BEFORE proceeding. Source of truth: `AI_Memory_Open/Memory_Agents/`.

---

## 9. Session History & Handover

- **Latest Summary:** `session-summary/AI-Session-Summary-2026-07-23_1310.md` — Epic 4 complete: data model + wizard + code profiles
- **Latest Decisions:** in the 2026-07-23 summary (JSONB+zod model, footprint-only-required defaults) and `decisions-learnings/Key-Decisions-2026-07-16_1051.md`
- **Master Indexes:** [Key-Decisions.md](./Key-Decisions.md), [Sessions.md](./Sessions.md)
- **Risk Registry:** [Risk-Registry.md](./Risk-Registry.md)
- **Next Steps:** [NextSteps.md](./NextSteps.md)
- **Architecture:** [FatalibuildersConstructionApp_architecture.md](./Product_Development/FatalibuildersApp/FatalibuildersConstructionApp_architecture.md)
- **Staging archive (pre-initialization history):** `projects/staging/FatalibuildersConstructionApp/`

---

## 10. Project Progress

### Release 1.0 — Sellable Core
- **Release File:** `Product_Development/Releases/fatalibuilders-app-build-instructions-1_0.md`
- **Completion:** ~52% (15/29) — [DONE]: **CORE-1.0 (app repo created & migrated 2026-07-23)**, 1.3, 2.0, 4.0, 4.1, 4.2, 5.0, 5.1, 5.2, 5.3, Epic 6 (6.0 views, 6.1 Excel, 6.2 PDF, 6.3 WhatsApp share). A completed project shows materials + cost (full/labour) + labor; paid users download a 4-sheet Excel BOQ and an A4 PDF BOQ; anyone can WhatsApp-share a summary (growth loop). 68 tests passing. **App now lives in its own private repo `fatalibuilders-cloud/fatalibuilders-app` (main branch).** Only open validation: labor productivity norms. **Remaining for a sellable MVP: Epic 3 (payments — the $30 checkout) + Epic 7 (product site/onboarding/legal) + Epic 8 (launch).**

### Future Releases (planned skeleton)
- **2.0 — See It:** 2D drawings, renders
- **3.0 — Engineering:** structural drawings + geotech report (legal gate)
- **4.0 — Run the Job:** job tracking, crew scheduling, site logs

---

## 11. Production Infrastructure

*None provisioned yet. Updated as CORE-1.x stories execute.*

---

## 12. Build & Deploy Reference

**IMPORTANT:** Before building or deploying ANY component, read [production-instructions.md](./Product_Development/FatalibuildersApp/production-instructions.md) first.

---

*This document is the master operational context for FatalibuildersConstructionApp. Updated every session by the closure protocol.*
