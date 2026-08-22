# AI Session Summary — 2026-08-21 14:51 UTC

**Executor:** Claude Code (remote/cloud session)
**Branch:** `claude/mosque-donation-website-c0qbk8`
**Scope:** Built **Masjid Fund** — a donation website where donors fund the construction of masajid, and communities apply to have theirs built. New application at `app-src/masjid-fund/`.
**Status at close of this entry:** five commits pushed; site runs end to end in test mode; payment rails beyond Stripe still outstanding.

---

## How the session ran

The owner drove this in short instructions, each one opening the next piece of work. In order:

| # | Owner asked | What was delivered |
|---|-------------|--------------------|
| 1 | "create a website where donors donate to build mosques" | The whole donation site: projects, donate flow, payments boundary, 37 tests |
| 2 | "what's next I want to launch it" | Launch plan split into what only the owner can do vs. what is code; four decisions taken (see below); receipts + admin built |
| 3 | "let me test the website first before I finish the payment methods" | Three ways to run it, a test-mode banner, a database guard, `TESTING.md` |
| 4 | "give an option where people can enter the site upload the information about the mosque… for approval" | Full application pipeline with document upload and staff review |
| 5 | "proceed" | Abuse throttling, security headers, privacy/terms/refunds |
| 6 | "link to the site" → "yes" | Explained no deployment exists; published a screen-by-screen walkthrough artifact |

---

## Decisions taken by the owner

Asked once, when the answers would have changed what was built:

| Question | Answer |
|----------|--------|
| Payment rails at launch | Stripe cards, **M-Pesa**, PayPal, and bank transfer / offline |
| Where donations land legally | **Kenyan NGO or waqf trust** |
| Hosting | **Vercel + managed PostgreSQL** |
| Build order | **Receipts + admin first** |

These shaped everything after: receipts carry Kenyan wording and claim no US/UK deductibility, policy pages are written to Kenyan law, and the payment layer was built as a swappable boundary rather than Stripe-specific code.

---

## What exists now

### Public

| Route | Purpose |
|-------|---------|
| `/` | Mission, live totals, featured masajid, what a gift buys, transparency |
| `/projects`, `/projects/[slug]` | Projects with story, costed items, build updates, donate panel |
| `/donate`, `/donate/thank-you` | Donation form and receipt |
| `/giving/[token]` | Donor cancels a monthly gift — no account |
| `/apply`, `/apply/submitted`, `/apply/status/[token]` | Community applies and tracks the review |
| `/checkout/[reference]` | Simulated checkout, test mode only |
| `/about`, `/faq`, `/privacy`, `/terms`, `/refunds` | Governance and policies |

### Staff (`/admin`, shared operator login)

Dashboard with self-diagnosing warnings · application queue and review with document downloads · project create/edit with costed items and build updates · donation ledger with CSV export · offline gift recording.

### API

`GET /api/projects`, `/api/stats`, `/api/health` · `POST /api/donations` · `GET /api/donations/[reference]` · `POST /api/payments/webhook` · `POST /api/payments/mock-complete` · `POST /api/applications` · `GET /admin/donations/export` · `GET /admin/applications/documents/[id]`

---

## Architecture decisions and why

| Decision | Rationale |
|----------|-----------|
| **Money as integer minor units everywhere** | Floats lose cents; decimals appear only at the display edge (`src/lib/money.ts`) |
| **Nothing counts until it settles** | Donations are written `pending`; only a provider confirmation moves them into totals. Settlement is idempotent, so a retried webhook cannot double-count |
| **Totals computed in SQL, never cached** | "Raised" = `SUM(completed donations) + offline_raised_cents`. No counter can drift from the ledger |
| **`PaymentProvider` boundary** | The donation flow never calls a payment API. Stripe implemented over REST (no SDK); a built-in simulator runs when no key is set; M-Pesa and PayPal are one file each |
| **`EmailProvider` boundary, receipts fired from `settleDonation()`** | The single point every provider path converges on, so no rail can settle without a receipt. Failures are logged, never thrown — a paid donation must not roll back because a mail service blinked |
| **Zakat never funds construction** | Detached from any project and pooled separately; masjid construction is not among the eight categories in at-Tawbah 9:60. Flagged to the owner as a decision to confirm with a scholar |
| **Approving = publishing** | An application cannot be approved without a project existing, so the site can never show an approved masjid with no page, or a page nobody approved |
| **Applications private until published** | The project is built from staff-checked values, not straight from the applicant's form |
| **Uploads trusted only as far as their bytes** | Format read from magic bytes, not the browser's content type; filenames stripped; staff-only downloads served as attachments with `nosniff` + sandbox CSP |
| **Throttling by counting rows** | Survives restarts and works across serverless instances, unlike an in-memory counter. IPs stored only as salted hashes |
| **Embedded PGlite when `DATABASE_URL` is unset** | The whole app runs with zero configuration; same Postgres dialect in dev and production |
| **Domain split from data access** (`donation.ts`/`donations.ts`, `application.ts`/`applications.ts`) | Client components import the domain; the database must never reach the browser bundle |

