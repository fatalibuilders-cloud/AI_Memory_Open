# Fatalibuilders Construction App — Complete Build & Session Log

**Owner:** Eng Ali Ahmed · Fatali Builders · fatalibuilders@gmail.com
**Document date:** 2026-07-23
**Status:** Release 1.0 in progress — ~55% (16 of 29 stories)
**Purpose:** A complete, self-contained record of everything built and decided in this project — where it lives, how to run and deploy it, and how another developer or AI can pick it up cold.

---

## 1. What This Product Is

A **public, Fatalibuilders-branded web app**. Anyone signs up, enters their construction project once, and gets a full set of results. Sold as **one payment of $30 for lifetime access**. Launched from Kenya, built for the worldwide market.

**The user enters project data once → the app produces seven outputs:**
1. Material quantities (cement, blocks, steel, sand, roofing, paint…)
2. Itemized cost estimate (BOQ, in KES) — two modes: full contract vs labour-only
3. Labor & time plan (crew per phase, duration, cost)
4. 2D drawings *(Release 2)*
5. Renders *(Release 2)*
6. Preliminary structural drawings *(Release 3 — engineer-review gated)*
7. Geotechnical report from soil type *(Release 3 — engineer-review gated)*

Built on recognized design codes as selectable **code profiles**: Eurocodes (EN 1990–1999) + British Standards first, US codes later, plus a Kenya/KEBS profile. Every output is stamped with the profile that produced it. Structural/geotechnical outputs always carry a "preliminary — requires licensed engineer review" disclaimer.

---

## 2. Where Everything Lives (URLs & Repos)

| Thing | Location |
|---|---|
| **App source code** (private) | `https://github.com/fatalibuilders-cloud/fatalibuilders-app` — branch `main` |
| **Project memory / planning** (fork of the AI Memory template) | `https://github.com/fatalibuilders-cloud/AI_Memory_Open` — branch `claude/fatalibuilders-construction-app-vqy1ie` |
| Memory folder for this project | `AI_Memory_Open/projects/FatalibuildersConstructionApp_AI_Training/` |
| Live app URL | **Not deployed yet** — assigned at hosting step (CORE-1.1) |
| Owner API-keys guide (beginner) | `AI_Memory_Open/API-Keys-Guide.md` |
| Brand banner asset | `.../assets/content-images/designandcontent/brand-banner-2026-07-16.png` |
| Company reference (rates/BOQ/worklog) | **Not stored in git** — data extracted into the app; raw files kept by owner only |

---

## 3. Technology & Architecture

- **Platform:** Mobile-first Progressive Web App (installable, works on any phone/computer, one codebase, no app-store gatekeeping).
- **Stack:** Next.js 15 (App Router) + React 19 + TypeScript + Tailwind CSS 4.
- **Backend:** Next.js API routes (Node/TypeScript); REST + webhooks (integration-first).
- **Database:** PostgreSQL in production (via `DATABASE_URL`); **embedded PGlite** for local dev/tests (same Postgres dialect, zero setup). Auto-selected — no code change between environments.
- **Auth:** email + password, argon2id hashing, 30-day httpOnly sessions.
- **Documents:** ExcelJS (.xlsx BOQ), pdfkit (A4 PDF BOQ). WhatsApp share via wa.me links.
- **Payments:** provider abstraction; sandbox "mock" provider works today; **Paddle** chosen for real card payments (worldwide, merchant-of-record); M-Pesa gateway (Pesapal/Flutterwave) for Kenya to follow.
- **Design principle:** ONE unified project-data input model feeds ALL outputs — users never re-enter data as new output types ship.
- **Engine integrity:** every calculation rule lives in a named, owner-validated assumptions table; every engine is unit-tested against hand-checked worked examples and stamped with an engine version.

**App code layout (`src/`):**
```
app/         routes: marketing (landing/pricing), app UI (projects, wizard, results,
             account, signup/login, checkout), api/ (auth, projects, exports, checkout, webhook)
engines/     profiles/ (code profiles) · materials/ · cost/ · labor/  (pure TS, tested)
components/  UI: Header, Footer, wizard, results/cost/labor views, ExportBar, BuyButton…
db/          schema + dual-driver (Postgres / PGlite) access
lib/         auth, sessions, project CRUD, payments, Excel/PDF export
```

---

## 4. What's Built and Verified (Release 1.0)

**Done (16 stories, 76 automated tests passing):**
- **Foundation:** app scaffolded, PWA shell, health endpoint, CI workflow, migrated to its own private repo.
- **Accounts:** signup / login / logout / sessions / account page (argon2, gated).
- **Project input:** 6-step mobile wizard with autosave; unified data model; code-profile picker. Only footprint dimensions are required — everything else has editable defaults.
- **Calculators (all three, owner-validated):**
  - *Materials* — full residential rule-set (foundation, slab, walling, frame, roof, finishes). Owner corrections applied: foundation depth 1.5 m, plaster 15–20 mm.
  - *Cost* — BOQ on the **Fatali Builders 2026 rate card**; dual pricing (full contract / labour-only); 5% contingency; grand totals.
  - *Labor* — crew, duration and cost per phase + supervision. Owner day rates: mason 1,500 · laborer 600 · carpenter 1,650 · painter/electrician/plumber 1,500 · engineer 5,000 KES.
- **Outputs & sharing:** on-screen results; **Excel** (4-sheet workbook) and **PDF** (A4 BOQ with per-page disclaimer) exports — both **gated behind the $30 paywall**; **WhatsApp share** (growth loop — every shared estimate advertises the app).
- **Payments:** full **$30 buy → unlock** flow working in **sandbox mode**; purchases table, idempotent entitlement grant, forge-proof signed checkout, success banner. Real provider (Paddle) swaps into the same slots with keys.

