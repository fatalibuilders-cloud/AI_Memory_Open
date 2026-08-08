# Social Automation Engine — design & rollout

**For:** Eng Ali Ahmed · **Purpose:** an in-app "back engine" that generates and
publishes marketing content to **Instagram, LinkedIn, and TikTok**.

> **Security:** platform tokens and secrets live only in environment variables
> (Vercel), never in git — same rule as the payment keys.

---

## 1. Architecture (fits the existing Next.js + Postgres + Vercel stack)

```
 app data ──► content engine ──► post queue ──► scheduler (cron) ──► adapters ──► platform APIs
 (estimates,   (auto-writes      (social_posts   (/api/social/       (instagram/
  completeness  captions)         table)          publish)            linkedin/tiktok)
  %, diary…)
```

- **Content engine** (`src/engines/social/content.ts`) — the unique part: turns
  the app's own data into post captions (the completeness hook, price/value,
  tips, sample-estimate highlights). Generic schedulers can't do this.
- **Post queue** (`social_posts` table) — body, media URL, target platforms,
  scheduled time, status, per-platform results.
- **Adapters** (`src/lib/social/adapters/*`) — one per platform behind a common
  `configured()` + `publish()` interface. **Real API call when its token is set;
  mock/preview otherwise** (the mock-until-keys pattern, same as payments).
- **Scheduler** — Vercel Cron calls `/api/social/publish` (guarded by
  `SOCIAL_CRON_SECRET`); it publishes due posts and records results.
- **Admin composer** (`/admin/social`) — compose/schedule posts, see the queue
  and auto-generated suggestions. Admin-gated.

Tokens are read from env (one account per platform) — simplest and consistent
with payments. Multi-account OAuth (a `social_accounts` table + connect flow) is
the later upgrade; see §4.

---

## 2. Per-platform access (owner-gated — the real prerequisites)

Each needs an approved developer app + a business account + review. Start these
early; approval takes days–weeks.

### Instagram (Graph Content Publishing API)
- Needs an **Instagram Business or Creator account** linked to a **Facebook Page**.
- Create a **Meta app** (developers.facebook.com) → add Instagram Graph API →
  request `instagram_content_publish`, `pages_read_engagement` → App Review.
- Publishing is 2 steps: create a media container (`POST /{ig-user-id}/media`
  with `image_url` + `caption`) then publish it (`POST /{ig-user-id}/media_publish`).
  **The image/video must be at a public URL.**
- Env: `IG_ACCESS_TOKEN` (long-lived), `IG_BUSINESS_ACCOUNT_ID`.

### LinkedIn (Posts API — friendliest)
- Create a **LinkedIn app**, associate a **Company Page**, request the
  **Community Management API** / `w_organization_social`.
- Post: `POST https://api.linkedin.com/rest/posts` with author
  `urn:li:organization:<id>`, commentary text.
- Env: `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_ORG_URN`.

### TikTok (Content Posting API — strictest, video-only)
- Create a **TikTok for Developers** app → Content Posting API → audit.
- **Video only** — text/image posts don't apply; needs a rendered video asset.
- Env: `TIKTOK_ACCESS_TOKEN`. (Treat as phase 2; needs a video pipeline.)

---

## 3. Rollout

1. **Now:** build the engine with adapters in mock/preview — compose, schedule,
   auto-generate captions, export/copy to post manually or via Buffer/Metricool.
2. **LinkedIn first** (easiest approval) → set its token → live posting.
3. **Instagram** next (needs the business account + public media URLs).
4. **TikTok** last (needs a video-generation step).

Live posting switches on **per platform** the moment its token is set — no
redeploy of logic, just the env var.

## 4. Later upgrades

- **Multi-account OAuth** — `social_accounts` table + per-platform connect flow +
  token refresh, so non-technical staff connect accounts from the UI.
- **Media generation** — auto-render branded images (estimate cards) and short
  videos (for TikTok/Reels) from project data.
- **Analytics back-read** — pull post reach/engagement to close the loop.

## 5. Honest scope

The code is the easy part; **platform approval + business accounts are the gate**
and only the owner can clear them. TikTok in particular needs a video pipeline
before it does anything. Build order above front-loads the value (content engine
+ LinkedIn) and defers the heaviest dependency (TikTok video).

*App integration: `src/engines/social/`, `src/lib/social/`,
`src/app/api/social/publish/`, `/admin/social` in `fatalibuilders-app`.*
