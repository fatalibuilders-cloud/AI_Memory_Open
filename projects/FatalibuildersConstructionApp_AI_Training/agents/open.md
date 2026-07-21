# open.md — Session Initialization Protocol — FatalibuildersConstructionApp

**Purpose:** Execute this file at the start of every AI session on FatalibuildersConstructionApp to load full project context before doing any work.

---

> **Prompt for AI:** "Execute the Session Initialization protocol from open.md:
>
> 0. **Sync AI Memory from Git:** `git pull` in the AI_Memory_Open repository root. The canonical repo is **https://github.com/fatalibuilders-cloud/AI_Memory_Open** — this project lives at `projects/FatalibuildersConstructionApp_AI_Training/`. Clone it first if absent.
>
> 1. **Clear Stale Memory:** Delete session-memory notes about project state/architecture/decisions (maintained here, not in assistant memory). Retain user-preference memories only (owner communication style: jargon-free, explicit action lists — see root `contacts/Eng-Ali-Ahmed.md`).
>
> 2. **Read Core Context Files (Tier 1), in order:**
>    - `Master-AI-Context.md`
>    - `Product_Development/FatalibuildersApp/FatalibuildersConstructionApp_architecture.md`
>    - `Product_Development/FatalibuildersApp/module-map.md`
>
> 3. **Read Current State:**
>    - `NextSteps.md`
>    - The active release file in `Product_Development/Releases/` (current version per NextSteps.md; at initialization: `fatalibuilders-app-build-instructions-1_0.md`)
>
> 4. **Read Key-Decisions.md** (index only; drill into `decisions-learnings/` on keyword match).
>
> 5. **Read Sessions.md** (index only; drill into `session-summary/` when prior work may exist).
>
> 6. **Read the two most recent files in `session-summary/`.**
>
> 7. **Read Risk-Registry.md** — check Critical/High risks affecting planned work.
>
> 8. **Create Live Session Files** (update incrementally all session):
>    a) `session-summary/AI-Session-Summary-[YYYY-MM-DD]_[HHMM].md` — What Was Done / Stories Completed / Key Decisions / Blockers / Environment State
>    b) `decisions-learnings/Key-Decisions-[YYYY-MM-DD]_[HHMM].md` — Decisions / Learnings
>    c) Standing instruction: append after EVERY significant action, in real time.
>
> 9. **If build/deploy likely:** read `Product_Development/FatalibuildersApp/production-instructions.md` FIRST.
>
> 10. **If UI/design work:** check `assets/content-images/designandcontent/`.
>
> 11. **If integrations work:** read `connectors/api-key-store.md`.
>
> 11a. **Review the Agent Index** (Master-AI-Context §8); consult `{Department}/agents/` files whenever the task touches their domain.
>
> 11b. **Read the Metrics table** at the bottom of `Product_Development/Releases/Bugs.md` (metrics only). Note Open/In-Progress bugs.
>
> 12. **Summarize your understanding:** project + phase, last session's work, immediate next steps, blockers, Critical/High risks, bug metrics. Ask what to work on, or continue from NextSteps.md if running autonomously.
>
> **Important:** No file modifications until this protocol completes. Don't read every file in subdirectories — indexes + 2 latest summaries only. Missing file → note and continue."

---

## Zoho Projects Integration

Not configured for this project (no enterprise OS selected at system setup). The shared connector at `AI_Memory_Open/zoho-mcp-server/` can be configured later if the owner adopts Zoho; this section is the placeholder for portal/project IDs.

---

*Execute this file by saying: "execute open.md" or "run the session initialization protocol"*
