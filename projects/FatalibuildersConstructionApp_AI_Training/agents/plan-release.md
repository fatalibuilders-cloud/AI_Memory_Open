# plan-release.md — Iterative Release Planning Protocol — FatalibuildersConstructionApp

**Purpose:** Execute when it is time to plan a new release. Reviews project state, consolidates outstanding tasks and risks, asks the owner targeted questions, and generates a structured release file in `Product_Development/Releases/` with incremental naming.

**Planned release skeleton (from staging, owner-approved):** 2.0 "See It" (2D drawings, renders) → 3.0 "Engineering" (structural + geotech, LEGAL GATE before ship) → 4.0 "Run the Job" (job tracking, crew scheduling, site logs).

---

> **Prompt for AI:** "Execute the Release Planning protocol:
>
> ## Phase A: Gather Context (autonomous)
> 1. `FatalibuildersConstructionApp_architecture.md` — design, stack, constraints
> 2. `Master-AI-Context.md` — progress, infrastructure, execution model
> 3. `Risk-Registry.md` — ALL Critical/High risks must be addressed or explicitly deferred with justification
> 4. `NextSteps.md` — pending tasks, backlog, risk mitigation items
> 5. `Product_Development/Releases/` — read the most recent release file: planned vs completed, [IN-PROGRESS] carry-forwards, last epic number, last story prefix
> 6. `Key-Decisions.md` keyword index — decisions affecting planning
> 7. Two most recent session summaries — momentum and blockers
>
> ## Phase B: Determine Version
> Increment from existing releases (`1_0` → next `2_0`, minor fixes `1_1`). Naming: `fatalibuilders-app-build-instructions-{version}.md`.
>
> ## Phase C: Ask the Owner (plain language, no jargon)
> C.1 State summary (last release %, carry-forwards, open risks, pending tasks) — confirm accuracy
> C.2 Release focus
> C.3 Codename (or 'auto')
> C.4 New features/requirements to include
> C.5 Human dependencies (accounts, keys, validations, legal reviews)
> C.6 Constraints (story cap, deadline, exclusions)
> **Special gates:** Release 3.0 planning MUST include the legal-review stories for engineering disclaimers and the owner-engineer rule-set validation stories.
>
> ## Phase D: Build the Release File (autonomous)
> Header (version, codename, prefix, epic continuation, predecessor) · Epic Overview table · granular stories with ID `{PREFIX}-{Epic}.{Story}`, label, description, acceptance criteria · carry-forward stories renumbered with original ID noted · one story (or mitigation) per Critical/High risk · story count summary by label.
>
> ## Phase E: Update Project Files
> 1. NextSteps.md — new release section
> 2. Master-AI-Context.md §10 — new release at 0%
> 3. Report the plan to the owner (epics, counts, file path)
>
> **Important:** Never modify previous release files. Never begin executing stories — the owner must explicitly say 'begin'."

---

*Execute this file by saying: "execute plan-release.md" or "plan the next release"*
