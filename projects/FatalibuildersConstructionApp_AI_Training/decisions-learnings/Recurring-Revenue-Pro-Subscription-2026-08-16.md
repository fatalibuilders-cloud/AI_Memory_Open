# Recurring revenue — Pro (Contractor) subscription (2026-08-16)

Owner: "make the app generate income on a monthly basis once officially launched
… attract its users to able and comfortably pay without a doubt." Built a
recurring **Pro** plan alongside the existing one-time **Lifetime**, honestly (no
dark patterns). App @ main; 242 tests green; tsc/lint/build clean.

## The model (honest, low-friction)
- **Free** — enter a project, get quantities, completeness preview, WhatsApp share. The hook; no card.
- **Pro (Contractor)** — monthly or annual, ongoing value that genuinely renews:
  unlimited projects/estimates/BOQs, professional + lender BOQ, live rate reference
  (1,900+ QS rates) + daily prices, drawing analysis + monthly AI reads/renders,
  contracts + marketplace, cost-breakdown/tender tools.
- **Lifetime** — one-time $30, unchanged.
- **14-day free trial** (one per account, anti-abuse), monthly/annual toggle
  (annual ≈ 2 months free), local **KES (M-Pesa)** + USD pricing, **cancel anytime**
  (access to period end), refund/terms linked. "No surprise charges — we remind you
  before renewal."

### Prepaid-period (not silent auto-charge) — deliberate
A payment grants **one billing interval** of full access; near expiry the owner
sends a renewal reminder (cron hook). Chosen so **no rail ever charges without
granting access** — works identically on mock / Paddle / Pesapal / M-Pesa, and
avoids the "recurring price charges the card but our DB didn't extend access" bug.
True card auto-renew (Paddle subscriptions) is a documented later enhancement that
needs subscription-renewal webhook wiring; until then use **one-time** Paddle price
ids for the Pro plans.

## Implementation
- `pricing.ts`: `pro_monthly`/`pro_annual` products; `PRO_MONTHLY_*`/`PRO_ANNUAL_*`/
  `TRIAL_DAYS` env (defaults $9/mo, $79/yr, KES 1,200 / 9,900, 14-day trial);
  `planIntervalDays`, `isSubscription`, `bothPricesForProduct`.
- `subscriptions` table + `subscriptions.ts`: `startTrial` (one/account),
  `activateSubscription` (interval; renewal stacks onto remaining time),
  `cancelSubscription` (at period end), `expireLapsedSubscriptions` (cron),
  `isActive`. **Access is driven by `current_period_end`** → lapses automatically
  even before the cron runs.
- `auth.ts`: `SafeUser.lifetimeAccess` now = Lifetime **OR** active Pro (so all 27
  existing gates unlock for subscribers with zero route changes) + new `hasLifetime`
  and `pro`; `getUserBySession` computes `pro` via `EXISTS` on active subscriptions.
- `payments.ts`/`paddle.ts`: `completePurchase` activates the subscription for
  `pro_*`; Paddle `PADDLE_PRO_MONTHLY/ANNUAL_PRICE_ID`; product-aware Pesapal desc.
- Routes: `/api/checkout` accepts `pro_*`; `/api/subscribe/trial`,
  `/api/subscribe/cancel`; `/api/cron/renew` + daily `vercel.json` cron (06:00).
- UI: redesigned `/pricing` (Free/Pro/Lifetime, toggle, trial) via `PlanChooser`;
  account page shows plan/status/renews-or-ends + `CancelSubscription`.
- Analytics: `TRIAL_STARTED`, `SUBSCRIPTION_CANCELED` events.

## Owner-gated to go live (as usual — I can't set/test keys)
- Set the live prices you want (`PRO_MONTHLY_*` etc.) in Vercel env.
- Payment keys (M-Pesa/Pesapal/Paddle) — same as the one-time flow; the
  subscription reuses the same rails. For Paddle, create **one-time** Pro price ids
  and set `PADDLE_PRO_MONTHLY/ANNUAL_PRICE_ID`.
- `CRON_SECRET` for the renewal cron (already used by the social cron).
- Decide final price points; consider a launch discount.

## Conversion model — "combine free preview + free trial + guarantee" ✅
Owner chose to combine the free-preview model with the free-trial + money-back
guarantee (make paying feel safe). Layered on:
- Pricing page: "See your full estimate free" hero + badge row (free trial ·
  money-back guarantee · cancel anytime · sample link) + reassurance panel
  (guarantee, secure checkout, M-Pesa/Visa/Mastercard, "we never store your PIN").
- `GUARANTEE_DAYS` env (default 14) drives the messaging (matches the existing
  14-day guarantee in the refund legal page).
- **Actionable guarantee:** `/api/refund-request` records the request
  (`REFUND_REQUESTED` event → owner processes the provider-side refund) and cancels
  any active subscription; `RefundRequest` control on the account page for paid
  users. Honest MVP — money movement stays provider-side.

## Files
`pricing.ts`, `subscriptions.ts`, `auth.ts`, `payments.ts`, `paddle.ts`,
`db/schema.ts`, `app/pricing/page.tsx`, `components/PlanChooser.tsx`,
`components/CancelSubscription.tsx`, `app/account/page.tsx`,
`app/api/subscribe/{trial,cancel}/route.ts`, `app/api/cron/renew/route.ts`,
`app/api/checkout/route.ts`, `vercel.json`, `.env.example` — app @ main.
