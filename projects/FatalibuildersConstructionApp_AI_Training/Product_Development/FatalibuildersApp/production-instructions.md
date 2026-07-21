# Production Instructions — FatalibuildersConstructionApp

**Document Purpose:** Master production deployment guide. Tells any AI executor exactly how to build, configure, and deploy every component. Updated every session with the latest working commands.

**Last Updated:** 2026-07-16

---

## 1. Deployment Architecture Overview

*To be filled as infrastructure is provisioned (CORE-1.1 / CORE-1.2).*

| Layer | Hosting | Provider | Purpose |
|-------|---------|----------|---------|
| Web app + API | *TBD (Vercel/Railway/Fly.io — chosen at CORE-1.1)* | *TBD* | Next.js PWA + API routes |
| Database | *TBD* | *TBD* | Managed PostgreSQL |
| File storage | *TBD* | *TBD* | Generated documents |

---

## 2. Build & Deploy Steps

*No deployments recorded yet. Updated by the closure protocol after every build or deploy attempt — successful or failed.*

---

## 3. Known Build Gotchas

*None yet. Failures and fixes are documented here so future sessions never repeat mistakes.*

---

## 4. Required Access Keys

See `../../connectors/api-key-store.md` for the credential inventory. Secrets live in hosting env vars — never in git.

---

*Single source of truth for production deployment. Update as infrastructure evolves.*
