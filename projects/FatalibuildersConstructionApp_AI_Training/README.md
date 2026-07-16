# FatalibuildersConstructionApp — AI Training Memory

**Project:** FatalibuildersConstructionApp
**Owner:** Eng Ali Ahmed (fatalibuilders@gmail.com)
**Role:** Owner, Fatali Builders
**Created:** 2026-07-16
**Memory Version:** 1.1

---

## What Is This Folder?

This is the **AI context memory** for the FatalibuildersConstructionApp project — a public Fatalibuilders product ($30 lifetime access, worldwide, launched from Kenya) where users insert construction project data and get seven outputs: material quantities, cost estimate, labor/time estimate, 2D drawings, renders, preliminary structural drawings, and a geotechnical report.

It contains everything an AI assistant needs to understand the project, pick up where the last session left off, and execute work without losing context between sessions.

**This folder is NOT the project source code.** The app's source code lives in its own repository (created in Release 1.0, Epic 1). This folder is the structured knowledge base inside the `AI_Memory_Open` fork at `https://github.com/fatalibuilders-cloud/AI_Memory_Open`.

---

## How to Use This Memory

### Starting a Session
Execute `agents/open.md` — the session initialization protocol. It instructs the AI to read all context files in the correct order before doing any work.

> Say: "Execute open.md" or "Run the session initialization protocol"

### Ending a Session
Execute `agents/closure.md` — the session closure protocol. It instructs the AI to finalize session summaries, update decision logs, consolidate risks, update progress, and push to git.

> Say: "Execute closure.md" or "Run the session closure protocol"

---

## Folder Structure

| Folder/File | Purpose |
|-------------|---------|
| `agents/open.md` | Session start protocol — loads all context |
| `agents/closure.md` | Session end protocol — saves all progress |
| `agents/plan-release.md` | Iterative release planning protocol |
| `Master-AI-Context.md` | Master AI instructions, progress, commands, execution model |
| `NextSteps.md` | Prioritized roadmap, completed/pending work |
| `Key-Decisions.md` | Index of all architectural decisions (keyword searchable) |
| `Sessions.md` | Index of all session summaries (keyword searchable) |
| `Risk-Registry.md` | Consolidated risk summary with severity levels |
| `session-summary/` | Timestamped session summary files |
| `decisions-learnings/` | Timestamped decision & learning files |
| `Marketing/` | Launch materials, landing page copy, promotional content |
| `Security/` | Risk reports, security audits, compliance docs |
| `Finance/` | Revenue tracking, unit economics, budgets |
| `Legal/` | Terms of service, privacy policy, refund policy, engineering disclaimers |
| `Product_Development/FatalibuildersApp/` | Architecture, module map, production instructions |
| `Product_Development/Releases/` | Versioned build instruction documents + Bugs.md |
| `Executive/` | Strategic plans, progress reports |
| `Operations/` | Runbooks, incident reports |
| `TechSupport/` | Support playbooks, FAQ documents, known issues |
| `People-n-Culture/` | Team/HR documents (future) |
| `connectors/` | API key inventory (names only, never values) |
| `assets/` | Design specs, images, content documents |
| `{Department}/agents/` | Domain-expert agents (AGENT.md operational, advisor.md strategic) |

---

## Quick Reference

- **Tech Stack:** Mobile-first PWA — Next.js (React) + TypeScript, PostgreSQL, S3-compatible object storage; per-code-profile calculation rule modules; SVG/three.js output engines
- **AI Execution Model:** Direct execution (Claude Code) with `[AI]` / `[Human]` / `[AI+Human]` story labels
- **Zoho Project:** Not configured (no enterprise OS selected; section reserved for future use)
- **Current Release:** 1.0 — Sellable Core (`Product_Development/Releases/fatalibuilders-app-build-instructions-1_0.md`)

---

## Bug & Change Request Tracking

Any change to the codebase, file structure, release plans, or environments that happens **outside** a formal release story is logged in `Product_Development/Releases/Bugs.md`.

- **Naming:** `bug-[Current Release]-[YYYY-MM-DD]-[HHMM]` (e.g., `bug-1.0-2026-08-01-1430`)
- **Labels:** `[AI]`, `[Human]`, `[AI + Human]` — same as release stories
- **Statuses:** Open → In Progress → Complete
- **Metrics:** Summary table at the bottom of Bugs.md; read at session init, updated at closure

---

*FatalibuildersConstructionApp AI Memory — initialized 2026-07-16*
