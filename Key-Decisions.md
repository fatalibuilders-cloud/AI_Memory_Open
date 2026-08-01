# Key Decisions — AI Memory System (Root Level)

> **SCOPE:** This file indexes decisions about the **AI Memory system itself** — its structure, standards, policies, shared resources, and cross-project infrastructure. This is NOT a project-level file. Project-specific decisions live in each project's own `Key-Decisions.md`.

**Last Updated:** 2026-08-01

---

## Keyword Index

When performing any action that matches a keyword below, read the referenced detail file before proceeding.

| Keyword | Decision / Topic | Detail File | Date |
|---------|-----------------|-------------|------|
| staging, project lifecycle | New projects enter via staging.md, not PROJECT_MEMORY_INIT.md, when foundation documents don't exist | `decisions-learnings/Key-Decisions-2026-07-16_0728.md` | 2026-07-16 |
| autonomous session, drafts | AI-drafted content in autonomous sessions must be flagged "pending owner review" | `decisions-learnings/Key-Decisions-2026-07-16_0728.md` | 2026-07-16 |
| FatalibuildersConstructionApp | First project staged in this fork (Software category) | `decisions-learnings/Key-Decisions-2026-07-16_0728.md` | 2026-07-16 |
| system setup, owner, repository | One-time setup executed; owner/fork/model configured; keys and enterprise OS deferred | `decisions-learnings/Key-Decisions-2026-07-16_0908.md` | 2026-07-16 |
| keys, credentials | No keys file created — owner adds git-ignored `FataliKeys.txt` locally when ready | `decisions-learnings/Key-Decisions-2026-07-16_0908.md` | 2026-07-16 |
| standards | CC/DE v2.0 and ACS v1.0 adopted as-is; customization deferred | `decisions-learnings/Key-Decisions-2026-07-16_0908.md` | 2026-07-16 |
| integrations, connectors | App integration directive: integrate with all kinds of tools (project-level decision) | `decisions-learnings/Key-Decisions-2026-07-16_0908.md` | 2026-07-16 |
| API keys, security, guide | AI never creates/holds keys; owner follows API-Keys-Guide.md; release 1 needs no keys (post-0959 revision) | `decisions-learnings/Key-Decisions-2026-07-16_0945.md` | 2026-07-16 |
| Excel, QuickBooks dropped, WhatsApp | App tooling revised: Excel-only accounting, WhatsApp+calls (project-level; guide updated accordingly) | `projects/staging/FatalibuildersConstructionApp/decisions-learnings/Key-Decisions-2026-07-16_0959.md` | 2026-07-16 |
| public product, pricing, payments | Product redefined: public app, login, $30 lifetime access; payment provider now required (project-level; guide updated) | `projects/staging/FatalibuildersConstructionApp/decisions-learnings/Key-Decisions-2026-07-16_1007.md` | 2026-07-16 |
| core tool, drawings, engineering outputs | Core tool defined (7 outputs); engineering-liability safeguards; 3-release phasing (project-level) | `projects/staging/FatalibuildersConstructionApp/decisions-learnings/Key-Decisions-2026-07-16_1019.md` | 2026-07-16 |
| standards, code profiles, Kenya | Standards baseline: Eurocodes+BS+US+KEBS as per-project code profiles; Kenya inferred as market (project-level) | `projects/staging/FatalibuildersConstructionApp/decisions-learnings/Key-Decisions-2026-07-16_1026.md` | 2026-07-16 |
| staging complete, worldwide, sign-off | All three staging documents complete: worldwide/Kenya launch, residential R1, management features R4 (project-level) | `projects/staging/FatalibuildersConstructionApp/decisions-learnings/Key-Decisions-2026-07-16_1030.md` | 2026-07-16 |
| initialization, promotion, PROJECT_MEMORY_INIT | FatalibuildersConstructionApp promoted to full project; Release 1.0 planned (29 stories); staging archived | `session-summary/AI-Session-Summary-2026-07-16_1044.md` | 2026-07-16 |
| onboarding, communication | Owner is a first-time app builder — communications must be jargon-free with explicit action lists | `decisions-learnings/Key-Decisions-2026-07-16_0945.md` | 2026-07-16 |
| Deriv, trading bot, crypto | `deriv-crypto-bot` built in `app-src/` directly (not staged); Python; crypto-only enforced at three points | `decisions-learnings/Key-Decisions-2026-08-01_0014.md` | 2026-08-01 |
| trading, real money, safety | Trading bots default to a demo account; real-money use requires an explicit opt-in flag and fails closed | `decisions-learnings/Key-Decisions-2026-08-01_0014.md` | 2026-08-01 |
| external API, runtime discovery | Where a remote API's specifics cannot be verified, discover them at runtime rather than hardcoding from memory | `decisions-learnings/Key-Decisions-2026-08-01_0014.md` | 2026-08-01 |

---

## Latest Decisions Summary

- **2026-07-16:** Staged **FatalibuildersConstructionApp** (Software) as this fork's first project via staging.md. Vision and scope are AI drafts pending owner review.
- **2026-07-16 (later):** **One-time system setup completed.** Owner: Fatali Builders (fatalibuilders@gmail.com); repository: fatalibuilders-cloud/AI_Memory_Open; primary model: Claude. Deferred: API keys, enterprise OS choice, standards customization, owner full name. The app itself will follow an integration-first architecture per owner directive.
- **2026-08-01:** **`deriv-crypto-bot` built** under `app-src/` — a cryptocurrency-only, 24/7 trading bot for the Deriv WebSocket API. Built directly rather than via `staging.md`, since the request was a concrete build. Safety posture: demo account by default, real money behind an explicit opt-in that fails closed, daily loss limit persisted across restarts, kill-switch file. 148 tests pass. Owner must supply a Deriv API token before it can run.

---

## File Chronology

| File | Date | Session Focus |
|------|------|---------------|
| `Key-Decisions-2026-07-16_0728.md` | 2026-07-16 | Stage FatalibuildersConstructionApp project |
| `Key-Decisions-2026-07-16_0908.md` | 2026-07-16 | One-time system setup; app integration directive |
| `Key-Decisions-2026-07-16_0945.md` | 2026-07-16 | API key guidance; first-time builder onboarding approach |
| `Key-Decisions-2026-08-01_0014.md` | 2026-08-01 | Deriv crypto trading bot: build location, safety defaults, runtime API discovery |

---

*This is a root-level system file. It tracks decisions about the AI Memory system, NOT individual projects.*
