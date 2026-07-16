# closure.md — Session Closure Protocol (AI Memory System — Root Level)

**Purpose:** Execute this protocol at the end of any session that modified the **AI Memory system itself** — its structure, standards, policies, shared resources, cross-project operations, or root-level files.

> **IMPORTANT — SCOPE DISTINCTION:**
> This closure protocol is for sessions that worked on the **AI Memory infrastructure**. If your session was focused on a **single project**, use that project's own `agents/closure.md` instead. If your session touched BOTH root-level AND project-level files, run BOTH closure protocols.

---

> **Prompt for AI:** "Execute the Root-Level Session Closure protocol:
>
> 1. **Finalize Session Summary:** The session summary file (`session-summary/AI-Session-Summary-[YYYY-MM-DD]_[HHMM].md`) was created at session start and updated incrementally. Now finalize it:
>    - Review all entries for completeness and accuracy
>    - Add the **Duration** field (calculate from start time)
>    - Fill in the **Standards Sync Status** section — list which project copies were updated if standards were modified
>    - Fill in the **Projects Affected** section — list all project folders that were modified
>    - Ensure all decisions and blockers are captured
>    - If the live file does not exist (session was not started with open.md), create it now from scratch by analyzing the conversation history
>
> 2. **Finalize Decisions & Learnings:** The decisions file (`decisions-learnings/Key-Decisions-[YYYY-MM-DD]_[HHMM].md`) was created at session start and updated incrementally. Now finalize it:
>    - Review all entries for completeness — ensure every decision has a rationale
>    - Review all learnings — ensure failures include the fix or workaround
>    - Add any decisions or learnings that were missed during incremental updates
>
> 3. **Update Key Decisions Index:** Read the session's decisions file and update `Key-Decisions.md`:
>    - Add new rows to the **Keyword Index** table for each decision topic
>    - Add a new row to the **File Chronology** table
>    - Update the **Latest Decisions Summary** section if decisions supersede existing summaries
>    - Update the "Last Updated" timestamp
>
> 4. **Update Sessions Index:** Update `Sessions.md`:
>    - Add a new row to the **Session Index** table with the session filename and up to 10 keywords
>    - Update the "Last Updated" timestamp
>
> 5. **Update Risk Registry:** If new risks were identified or existing risks were mitigated:
>    - Add or update rows in `Risk-Registry.md`
>    - Update the "Last Updated" timestamp
>
> 6. **Update NextSteps.md:** Based on what was done and what remains:
>    - Move completed items to the "Recently Completed" table
>    - Add any new pending items to the Priority Queue
>    - Re-prioritize if needed
>    - Update the "Last Updated" timestamp
>
> 7. **Update Master-AI-Context.md:** If system-level changes were made:
>    - Update the session history references (latest session, latest decisions)
>    - Update the repository structure diagram if folders were added/removed
>    - Update the project portfolio table if projects were added/modified
>    - Update the shared resources section if resources were added/modified
>
> 8. **Update Live Workspace Index in `agents/open.md`:**
>    - Scan the `AI_Memory_Open/projects/` directory for project folders (e.g., `*_AI_Training/`). List the top 5 most recently modified under **Recent Projects**.
>    - Scan the `AI_Memory_Open/projects/staging/` directory for staged project folders. List the top 5 most recently modified under **Staging Projects**.
>    - Scan the main `AI_Memory_Open/` directory for all root-level `.md` files. Update the **Root Directory File Index** section if any files were added or removed.
>    - Replace the corresponding sections in the **Live Workspace Index** at the bottom of `agents/open.md` with these updated lists.
>
> 8b. **Stage All Changes:** Run `git add .` in the `AI_Memory_Open` repository to stage all modified files before committing. This ensures session summaries, decision logs, index updates, and any other changes are included.
>
> 9. **Standards Propagation Verification:** If either standard was modified during this session:
>    - Verify the root copy is the latest version
>    - List which project `Standards and Policy/` copies were updated
>    - Flag any project copies that were NOT updated (they need to be synced)
>    - Log the sync status in the session summary
>
> 10. **Push AI Memory to Git:**
>    ```bash
>    cd <path-to-AI_Memory_Open>
>    git add .
>    git commit -m "Root session closure [YYYY-MM-DD_HHMM]: <brief summary>"
>    git push origin main
>    ```
>    - The remote is this system's fork: **https://github.com/fatalibuilders-cloud/AI_Memory_Open**. Never push to the upstream template (Qosil/AI_Memory_Open).
>    - If in Cowork (sandbox), remind the user to run `git add . && git commit -m "..." && git push` manually.
>    - **Do NOT push sensitive files** — ensure `.gitignore` excludes credential files.
>
> 11. **Confirm:** Let the user know:
>    - What was tracked in the session summary
>    - Whether standards are in sync across all projects
>    - Whether the repository was pushed (or needs manual push)
>    - What the top priorities are for the next session"

---

*This is a root-level system file. It governs closure of sessions that modify the AI Memory Open system, NOT individual projects.*
