# API Keys Guide — Fatali Builders (Beginner-Friendly)

**Owner:** Eng Ali Ahmed
**Last Updated:** 2026-07-16
**Purpose:** Everything you need to know about API keys for the Fatalibuilders Construction App — what they are, which ones you'll need, exactly how to create each one, and how to store them safely.

> **The one rule that matters most:** An API key is like the key to your office. Never post it publicly, never paste it into a chat or email, never commit it to GitHub. If a key ever leaks, log into the service and revoke/regenerate it immediately.

---

## 1. What Is an API Key? (Plain Language)

When your app needs to talk to another service — for example, telling QuickBooks "create this invoice" — that service needs to know the request really comes from you and not a stranger. An **API key** (or a Client ID + Client Secret pair) is the password your app uses to prove that.

Three facts every beginner should know:

1. **Only YOU can create your keys.** Each service issues keys to your account, on their website, after you log in. Nobody else can create them for you — treat anyone who offers to as suspicious.
2. **Keys are free to create** for everything in this guide. You pay (if at all) for usage, not for the key itself.
3. **You don't need any keys today.** Keys are only needed when we start *building* the integrations. Creating them early is fine, but don't feel rushed — the "When Do I Need Each Key?" table below shows the timing.

---

## 2. When Do I Need Each Key?

| Project Phase | Where We Are | Keys Needed |
|---|---|---|
| Staging (planning documents) | ✅ **We are here** | **None** |
| Design (architecture + release plan) | Next | **None** |
| Build — Core tool + Excel export | During development | **None** (Excel is file-based, no key needed) |
| Build — WhatsApp share links | During development | **None** (wa.me links need no key) |
| Build — **$30 checkout (payments)** | During development | **Payment provider keys** (test mode first — see §3.4) |
| Launch (paying customers) | After testing | Payment provider **live** keys + hosting provider account |
| Later — WhatsApp Business API (automated messages) | If/when decided | Meta/WhatsApp Business keys |
| Later integrations (email, maps…) | As decided | One key each, created the same way |

> **Updated 2026-07-16:** Because the app now sells **$30 lifetime access**, one key became necessary: a **payment provider** account (so customers can pay you securely by card). Everything else stays key-free. Like all keys, it has a free "test mode" — no real money moves until launch.

---

## 3. The Keys, One by One

### 3.1 Microsoft Excel (Priority 1 — no key needed) ✅

**Nothing to create.** Excel integration works with .xlsx files directly — the app reads and writes the files themselves. No account, no key, no setup.

*(Only if we later decide the app should read spreadsheets stored in OneDrive/Microsoft 365 automatically would we need a Microsoft key — skip for now.)*

### 3.2 WhatsApp (Priority 2 — no key needed for the first version) ✅

The app will use WhatsApp in two stages:

**Stage 1 — Share links (first release, NO key needed):** The app prepares a message (for example, a quote or a job update) and opens WhatsApp on your phone with the message and the client's number already filled in — you just press Send. This uses standard "wa.me" links that work with your existing WhatsApp; nothing to create or configure.

**Stage 2 — WhatsApp Business API (later, optional):** If you eventually want the app to send messages *automatically* (appointment reminders at 7am, automatic "invoice sent" notifications), that requires a **WhatsApp Business API** account:
1. Go to **https://developers.facebook.com** and sign in with the Facebook account tied to your business.
2. Create an app → add the **WhatsApp** product → follow the business verification steps (Meta requires verifying your business — this can take days).
3. Copy the access token and phone number ID into `AliKeys.txt`.

Don't do Stage 2 now — decide after you've used Stage 1 for a while.

### 3.3 Phone Calls (no key needed) ✅

Tap-to-call uses your phone's normal dialer — no integration, no key, no cost.

### ~~QuickBooks~~ (REMOVED 2026-07-16)

You decided to use Excel only and drop QuickBooks, so **no Intuit/QuickBooks keys are needed.** If you ever change your mind, this guide's git history has the full instructions.

### 3.4 Payment Provider (needed at build time for the $30 checkout)

To accept the $30 lifetime-access payment, the app needs a payment provider. **Wait for the architecture session (Document 2) to pick which one** — the AI will recommend based on your country and target market. The main candidates:

