# Decision Logging Protocol — AITrader (Staging)

**Purpose:** Instructions for capturing decisions made during AITrader staging sessions.

---

## When to Log a Decision

Log a decision whenever the session settles something that will constrain future work: a scope choice, a rejected alternative, a regulatory/legal position, an architecture choice, a naming choice, etc. Not every discussion needs a log entry — only decisions that future sessions must respect.

## How to Log a Decision

1. Create a file: `decisions-learnings/[YYYY-MM-DD]_[short-slug].md`
2. Include:
   - **Decision:** One-sentence statement of what was decided
   - **Context:** Why this came up
   - **Alternatives Considered:** What else was on the table
   - **Rationale:** Why this option won
   - **Owner:** Who made/approved the call
   - **Date:** When
3. Add a row to `Key-Decisions.md` with the keyword(s), a one-line summary, and a link to the detail file.

## Retrieval

Before starting new staging work, scan `Key-Decisions.md` (index only). Drill into a detail file only when its keyword matches your current task.
