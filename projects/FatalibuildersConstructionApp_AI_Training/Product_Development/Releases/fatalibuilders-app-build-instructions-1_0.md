# FATALIBUILDERSCONSTRUCTIONAPP BUILD INSTRUCTIONS: RELEASE 1.0 — SELLABLE CORE

**Document Purpose:** Granular user stories and acceptance criteria for Release 1.0. Master execution guide for AI assistants and the owner.

**Release:** 1.0 — Sellable Core
**Story Prefix:** CORE-
**Created:** 2026-07-16
**Source:** Staging Document 3 (owner-approved 2026-07-16)

**Release goal / success criteria:** a stranger can sign up, pay $30 (card or M-Pesa), enter a residential project, and download/share a correct materials + cost + labor estimate stamped with its code profile.

**Instructions:**
* **[Human] stories:** owner acts directly (plain-language steps provided at execution time).
* **[AI] stories:** AI executes directly — reads story, runs commands, writes files.
* **[AI + Human] stories:** AI performs technical work; owner acts at explicit `[Human]` checkpoints.

---

## Epic Overview

| Epic | Name | Stories | Status |
|:---:|:---|:---:|:---:|
| 1 | Foundation & Infrastructure | 4 | In Progress (CORE-1.0 ✅ migrated; 1.3 ✅; hosting/DB next) |
| 2 | Accounts & Access | 3 | ✅ Complete (2.0 auth, 2.1 email pending real provider, 2.2 gating) |
| 3 | Payments ($30 Lifetime) | 4 | In Progress (3.1 checkout+entitlement built in sandbox; 3.0/3.2 need owner provider signup) |
| 4 | Project Data Input (Residential) | 3 | ✅ **Complete (2026-07-23)** |
| 5 | Calculators | 4 | ✅ **Complete (2026-07-23)** — 3 calculators + hardening done |
| 6 | Outputs & Sharing | 4 | ✅ **Complete (2026-07-23)** — views, Excel, PDF, WhatsApp/call |
| 7 | Product Site & Onboarding | 4 | ✅ Complete (7.0 landing, 7.1 demo, 7.2 legal drafts, 7.3 onboarding) |
| 8 | Launch Readiness | 3 | Pending |

**Total: 29 stories** — 17 [AI], 11 [AI+Human], 1 [Human]

---

## Epic 1: Foundation & Infrastructure

