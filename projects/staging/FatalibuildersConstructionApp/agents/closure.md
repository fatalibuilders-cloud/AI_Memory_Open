# closure.md — Session Closure Protocol (FatalibuildersConstructionApp — Staging)

**Purpose:** Execute this protocol at the end of any AI session that worked on the **FatalibuildersConstructionApp staging project**. If the session also touched root-level AI Memory files, run the root `AI_Memory_Open/agents/closure.md` as well.

---

> **Prompt for AI:** "Execute the FatalibuildersConstructionApp staging session closure:
>
> 1. **Finalize the Decision Log:** Review the session's `decisions-learnings/Key-Decisions-[YYYY-MM-DD]_[HHMM].md`:
>    - Every decision has context, options considered, decision, rationale, and impact
>    - Learnings include the fix or workaround for any failures
>    - Blockers and open questions are captured
>    - Keywords for indexing are listed
>    - If the live file does not exist (session was not opened with open.md), create it now from the conversation history
>
> 2. **Update Key-Decisions.md:** Add a row to the index table for the session's decision log with date, keywords, filename, and a one-sentence summary. Update the "Recent Decisions" section.
>
> 3. **Update Sessions.md:** Add a row to the session index with date, approximate duration, keywords, and summary. Update the "Session History" section.
>
> 4. **Update NextSteps.md:** Update document statuses, completed sections, next actions, and blockers/open questions. Update the "Last Updated" date.
>
> 5. **Update Master-Context.md:** Update the Staging Roadmap status fields and "Last Updated" date. If document sections were filled in, ensure the content is consolidated there.
>
> 6. **Update the Status Snapshot** at the bottom of `agents/open.md` to reflect current document statuses and the top blocker.
>
> 7. **Commit & Push:**
>    ```bash
>    cd <path-to-AI_Memory_Open>
>    git add .
>    git commit -m "FatalibuildersConstructionApp staging [YYYY-MM-DD_HHMM]: <brief summary>"
>    git push
>    ```
>    Do NOT push sensitive files — API keys, credentials, and client personal data must never be committed.
>
> 8. **Confirm to the user:** What was accomplished, what document statuses changed, what the next session should start with, and any owner input required."

---

*Project-level closure protocol. Root-level system changes are closed via `AI_Memory_Open/agents/closure.md`.*
