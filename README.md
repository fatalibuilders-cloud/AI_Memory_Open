# AI_Memory_Open — Universal AI Context Memory System

**Repository:** https://github.com/fatalibuilders-cloud/AI_Memory_Open (fork of upstream template https://github.com/Qosil/AI_Memory_Open)
**Memory Design Version:** 1.1
**License:** GPL v3

---

## What Is This?

AI_Memory_Open is a **persistent memory system for AI assistants**. It solves a fundamental problem: AI sessions are stateless. Every time you start a new conversation with Claude, Gemini, or any LLM, it has zero knowledge of your project — what was built, what decisions were made, what failed, or what comes next.

AI_Memory_Open fixes that. It stores structured project knowledge in markdown files committed to git, so any AI assistant can load full project context at the start of a session and pick up exactly where the last one left off. No repeated explanations, no re-discovered bugs, no forgotten architectural decisions.

---

## Getting Started

### Prerequisites

- **Git** installed on your machine
- **An AI assistant with file system access** — Claude (via Cowork, Claude Code, or Coder), Gemini, or any LLM that can read and write local files

### Step 1: Fork & Clone

**Fork this repository** into your own GitHub account first. Do NOT push changes directly to `Qosil/AI_Memory_Open` — it is a read-only upstream template.

```bash
# After forking on GitHub, clone YOUR fork:
git clone https://github.com/YourUsername/AI_Memory_Open.git
cd AI_Memory_Open
```

### Step 2: Initialize

Open a session with your AI assistant (make sure it has access to the cloned folder) and say:

> "Execute setup-AI-Memory.md to initialize the AI Memory system for the first time."

The AI will walk you through a one-time setup process (~10-15 minutes):

1. **System Configuration** — Identify yourself, register API keys, configure AI model preferences
2. **Repository Configuration** — Point the system to your forked repo URL
3. **Standards Customization** — Review and optionally customize the operating and communication standards
4. **First Project** — Stage your first project using the staging protocol

After setup, every future session starts with `agents/open.md` — the AI will detect this automatically.

---

## How It Works

Each project gets its own subfolder named `{ProjectName}_AI_Training/`. Inside that folder is a standardized set of files and directories that give an AI everything it needs:

**Operational context** — what the project is, how it's built, what commands to run, what conventions to follow. This lives in `Master-AI-Context.md`, the first file any AI reads.

**Architectural knowledge** — the design philosophy, security model, infrastructure constraints. This lives in a separate `{ProjectName}_architecture.md` file so it can be provided during ideation sessions and preserved verbatim.

**Session continuity** — timestamped session summaries and decision logs, indexed by keyword so AIs can look up relevant history without reading every file.

**Live session files** — session summaries and decision logs are created at the *start* of each session (not the end) and updated incrementally as work happens. This means context is preserved even if a session crashes or the context window fills up.

**Release planning** — versioned build instruction files with granular stories, acceptance criteria, and `[AI]`/`[Human]`/`[AI+Human]` labels that tell the AI exactly what it can execute autonomously vs. what requires human input.

**Risk tracking** — a risk registry that categorizes active risks by severity, so AIs prioritize critical issues.

---

## Lazy-Loading Memory Pattern

The system avoids the "context-U" problem (filling the context window with historical data) using a **3-tier lazy-loading pattern**:

**Tier 1 (Always Read):** `Master-AI-Context.md`, the architecture file, `module-map.md`, and `NextSteps.md`. These give the AI enough to understand the project and start working.

**Tier 2 (Index Only):** `Key-Decisions.md`, `Sessions.md`, `Risk-Registry.md`, and the governing standards. The AI reads the keyword index and only drills into specific detail files when a task matches a keyword.

**Tier 3 (On Demand):** Release files, production instructions, design specs, and connector configs. Only loaded when actively needed.

---

## What's Included

### 51 Domain Expert Agents (`Memory_Agents/`)

Pre-built AI advisor agents across 20 domains: Finance, Legal, Marketing, Operations, Sales, Strategy, Software Development, Infrastructure, Product Development, People & Culture, and more. Each agent has a configuration file and a detailed advisor protocol. These are automatically deployed into project folders during initialization.

### CC/DE Operating Standard v2.0 (`Standards and Policy/`)

The Centralized Command, Decentralized Execution management framework. Governs project management, financial controls, agent network management, CRM contact tracking, reporting cadences, and decision-making authority.

### Adaptive Communication Standard v1.0 (`Standards and Policy/`)

A comprehensive communication framework integrating DISC behavioral profiling, Big Five (OCEAN) personality assessment, SPIKES protocol for difficult news, Hofstede cultural dimensions, and NVC principles. Includes a contact profiling system for personalized communication.

### Zoho MCP Connector (`zoho-mcp-server/`)

A reference MCP connector for Zoho Projects, CRM, Books, Desk, and Sign. Requires your own Zoho API credentials to configure.

### 3-Step Project Lifecycle

1. **`setup-AI-Memory.md`** — One-time system initialization (you do this once)
2. **`staging.md`** — Per-project ideation and planning (collaborative "design sprint")
3. **`PROJECT_MEMORY_INIT.md`** — Per-project full build (AI autonomously constructs the project folder)

### Model Validation & White Papers (`Model_Validation/`)

Research documents and white papers covering the AI Memory methodology, design system patterns, development release processes, and project management approaches.

---

## Repository Structure

```
AI_Memory_Open/
├── ─── SYSTEM FILES ───
├── Master-AI-Context.md              # System-level operational context
├── README.md                         # This file
├── Standards and Policy/             # Governing standards (master copies)
│   ├── CCDE-Operating-Standard.md    # CC/DE v2.0
│   └── Communication-Standard.md     # ACS v1.0
├── setup-AI-Memory.md                # One-time setup (Step 1)
├── staging.md                        # Project ideation (Step 2)
├── PROJECT_MEMORY_INIT.md            # Project build (Step 3)
│
├── ─── SYSTEM FOLDERS ───
├── agents/                           # Session lifecycle protocols
├── session-summary/                  # Session summaries
├── decisions-learnings/              # Decision logs
├── contacts/                         # Contact profiles (DISC/OCEAN)
├── Memory_Agents/                    # 51 domain expert agents
├── Model_Validation/                 # White papers & methodology
├── zoho-mcp-server/                  # Reference Zoho MCP connector
│
├── ─── SESSION TRACKING ───
├── Key-Decisions.md                  # Decision keyword index
├── Sessions.md                       # Session keyword index
├── Risk-Registry.md                  # Risk tracking
├── NextSteps.md                      # Priority queue
│
├── ─── PROJECTS ───
├── projects/                         # Your projects go here
│   └── staging/                      # Projects being planned
```

---

## Session Lifecycle

Every AI session follows the same lifecycle, enforced by protocols in `agents/`:

**Open** (`agents/open.md`) — Pull from git. Read context files. Read standards. Read indexes. Read recent session summaries. Create live session files. Begin work.

**Work** — Execute tasks. After every significant action, immediately append to live session files.

**Close** (`agents/closure.md`) — Finalize live files. Update indexes. Update context. Push to git.

Live files are created at **start** and updated incrementally, so context is preserved even if a session ends unexpectedly.

---

## Contributing

AI_Memory_Open is open source under the GPL v3 license. Contributions are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to your branch
5. Open a Pull Request against `Qosil/AI_Memory_Open`

Please do not include personal data, API keys, or project-specific content in pull requests.

---

## License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.

---

*Memory Design Version 1.1 — Built with Claude (Opus 4.6)*
