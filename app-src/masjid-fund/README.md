# Masjid Fund

A donation website for building masajid. Donors browse verified construction
projects, see exactly what each unit of money buys, give once or monthly, and
follow the build through to handover.

Built with Next.js 15 (App Router), React 19, Tailwind CSS 4 and PostgreSQL.

How it was built, and why each decision went the way it did:
[`session-summary/AI-Session-Summary-2026-08-21_1451.md`](../../session-summary/AI-Session-Summary-2026-08-21_1451.md).

## Quick start

```bash
npm install
npm run dev        # http://localhost:3000
```

No configuration is needed to run it. With no `DATABASE_URL` the app uses an
embedded PostgreSQL (PGlite, stored in `.pglite/`) and seeds five sample masjid
projects; with no `STRIPE_SECRET_KEY` it uses the built-in payment simulator, so
the entire donation journey — including the failure path — works without keys.

```bash
npm run lint       # eslint
npm test           # vitest
npm run build      # production build
```

## What the site does

| Route | Purpose |
| --- | --- |
| `/` | Mission, live totals, featured projects, cost breakdown, transparency |
| `/projects` | All building projects, split into open and completed |
| `/projects/[slug]` | Project story, costed items, build updates, donate panel |
| `/donate` | Donation form — amount, one-time/monthly, project, intent, dedication |
| `/donate/thank-you` | Receipt with reference and donation status |
| `/giving/[token]` | Donor self-service: view and cancel a monthly gift, no account needed |
| `/apply` | Communities apply for funding — details plus title deed, drawings and BoQ |
| `/apply/status/[token]` | Applicant tracks the review and reads what is still needed |
| `/donate/mpesa/[reference]` | Waiting page while the donor enters their M-Pesa PIN |
| `/donate/transfer/[reference]` | Bank and paybill details, with the reference to quote |
| `/checkout/[reference]` | Simulated hosted checkout (test mode only) |
| `/about`, `/faq` | Governance, and the zakat/sadaqah questions donors ask |
| `/privacy`, `/terms`, `/refunds` | Policies, filled in from the `ORG_*` values at request time |

### Admin

Staff screens at `/admin`, behind a shared operator login. Set `ADMIN_EMAIL` and
`ADMIN_PASSWORD_HASH` (`npm run admin:hash -- 'the password'`); with those unset,
development accepts `admin@localhost` / `masjidfund-dev` and production refuses
sign-in altogether.

| Route | Purpose |
| --- | --- |
| `/admin` | Totals, latest donations, and warnings for anything not configured |
| `/admin/applications` | Review applications, read the documents, decide, publish |
| `/admin/projects` | Add and edit projects, costed items and build updates |
| `/admin/donations` | Filterable ledger; record bank-transfer or cash gifts |
| `/admin/donations/export` | CSV of the ledger for the accounts |

### API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/projects` | Projects with goal, raised total and donor count |
| `GET /api/stats` | Fund-wide totals |
| `POST /api/donations` | Validate a gift, record it as pending, return a checkout URL |
| `GET /api/donations/[reference]` | Public receipt lookup (no personal data) |
| `POST /api/payments/webhook` | Stripe settlement callback (signature-verified) |
| `POST /api/payments/mpesa/callback` | Daraja STK callback (unsigned — matched on CheckoutRequestID) |
| `GET /api/payments/paypal/return` | Captures an approved PayPal order, then shows the receipt |
| `POST /api/payments/paypal/webhook` | PayPal settlement callback (verified by asking PayPal) |
| `POST /api/payments/mock-complete` | Simulated settlement; refuses to run in live mode |
| `GET /api/health` | Liveness with a database round-trip |

## Domain rules worth knowing

- **Money is integer cents everywhere.** Decimals appear only at the display edge
  (`src/lib/money.ts`).
- **Nothing counts until it settles.** A donation is written as `pending` and only
  joins project totals once the provider confirms it. Settlement is idempotent, so
  a retried webhook cannot double-count a gift.
- **One accounting currency.** Project budgets and every published total are USD.
  A donation charged in shillings stores both figures and the rate that linked
  them, fixed at creation, so a receipt and the ledger can never disagree later.
- **Four rails, one flow.** Card (Stripe), M-Pesa (Daraja STK push), PayPal
  (Orders v2) and bank transfer all enter through `createDonation()` and settle
  through `settleDonation()`. Each falls back to the simulator without keys —
  except bank transfer, which is simply not offered until account details exist.
- **Bank transfers settle by hand, on purpose.** The donation is recorded pending
  with a reference for the donor to quote; a member of staff matches it against
  the statement in `/admin/donations`. That manual step is the only honest way to
  confirm money no software watched arrive.
- **PayPal approval is not payment.** The money is captured when the donor
  returns, with the webhook as the safety net if they close the tab; PayPal
  answering "already captured" is treated as success, not an error.
- **M-Pesa callbacks are unsigned, so they are treated as hints.** A settlement
  is accepted only when its CheckoutRequestID matches a donation already waiting
  on it; an unsolicited callback settles nothing. Restrict that path to
  Safaricom's IP ranges at the edge too.
- **Zakat never funds construction.** Selecting Zakat detaches the gift from any
  building project and records it in a separate pool for eligible recipients —
  masjid construction is not one of the eight categories in Surah at-Tawbah (9:60).
