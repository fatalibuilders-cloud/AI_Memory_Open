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
| Build — Excel import/export (priority 1) | During development | **None** (Excel is file-based, no key needed) |
| Build — WhatsApp share links (priority 2, first version) | During development | **None** (wa.me links need no key) |
| Launch (real company data) | After testing | Hosting provider account only |
| Later — WhatsApp Business API (automated messages) | If/when decided | Meta/WhatsApp Business keys |
| Later integrations (email, maps…) | As decided | One key each, created the same way |

> **Good news (updated 2026-07-16):** With Excel-only accounting and WhatsApp share links, the first version of your app needs **NO API keys at all** to build. Your first key will likely be the hosting account at launch.

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

### 3.4 Anthropic / Claude (optional — only if the app gets AI features)

If we build AI features into the app (like auto-drafting an estimate from a site description):
1. Go to **https://console.anthropic.com**
2. Sign up / sign in → **API Keys** → **Create Key**.
3. Name it `fatalibuilders-app`, copy it into `AliKeys.txt` immediately (it is shown only once).

### 3.5 Future keys (create only when we decide to build these)

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
#Hosting:

API Token: ADD_AT_LAUNCH

#WhatsApp Business (only if Stage 2 is ever activated):

Access Token: ADD_LATER_IF_NEEDED
Phone Number ID: ADD_LATER_IF_NEEDED

#Claude:

API Key: PASTE_HERE_IF_CREATED
```

*(Right now this file has nothing urgent to hold — your first release needs no keys. Create the file when the first real key arrives.)*

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
   ↳ No keys needed (Excel + WhatsApp links are key-free)
6. LAUNCH                 → Real data, real crews; hosting account created here
7. IMPROVE                → New integrations and features, one release at a time
```

**Your only jobs right now:**
1. Read the app vision in `projects/staging/FatalibuildersConstructionApp/Master-Context.md` and say "looks right" or what to change.
2. Tell the AI where job photos/documents live today (phone gallery? Google Drive? paper?).
3. Tell the AI how you schedule crews today (paper, Excel, calendar app?).

That's it — no keys to create for now.

---

*This guide is part of the AI Memory system. It will be updated as integration decisions are made in staging.*
