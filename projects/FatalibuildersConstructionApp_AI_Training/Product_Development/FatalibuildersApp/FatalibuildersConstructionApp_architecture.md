# FatalibuildersConstructionApp — Architecture & Design Philosophy

**Document Purpose:** This is the architectural design document for FatalibuildersConstructionApp. It defines the system architecture, security model, infrastructure design, data flow patterns, and development constraints. All AI assistants must read and adhere to this document before generating code or infrastructure changes.

**Source:** Consolidated from the staging Document 2 (approved by owner 2026-07-16).
**Last Updated:** 2026-07-16

---

## 1. Core Philosophy & Constraints

1. **One input, seven outputs.** The user enters their residential project data ONCE; every output (material quantities, cost estimate, labor/time estimate, 2D drawings, renders, structural drawings, geotechnical report) derives from that single dataset. No output may require re-entering data another output already collected.
2. **Integration-first.** API-first core with webhooks; Excel and WhatsApp are first-class citizens; future connectors plug in without re-architecture.
3. **Code-profile integrity.** Every calculation and generated document is traceable to a selected code profile (Eurocode / BS / US / KEBS). No output ships without its profile stamp.
4. **Engineering responsibility.** Structural drawings and geotechnical reports are PRELIMINARY. Every such document carries a watermark and disclaimer: *"Preliminary — for guidance only. Requires review by a licensed engineer before construction use."* Legal review gates their release (R3).
5. **Worldwide from Kenya.** Global product; USD-primary multi-currency (KES prominent); English-first translation-ready UI; payments must work both for global cards and M-Pesa.
6. **Lifetime-access economics.** Revenue per customer is capped at $30 — per-user infrastructure cost must remain near zero (serverless/static-first, aggressive caching, minimal storage per user).
7. **First-time-owner clarity.** The owner is not a developer. All human checkpoints must be written as plain-language instructions with no assumed developer knowledge.

## 2. Technology Stack & Tooling

| Layer | Choice | Notes |
|---|---|---|
| Platform | Mobile-first **PWA** (installable web app) | One codebase, worldwide reach, no app-store gatekeeping; native apps deferred |
| Frontend | **Next.js (React) + TypeScript**, Tailwind CSS | Responsive; calculators cached offline via PWA service worker |
| Backend | Next.js API routes (Node.js + TypeScript) | REST + webhooks; integration-first |
| Database | **PostgreSQL** (managed) | Users, projects, entitlements, results metadata |
| File storage | S3-compatible object storage | Generated PDFs/XLSX/drawings, user uploads |
| Calc engines | Pure TypeScript rule modules per code profile | Unit-tested against owner-validated worked examples |
| 2D drawings (R2) | SVG generation → PDF/DXF export | Derived from input geometry |
| Renders (R2) | three.js from the same geometry | Server- or client-rendered visualizations |
| Documents | PDF generator (report sheets), `xlsx` library (Excel) | All documents carry code-profile stamp + disclaimers |
| Payments | Merchant-of-record card checkout (Paddle or Lemon Squeezy) + M-Pesa gateway (Pesapal/Flutterwave/DPO) | Dual stack; final vendor pick at CORE-3.0 |
| Hosting | Vercel / Railway / Fly.io (final pick at CORE-1.1) | Low fixed cost; CI/CD from GitHub |
| Analytics | Privacy-light product analytics (signups, activation, purchases) | Choice at CORE-8.0 |

## 3. System Architecture

```text
[Browser / installed PWA]
   │  (HTTPS)
   ▼
[Next.js app] ── static marketing pages (landing, pricing)
   │            ── app UI (input wizard, results, account)
   ▼
[API routes]
   ├── auth (signup/login/reset, session cookies)
   ├── projects (CRUD on project input data)
   ├── results (invoke calc engines, persist outputs)
   ├── exports (PDF / XLSX generation → object storage → signed URL)
   ├── payments (checkout session create, provider webhooks → entitlement)
   └── webhooks/api (integration surface for future connectors)
   ▼
[PostgreSQL]  users · entitlements · projects · results · price-tables
[Object storage]  generated documents
[Calc engines]  materials · cost · labor  (per code profile; R2: geometry→SVG/render; R3: structural/geotech)
```

**Data flow:** input wizard → validated project record → user picks outputs → engines compute from the record + code profile + price tables → results stored + rendered → export/share (XLSX, PDF, wa.me link).

**Entitlement flow:** signup (free) → preview allowance (sample calculation, limited output) → $30 checkout (card or M-Pesa) → provider webhook → `lifetime_access=true` → full outputs + saved projects + exports.

## 4. Security Model

- HTTPS everywhere; HSTS. Passwords hashed with argon2 (bcrypt fallback). Secure, httpOnly session cookies.
- Secrets ONLY in environment variables / hosting secret manager — never in git, never echoed by AI. Placeholder convention: `__HUMAN_PROVIDED__`.
- Roles: `user`, `admin` (Fatalibuilders staff). R4 adds per-project roles (owner/supervisor/crew).
- Payment data never touches our servers — provider-hosted checkout; we store only entitlement status + provider transaction reference.
- Data protection: Kenya Data Protection Act 2019 + GDPR-compatible practices. Minimal PII (email, name optional). Export/delete-my-data supported (R1 minimal: manual on request; automated later).
- Generated engineering documents: watermark + code-profile stamp + engineer-review disclaimer rendered into the document itself (not just the UI).

## 5. Infrastructure Design

- Single production environment + preview deployments per branch (hosting platform default).
- Managed PostgreSQL (small tier), S3-compatible bucket, CDN-cached static assets.
- CI/CD: GitHub → hosting platform auto-deploy; migrations run on deploy.
- Cost guardrail: fixed monthly cost target < $50 at launch; per-user marginal cost ≈ storage of their documents only.
- Backups: daily DB snapshots (hosting-managed); object storage versioning off (documents regenerable from stored inputs).

## 6. Data Flow & Integration Patterns

- **Excel:** export any result set to .xlsx; import of existing estimate spreadsheets (mapping wizard) in a later minor release.
- **WhatsApp:** R1 = wa.me share links with pre-filled message + document link; Business API (automated sends) later, behind its own connector module.
- **Calls:** `tel:` links (tap-to-call) wherever a phone number appears.
- **Future connectors:** each integration is a self-contained module registering webhooks/API endpoints — no core rewrites.

## 7. Development Standards & Conventions

- TypeScript strict mode; ESLint + Prettier; conventional commits.
- Every calc rule module ships with unit tests against **owner-validated worked examples** (the owner is a licensed engineer — validation checkpoints are `[AI+Human]` stories).
- Silent error catching banned; errors logged with context.
- Code blocks in memory files include exact file paths; no truncated snippets.
- Trunk-based development: small PRs to `main` via feature branches; preview deploy per PR.
- The app source code lives in its OWN repository (created at CORE-1.0), separate from this memory repo.

---

*This document is the architectural constitution for FatalibuildersConstructionApp. Update it when architecture changes are made.*