- **Totals are computed, never cached.** "Raised" is always
  `SUM(completed donations) + offline_raised_cents`, in SQL.
- **Receipts follow settlement, not checkout.** `settleDonation()` is the single
  point every provider converges on, so it is where the receipt goes out and
  `email_log` is written. A mail failure is logged, never thrown — a paid
  donation must not roll back because a mail service blinked.
- **Monthly gifts are managed by a link, not an account.** The receipt carries a
  256-bit token; `/giving/[token]` cancels at the provider and records the
  instruction locally even if the provider call fails.
- **Receipts never overstate the organisation.** Wording comes from `ORG_*` env
  values, and with no registration number configured the receipt says so rather
  than implying a charity status that does not exist.
- **An application is never public.** It becomes visible only when staff publish
  it as a project, and the project is created from staff-checked values rather
  than straight from the form. Approving is not a separate button — it is what
  publishing does, so the site can never show an "approved" masjid that has no
  page, or a page for something nobody approved.
- **Uploads are trusted as far as their bytes.** Format is decided by the file's
  leading bytes, not the browser's content type; filenames are stripped of paths
  and odd characters; documents are served only to a signed-in staff session, as
  attachments, with `nosniff` and a `sandbox` CSP.
- **Submissions are throttled by counting rows, not by an in-memory counter.**
  That survives restarts and works across serverless instances. Limits live in
  `src/lib/rate-limit.ts`; addresses are stored only as salted hashes, so the
  table never holds a reversible IP.

## Going live

1. **Database** — set `DATABASE_URL` to a managed PostgreSQL instance. Schema
   bootstrap is idempotent and runs on boot.
2. **Payments** — set `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`, and point a
   Stripe webhook at `POST /api/payments/webhook` for
   `checkout.session.completed`, `checkout.session.async_payment_succeeded`,
   `checkout.session.async_payment_failed` and `checkout.session.expired`.
   One-time gifts use Checkout in `payment` mode; monthly gifts use `subscription`
   mode with an inline monthly price. The simulator disables itself automatically
   once a live provider is configured.
3. **PayPal** — set `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` and
   `PAYPAL_WEBHOOK_ID`, point a webhook at `POST /api/payments/paypal/webhook`
   for `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED` and
   `CHECKOUT.ORDER.APPROVED`, and set `PAYPAL_ENV=production` when leaving the
   sandbox.
4. **Bank transfer** — set `BANK_ACCOUNT_NAME`, `BANK_NAME` and
   `BANK_ACCOUNT_NUMBER` (plus branch, SWIFT and paybill where they apply). The
   rail appears to donors only once these exist, and someone needs to check the
   account daily and mark transfers received.
5. **M-Pesa** — set `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`,
   `MPESA_SHORTCODE`, `MPESA_PASSKEY` and `MPESA_SHORTCODE_TYPE`, register
   `POST /api/payments/mpesa/callback` as the Daraja callback URL, and set
   `MPESA_ENV=production` when leaving the sandbox. Check `USD_KES_RATE`. The
   callback is unsigned, so restrict that path to Safaricom's published IP
   ranges at the edge.
6. **Email** — set `RESEND_API_KEY` and `EMAIL_FROM`, and add SPF and DKIM records
   for the sending domain, or receipts land in spam.
7. **Organisation** — set the `ORG_*` values so receipts carry the real
   registration; until then they say plainly that none is configured.
8. **Admin** — set `ADMIN_EMAIL` and `ADMIN_PASSWORD_HASH`.
9. **Real projects** — set `SKIP_SEED=1`, then add projects through `/admin`
   (the sample rows only load into an unseeded database).

Another payment rail means one new file implementing `PaymentProvider` in
`src/lib/payments/` — nothing else in
the donation flow talks to a payment API.

## Not yet built

- **Recurring giving beyond cards** — Daraja has no recurring mandate, and PayPal
  needs billing plans created up front, so monthly giving is card-only. The form
  greys the other rails out for monthly rather than taking one payment and
  calling it monthly.
- **Automatic bank reconciliation** — transfers are matched by hand. A bank feed
  or statement import would remove that step.
- **A live FX rate** — `USD_KES_RATE` is set by hand; see the note in `money.ts`
  for why that is deliberate, and review it when the rate moves.
- **Stripe Radar rules** — the app throttles donation attempts per email and per
  network, but the provider-side fraud rules still need configuring when the
  Stripe account is live.
- **Legal review** — the privacy, terms and refund pages are written to match what
  the code actually does, but they are drafts. A Kenyan advocate should read them
  against your registration before you take public donations.
- **Object storage for documents** — uploads live in the database, capped at 4 MB
  each. That is a real constraint for large drawing sets, and serverless hosts cap
  request bodies around the same size. `src/lib/files/` is where an S3 or R2
  adapter with direct-to-storage uploads would go.
- **Virus scanning** — format and size are checked, contents are not. Worth adding
  a scanner before staff open attachments routinely.
- **Legal pages** — privacy, terms and refund policy.
- **Real migrations** — schema is bootstrapped idempotently on boot, which is fine
  so far but is not a migration history.
- **Project photography** — artwork is drawn in SVG (`src/components/MasjidScene.tsx`).