| Provider | Why consider it |
|---|---|
| **Paddle** (https://paddle.com) or **Lemon Squeezy** (https://lemonsqueezy.com) | They act as the "merchant of record" — they handle sales tax/VAT worldwide for you. **Usually the easiest choice for a first-time seller.** |
| **Stripe** (https://stripe.com) | The industry standard, most flexible, but YOU handle tax obligations. Not available in every country. |

Whichever is chosen, the pattern is the same: sign up with your business details → the dashboard gives you **test keys** (fake money, for building) and **live keys** (real money, for launch) → copy them into `AliKeys.txt`. Each provider takes a small fee per sale (roughly 3-6%) — that's how they're paid; creating the account is free.

> **Important:** Payment providers will ask for identity/business verification (this protects you and your customers). Have your ID and bank account details ready when you sign up.

### 3.5 Anthropic / Claude (optional — only if the app gets AI features)

If we build AI features into the app (like auto-drafting an estimate from a site description):
1. Go to **https://console.anthropic.com**
2. Sign up / sign in → **API Keys** → **Create Key**.
3. Name it `fatalibuilders-app`, copy it into `AliKeys.txt` immediately (it is shown only once).

### 3.6 Future keys (create only when we decide to build these)

| Service | Where to create | For |
|---|---|---|
| Google (Gmail/Drive/Calendar sync) | https://console.cloud.google.com → "Credentials" → OAuth Client ID | Emailing clients, storing job photos in Drive |
| SendGrid/Resend (email) | https://sendgrid.com or https://resend.com | Sending invoices/notifications by email |
| Hosting (to run the app) | Provider chosen in Document 2 (e.g., https://vercel.com, https://railway.app) | Deploying the app to the internet |

Each follows the same pattern: sign up → find "API keys" or "Credentials" in settings → create → copy into `AliKeys.txt`.

---

## 4. Where to Store Keys: Your `AliKeys.txt` File

Create a plain text file named **`AliKeys.txt`** in the root of your AI_Memory_Open folder **on your own computer**. This repository's `.gitignore` already excludes it, so it can never be accidentally uploaded to GitHub.

**Format (copy this template):**

```
#Payments (provider chosen in Document 2 — Paddle / Lemon Squeezy / Stripe):

Test/Sandbox Key: ADD_AT_BUILD_TIME
Live Key: ADD_AT_LAUNCH

#Hosting:

API Token: ADD_AT_LAUNCH

#WhatsApp Business (only if Stage 2 is ever activated):

Access Token: ADD_LATER_IF_NEEDED
Phone Number ID: ADD_LATER_IF_NEEDED

#Claude:

API Key: PASTE_HERE_IF_CREATED
```

*(The first real key you'll create is the payment provider's test key, during the build phase — the AI will tell you exactly when.)*

Add a new `#ServiceName:` section for each service as you create keys.

**Rules:**
- ✅ Keep `AliKeys.txt` on your own computer (and a backup somewhere private, e.g., a password manager — recommended).
- ✅ When an AI session needs a key during development, it will tell you exactly which one and where it goes (usually an environment variable) — you paste it there yourself.
- ❌ Never paste keys into chat messages, emails, WhatsApp, or screenshots.
- ❌ Never rename the file to something not covered by `.gitignore` (`*Keys.txt` and `keys.txt` are protected).
- 🔄 If a key leaks anyway: log into that service and click "regenerate" or "revoke" — the old key stops working instantly.

> **Note for cloud AI sessions (like this one):** These sessions run on temporary computers that are wiped afterwards, and this repository is public-facing infrastructure — so keys should NEVER be given to a session by pasting them into chat. During the build phase, keys go into the app's hosting environment as "environment variables" (the guide for that will be part of the deployment docs in Document 2).

---

## 5. Your Overall Roadmap (So You Always Know Where You Are)

Building an app for the first time follows this path — we track it all in this memory system, so any session can pick up where the last left off:

```
1. STAGING (now)          → Agree on WHAT we're building (vision, users, features)
2. ARCHITECTURE (next)    → Agree on HOW (tech stack, integrations, security)
3. RELEASE PLAN           → Break the work into small, ordered steps
4. INITIALIZE PROJECT     → PROJECT_MEMORY_INIT.md builds the full project workspace
5. BUILD, in releases     → AI develops the app step by step; you test each release
   ↳ Payment provider TEST keys needed here (fake money, free)
6. LAUNCH                 → Payment provider LIVE keys + hosting account; real customers pay $30
7. IMPROVE                → New integrations and features, one release at a time
```

**Your only jobs right now:**
1. **Define the core tool** (this is the big one): what exactly does a user type in, and what results come out? For example: "enter room dimensions → get cement, blocks, and steel quantities" or "enter project details → get a full cost estimate."
2. Say whether job tracking / crew scheduling / site logs should ALSO be in the product, or if it's the focused calculator only.
3. Tell the AI your primary market/country — it decides the best payment provider and any tax/legal needs for selling at $30.

No keys to create yet — the payment provider gets chosen during the design phase, and I'll walk you through its signup when we get there.

---

*This guide is part of the AI Memory system. It will be updated as integration decisions are made in staging.*
