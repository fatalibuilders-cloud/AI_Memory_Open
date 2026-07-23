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
| 1 | Foundation & Infrastructure | 4 | In Progress (CORE-1.0 built & verified) |
| 2 | Accounts & Access | 3 | In Progress (CORE-2.0 done) |
| 3 | Payments ($30 Lifetime) | 4 | Pending |
| 4 | Project Data Input (Residential) | 3 | ✅ **Complete (2026-07-23)** |
| 5 | Calculators | 4 | In Progress (5.0 ✅ validated; 5.1 ✅ done; 5.2 next) |
| 6 | Outputs & Sharing | 4 | In Progress (6.0 materials view done) |
| 7 | Product Site & Onboarding | 4 | Pending |
| 8 | Launch Readiness | 3 | Pending |

**Total: 29 stories** — 17 [AI], 11 [AI+Human], 1 [Human]

---

## Epic 1: Foundation & Infrastructure

**CORE-1.0 [AI] — Scaffold the app repository** `[IN-PROGRESS — built & verified 2026-07-16; awaiting repo migration]`
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

**CORE-2.2 [AI] — Entitlement & preview gating**
`lifetime_access` flag on user; free preview allowance (one sample calculation, limited output, no export); paid users unrestricted.
*Acceptance:* preview limits enforced server-side; upgrade path visible to free users.

## Epic 3: Payments ($30 Lifetime)

**CORE-3.0 [AI+Human] — Choose & set up merchant-of-record provider**
AI presents final Paddle vs Lemon Squeezy recommendation for a Kenya-based seller selling worldwide; `[Human]` owner signs up, completes identity/business verification (ID + bank details), creates the "$30 lifetime access" product, and pastes TEST keys into env vars — all with step-by-step plain-language instructions.
*Acceptance:* provider account verified; test keys configured; product exists in the provider dashboard.

**CORE-3.1 [AI] — Card checkout integration**
Provider-hosted checkout from the pricing page; webhook receiver sets `lifetime_access=true`; idempotent handling; test-mode purchase flow verified.
*Acceptance:* test purchase grants access automatically within seconds; webhook signature verified; failure paths logged.

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

**CORE-5.2 [AI+Human] — Labor & time engine**
Crew composition and duration estimates from productivity rates per trade; `[Human]` owner validates rates and a worked example.
*Acceptance:* outputs crew size + duration per phase; owner-validated example passes.

**CORE-5.3 [AI] — Engine hardening**
Edge-case tests (tiny/large inputs, missing optionals), input bounds with friendly validation messages, deterministic outputs, engine versioning (results record engine + profile version).
*Acceptance:* test suite green; nonsense inputs rejected with clear messages; results reproducible.

## Epic 6: Outputs & Sharing

**CORE-6.0 [AI] — Results screens** `[IN-PROGRESS — materials view done 2026-07-23]`
Mobile-first results: summary cards + itemized tables per output type; per-project results history.
*Acceptance:* all three calculator outputs render clearly on a phone; saved and reloadable.
*Status note:* Materials results live on the project page: totals cards (cement/sand/ballast/blocks/steel/roof/paint), collapsible per-element tables, code-profile + engine-version stamp, estimating disclaimer. Results computed on demand from stored project data (always current). Cost + labor views land with their engines (CORE-5.1/5.2).

**CORE-6.1 [AI] — Excel export**
.xlsx export (quantities, cost estimate, labor plan as sheets) with code-profile stamp and project header.
*Acceptance:* file opens correctly in Excel; matches on-screen results.

**CORE-6.2 [AI] — PDF export**
Branded PDF result sheets with project details, code-profile stamp, and the standard disclaimer block.
*Acceptance:* clean A4 output; stamp + disclaimer on every page footer.

**CORE-6.3 [AI] — WhatsApp share & tap-to-call**
wa.me share links with pre-filled summary + document link; `tel:` links on contact surfaces.
*Acceptance:* share opens WhatsApp with correct message on mobile; links work from exported PDFs where applicable.

## Epic 7: Product Site & Onboarding

**CORE-7.0 [AI] — Landing & pricing pages**
Landing page (what it does, the 7 outputs with R2/R3 marked "coming"), pricing page ($30 lifetime), FAQ.
*Acceptance:* pages live, mobile-first, load fast; checkout reachable from pricing.

**CORE-7.1 [AI] — Free preview flow**
Sample calculation for visitors/free accounts with limited output and a clear upgrade prompt.
*Acceptance:* preview works without payment; export blocked with friendly upgrade message.

**CORE-7.2 [AI+Human] — Legal pages**
AI drafts Terms of Service, Privacy Policy (Kenya DPA + GDPR-aware), Refund Policy; `[Human]` owner reviews (and may consult a lawyer) before publishing.
*Acceptance:* pages published and linked from footer + checkout; provider requirements satisfied.

**CORE-7.3 [AI] — First-run onboarding**
Post-signup guidance: 3-step intro → start first project; empty states teach the flow.
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
