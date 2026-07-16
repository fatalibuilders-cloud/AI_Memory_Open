# Session Closure & Handover Protocol — FatalibuildersConstructionApp

**Purpose:** Execute at the end of every AI session to preserve context, track progress, consolidate risks, and prepare handover.

---

> **Prompt for AI:** "Execute the Session Closure & Handover protocol:
>
> 1. **Finalize the Session Summary** (`session-summary/AI-Session-Summary-[date]_[time].md`): review entries, add Duration, fill Environment State, capture all stories/decisions/blockers. Create from conversation history if the live file is missing.
>
> 2. **Update Master Context & Architecture:**
>    - `Master-AI-Context.md`: link the new summary (§9), update progress (§10), infrastructure (§11), stack (§2) — only changed sections.
>    - `FatalibuildersConstructionApp_architecture.md`: update only if architecture/security/infrastructure changed this session.
>
> 3. **Finalize Decisions & Learnings** (`decisions-learnings/Key-Decisions-[date]_[time].md`): every decision has rationale + impact; every failure has its fix.
>
> 3a. **Update Key-Decisions.md:** File Chronology row, Keyword Index entries, Latest Decisions Summary, timestamp.
>
> 3b. **Update Sessions.md:** Session Index row (filename + up to 10 keywords), timestamp.
>
> 4. **Update Risk Registry:** new risks → `Security/Risk-Report-[date]_[time].md`; update `Risk-Registry.md` (severity counts, keyword index, resolved marks, timestamp).
>
> 5. **Update the active release file:** mark stories [DONE]/[IN-PROGRESS] — only those actually worked on.
>
> 5a. **Update `Product_Development/Releases/Bugs.md`:** log any out-of-story changes, complete In-Progress entries, recalculate Metrics, include bug metrics in the session summary.
>
> 6. **Update NextSteps.md:** completed items [DONE], new items, reprioritize, refresh the `## Risk Mitigation` section for Critical/High risks.
>
> 7. **If any build/deploy was attempted:** update `production-instructions.md` with working commands AND failures+fixes.
>
> 8. **If app source structure changed:** update `module-map.md`.
>
> 9. **Push AI Memory to Git:**
>    ```bash
>    cd <AI_Memory_Open root>
>    git add projects/FatalibuildersConstructionApp_AI_Training/
>    git commit -m "FatalibuildersConstructionApp session closure [YYYY-MM-DD_HHMM]: <summary>"
>    git push
>    ```
>    Push to the fork **fatalibuilders-cloud/AI_Memory_Open** on the session's working branch. Never push secrets.
>
> **Important:** Ensure all folders exist before writing files."

---

*Status: FatalibuildersConstructionApp memory initialized 2026-07-16. Last closure: (none yet).*
