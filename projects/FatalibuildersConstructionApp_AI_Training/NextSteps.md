# NextSteps.md — FatalibuildersConstructionApp

**Last Updated:** 2026-07-16
**Current Status:** Project memory initialized. Release 1.0 (Sellable Core) planned — awaiting first build session.
**Active Executor:** Direct AI execution (Claude Code) with [AI]/[Human]/[AI+Human] story labels.

---

## Immediate Next Steps

### 1. Owner action — create the app's GitHub repository (5 minutes, whenever convenient)
The AI cannot create repositories, so this one needs you:
1. Go to **https://github.com/new** (logged in as `fatalibuilders-cloud`)
2. Repository name: **`fatalibuilders-app`** (exactly this)
3. Choose **Private** (recommended for now — can be changed later)
4. Do NOT tick any of the "initialize" checkboxes (no README, no .gitignore, no license) — leave it completely empty
5. Click **Create repository** — done. Tell the AI "the repo is created" in any session and it will move the code over automatically.
*(Development is NOT blocked while you wait — the app lives temporarily at `app-src/fatalibuilders-app/` in this repository.)*

### 2. Next build session
- [x] ~~CORE-1.0 scaffold~~ **BUILT & VERIFIED 2026-07-16** (8/8 tests, lint, build, health check ✅) — [DONE] after repo migration
- [x] ~~CORE-1.3 base app shell~~ **[DONE] 2026-07-16** (header/footer/pricing placeholder/error/loading/404, all routes verified live)
- [x] ~~CORE-2.0 signup & login~~ **[DONE] 2026-07-16** (argon2 + sessions + pages; 16/16 tests; live smoke test ✅; prod wiring at CORE-1.2)
- [x] ~~CORE-4.0/4.1/4.2~~ **[DONE] 2026-07-23 — Epic 4 complete.** Data model + 6-step wizard + code profiles; 25/25 tests; live end-to-end verified
- [x] ~~CORE-5.0~~ **[DONE — OWNER-VALIDATED 2026-07-23]** (corrections applied: foundation 1.5 m, plaster 15-20 mm; engine v0.2.1)
- [~] **CORE-6.0** — materials results view done; cost/labor views land with CORE-5.1/5.2
- [ ] **CORE-5.1** — cost estimation engine (needs owner-approved baseline Kenyan unit rates)
- [ ] **CORE-5.2** — labor & time engine
- [ ] **CORE-2.2** — entitlement & preview gating (pure [AI])
- [ ] **CORE-1.1** — hosting platform: AI recommends, then the owner's checkpoint is creating the hosting account
- [ ] **MKT-1/MKT-2** — brand kit (from saved banner) + launch kit
- [ ] Design task: align app theme to the navy brand banner (currently amber placeholder)

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

## Marketing Workstream (added 2026-07-16 — owner request: automated marketing system)

Plan: `Marketing/Marketing-Automation-Plan.md`. Stage A (AI content engine: brand kit, launch kit, 90-day calendar, email sequences) runs alongside R1 development; Stage B (auto-publishing on owner's Meta/email accounts) activates launch month; Stage C (in-product growth loops) ships inside R1 stories CORE-6.2/6.3/7.1/8.0.
- [ ] MKT-1 [AI] Brand kit · MKT-2 [AI] Launch kit · MKT-3 [AI] 90-day calendar · MKT-4 [AI] email sequences · MKT-5 [AI+Human] scheduler on owner's accounts (launch month)

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
