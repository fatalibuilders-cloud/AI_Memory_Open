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
| Build — QuickBooks connector | During development | QuickBooks **sandbox** keys (test mode — free, no risk to real data) |
| Build — Excel import/export | During development | **None** (Excel is file-based, no key needed) |
| Launch (real company data) | After testing | QuickBooks **production** keys + hosting provider account |
| Later integrations (email, WhatsApp, maps…) | As decided | One key each, created the same way |

---

## 3. The Keys, One by One

### 3.1 QuickBooks (Priority 1 — needed at build time)

QuickBooks keys come from Intuit's developer portal. You get a **Client ID** and **Client Secret**.

**Before you start:** Confirm you use **QuickBooks Online** (in a web browser / mobile app). If you use QuickBooks **Desktop** (installed program on one PC), tell the AI in the next session — the integration approach is different.

**Steps (about 15 minutes):**
1. Go to **https://developer.intuit.com** in your browser.
2. Click **Sign In** (top right). Use the SAME Intuit account you use for QuickBooks. If asked, agree to the developer terms — this is free.
3. Once signed in, click **Dashboard**, then **Create an app**.
4. Choose **QuickBooks Online and Payments** as the platform.
5. Name the app: `Fatalibuilders Construction App`. For scopes, select **Accounting** (com.intuit.quickbooks.accounting).
6. After the app is created, open it and go to **Keys & credentials**. You'll see two tabs:
   - **Development keys** (sandbox — use these first)
   - **Production keys** (real data — only needed at launch)
7. Copy the **Client ID** and **Client Secret** from the Development tab into your `AliKeys.txt` file (see Section 4).
8. Also under the Dashboard, find **Sandbox** and note your **sandbox company** — Intuit gives you a fake company with fake invoices to test against safely.

### 3.2 Microsoft Excel (Priority 2 — no key needed)

Good news: **nothing to create.** Excel integration works with .xlsx files directly — the app reads and writes the files themselves. No account, no key.

*(Only if we later decide the app should read spreadsheets stored in OneDrive/Microsoft 365 automatically would we need a Microsoft key — skip for now.)*

### 3.3 Anthropic / Claude (optional — only if the app gets AI features)

If we build AI features into the app (like auto-drafting an estimate from a site description):
1. Go to **https://console.anthropic.com**
2. Sign up / sign in → **API Keys** → **Create Key**.
3. Name it `fatalibuilders-app`, copy it into `AliKeys.txt` immediately (it is shown only once).

### 3.4 Future keys (create only when we decide to build these)

| Service | Where to create | For |
|---|---|---|
| Google (Gmail/Drive/Calendar sync) | https://console.cloud.google.com → "Credentials" → OAuth Client ID | Emailing clients, storing job photos in Drive |
| WhatsApp Business | https://developers.facebook.com → Create App → WhatsApp | Messaging clients/crews from the app |
| Twilio (SMS) | https://www.twilio.com → Console | Text message notifications |
| SendGrid/Resend (email) | https://sendgrid.com or https://resend.com | Sending invoices/notifications by email |
| Hosting (to run the app) | Provider chosen in Document 2 (e.g., https://vercel.com, https://railway.app) | Deploying the app to the internet |

Each follows the same pattern: sign up → find "API keys" or "Credentials" in settings → create → copy into `AliKeys.txt`.

---

## 4. Where to Store Keys: Your `AliKeys.txt` File

Create a plain text file named **`AliKeys.txt`** in the root of your AI_Memory_Open folder **on your own computer**. This repository's `.gitignore` already excludes it, so it can never be accidentally uploaded to GitHub.

**Format (copy this template):**

```
#QuickBooks:

Client ID (Development): PASTE_HERE
Client Secret (Development): PASTE_HERE
Client ID (Production): ADD_AT_LAUNCH
Client Secret (Production): ADD_AT_LAUNCH
Sandbox Company ID: PASTE_HERE

#Claude:

API Key: PASTE_HERE_IF_CREATED
```

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
   ↳ QuickBooks sandbox keys needed here
6. LAUNCH                 → Real data, real crews, production keys
7. IMPROVE                → New integrations and features, one release at a time
```

**Your only jobs right now:**
1. Read the app vision in `projects/staging/FatalibuildersConstructionApp/Master-Context.md` and say "looks right" or what to change.
2. Tell the AI: QuickBooks **Online** or **Desktop**?
3. (Whenever convenient) Tell the AI what you use for client contacts, messaging, photos, and scheduling.
4. (Optional, no rush) Create the QuickBooks developer keys using Section 3.1 above.

---

*This guide is part of the AI Memory system. It will be updated as integration decisions are made in staging.*
