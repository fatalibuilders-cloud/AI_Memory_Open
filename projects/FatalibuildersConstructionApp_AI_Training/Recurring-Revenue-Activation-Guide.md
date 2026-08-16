# Recurring Revenue & Email Activation Guide — Fatalibuilders

**For:** Eng Ali Ahmed · **Created:** 2026-08-16
**Status:** The Pro subscription, free trial, money-back guarantee, and renewal/
refund emails are **built, tested, and pushed** (app @ main). Mock-until-keys:
everything works in the sandbox now; set the env values below (Vercel → Settings →
Environment Variables) to go live. No keys live in the repo.

---

## 1. Set your prices & policy (optional — sensible defaults ship)
```
PRO_MONTHLY_USD=9        PRO_MONTHLY_KES=1200
PRO_ANNUAL_USD=79        PRO_ANNUAL_KES=9900
TRIAL_DAYS=14            # free Pro trial length (0 disables)
GUARANTEE_DAYS=14        # money-back guarantee window (0 disables messaging)
```
The pricing page and emails read these automatically.

## 2. Payments (same rails as the one-time flow)
The subscription reuses your existing checkout. Whatever you set for M-Pesa/
Pesapal/Paddle already works for Pro. **Model = prepaid period:** one payment =
one month/year of access; near expiry the app emails a renewal reminder. No silent
auto-charge, so no one is ever billed without getting access.
- **Paddle (cards, worldwide):** create **one-time** prices for the Pro plans and set
  `PADDLE_PRO_MONTHLY_PRICE_ID` / `PADDLE_PRO_ANNUAL_PRICE_ID`. (Switch to recurring
  prices only once subscription-renewal webhooks are wired — a later enhancement.)
- **M-Pesa / Pesapal (Kenya):** nothing extra — buyers pay the KES price; access is
  granted for the period; they re-pay to renew (reminder email sent).

## 3. Renewal reminders & refund emails
```
EMAIL_API_URL=            # a Resend/SendGrid-style JSON endpoint
EMAIL_API_KEY=            # Bearer key
EMAIL_FROM=Fatalibuilders <noreply@yourdomain>
REMINDER_WINDOW_DAYS=3    # days before period end to send the reminder
CRON_SECRET=...           # already used by the social cron; needed by /api/cron/renew
```
- The daily cron `/api/cron/renew` (06:00 UTC, in `vercel.json`) emails trials/
  subscriptions ending within the window, marks them reminded (no double-send),
  then flags lapsed ones `past_due`.
- `/api/refund-request` emails a confirmation when a user invokes the guarantee.
- **Until `EMAIL_API_*` are set, emails are logged only** (safe no-op) — the flow
  still works, nobody gets email.

## 4. The money-back guarantee (how it actually refunds)
The app makes the guarantee easy and auditable: the **Request a refund** button on
the account page records a `refund_requested` event (visible in admin metrics),
stops the subscription renewing, and emails a confirmation. **You process the
actual money-back** in your payment provider's dashboard (M-Pesa/Pesapal/Paddle) —
the app never moves money on its own. Keep the promise within `GUARANTEE_DAYS`.

## 5. Go-live checklist
1. Set prices (§1) + `CRON_SECRET` + payment keys (§2).
2. (Recommended) set `EMAIL_API_*` so reminders actually send (§3).
3. Test in sandbox: start a trial → see it in Account; run `/api/cron/renew`
   (admin) → check the mock email log; request a refund → see the event + email.
4. Flip payment provider to production, do one small real payment, confirm access.

---

## SMS reminders (Africa's Talking) ✅ built
Phone capture is live: optional phone at signup + editable on the account page
(`users.phone`). The renewal cron texts users who gave a number. Turn on:
```
AT_USERNAME=            # Africa's Talking username ("sandbox" for testing)
AT_API_KEY=             # AT API key
AT_ENV=production       # or "sandbox"
AT_SENDER=              # optional short-code / alphanumeric sender id
```
Until set, SMS is logged only (mock). `normalizePhone` maps 07../254../+254.. to
E.164; only people with a number are texted.

## Coupons / launch discounts ✅ built
Percent-off codes (correct across USD & KES). Manage at **/admin/coupons**
(owner-only): code, % off, product scope (any/lifetime/pro), max redemptions,
expiry, active. Buyers enter a code on /pricing → `/api/coupon/validate` previews
the discount; it's applied at checkout and redeemed on completion (redemption
count enforced). e.g. create `LAUNCH50` = 50% off, 100 redemptions, expires in a
month for the first wave.

## Not yet built (noted)
- **True card auto-renew** (Paddle recurring subscriptions + renewal webhooks) —
  optional; the prepaid + reminder model gives predictable revenue without it.

*App: `lib/subscriptions.ts`, `lib/notify.ts`, `lib/pricing.ts`, `lib/payments.ts`,
`app/api/subscribe/*`, `app/api/cron/renew`, `app/api/refund-request`,
`app/pricing`, `components/PlanChooser|CancelSubscription|RefundRequest` — app @ main.*
