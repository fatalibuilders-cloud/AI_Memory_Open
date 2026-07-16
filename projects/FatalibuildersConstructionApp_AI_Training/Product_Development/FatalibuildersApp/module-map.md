# Module Map — FatalibuildersConstructionApp

**Document Purpose:** Maps the logical architectural modules of FatalibuildersConstructionApp to their physical directory locations within the app codebase (`fatalibuilders-app` repository, created at CORE-1.0).

**Last Updated:** 2026-07-16

---

## Planned Module Structure (target for CORE-1.0 scaffold)

```text
fatalibuilders-app/
├── src/
│   ├── app/                    # Next.js routes: marketing pages, app UI, api/
│   │   ├── (marketing)/        # landing, pricing, legal
│   │   ├── (app)/              # wizard, results, account
│   │   └── api/                # auth, projects, results, exports, payments, webhooks
│   ├── engines/                # calculation rule modules (pure TS, unit-tested)
│   │   ├── profiles/           # code profiles: eurocode/, bs/, kebs/, us/ (later)
│   │   ├── materials/          # quantities engine
│   │   ├── cost/               # cost estimation engine (+ price tables)
│   │   └── labor/              # labor & time engine
│   ├── documents/              # PDF / XLSX generation, disclaimer blocks
│   ├── db/                     # schema, migrations, data access
│   └── lib/                    # auth, entitlements, currency, sharing (wa.me/tel:)
├── public/                     # PWA manifest, icons
└── tests/                      # engine worked-example tests, API tests
```

## Key Files

| File | Purpose |
|------|---------|
| *(populated as files are created)* | |

## Production Deployment Mapping

| Component | Source | Production Host | Domain | Status |
|-----------|--------|----------------|--------|--------|
| *(populated as infrastructure is provisioned)* | | | | |

---

*Updated every session by the closure protocol when source structure changes.*
