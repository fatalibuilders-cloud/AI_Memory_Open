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

> **Current physical location (temporary):** `AI_Memory_Open/app-src/fatalibuilders-app/` — moves to its own repository `fatalibuilders-cloud/fatalibuilders-app` once the owner creates it (see NextSteps).

## Key Files

| File | Purpose |
|------|---------|
| `package.json` | Scripts: dev, build, start, lint, test |
| `src/app/layout.tsx`, `src/app/page.tsx` | App shell + placeholder landing page |
| `src/app/api/health/route.ts` | Health check endpoint |
| `src/engines/profiles/index.ts` | Code profiles (Eurocode/BS/KEBS) + document stamp helper |
| `src/engines/materials/index.ts` | Materials engine v0.1.0: concreteVolume, concreteMaterials (1:2:4 mix), wallBlocks |
| `src/engines/materials/materials.test.ts` | 8 unit tests incl. 1 m³ worked example (owner validation pending, CORE-5.0) |
| `public/manifest.webmanifest`, `public/icon.svg` | PWA installability |
| `.github/workflows/ci.yml` | CI: lint + test + build (activates after repo migration) |
| `vitest.config.ts`, `eslint.config.mjs`, `tsconfig.json` | Tooling config |

## Production Deployment Mapping

| Component | Source | Production Host | Domain | Status |
|-----------|--------|----------------|--------|--------|
| *(populated as infrastructure is provisioned)* | | | | |

---

*Updated every session by the closure protocol when source structure changes.*
