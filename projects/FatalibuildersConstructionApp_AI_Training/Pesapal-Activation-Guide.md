# Pesapal Activation Guide — Fatalibuilders Construction App

**For:** Eng Ali Ahmed · **Created:** 2026-08-02
**Status:** The Pesapal integration is **built, tested, and pushed** (app repo `fatalibuilders-cloud/fatalibuilders-app` @ main). This is the recommended fastest path to accepting **M-Pesa + cards** in Kenya, with money settling to your existing **KCB** account. This guide is the step-by-step to switch it on.

> **Security:** No account numbers, paybills, or API keys are written anywhere in this repository. They live only in the app's environment variables (never committed to git). Enter them in the hosting dashboard — not in chat, not in files.

---

## Why Pesapal (recap)

A plain paybill on an invoice lets a customer *manually* pay you, but it can't tell the app "this person paid" so access unlocks automatically. Pesapal solves that: it's a licensed Kenyan aggregator that already holds the Safaricom relationship. You sign up once and get API keys that drive **one hosted checkout** offering **M-Pesa STK push and cards**, and **settle the money to your bank account (KCB)**. Live in days, not the weeks a direct Daraja go-live takes. Fee is ~small % per sale.

The app is built so the provider is swappable — if you later want lower fees via your own Daraja shortcode, that's a config change, not a rebuild.

---

## What's already built (so you know what "on" means)

- **`src/lib/pesapal.ts`** — auth token, create order (`SubmitOrderRequest`), confirm status (`GetTransactionStatus`), status mapping.
- **`createCheckout` "pesapal" branch** — when keys are set, creates a Pesapal order and redirects the buyer to Pesapal's hosted page. **Until keys are set, it safely falls back to the mock checkout**, so nothing breaks.
- **`/api/payments/pesapal/ipn`** — Pesapal's server-to-server notification; confirms the real status and grants lifetime access (idempotent — safe if it fires more than once).
- **`/api/payments/pesapal/callback`** — where the buyer's browser returns after paying; double-checks status so access unlocks immediately, then sends them to their account.
- **6 tests** covering status mapping + config (full suite: 101 passing).

---

## Step-by-step activation

### 1. Create a Pesapal merchant account
- Go to **https://www.pesapal.com** → sign up as a business (Kenya).
- Complete KYC and add your **KCB** settlement bank details (this is where your $30 sales land). *These bank details go to Pesapal directly — never into this app or repo.*

### 2. Get your API keys
- In the Pesapal dashboard: **Account → API Keys** (or Developer/Integrations).
- Copy your **Consumer Key** and **Consumer Secret**.
- There are **sandbox** keys (for testing) and **live** keys (for real money) — start with sandbox.

### 3. Register your IPN URL (one-time) → get the IPN id
The app needs a `PESAPAL_IPN_ID`. You get it by registering your notification URL with Pesapal once. Two ways:

**Easiest:** in the Pesapal dashboard, find **IPN / Instant Payment Notification settings**, add:
```
https://YOUR-APP-URL/api/payments/pesapal/ipn
```
choose **GET**, save, and copy the **IPN ID** it gives back.

**Or via API** (if you prefer): first get a token from `POST /api/Auth/RequestToken` with your key+secret, then:
```
POST {baseUrl}/api/URLSetup/RegisterIPN
Authorization: Bearer <token>
{ "url": "https://YOUR-APP-URL/api/payments/pesapal/ipn", "ipn_notification_type": "GET" }
```
The response contains `ipn_id` — that's your `PESAPAL_IPN_ID`.

> Base URLs: sandbox `https://cybqa.pesapal.com/pesapalv3`, live `https://pay.pesapal.com/v3`.

### 4. Set the environment variables (Vercel → Settings → Environment Variables)
```
PAYMENTS_PROVIDER=pesapal
PESAPAL_ENV=sandbox            # then "production" at go-live
PESAPAL_CONSUMER_KEY=...
PESAPAL_CONSUMER_SECRET=...
PESAPAL_IPN_ID=...             # from step 3
APP_URL=https://YOUR-APP-URL   # so callback/IPN URLs are correct
```
Redeploy so the app picks them up.

### 5. Test in sandbox
- Sign in → start a purchase → you're redirected to Pesapal's sandbox page.
- Pay with Pesapal's **sandbox M-Pesa / test card** details (from their docs).
- Confirm: after paying you land back on your account page **with access unlocked**, and the IPN grant fires server-side.

### 6. Go live
- Swap sandbox keys for **live** keys, set `PESAPAL_ENV=production`, re-register the IPN against the live base URL (get a new live `PESAPAL_IPN_ID`), redeploy.
- Do **one small real payment** (e.g. KES equivalent) and confirm it settles to your KCB account.
- You're live — selling M-Pesa + cards in Kenya.

---

## Notes

- **Currency:** the app requests the order in **USD** ($30). Pesapal presents M-Pesa in KES at the day's rate. If you'd prefer to price directly in KES (e.g. a fixed KES amount instead of USD conversion), say so — it's a one-line change in `createCheckout`.
- **Idempotency:** both the IPN and the browser callback confirm status and grant access; calling twice is safe, so no double-unlock or double-charge risk on our side.
- **Fallback safety:** if keys are ever missing/mis-set, checkout falls back to the mock page rather than erroring — but real sales require the live keys above.

---

*Owner's KCB settlement details (from the Mae Ridge invoice) are kept by the owner and given directly to Pesapal during signup — deliberately NOT stored here. The app only ever holds the Pesapal API credentials, via environment variables.*

*App integration: `src/lib/pesapal.ts`, `src/app/api/payments/pesapal/ipn/`, `src/app/api/payments/pesapal/callback/`, and the `pesapal` branch in `src/lib/payments.ts` — in `fatalibuilders-cloud/fatalibuilders-app`.*
