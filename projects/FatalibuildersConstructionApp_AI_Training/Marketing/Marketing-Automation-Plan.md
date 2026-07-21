# Marketing Automation System — FatalibuildersConstructionApp

**Owner:** Eng Ali Ahmed (Fatali Builders)
**Created:** 2026-07-16
**Status:** Approved plan — Stage A executes alongside Release 1.0; Stages B-C activate at launch
**Advisors consulted:** Marketing AGENT (campaign planning, content engine, email sequences), Growth-n-Revenue advisor (channels, funnel, unit economics)

---

## What "Automated Marketing" Means Here — Honest Version

An automated marketing system has three layers. Two can be built by AI alone; one needs accounts only the owner can create:

| Layer | What it does | Who can build it | When |
|---|---|---|---|
| **A. Content engine** | AI produces all marketing assets on a schedule: social posts, blog articles, WhatsApp broadcast copy, email sequences, launch kit | ✅ AI alone, starting now | During R1 build |
| **B. Distribution automation** | Assets publish themselves: scheduled social posts, automatic emails, WhatsApp broadcasts | AI builds it, but it runs on the **owner's accounts + API keys** (Meta/Facebook, email service, scheduling tool) | Set up in launch month |
| **C. In-product growth loops** | The app markets itself: free preview → upgrade prompts, share-your-estimate WhatsApp loop (every shared PDF/quote carries Fatalibuilders branding + link), referral hooks | ✅ AI alone — it's product code (already partly in R1: free preview CORE-7.1, WhatsApp share CORE-6.3) | R1 stories |

**Why not switch everything on today:** automated posting with nothing to sell sends traffic to a "coming soon" page and wastes the one-time attention of a launch. Correct sequencing: build the content engine now → warm-up content 2-3 weeks pre-launch → full automation at launch.

---

## The System Design

### Stage A — Content Engine (AI-built, starts now)
1. **Brand kit** — voice, messaging pillars, visual language from the owner's brand banner: *"Build Better. Manage Smarter."*, navy-blue identity, builder-first tone. → `Marketing/Brand-Kit.md`
2. **Launch kit** — landing page copy (feeds CORE-7.0), app store–style description, 10 launch social posts, WhatsApp broadcast message, press-style announcement. → `Marketing/Launch-Kit/`
3. **Evergreen content calendar** — 90 days of post templates in three recurring formats builders actually engage with: *"How much cement does a 3-bedroom house need?"* (calculator teasers), before/after estimate stories, code-profile explainers. → `Marketing/Content-Calendar.md`
4. **Email sequences** — welcome (signup→first calculation), upgrade nudge (preview→$30), post-purchase onboarding. Wired into the app at CORE-2.1/8.0.

### Stage B — Distribution Automation (needs owner accounts, launch month)
| Channel | Tool | Owner provides | Monthly cost |
|---|---|---|---|
| Facebook + Instagram (primary for Kenyan construction audience) | Meta Business Suite scheduler (free) or Buffer (free tier) | Facebook Business account login | $0 |
| WhatsApp broadcasts | WhatsApp Business app broadcast lists (manual-ish) → Business API later | Existing WhatsApp Business | $0 |
| Email automation | Same provider as app transactional email (Resend/similar) | Account already created at CORE-2.1 | $0 at small scale |
| TikTok/YouTube Shorts (calculator demo clips) | Optional, phase 2 | Account if wanted | $0 |

AI prepares every post; the scheduler publishes them; the owner approves batches weekly (15 minutes) — approval stays human, publishing is automatic.

### Stage C — In-Product Growth Loops (product code)
- Every exported PDF/Excel and WhatsApp share carries Fatalibuilders branding + link → **each user's quote markets the app to their client** (CORE-6.2/6.3 — being built anyway)
- Free preview → upgrade funnel with measured conversion (CORE-7.1 + CORE-8.0 analytics)
- Post-launch: referral incentive experiment (e.g., share-with-3-builders unlock) — plan-release.md item for R2

### KPIs (Growth advisor framework)
Visitors → previews run → signups → purchases ($30) · content engagement per channel · share-loop coefficient (shares per paying user). Reviewed monthly against the funnel in CORE-8.0 analytics.

---

## Decision Requested From Owner (later, not now)
1. At launch month: create the Facebook Business account (or confirm existing) — the only account Stage B strictly needs on day one.
2. Confirm the primary social channel guess (Facebook/Instagram + WhatsApp for Kenya; LinkedIn optional for pro audience).

---

## Execution Queue (added to project backlog)
- [ ] MKT-1 [AI]: Brand-Kit.md from the owner's banner
- [ ] MKT-2 [AI]: Launch-Kit (landing copy → CORE-7.0, 10 posts, WhatsApp broadcast, announcement)
- [ ] MKT-3 [AI]: 90-day content calendar
- [ ] MKT-4 [AI]: Email sequence copy (wired in at CORE-2.1/8.0)
- [ ] MKT-5 [AI+Human]: Scheduler setup on owner's Meta account (launch month)

---

*Maintained by the Marketing workstream. Consult `Marketing/agents/Marketing-AGENT.md` before executing content work.*
