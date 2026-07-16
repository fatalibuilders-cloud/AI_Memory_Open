# open.md — Session Initialization Protocol (FatalibuildersConstructionApp — Staging)

**Purpose:** Execute this protocol at the start of any AI session working on the **FatalibuildersConstructionApp staging project**. This is a project-level protocol — for work on the AI Memory system itself, use the root `AI_Memory_Open/agents/open.md` instead.

---

> **Prompt for AI:** "Execute the FatalibuildersConstructionApp staging session initialization:
>
> 0. **Sync from Git:** Pull the latest repository state before doing anything else.
>
> 1. **Read Master Context First:** Read `Master-Context.md` in this folder. It contains the project vision, staging roadmap, document templates, current progress, and the Available Agents index.
>
> 2. **Read Current State:**
>    - `NextSteps.md` — staging progress, blockers, and open questions
>    - `Key-Decisions.md` — decision keyword index (drill into `decisions-learnings/` files on keyword match)
>    - `Sessions.md` — session history index
>
> 3. **Consult Domain Agents:** Before working on any task that touches a domain listed in the Available Agents table in Master-Context.md, read the relevant `{Department}/agents/{Source}-advisor.md` (strategic guidance) and/or `{Source}-AGENT.md` (operational workflows).
>
> 4. **Create Live Decision Log:** Create `decisions-learnings/Key-Decisions-[YYYY-MM-DD]_[HHMM].md` using the template in `decisions-learnings/session-protocol.md`. Update it incrementally after every significant decision — do NOT wait until the end of the session.
>
> 5. **Ask the user what to work on** (or continue from the "Next Action" items in NextSteps.md if running autonomously):
>    - Document 1 (Project Context) — vision, goals, users, metrics, constraints
>    - Document 2 (Architecture/Design) — system design, tech stack, integrations, security
>    - Document 3 (Release Plan) — epics, stories, milestones, risks
>
> 6. **Standing rule:** Update Master-Context.md status fields and NextSteps.md incrementally as sections are completed.
>
> **Important:** Do NOT begin modifications until this protocol is complete. When the session ends, execute `agents/closure.md`."

---

## Current Staging Status Snapshot

*Updated by the closure protocol.*

- **PRODUCT DIRECTION (owner, 2026-07-16):** Public Fatalibuilders app — anyone logs in, inserts construction data, gets results; **$30 one-time lifetime access**.
- **Document 1 (Project Context):** In Progress — vision/audience/business model owner-confirmed. **BLOCKING: core tool definition (what data in, what results out) and whether management features stay (Epic 5).**
- **Document 2 (Architecture/Design):** In Progress — integration-first; auth + payment provider added; Excel export priority 1, WhatsApp share priority 2.
- **Document 3 (Release Plan):** Epics restructured: 1) Accounts & Payment, 2) Core Tool, 3) Output & Sharing, 4) Product Site, 5) management features (pending).
- **Top blocker:** Core tool definition from owner.
