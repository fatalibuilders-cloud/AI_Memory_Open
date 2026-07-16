# Master AI Context — AI Memory System (Root Level)

**Document Purpose:** This is the primary operational context file for any AI assistant working on the **AI Memory system itself** — its structure, standards, policies, shared resources, cross-project coordination, and infrastructure. This is NOT a project-level context file. Each project has its own `Master-AI-Context.md` inside its `{ProjectName}_AI_Training/` folder.

**Memory Design Version:** 1.1
**Last Updated:** 2026-07-16
**System Owner:** Eng Ali Ahmed (fatalibuilders@gmail.com)
**Organization:** Fatali Builders
**Repository:** https://github.com/fatalibuilders-cloud/AI_Memory_Open

---

## Governing Standards

**Standards and Policy:** The two standards below govern ALL operations and ALL communications across every project in this system. They are the authoritative root copies. Each project has local copies in its own `Standards and Policy/` folder.

**Operating Standard:** [CC/DE Operating Standard v2.0](Standards%20and%20Policy/CCDE-Operating-Standard.md) — Governs ALL operations: project management, financial controls, agent network management, CRM contact tracking, reporting cadences, and decision-making authority. **This is the master copy. When updating, propagate changes to all project `Standards and Policy/` folders.**

**Communication Standard:** [Adaptive Communication Standard v1.0](Standards%20and%20Policy/Communication-Standard.md) — Governs ALL communications: message composition, stakeholder management, DISC/OCEAN profiling, information delivery pacing, channel selection, and difficult news delivery. **This is the master copy. When updating, propagate changes to all project `Standards and Policy/` folders.**

**Contact Profiles:** `contacts/` — Per-person markdown files containing DISC style, OCEAN indicators, cultural context, observed communication patterns, relationship trust account status, and cross-project utility assessments. Template: `contacts/_PROFILE-TEMPLATE.md`. AI assistants MUST consult a contact's profile before composing any significant message to them.

**CRM:** If configured, contacts can be tracked in your CRM with tags per CC/DE Section 7 (Project Tags, Role Tags, Specialty Tags, Geographic Tags).

---

## 1. System Overview

AI_Memory_Open is a **persistent memory system for AI assistants**. It stores structured project knowledge in markdown files committed to git, so any AI assistant (Claude, Gemini, or any LLM) can load full project context at the start of a session and pick up exactly where the last one left off.

The system operates at two levels:

**Root Level (this context)** — Manages the memory system itself: standards, policies, shared resources, project scaffolding, cross-project coordination, and system-level infrastructure. Sessions at this level use the root `agents/open.md` and `agents/closure.md`.

**Project Level** — Each project has its own independent workspace (`{ProjectName}_AI_Training/`) with its own Master-AI-Context.md, architecture docs, session tracking, and release management. Sessions at this level use the project's own `agents/open.md` and `agents/closure.md`.

---

## 2. Project Portfolio

| Project | Folder | Type | Status | Description |
|---------|--------|------|--------|-------------|
| FatalibuildersConstructionApp | `projects/staging/FatalibuildersConstructionApp/` | Software (public product) | Staging (Document 1 nearly complete) | Public Fatalibuilders app, $30 lifetime access: project data in → material quantities, cost & labor estimates, 2D drawings, renders, preliminary structural drawings, geotech report. Excel export + WhatsApp share |

---

## 3. Directory Structure

> **CRITICAL — FOLDER TYPE DISTINCTION:**
> When looking at the root AI_Memory_Open directory, AI assistants MUST distinguish between **system folders** (supporting the AI Memory infrastructure) and **project folders** (inside `projects/`, independent project workspaces). System folders are NOT projects. Project folders have their own session protocols and should not be modified during root-level sessions unless doing cross-project work.

