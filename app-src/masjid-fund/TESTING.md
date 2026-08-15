# Testing Masjid Fund

Everything below runs in **test mode**: payments are simulated, no card is taken,
and receipts are printed to the server console instead of being emailed. A gold
banner sits across the top of every page saying so, and it disappears on its own
once a real payment provider is configured — so a preview link can be shared with
your committee without anyone believing their money moved.

## Three ways to run it

### 1. GitHub Codespaces — nothing to install

On the repository page, choose **Code → Codespaces → Create codespace on
`claude/mosque-donation-website-c0qbk8`**. It installs dependencies, starts the
site and opens it on port 3000. Free-tier hours cover this comfortably.

### 2. On your own machine

Needs Node 22 or newer.

```bash
git clone https://github.com/fatalibuilders-cloud/AI_Memory_Open.git
cd AI_Memory_Open/app-src/masjid-fund
git checkout claude/mosque-donation-website-c0qbk8
npm install
npm run dev          # http://localhost:3000
```

The database is embedded — no PostgreSQL to install. It writes to `.pglite/` in
the project folder; delete that folder to start over with fresh sample data.

### 3. A shared preview on Vercel

Import the repo at [vercel.com/new](https://vercel.com/new), set the root
directory to `app-src/masjid-fund`, and add one environment variable:

```
ALLOW_EPHEMERAL_DB=1
```

That opts into a throwaway in-memory database: fine for clicking around, and
donations disappear whenever the instance restarts. Without it the app refuses to
boot in production, so a real deployment can never quietly run on a disposable
database — for that, set `DATABASE_URL` to a managed PostgreSQL instance
(Neon and Supabase both have free tiers) and leave `ALLOW_EPHEMERAL_DB` unset.

Add `APP_URL=https://your-preview.vercel.app` so links in receipts point at the
right place.

## Signing in to the admin

Running locally or in Codespaces, admin sign-in accepts:

- **Email:** `admin@localhost`
- **Password:** `masjidfund-dev`

This fallback only exists in development builds. In production it is off, and
sign-in needs `ADMIN_EMAIL` plus `ADMIN_PASSWORD_HASH`
(`npm run admin:hash -- 'your password'`). On a Vercel preview, set both if you
want to reach `/admin` there.

## What to try

### As a donor

1. **Home page.** Totals, the featured masajid, what a gift buys.
2. **A project page** — `/projects` then any project. Check the story, the costed
   items, the build updates and the progress bar.
3. **"Fund this"** on a costed item. It should carry that exact amount into the
   donation form.
4. **Donate.** Try a preset and a typed amount; switch between *Give once* and
   *Give monthly*; add a dedication. Worth testing deliberately badly: an amount of
   `0.50`, a malformed email, an empty amount — each should explain itself rather
   than fail silently.
5. **Choose Zakat** in *Type of giving*. The project selector should disable
   itself and the note should explain that zakat is never spent on construction.
6. **Complete the simulated payment,** then try the **declined** button on a
   second donation and confirm nothing is charged and the totals do not move.
7. **The receipt page.** Reference, amount, project, dedication.
8. **Go back to the project.** The raised total and donor count should have moved
   by exactly your donation.

### Reading the receipt email

Nothing is actually sent in test mode, so the receipt is printed in the terminal
where the site is running (in Codespaces, the terminal panel). You will see the
full message including the monthly-giving link. That link also appears in the
admin donation list, under the status column of any active monthly gift.

### Cancelling a monthly gift

Make a monthly donation, open the link from the receipt (or the *manage* link in
admin), and cancel. The page should confirm the cancellation, say that past gifts
stay with their project, and show no cancel button when you revisit it.

### As staff

1. **`/admin`** — the dashboard flags anything unconfigured, which on a test run
   means simulated payments and log-only email. That is expected here.
2. **Add a project** at `/admin/projects/new`. Try a bad slug like `My Masjid` to
   see the validation. Then add a costed item and post a build update, and check
   both appear on the public project page.
3. **Record an offline gift** at `/admin/donations` — a bank transfer or cash.
   It counts towards the project immediately.
4. **Download the CSV** and open it in Excel or Google Sheets. Everything is
   quoted, and donor names that begin with `=` or `+` are neutralised so a name
   can never run as a formula.
5. **Sign out**, then visit `/admin` again — it should send you back to sign-in.

## What is deliberately not there yet

- **M-Pesa, PayPal, bank-transfer instructions** — Stripe is written and tested
  but inactive until keys are set; the other rails come next.
- **Prices are USD.** Multi-currency lands with M-Pesa, which settles in KES.
- **No rate limiting** on the donation endpoint yet. Fine for testing, needs to
  be in place before the site is public.
- **No privacy, terms or refund pages.**
- **The five listed masajid are sample data** — plausible but invented, so that
  there is something to click. Replace them through `/admin` before launch.

## Telling me what you find

Notes in any form work. The most useful things to capture: which page, what you
did, what you expected, what happened. Screenshots help for anything visual, and
if a page errors, the text in the terminal running the site is worth pasting.
