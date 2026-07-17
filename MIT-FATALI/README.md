# MIT-FATALI

MIT-FATALI is an open-source mobile-first platform combining student financial literacy and household micro-savings with an image + SMS agricultural advisory triage system.

This repository contains a monorepo scaffold: frontend (React PWA), backend (Fastify + TypeScript), payment adapters, docs and infra to get started.

Quickstart (local dev)
1. Install Docker and Docker Compose.
2. Copy .env.example to .env and set local values (DB, REDIS). Do NOT add secrets to the repo.
3. Start local dev stack:

   docker-compose up --build

4. Backend: http://localhost:4000
   Frontend: http://localhost:3000

Docs: see docs/MIT-FATALI-Project-Report.md for full project report.

Contributing
See CONTRIBUTING.md for developer onboarding and run instructions.