```
AI_Memory_Open/
├── ─── SYSTEM FILES (Root Level) ───
├── Master-AI-Context.md              # THIS FILE — system-level operational context
├── README.md                         # Repository documentation and memory design explanation
├── Standards and Policy/             # Root-level MASTER COPIES of governing standards
│   ├── CCDE-Operating-Standard.md    # CC/DE v2.0 — MASTER COPY (propagate changes to projects)
│   ├── CCDE-Operating-Standard-v2.0.docx # Word document version
│   ├── CCDE-Management-Standard-v1.0.docx # Historical v1.0 Word document
│   └── Communication-Standard.md     # ACS v1.0 — MASTER COPY (propagate changes to projects)
├── setup-AI-Memory.md                # One-time first-run initialization protocol (Step 1)
├── staging.md                        # Per-project ideation and planning protocol (Step 2)
├── PROJECT_MEMORY_INIT.md            # Per-project full build protocol (Step 3)
├── .gitignore                        # Git ignore rules
│
├── ─── SYSTEM FOLDERS ───
├── agents/                           # Root-level session lifecycle protocols
│   ├── open.md                       # Session initialization (for system-level work)
│   └── closure.md                    # Session closure (for system-level work)
├── session-summary/                  # Timestamped system-level session summaries
├── decisions-learnings/              # Timestamped system-level decision logs
├── contacts/                         # Contact profiles (DISC/OCEAN/cultural profiling)
│   └── _PROFILE-TEMPLATE.md          # Template for new profiles
├── Memory_Agents/                    # Source-of-truth for domain expert agents deployed to projects
├── Model_Validation/                 # AI model validation and white papers
├── zoho-mcp-server/                  # Reference Zoho MCP connector (requires configuration)
│
├── ─── SESSION TRACKING (Root Level) ───
├── Key-Decisions.md                  # System-level decision keyword index
├── Sessions.md                       # System-level session keyword index
├── Risk-Registry.md                  # System-level risk tracking
├── NextSteps.md                      # System-level priority queue
│
├── ─── PROJECT FOLDERS (Independent Workspaces) ───
├── projects/                         # All project workspaces live here
│   ├── {YourProject}_AI_Training/    # ← Created by PROJECT_MEMORY_INIT.md
│   └── staging/
│       └── {YourProject}/            # ← Created by staging.md
```

---

## 4. Memory Design — Lazy Loading Pattern

The system uses a **3-tier lazy-loading memory pattern** to avoid the context-U problem (filling the context window with data that may not be relevant):

**Tier 1 — Always Read (Session Init):** Master-AI-Context.md, architecture file, module-map.md, NextSteps.md. These give the AI enough to understand the project/system and start working.

**Tier 2 — Index Only, Drill Down on Match:** Key-Decisions.md, Sessions.md, Risk-Registry.md, `Standards and Policy/CCDE-Operating-Standard.md`, `Standards and Policy/Communication-Standard.md`. The AI reads the keyword index. When a task matches a keyword, it drills down into the specific detail file. It never reads all files in `session-summary/` or `decisions-learnings/`.

**Tier 3 — On Demand:** Release files, production instructions, design specs, connector configs. Only loaded when the AI is actively working on something that needs them.

---

## 5. Shared Resources

### Standards (Root = Authoritative Master Copies)

| Standard | File | Version | Scope |
|----------|------|---------|-------|
| CC/DE Operating Standard | `Standards and Policy/CCDE-Operating-Standard.md` | v2.0 | All project operations, financial controls, CRM, agent management |
| Adaptive Communication Standard | `Standards and Policy/Communication-Standard.md` | v1.0 | All communications, DISC/OCEAN profiling, stakeholder management |

**Propagation Rule:** When either standard is updated at the root level, the changes MUST be propagated to all project `Standards and Policy/` folders inside `projects/`.

### Connectors

| Connector | Location | Purpose | Status |
|-----------|----------|---------|--------|
| Zoho MCP Server | `zoho-mcp-server/` | Zoho Projects, CRM, Books, Desk, Sign integration | Included (requires configuration) |

### Domain Expert Agents

| Source | Location | Purpose |
|--------|----------|---------|
| Memory Agents | `Memory_Agents/` | Source-of-truth for all domain expert agent definitions (Finance, Marketing, Legal, Security, Executive, Operations, Product Development, Tech Support, People & Culture). Deployed as copies into each project's department folders. |