---

## Bugs found and fixed during the build

1. **Soft 404s.** Every missing page returned HTTP 200 with the not-found body. The root `loading.tsx` flushed the response shell before `notFound()` could set the status. Removed; the reason is documented in `not-found.tsx` so nobody re-adds it.
2. **Policy pages froze their organisation details.** They prerendered at build time, so a deployment configuring `ORG_*` at runtime would have published a privacy policy claiming no registration exists. Now `force-dynamic`.
3. **Client bundle pulled in the database.** The public application form imported from the data-access module, dragging `pg` into the browser build. Fixed by the domain/data split above.
4. **Project edits would have reset hidden fields.** The edit form did not carry `offline_raised_cents` or `position`, so saving would have zeroed them. Both are now part of the read model and the form.

---

## Verification

Every milestone was driven in a real browser (Playwright + Chromium), not only unit-tested.

- **88 tests**, lint clean, production build clean.
- Donation lifecycle: pending → settled → totals move; repeat settlement changes nothing; failed payments excluded.
- Monthly giving: token issued, subscription reference captured, cancel works and stays cancelled, past gifts stay with the project.
- Applications: a PHP script renamed `.pdf` rejected; missing BoQ refused; complete submission accepted; invisible on `/projects` until published; staff download 200 with `attachment` + `nosniff`, anonymous download 401; empty decision note refused; publishing made it public with the right budget.
- Abuse limits: 12 attempts from one network accepted, 13th refused 429, other networks unaffected.
- Headers verified on a live response; both light and dark themes checked; no horizontal overflow at 390 px.

---

## Commits on this branch

| Commit | Subject |
|--------|---------|
| `015d315` | Add Masjid Fund: a donation site for building mosques |
| `824ca07` | Add donation receipts, donor self-service and admin screens |
| `2180bc3` | Make the site safe and easy to test before payments are live |
| `08bfae0` | Add an application pipeline for communities seeking funding |
| `45e05a5` | Throttle donation attempts, add security headers and policy pages |

---

## Configuration

Everything runs unconfigured; each variable switches a simulator off for a real service.

`DATABASE_URL` · `ALLOW_EPHEMERAL_DB` · `APP_URL` · `SKIP_SEED` · `STRIPE_SECRET_KEY` · `STRIPE_WEBHOOK_SECRET` · `RESEND_API_KEY` · `EMAIL_FROM` · `EMAIL_REPLY_TO` · `ORG_NAME` · `ORG_REGISTRATION` · `ORG_REGISTRAR` · `ORG_ADDRESS` · `ORG_EMAIL` · `IP_HASH_SALT` · `ADMIN_EMAIL` · `ADMIN_PASSWORD_HASH`

Guard worth knowing: in production with no `DATABASE_URL` the app refuses to boot rather than running on a disposable database. `ALLOW_EPHEMERAL_DB=1` is the explicit opt-in for a throwaway preview.

---

## Outstanding — owner actions

1. **Entity and bank account** — donations must land in a registered trust account. Everything else waits on this.
2. **Fundraising registration** — NGOs Co-ordination Board plus county permits; separate registration if soliciting US or UK donors.
3. **Stripe business verification** (days of lead time) and **Daraja/M-Pesa credentials** (paybill in the trust's name).
4. **Legal review** of the privacy, terms and refund drafts by a Kenyan advocate.
5. **Real project data** — the five listed masajid are invented samples and must be replaced through `/admin`.
6. **Test the site** — Codespaces or local; `TESTING.md` has the walkthrough.

## Outstanding — engineering

- **M-Pesa and PayPal adapters**; M-Pesa brings KES and multi-currency with it.
- **Object storage** for application documents (currently database bytes, 4 MB cap).
- **Malware scanning** on uploads — format and size are checked, contents are not.
- **Stripe Radar rules** once the account is live.
- **Real migrations** in place of idempotent bootstrap DDL.
- **Monthly reminder emails** and richer donor communications.

---

## Artefacts

- Code: `app-src/masjid-fund/` — see its `README.md` (architecture, go-live steps) and `TESTING.md` (how to run and what to try).
- Screen-by-screen walkthrough published for owner review as a private artifact.

---

*Session record for the Masjid Fund build. The app is a new product line, distinct from FatalibuildersConstructionApp; it has no project workspace under `projects/` yet.*
