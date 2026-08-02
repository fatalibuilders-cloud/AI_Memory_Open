# M-Pesa Activation Guide — Fatalibuilders Construction App

**For:** Eng Ali Ahmed · **Created:** 2026-08-02
**Status:** The app's M-Pesa (Daraja STK-push) integration is built and tested. This guide explains how to switch it on — and, importantly, why "a paybill on an invoice" is not the same thing as "STK-push credentials."

> **Security:** No account numbers, paybills, or keys are written in this repository. They belong only in the app's environment variables (never committed to git). Share credentials with the app through the hosting dashboard, not through chat or files.

---

## The key distinction (please read this first)

There are two very different things:

1. **A paybill/till on your invoice** — how a customer *manually* types a payment to you (they open M-Pesa, choose Paybill, enter the number + your account, and pay). Money settles to your bank. This works today, but it's manual and there's no automatic confirmation back to an app.

2. **Daraja STK Push ("Lipa na M-Pesa Online")** — what the *app* does: it pushes a prompt straight to the customer's phone, they enter their PIN, and Safaricom notifies the app automatically so access unlocks instantly. **This needs API credentials — a Consumer Key, Consumer Secret, and a Passkey — tied to an STK-enabled shortcode.** A plain paybill number alone cannot do this.

So the paybill on your invoice confirms *how you bank*, but to power the in-app one-tap M-Pesa checkout we need Daraja credentials. There are three ways to get them.

---

## Three paths (pick one)

### Path A — Payment aggregator (fastest, recommended to launch) ⭐
Use **Pesapal**, **Flutterwave**, or **DPO**. They already hold the Safaricom relationship; you sign up, and they give you API keys that do M-Pesa STK push (and cards too) and **settle the money to your existing bank account**.
- **Pros:** live in days, not weeks; M-Pesa + cards in one; they handle Safaricom go-live.
- **Cons:** a small fee per transaction (~2–3.5%).
- **Best if:** you want to start selling quickly.

### Path B — Your own Daraja shortcode (lowest fees, more setup)
Register a **Lipa na M-Pesa Online** shortcode directly with Safaricom (M-Pesa Business / Daraja), which comes with its own **Passkey**.
- **Pros:** lowest cost per sale; direct settlement.
- **Cons:** Safaricom "Go Live" approval can take a couple of weeks and paperwork.
- **Best if:** you expect high volume and want to minimise fees.

### Path C — Manual paybill + confirmation (interim, no new signup)
Show the buyer "Pay KES X to Paybill [yours], account [yours]", then confirm via an M-Pesa C2B confirmation webhook (or manual check) before unlocking.
- **Pros:** uses what you already have; no new account.
- **Cons:** clunkier UX; needs C2B API registration anyway for auto-confirmation.
- **Best if:** you want a stopgap while Path A/B is set up.

**Recommendation:** **Path A (Pesapal or Flutterwave)** to launch fast, then optionally move to Path B later to cut fees. The app is built so the payment provider is swappable — moving from one to another is a config change, not a rebuild.

---

## What the app needs (whichever path)

Set these in the hosting environment (Vercel → Settings → Environment Variables), never in code:

```
PAYMENTS_PROVIDER=mpesa
MPESA_ENV=sandbox            # then "production" at go-live
MPESA_CONSUMER_KEY=...        # from Daraja or the aggregator
MPESA_CONSUMER_SECRET=...
MPESA_SHORTCODE=...           # the STK-enabled Paybill/Till
MPESA_PASSKEY=...             # Lipa na M-Pesa Online passkey
MPESA_CALLBACK_URL=https://YOUR-APP-URL/api/payments/mpesa/callback
```

Until these are set, the app runs M-Pesa in **safe sandbox mode** — the phone-number checkout page works and simulates a successful payment, so you can test the whole flow now with no real money.

---

## Sandbox testing (Daraja provides test credentials)

- Register at **https://developer.safaricom.co.ke** → create an app → you get sandbox Consumer Key/Secret + a test passkey + test shortcode (174379).
- Use Safaricom's sandbox test phone numbers to trigger a test STK push.
- Verify: enter phone → prompt → success → account unlocks.

## Going live

- Path A: switch the aggregator to live keys.
- Path B: complete Safaricom "Go Live", swap in production shortcode + passkey, set `MPESA_ENV=production`.
- Do one real small payment to confirm settlement to your bank, then you're live.

---

*Owner's current M-Pesa collection details (bank paybill + account, from the Mae Ridge invoice) are kept by the owner only — deliberately NOT stored here. They confirm the settlement bank; the app itself only ever holds the Daraja/aggregator API credentials above, via environment variables.*

*App integration: `src/lib/mpesa.ts`, `src/app/api/checkout/mpesa/`, `src/app/api/payments/mpesa/callback/` in `fatalibuilders-cloud/fatalibuilders-app`.*