**Agent Refresh Rule:** If a project's local agent copies are outdated, refresh from `Memory_Agents/`.

---

## 6. Session Lifecycle (Root Level)

Root-level sessions follow the same lifecycle as project sessions:

**Open** (`agents/open.md`) — Pull from git. Read Master-AI-Context.md + README.md. Read standards. Read indexes. Read two most recent session summaries. Create live session files. Begin work.

**Work** — Execute tasks. After every significant action, immediately append to live session files. Before modifying a standard, read Risk-Registry.md for R-ROOT-001 (standards drift risk).

**Close** (`agents/closure.md`) — Finalize live files. Update indexes (Key-Decisions.md, Sessions.md). Update Risk-Registry.md. Update NextSteps.md. Update Master-AI-Context.md. Verify standards sync. Push to git.

---

## 7. CRM Integration

If you use a CRM (Zoho, Salesforce, HubSpot, etc.), contacts across all projects can be tracked using the tagging taxonomy defined in CC/DE Operating Standard Section 7:

- **Project Tags:** One tag per project
- **Role Tags:** Tier1-Core, Tier2-Specialist, Tier3-Vendor, Tier4-Advisory, Client, Lead, Government
- **Specialty Tags:** Electrician, Plumber, Legal, Developer, Designer, Marketing, Finance, etc.
- **Geographic Tags:** Location-based tags for your operational areas

CRM integration is configured during setup (`setup-AI-Memory.md`).

---

## 8. AI Model Preferences

| Purpose | Model | Notes |
|---------|-------|-------|
| Primary | Claude (Anthropic) | Default for most tasks — used via Claude Code sessions on this repository |
| Code Generation | Claude (Anthropic) | Used for software development sessions |
| Writing & Communication | Claude (Anthropic) | Used for content, messaging, documentation |
| Analysis & Research | Claude (Anthropic) | Used for research, data analysis, decision support |

**All Available Models:** Claude (Anthropic). *(Other models can be registered later by re-running the model preferences step.)*

**API Keys:** Not yet registered. Owner follows **`API-Keys-Guide.md`** (beginner-friendly, at repo root) to create keys when the build phase needs them, storing them in a local git-ignored `AliKeys.txt` (pattern `*Keys.txt` is already excluded by `.gitignore`).

---

## 9. Session History & Handover

- **Latest Session:** `session-summary/AI-Session-Summary-2026-07-16_1026.md` — Standards baseline set (Eurocodes/BS/US/KEBS code profiles); Kenya inferred as primary market
- **Latest Decisions:** staging project's `Key-Decisions-2026-07-16_1026.md` (code profiles, market inference, M-Pesa implications)
- **Master Indexes:** [Key-Decisions.md](Key-Decisions.md), [Sessions.md](Sessions.md)
- **Risk Registry:** [Risk-Registry.md](Risk-Registry.md)
- **Next Steps:** [NextSteps.md](NextSteps.md)

---

## 10. Key Operational Rules

1. **Root copies of standards are authoritative.** When a standard is updated, the root copy is updated first, then propagated to all project `Standards and Policy/` folders.

2. **Project folders are independent.** All projects live inside `projects/`. Do not modify project-level files during a root-level session unless performing explicit cross-project work (like propagating standards).

3. **Session tracking is mandatory.** Every root-level session must create live session files (per agents/open.md) and close properly (per agents/closure.md). This ensures system-level changes are tracked with the same rigor as project-level changes.

4. **Contact profiles are shared.** The `contacts/` folder at the root level is the master copy. Projects may also have local copies in their own `contacts/` folder for contacts relevant to that project.

5. **Never commit secrets.** `.gitignore` excludes credential files. API keys, tokens, and passwords must never appear in any tracked file.

6. **Communication preferences are personal.** Your preferred communication style, cadence, and channels will be configured during setup and reflected in the CC/DE standard.

---

*This document is the master operational context for the AI Memory system. It is updated every root-level session by the closure protocol.*