**Worked example that's hand-verified (12 × 9 m bungalow):** excavation 37.8 m³ · ground slab 10.8 m³ · net walls 165.3 m² · 2,170 blocks · pitched roof 124.2 m² · full-contract cost ≈ KES 2.7M / labour-only ≈ KES 0.97M · ≈8 weeks.

---

## 5. How to Run It Locally

```bash
git clone https://github.com/fatalibuilders-cloud/fatalibuilders-app
cd fatalibuilders-app
npm install
npm run dev        # http://localhost:3000  (uses embedded PGlite — no DB setup)
npm test           # 76 tests
npm run build      # production build
npm run lint
```
No environment variables are needed for local development. Payments run in sandbox mode by default.

---

## 6. How to Deploy From GitHub (when ready — CORE-1.1)

The app is a standard Next.js project and deploys from its GitHub repo with no code changes:

1. **Pick a host** (recommended: Vercel — free tier, native Next.js). Alternatives: Railway, Fly.io.
2. **Connect the repo:** in the host's dashboard, "New Project" → import `fatalibuilders-cloud/fatalibuilders-app` → it auto-detects Next.js.
3. **Add a database:** create a managed PostgreSQL (the host's add-on, or Neon/Supabase free tier) and copy its connection string.
4. **Set environment variables** in the host:
   - `DATABASE_URL` = the Postgres connection string
   - `APP_URL` = the deployed URL (e.g. `https://fatalibuilders.app`)
   - `APP_SECRET` = a long random string (for signing)
   - *(payments, when live)* `PAYMENTS_PROVIDER=paddle`, `PADDLE_API_KEY`, `PADDLE_CLIENT_TOKEN`, `PADDLE_WEBHOOK_SECRET`
5. **Deploy.** Every push to `main` auto-deploys. Point a custom domain at it when ready.

> The app already runs its own database bootstrap on first boot, so the schema is created automatically.

---

## 7. Key Decisions (the "why")

- **Public product, not internal tool; $30 lifetime** — owner directive. Advisor flagged: lifetime pricing caps revenue per customer, so keep per-user cost near zero (serverless) and treat $30 as a launch offer that can gain a future pro tier.
- **Excel-only accounting (QuickBooks dropped); WhatsApp + calls** — owner tool choices.
- **Worldwide, launched from Kenya** — dual payment stack (global cards + M-Pesa), multi-currency, translation-ready.
- **Residential first** — accuracy over breadth for Release 1.
- **Management features (job tracking, scheduling, site logs)** — kept, scheduled for Release 4.
- **Engineering outputs safeguarded** — watermark + disclaimer + legal gate before Release 3; owner (a licensed engineer) validates all rule-sets.
- **App moved to its own private repo** — company rate data out of the public memory repo.
- **Paddle** chosen as the card provider (merchant-of-record handles worldwide tax).

Full decision trail with timestamps: `.../decisions-learnings/` and `Key-Decisions.md` in the project memory.

---

## 8. How Another Developer or AI Picks This Up Cold

1. **Read the memory first** (in `AI_Memory_Open/projects/FatalibuildersConstructionApp_AI_Training/`):
   - `Master-AI-Context.md` — overview, stack, conventions, progress
   - `Product_Development/FatalibuildersApp/FatalibuildersConstructionApp_architecture.md` — architecture constitution
   - `Product_Development/Releases/fatalibuilders-app-build-instructions-1_0.md` — the 29-story release plan with status
   - `NextSteps.md` — what to do next
   - `Key-Decisions.md` / `Sessions.md` — indexed history
2. **Run the session protocol:** `agents/open.md` (start) and `agents/closure.md` (end) — these keep the memory current across sessions.
3. **Clone the app repo** and run it locally (Section 5).
4. **For AI (Claude Code):** `add_repo fatalibuilders-cloud/fatalibuilders-app`, clone, work there, push to `main`.

---

## 9. Release Roadmap

| Release | Name | Scope | Status |
|---|---|---|---|
| **1.0** | Sellable Core | accounts, payment, calculators, exports, product site | **In progress (~55%)** |
| 2.0 | See It | 2D drawings, renders | Planned |
| 3.0 | Engineering | structural drawings + geotech report (legal gate) | Planned |
| 4.0 | Run the Job | job tracking, crew scheduling, daily site logs | Planned |

---

## 10. What's Left for a Sellable MVP (Release 1.0)

**Needs the owner:**
- **CORE-3.0 — Paddle:** create Paddle account → verify → make the "$30 Lifetime Access" product → paste sandbox keys. (Owner chose Paddle 2026-07-23.)
- **CORE-3.2 — M-Pesa:** sign up with Pesapal/Flutterwave → paste keys.
- **CORE-1.1/1.2 — Hosting + DB:** create a hosting account (Vercel) + managed Postgres.
- **CORE-7.2 — Legal:** review the Terms/Privacy/Refund pages before publishing.

**AI can do without the owner:**
- Wire Paddle + M-Pesa into the existing payment abstraction (once keys exist).
- CORE-2.2 free-preview gating; Epic 7 landing/onboarding/legal drafts; CORE-8.0 analytics.

**Open validation (non-blocking):** labor productivity norms (m²/day per trade).

---

## 11. Marketing (attached plan)

An automated marketing system is planned (`Marketing/Marketing-Automation-Plan.md`): AI content engine (brand kit, launch kit, 90-day calendar, email sequences) now; auto-publishing on the owner's Meta/email accounts at launch; in-product growth loops (WhatsApp share, free preview) already shipping inside Release 1.

---

*Generated 2026-07-23. Living document — regenerate from the project memory as the build progresses.*
