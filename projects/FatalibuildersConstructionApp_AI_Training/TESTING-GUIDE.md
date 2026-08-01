# How to Test the Fatalibuilders App

**For:** Eng Ali Ahmed · **Updated:** 2026-07-23

The app isn't deployed to a public address yet, so there are two ways to try it. Pick whichever suits you.

---

## Option A — Get a shareable public link (Vercel) · recommended

This puts the app on the internet at a real URL you (and testers) can open on any phone. ~10 minutes, free.

### Step 1 — Deploy
1. Go to **https://vercel.com** → **Sign up** → choose **"Continue with GitHub"** (log in as `fatalibuilders-cloud`).
2. Click **Add New… → Project**.
3. Find **`fatalibuilders-app`** in the list → **Import**.
4. Leave all settings as detected (it's a Next.js app) → click **Deploy**.
5. Wait ~2 minutes. You'll get a URL like `https://fatalibuilders-app.vercel.app`.

At this point the **landing page, sample estimate (/demo), and pricing page work immediately** — great for a first look and screenshots.

### Step 2 — Add a database (so sign-up & projects work)
Accounts and saved projects need a database. Free option:
1. Go to **https://neon.tech** → sign up → create a project → copy the **connection string** (starts `postgresql://…`).
2. Back in Vercel → your project → **Settings → Environment Variables** → add:
   - Name: `DATABASE_URL`  ·  Value: the Neon connection string
   - Name: `APP_SECRET`  ·  Value: any long random text
3. **Deployments → … → Redeploy.**

Now the full app works at your public URL: sign up, enter a project, see the material preview, hit the $30 paywall, and (in sandbox mode) test the checkout → unlock.

> Payments stay in safe **sandbox mode** until you add the Paddle keys (see `Paddle-Activation-Guide.md`) — no real money is taken while testing.

---

## Option B — Run it on your own computer · full features, no accounts

Best if you're comfortable with a terminal. Everything works locally, including saved data and the sandbox checkout.

1. Install **Node.js** (LTS) from **https://nodejs.org** — one-time.
2. Open a terminal and run:
   ```bash
   git clone https://github.com/fatalibuilders-cloud/fatalibuilders-app
   cd fatalibuilders-app
   npm install
   npm run dev
   ```
3. Open **http://localhost:3000** in your browser.

No configuration needed — it uses a built-in local database. Data is saved to a `.pglite` folder on your machine.

---

## What to try once it's running

1. **Landing page** → "See a sample estimate" (/demo) — real material quantities, no signup.
2. **Sign up** (free) → **New project** → enter a building (e.g. 12 × 9 m, 1 floor) → **Finish**.
3. See the **material quantities** (free preview) and the **"unlock for $30"** panel.
4. Click **Get lifetime access** → in sandbox, press **Pay $30 (test)** → your account unlocks.
5. Now see the **cost estimate** + **labour plan**, and **download the Excel/PDF BOQ** and **Share on WhatsApp**.
6. Check the **Account** page shows "✓ Lifetime access".

---

## Which should I choose?

- **Want a link to open on your phone / show others?** → Option A (Vercel).
- **Just want to see everything work right now and you have Node?** → Option B (local).
- **Not sure / not technical?** → Option A, and tell me once the Vercel project + Neon database exist; I'll help confirm the environment variables and run a live end-to-end check.

*App repo: https://github.com/fatalibuilders-cloud/fatalibuilders-app*