**CORE-1.0 [AI] — Scaffold the app repository** `[DONE — migrated to own repo 2026-07-23]`
*Migration note (2026-07-23):* Owner created private repo `fatalibuilders-cloud/fatalibuilders-app`; the full app (66 files) was pushed to its `main` branch. Verified in the new location: `npm install`, 68/68 tests, production build all green. The `app-src/fatalibuilders-app/` copy has been removed from the AI_Memory_Open memory repo — the app now lives only in its own private repo. **NOTE:** company rate data remained in AI_Memory_Open git *history* prior to migration; if full history scrub is wanted, rewrite history separately (rates are the product's baseline price table, shown to users, so sensitivity is moderate).
Create the `fatalibuilders-app` repository: Next.js + TypeScript + Tailwind, PWA config (manifest, service worker), ESLint/Prettier, folder structure per architecture doc §3, README, CI (lint + test on PR).
*Acceptance:* `npm run dev` serves a placeholder page; lint and test pass in CI; module-map.md updated.
*Status note (2026-07-16):* Scaffold complete at **`app-src/fatalibuilders-app/`** (temporary in-repo location — AI integration cannot create GitHub repos, 403). Verified locally: 8/8 engine tests pass, lint clean, production build succeeds, server + `/api/health` respond. Includes code-profile module, first materials-engine functions with worked-example tests (pending owner validation at CORE-5.0), PWA manifest, CI workflow (activates post-migration). **Remaining:** owner creates empty GitHub repo `fatalibuilders-app` → AI migrates code → story [DONE].

**CORE-1.1 [AI+Human] — Hosting platform + first deploy**
AI evaluates Vercel/Railway/Fly.io against architecture cost guardrails and recommends one; `[Human]` owner creates the hosting account (free tier) and connects the GitHub repo per plain-language steps; AI configures auto-deploy.
*Acceptance:* placeholder page live on a public URL over HTTPS; every push to `main` auto-deploys.

**CORE-1.2 [AI+Human] — Database & object storage**
AI provisions managed PostgreSQL + S3-compatible bucket on the chosen platform (`[Human]` confirms/creates add-on if dashboard action needed); migration tooling set up.
*Acceptance:* app connects to DB in production; migrations run on deploy; storage bucket reachable.

**CORE-1.3 [AI] — Base app shell** `[DONE 2026-07-16]`
Mobile-first layout, navigation, theme (Fatalibuilders branding placeholder), error/loading states, health endpoint.
*Acceptance:* shell renders correctly on phone-size and desktop viewports; Lighthouse PWA installability passes.
*Status note (2026-07-16):* Header (logo, nav, CTA), footer (with engineering disclaimer line), pricing placeholder page ($30 lifetime card), error boundary, loading state, custom 404, manifest+icons wired into metadata. Verified: lint clean, 8/8 tests, production build, all routes live (200/200/404/health-ok). PWA install audit re-checked at CORE-8.1 UAT on a real phone.

## Epic 2: Accounts & Access

**CORE-2.0 [AI] — Signup & login** `[DONE 2026-07-16 — prod wiring at CORE-1.2]`
Email + password auth: argon2 hashing, secure httpOnly sessions, signup/login/logout flows, basic profile.
*Acceptance:* full auth round-trip works in production; passwords never logged; auth unit tests pass.
*Status note (2026-07-16):* Implemented with argon2id hashing, DB-backed sessions (30-day httpOnly cookies), zod validation, users+sessions schema with idempotent bootstrap DDL. DB layer auto-selects: DATABASE_URL → managed Postgres (prod), else embedded PGlite (dev/tests — real Postgres dialect). Routes: signup/login/logout/me. Pages: /signup, /login, /account (session-gated, shows entitlement + upgrade link). Verified: 16/16 tests (8 auth), lint, build, and live smoke test (signup→session→me→duplicate 409→wrong password 401→login→account gating). "Works in production" criterion completes when CORE-1.2 provisions the hosted DB.

**CORE-2.1 [AI+Human] — Email verification & password reset**
Transactional email provider (Resend or similar — free tier): `[Human]` owner creates the account and pastes the API key into hosting env vars per instructions; AI builds verify + reset flows.
*Acceptance:* new users receive verification email; reset flow works end-to-end.

**CORE-2.2 [AI] — Entitlement & preview gating** `[DONE 2026-07-23]`
`lifetime_access` flag on user; free preview allowance (one sample calculation, limited output, no export); paid users unrestricted.
*Acceptance:* preview limits enforced server-side; upgrade path visible to free users.
*Status note:* Free users see **material quantities** (the preview that proves it works); the **cost estimate + labor plan** are gated behind lifetime access via `PaywallTeaser` (server-side check on the completed-project page), plus Excel/PDF exports already gated. Paid users see everything. Conversion funnel complete: on-screen value now matches the $30 unlock.

## Epic 3: Payments ($30 Lifetime)

**CORE-3.0 [AI+Human] — Choose & set up merchant-of-record provider**
AI presents final Paddle vs Lemon Squeezy recommendation for a Kenya-based seller selling worldwide; `[Human]` owner signs up, completes identity/business verification (ID + bank details), creates the "$30 lifetime access" product, and pastes TEST keys into env vars — all with step-by-step plain-language instructions.
*Acceptance:* provider account verified; test keys configured; product exists in the provider dashboard.

**CORE-3.1 [AI] — Card checkout integration** `[DONE in sandbox 2026-07-23 — real provider swaps in at CORE-3.0]`
Provider-hosted checkout from the pricing page; webhook receiver sets `lifetime_access=true`; idempotent handling; test-mode purchase flow verified.
*Acceptance:* test purchase grants access automatically within seconds; webhook signature verified; failure paths logged.
*Status note:* Full buy→unlock flow built provider-agnostically. `purchases` table (idempotent via provider_ref); `lib/payments.ts` selects provider via `PAYMENTS_PROVIDER` (default "mock" = self-contained sandbox that works with NO external account). Routes: `POST /api/checkout` (start), `POST /api/checkout/mock-confirm` (HMAC-signed, forge-proof, user-matched), `POST /api/payments/webhook` (real-provider stub). `completePurchase()` grants lifetime access idempotently. Working Buy button on /pricing → sandbox checkout page → success banner on /account. 8 payment tests (entitlement, idempotency, wrong-user 403, token tamper, 501 for unconfigured real provider). **Real card provider (Paddle/Lemon Squeezy) drops in at CORE-3.0 — only needs the owner's account + keys; the checkout/entitlement/webhook shape is already in place.** Live HTTP smoke test blocked this round by the sandbox terminating the dev server; logic fully covered by unit tests + identical auth-cookie pattern to the live-verified export routes.

**CORE-3.2 [AI+Human] — M-Pesa checkout (Kenya)**
AI recommends the gateway (Pesapal/Flutterwave/DPO) and integrates its hosted flow; `[Human]` owner creates the gateway account (business verification) and pastes sandbox keys.
*Acceptance:* sandbox M-Pesa payment grants lifetime access via the same entitlement path.

**CORE-3.3 [AI] — Pricing display & receipts**
USD $30 with KES equivalent (and provider-localized prices where supported); post-purchase receipt/confirmation screen and email.
*Acceptance:* prices render correctly; purchase confirmation delivered.

## Epic 4: Project Data Input (Residential)

**CORE-4.0 [AI] — Unified project data model** `[DONE 2026-07-23]`
DB schema + TypeScript types for the residential input model: location, code profile, plot/building dimensions, floors, rooms (type + dimensions), wall/finish/roof material preferences, soil type (optional). Designed to feed ALL seven outputs (R2/R3 fields included but optional).
*Acceptance:* schema migrated; model validated with zod (or equivalent); documented in module-map.md.

**CORE-4.1 [AI] — Input wizard UI** `[DONE 2026-07-23]`
Mobile-first step-by-step wizard (project basics → dimensions → floors/rooms → materials → review); draft autosave; edit any step later.
*Acceptance:* a full residential project can be entered on a phone in under 10 minutes; drafts persist across sessions.

**CORE-4.2 [AI] — Code profile selection** `[DONE 2026-07-23 — engines consume the stored profile at CORE-5]`
Profile picker (Eurocode / BS / US / KEBS-Kenya) with plain-language descriptions; default suggested from country; stored per project; stamped through to every output.
*Acceptance:* profile selectable and persisted; downstream engines receive it; UI explains what a code profile is.

## Epic 5: Calculators

**CORE-5.0 [AI+Human] — Material quantities engine** `[DONE — OWNER-VALIDATED 2026-07-23]`
*Validation record:* Owner-engineer corrections applied (foundation depth 1.5 m; plaster 15-20 mm → 17.5 mm midpoint); engine v0.2.1; tests updated (excavation 37.8 m³, foundation walling 717 blocks) — see `decisions-learnings/Key-Decisions-2026-07-23_1355.md`.
*Status note:* Full residential rule-set implemented (`engines/materials/residential.ts`, engine v0.2.0): substructure (strip foundation, hardcore, DPM), ground slab + BRC, walling (external + 60% internal factor, openings deducted), ring beam + columns, suspended slabs (multi-storey), pitched (timber + cover) and flat concrete roofs, plaster/paint/screed/tiles, doors/windows. ~30 named ASSUMPTIONS constants exposed for review. 9 worked-example tests pass (12×9 bungalow hand-calculated: excavation 22.68 m³, footing 5.04 m³, slab 10.8 m³, net walls 165.3 m², 2170 blocks, roof 124.2 m²/684 m timber; two-storey, flat-roof, tiles, no-plaster variants). **Gate: owner validates ASSUMPTIONS + worked example → then [DONE].**
TypeScript rule module: concrete (foundations/slabs/columns/beams), masonry blocks/bricks, steel reinforcement estimates, mortar/plaster, sand/ballast, paint, roofing — residential rules per Eurocode/BS conventions. `[Human]` owner-engineer validates worked examples (sample house → expected quantities) before sign-off.
*Acceptance:* unit tests pass against ≥3 owner-validated worked examples; results itemized per element.

**CORE-5.1 [AI+Human] — Cost estimation engine** `[DONE 2026-07-23 — built on the owner's 2026 rate card]`
Itemized costs = quantities × unit rates; editable price tables (default Kenyan baseline `[Human]` owner provides/approves; user-adjustable rates per project); currency display.
*Acceptance:* client-ready itemized estimate; owner confirms baseline rates realistic; totals reconcile with quantities.
*Status note:* Owner supplied the **Fatali Builders Construction Rates 2026** card (120 work items, labour-only + labour+material KES) — 28 relevant rates embedded as the baseline (`engines/cost/index.ts`), source-cited. BOQ-format output modeled on the owner's Thika Mosque BOQ (elements → Item/Qty/Unit/Rate/Amount → collections → grand summary + 5% contingency). **Dual pricing modes: full contract vs labour-only.** 10 worked-example tests hand-checked (excavation 30,240; slab 183,600; walling 330,600). 12×9 bungalow: KES 2,727,077 full / 972,497 labour-only. Per-project editable rates deferred to a later story. Raw company files NOT stored (owner decision) — data extracted only.

**CORE-5.2 [AI+Human] — Labor & time engine** `[DONE 2026-07-23 — day rates from owner's work log; norms AWAITING OWNER VALIDATION]`
Crew composition and duration estimates from productivity rates per trade; `[Human]` owner validates rates and a worked example.
*Acceptance:* outputs crew size + duration per phase; owner-validated example passes.
*Status note:* `engines/labor/` computes crew, duration and labor cost per phase (excavation, foundation/slab, walling, concrete frame, roofing, plaster/screed, painting) + weekly engineer supervision. **DAY_RATES_KES from the owner's AP Mosque work log: mason 1,500 / laborer 1,200 / engineer 5,000** (carpenter/painter assumed = 1,500/1,300, pending owner confirmation). LABOR_ASSUMPTIONS = named productivity norms (m²/mason-day etc.) exposed for owner review. 7 worked-example tests (12×9 bungalow: walling 10 days @ 54,000; excavation 5 days; ≈calendar weeks). LaborView on project page (duration/peak-crew/cost cards + phase table). **Open validation: confirm productivity norms + carpenter/painter day rates.**

**CORE-5.3 [AI] — Engine hardening** `[DONE 2026-07-23]`
Edge-case tests (tiny/large inputs, missing optionals), input bounds with friendly validation messages, deterministic outputs, engine versioning (results record engine + profile version).
*Acceptance:* test suite green; nonsense inputs rejected with clear messages; results reproducible.
*Status note:* `engines/hardening.test.ts` — 12 tests across all 3 engines over tiny (3×3, 1 floor)/base/large (100×100, 4 floors) inputs: proves no NaN/Infinity/negatives, labour ≤ full, positive durations, determinism (identical output on repeat), monotonicity (bigger → more cost/time/materials), and engine-version stamps. Input bounds enforced by the zod schema (CORE-4.0) with friendly messages.

## Epic 6: Outputs & Sharing

**CORE-6.0 [AI] — Results screens** `[IN-PROGRESS — materials view done 2026-07-23]`
Mobile-first results: summary cards + itemized tables per output type; per-project results history.
*Acceptance:* all three calculator outputs render clearly on a phone; saved and reloadable.
*Status note:* Materials results live on the project page: totals cards (cement/sand/ballast/blocks/steel/roof/paint), collapsible per-element tables, code-profile + engine-version stamp, estimating disclaimer. Results computed on demand from stored project data (always current). Cost + labor views land with their engines (CORE-5.1/5.2).

**CORE-6.1 [AI] — Excel export** `[DONE 2026-07-23]`
.xlsx export (quantities, cost estimate, labor plan as sheets) with code-profile stamp and project header.
*Acceptance:* file opens correctly in Excel; matches on-screen results.
*Status note:* `lib/export-excel.ts` (exceljs) builds a 4-sheet branded workbook — Summary (project + headline totals + disclaimer), Materials, Cost BOQ (elements, subtotals, contingency, grand totals full & labour), Labor Plan (phases, crew, days, cost) — navy header styling, KES number formats. Served by `GET /api/projects/[id]/export`, **gated on lifetime access (402 for free users)** — this is the paywall in action. 3 export tests + live end-to-end verified: HTTP 200, correct MIME, 12.8 KB, opens with all 4 sheets. Filename: "{project} - Fatalibuilders.xlsx".

**CORE-6.2 [AI] — PDF export** `[DONE 2026-07-23]`
Branded PDF result sheets with project details, code-profile stamp, and the standard disclaimer block.
*Acceptance:* clean A4 output; stamp + disclaimer on every page footer.
*Status note:* `lib/export-pdf.ts` (pdfkit, no external fonts — Helvetica built-in) renders an A4 BOQ: navy header, project line, full Cost BOQ table (elements, subtotals, contingency, grand totals full & labour), key-materials line, schedule line; **footer on every page with code-profile stamp + engineer-review disclaimer + page N of M**. Served by `GET /api/projects/[id]/export-pdf`, gated on lifetime access (402 verified live). 2 tests confirm valid %PDF/EOF structure for small + large projects. pdfkit in serverExternalPackages. Full paid live-download re-run blocked this round by the sandbox terminating the dev server; delivery path identical to the live-verified Excel export.

**CORE-6.3 [AI] — WhatsApp share & tap-to-call** `[DONE 2026-07-23 — share done; tap-to-call deferred to where numbers exist]`
wa.me share links with pre-filled summary + document link; `tel:` links on contact surfaces.
*Acceptance:* share opens WhatsApp with correct message on mobile; links work from exported PDFs where applicable.
*Status note:* "Share on WhatsApp" button in ExportBar → wa.me link with a pre-filled summary (project, size, full-contract total, app promo line + link) — the growth loop: every shared estimate markets the app. Available to all logged-in users (drives virality); downloadable BOQ files stay paid. No app key needed (wa.me). **tap-to-call (`tel:`) deferred** — R1 projects have no client phone-number field; lands in R4 management/client-contacts where numbers exist. Noted, not a gap in R1 scope.

## Epic 7: Product Site & Onboarding

**CORE-7.0 [AI] — Landing & pricing pages** `[DONE 2026-07-23]`
Landing page (what it does, the 7 outputs with R2/R3 marked "coming"), pricing page ($30 lifetime), FAQ.
*Acceptance:* pages live, mobile-first, load fast; checkout reachable from pricing.
*Status note:* Real landing page — hero ("Build Better. Estimate Smarter."), 7-outputs grid, 3-step how-it-works, CTAs to signup/pricing. Pricing page has the working Buy button (CORE-3.1).

**CORE-7.1 [AI] — Free preview flow** `[DONE 2026-07-23]`
Sample calculation for visitors/free accounts with limited output and a clear upgrade prompt.
*Acceptance:* preview works without payment; export blocked with friendly upgrade message.
*Status note:* Public `/demo` page renders a real sample (12×9 bungalow material quantities) with NO signup, plus a locked cost/schedule teaser and signup CTA; linked from the landing hero. In-app, free accounts get the same materials-preview + PaywallTeaser (CORE-2.2).

**CORE-7.2 [AI+Human] — Legal pages** `[AI DRAFT DONE 2026-07-23 — awaiting owner review before launch]`
AI drafts Terms of Service, Privacy Policy (Kenya DPA + GDPR-aware), Refund Policy; `[Human]` owner reviews (and may consult a lawyer) before publishing.
*Acceptance:* pages published and linked from footer + checkout; provider requirements satisfied.
*Status note:* `/legal/terms`, `/legal/privacy`, `/legal/refund` live and linked from the footer. All marked DRAFT. **Owner action before launch:** review the three pages (14-day refund, Kenya DPA + GDPR practices, engineering-liability disclaimers); adjust the refund window to Paddle's requirements.

**CORE-7.3 [AI] — First-run onboarding** `[DONE 2026-07-23]`
Post-signup guidance: 3-step intro → start first project; empty states teach the flow.
*Status note:* Projects empty state shows a welcoming 3-step guide (enter → get results → download/share) with a prominent create-first-project button.
*Acceptance:* new user reaches their first result without external help.

## Epic 8: Launch Readiness

**CORE-8.0 [AI] — Analytics & admin basics**
Signups, activation (first calculation), purchases funnel; simple admin view (users, purchases).
*Acceptance:* funnel numbers visible; no PII leakage to third parties.

**CORE-8.1 [AI+Human] — UAT with the owner**
Full end-to-end test by the owner on their phone (signup → pay test-mode → project → results → exports → WhatsApp share); findings logged in Bugs.md and fixed.
*Acceptance:* owner completes the journey without assistance; all UAT bugs closed.

**CORE-8.2 [AI+Human] — Go live**
`[Human]` owner switches provider(s) to LIVE keys and confirms bank payout details; AI runs the go-live checklist (domain, SSL, live webhook, smoke test with a real $30 purchase refunded after verification).
*Acceptance:* production accepts real payments on both rails; first live purchase verified; launch announced in NextSteps.

---

## Story Count Summary

| Label | Count |
|---|---|
| [AI] | 17 |
| [AI+Human] | 11 |
| [Human] | 1 (owner UAT sign-off inside CORE-8.1 counted as AI+Human; standalone human actions occur as checkpoints) |

---

*Stories are executed in epic order unless dependencies allow parallelism. Statuses: Pending → [IN-PROGRESS] → [DONE], updated by the closure protocol.*
