# Paddle Activation Guide — Fatalibuilders Construction App

**For:** Eng Ali Ahmed · **Created:** 2026-07-23
**Status:** The app's Paddle integration is fully built and tested. This guide is the exact steps to switch it on. It becomes a ~10-minute job once your Paddle account is verified.

---

## The one-time setup (you do this in the Paddle dashboard)

1. **Create a Paddle account** at https://www.paddle.com → sign up as a seller.
2. **Complete seller verification** — Paddle reviews your business details and ID. *This can take 1–3 business days, so start it early.* You can do everything below in **Sandbox** mode meanwhile.
3. **Switch to Sandbox** (toggle in the dashboard) for testing.
4. **Create the product & price:**
   - Catalog → Products → New product → name it "Fatalibuilders Lifetime Access".
   - Add a **one-time price** of **USD 30**. Save.
   - Copy the **Price ID** — it looks like `pri_01h...`.
5. **Get your client token:** Developer Tools → Authentication → copy the **client-side token** (`test_...` in sandbox).
6. **Set up the webhook:** Developer Tools → Notifications → New destination:
   - URL: `https://YOUR-APP-URL/api/payments/webhook` (you'll have this after hosting is set up)
   - Subscribe to the **`transaction.completed`** event.
   - Copy the **webhook secret** (`pdl_ntf_...`).

## What you give me (or paste into the hosting environment)

Set these environment variables (I'll show you where in your host, e.g. Vercel → Settings → Environment Variables):

```
PAYMENTS_PROVIDER=paddle
PADDLE_ENV=sandbox            # then "production" at launch
PADDLE_CLIENT_TOKEN=test_xxxxxxxx
PADDLE_PRICE_ID=pri_01hxxxxxxxx
PADDLE_WEBHOOK_SECRET=pdl_ntf_xxxxxxxx
APP_URL=https://your-app-url
APP_SECRET=<a long random string>
```

That's it. The moment these are set, the "Get lifetime access — $30" button opens the real Paddle checkout, and a completed payment automatically unlocks the buyer's account (via the verified webhook).

## Testing in sandbox (before real money)

- Paddle provides **test card numbers** (e.g. `4242 4242 4242 4242`, any future expiry/CVC).
- Buy as a test user → the webhook grants lifetime access → exports unlock. No real money moves.

## Going live (launch day)

1. Finish Paddle verification (approved for live).
2. Recreate the product/price in **Production**, get the production client token, price id, and a production webhook secret.
3. Flip `PADDLE_ENV=production` and swap in the production values.
4. Do one real $30 purchase to confirm, then refund it from the dashboard.

---

## What's already built (so you don't have to worry about the code)

- Real Paddle.js overlay checkout, opened from the pricing page.
- Webhook signature verification (HMAC, replay-protected) — forged webhooks are rejected.
- Idempotent access grant — a buyer is never double-charged access, and duplicate webhooks are safe.
- Everything falls back to the self-contained **sandbox mock** until `PAYMENTS_PROVIDER=paddle` is set, so the app keeps working during setup.

*Reference: app repo `fatalibuilders-cloud/fatalibuilders-app` — `src/lib/paddle.ts`, `src/lib/payments.ts`, `src/app/api/payments/webhook/route.ts`.*
