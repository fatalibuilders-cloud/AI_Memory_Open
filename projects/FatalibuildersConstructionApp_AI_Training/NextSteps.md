# NextSteps.md — FatalibuildersConstructionApp

**Last Updated:** 2026-07-16
**Current Status:** Project memory initialized. Release 1.0 (Sellable Core) planned — awaiting first build session.
**Active Executor:** Direct AI execution (Claude Code) with [AI]/[Human]/[AI+Human] story labels.

---

## Immediate Next Steps

### 1. First Build Session
- [ ] **Run `agents/open.md`** to load context
- [ ] **Begin Release 1.0, Epic 1:** CORE-1.0 (scaffold the `fatalibuilders-app` repository) — pure [AI], no owner action needed
- [ ] Continue CORE-1.1 → hosting choice; the owner's first checkpoint is creating the hosting account (plain-language steps will be provided)

### Release 1.0 — Sellable Core (0%)
**File:** `Product_Development/Releases/fatalibuilders-app-build-instructions-1_0.md`

| Epic | Name | Stories |
|:---:|:---|:---:|
| 1 | Foundation & Infrastructure | 4 |
| 2 | Accounts & Access | 3 |
| 3 | Payments ($30 Lifetime) | 4 |
| 4 | Project Data Input (Residential) | 3 |
| 5 | Calculators | 4 |
| 6 | Outputs & Sharing | 4 |
| 7 | Product Site & Onboarding | 4 |
| 8 | Launch Readiness | 3 |

**Owner actions coming up (no rush, will be prompted at the right story):**
- CORE-1.1: create the hosting account
- CORE-2.1: create the email service account
- CORE-3.0: sign up with the card payment provider (ID + bank details needed)
- CORE-3.2: sign up with the M-Pesa gateway
- CORE-5.x: validate the engineering worked examples (quantities, rates)
- CORE-7.2: review the legal pages

---

## Risk Mitigation

- **RISK-002 (High, calculator accuracy):** enforced inside CORE-5.x acceptance criteria — no engine ships without owner-validated worked examples.
- **RISK-001 (High, engineering outputs):** no action in R1; MUST gate Release 3.0 planning (plan-release.md enforces).

---

## Backlog (Future Work)

- Release 2.0 — See It: 2D drawings, renders
- Release 3.0 — Engineering: structural drawings + geotech report (legal gate)
- Release 4.0 — Run the Job: job tracking, crew scheduling, daily site logs
- Excel import (mapping wizard) for existing estimate spreadsheets
- WhatsApp Business API (automated messages)
- Additional construction types beyond residential; US code profiles
- Multi-language UI

---

## Bug & Change Request Tracking

All ad-hoc changes are tracked in **`Product_Development/Releases/Bugs.md`**.

| Metric | Count |
|--------|-------|
| Total Logged | 0 |
| Open | 0 |
| In Progress | 0 |
| Complete | 0 |

**Open Bugs:** None

---

## Session Management (Run at End of Every Session)

Use `agents/closure.md`: finalize session summary + decisions log, update risk registry, story statuses, Bugs.md metrics, this file, Master-AI-Context, then push to git.

---

*This file is the primary entry point for "what do I work on next?" — updated every session by the closure protocol.*
