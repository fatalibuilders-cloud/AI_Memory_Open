# Fatalibuilders Construction App

> **⚠️ TEMPORARY LOCATION:** This app is scaffolded inside the AI_Memory_Open repository at `app-src/fatalibuilders-app/` because the AI integration cannot create GitHub repositories. Once the owner creates the empty repository `fatalibuilders-cloud/fatalibuilders-app` on GitHub, this folder's contents move there (single push — nothing else changes) and this copy is removed. The CI workflow in `.github/workflows/` activates after migration.

A public product by **Fatali Builders**: enter your construction project data once — get material quantities, cost estimates, labor plans, 2D drawings, renders and engineering reports. Built on recognized design codes (Eurocodes, British Standards, KEBS). **One payment, $30, lifetime access.**

## Stack

Next.js (App Router) · TypeScript · Tailwind CSS · PWA · PostgreSQL (upcoming) · Vitest

## Development

```bash
npm install
npm run dev      # http://localhost:3000
npm run lint
npm test
npm run build
```

## Structure

```
src/
├── app/            # routes: marketing pages, app UI, api/
│   └── api/health  # health check endpoint
├── engines/        # calculation rule modules (pure TS, unit-tested)
│   ├── profiles/   # code profiles (Eurocode / BS / KEBS)
│   └── materials/  # material quantities engine (first building blocks)
public/             # PWA manifest + icons
```

Engine rules follow the project's architecture constitution: every function is unit-tested against **owner-engineer-validated worked examples** before release, and every output is stamped with its code profile.

## Project memory

Full context, release plan (29 stories), and decision history: `projects/FatalibuildersConstructionApp_AI_Training/` in the AI_Memory_Open repository.
