# Masjid Fund

A donation website for building masajid. Donors browse verified construction
projects, see exactly what each unit of money buys, give once or monthly, and
follow the build through to handover.

Built with Next.js 15 (App Router), React 19, Tailwind CSS 4 and PostgreSQL.

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
| `/checkout/[reference]` | Simulated hosted checkout (test mode only) |
| `/about`, `/faq` | Governance, and the zakat/sadaqah questions donors ask |

### API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/projects` | Projects with goal, raised total and donor count |
| `GET /api/stats` | Fund-wide totals |
| `POST /api/donations` | Validate a gift, record it as pending, return a checkout URL |
| `GET /api/donations/[reference]` | Public receipt lookup (no personal data) |
| `POST /api/payments/webhook` | Provider settlement callback (signature-verified) |
| `POST /api/payments/mock-complete` | Simulated settlement; refuses to run in live mode |
| `GET /api/health` | Liveness with a database round-trip |

## Domain rules worth knowing

- **Money is integer cents everywhere.** Decimals appear only at the display edge
  (`src/lib/money.ts`).
- **Nothing counts until it settles.** A donation is written as `pending` and only
  joins project totals once the provider confirms it. Settlement is idempotent, so
  a retried webhook cannot double-count a gift.
- **Zakat never funds construction.** Selecting Zakat detaches the gift from any
  building project and records it in a separate pool for eligible recipients —
  masjid construction is not one of the eight categories in Surah at-Tawbah (9:60).
- **Totals are computed, never cached.** "Raised" is always
  `SUM(completed donations) + offline_raised_cents`, in SQL.

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
3. **Real projects** — set `SKIP_SEED=1` and load your own rows into `projects`,
   `project_costs` and `project_updates` (see `src/db/schema.ts`).
4. **Receipt email** — donations are recorded and the reference is shown on the
   thank-you page, but no mail is sent yet. Wire a transactional email provider to
   the settlement path in `src/lib/donations.ts`.

Another payment provider (M-Pesa, PayPal, bank transfer reconciliation) means one
new file implementing `PaymentProvider` in `src/lib/payments/` — nothing else in
the donation flow talks to a payment API.

## Not yet built

- Receipt and monthly-reminder emails.
- Donor accounts and self-service cancellation of monthly giving (the FAQ promises
  a cancel link, which needs the email path above).
- An admin surface for adding projects and posting build updates.
- Multi-currency: amounts are stored per-donation with a currency, but the UI is
  USD only.
- Project photography — artwork is drawn in SVG (`src/components/MasjidScene.tsx`).
