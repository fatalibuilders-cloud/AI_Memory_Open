# API Key Store — FatalibuildersConstructionApp

**Purpose:** Inventory of all API keys, tokens, and credentials this project requires. **Names and providers ONLY — actual secret values are NEVER stored here** (or anywhere in git).

**Security Rule:** AI assistants must NEVER read, store, echo, or log actual credential values. When a credential is needed, leave a `__HUMAN_PROVIDED__` placeholder and give the owner plain-language instructions for where to paste the real value (hosting env vars / `.env.local`).

**Owner guide:** the beginner-friendly walkthrough for creating each of these lives at the repo root: `API-Keys-Guide.md`.

---

## Credential Inventory

| Key Name | Service/Provider | Used By | Purpose | Who Provides | Status |
|----------|-----------------|---------|---------|-------------|--------|
| `DATABASE_URL` | Hosting platform (PostgreSQL) | App backend | Database connection | Auto (platform) at CORE-1.2 | Pending |
| `STORAGE_*` (endpoint/key/secret/bucket) | S3-compatible storage | App backend | Generated documents | Auto/owner at CORE-1.2 | Pending |
| `EMAIL_API_KEY` | Resend (or similar) | App backend | Verification + reset + receipts | Owner at CORE-2.1 | Pending |
| `PAYMENT_TEST_KEY` / `PAYMENT_LIVE_KEY` (+ webhook secret) | Paddle or Lemon Squeezy | App backend | $30 lifetime card checkout | Owner at CORE-3.0 (test) / CORE-8.2 (live) | Pending |
| `MPESA_GATEWAY_*` (consumer key/secret) | Pesapal / Flutterwave / DPO | App backend | M-Pesa checkout (Kenya) | Owner at CORE-3.2 | Pending |
| `ANALYTICS_KEY` | TBD at CORE-8.0 | App frontend | Product analytics | Owner/AI at CORE-8.0 | Pending |
| `WHATSAPP_BUSINESS_TOKEN` | Meta | App backend | Automated messaging (post-R1, optional) | Owner (future) | Not needed yet |
| `ANTHROPIC_API_KEY` | Anthropic | App backend | AI features (future, optional) | Owner (future) | Not needed yet |

---

## How to Add a New Credential

1. Add a row above (name, provider, purpose).
2. The **owner** obtains the value from the provider's dashboard (see `API-Keys-Guide.md`).
3. The value goes into hosting env vars or `.env.local` — NEVER into any committed file.
4. Update **Status**: `Pending` / `Configured` / `Expired` / `Rotated`.

---

## Connector Configurations

Project-specific integration modules and configs live in this `connectors/` directory.

- **wa.me WhatsApp links (R1):** no credentials required.
- **Zoho Projects (shared, optional):** `AI_Memory_Open/zoho-mcp-server/` — not configured for this project.

---

*Last updated: 2026-07-16 — initialized by PROJECT_MEMORY_INIT.md*
