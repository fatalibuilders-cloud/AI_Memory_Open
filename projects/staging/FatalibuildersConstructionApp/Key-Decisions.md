# Key Decisions Index — FatalibuildersConstructionApp Staging

This is a keyword-searchable index of all architectural and product decisions made during staging.

## How to Use

When working on FatalibuildersConstructionApp, search this index for relevant keywords. If a keyword matches your current task, read the linked decision file for full context.

| **Date** | **Keywords** | **File** | **Summary** |
|---|---|---|---|
| 2026-07-16 | staging, initialization, project category, naming, autonomous session | `decisions-learnings/Key-Decisions-2026-07-16_0728.md` | Staged the project autonomously from the task name; classified as Software; AI-drafted vision pending owner review |
| 2026-07-16 | integrations, architecture, API-first, connectors, owner directive | `decisions-learnings/Key-Decisions-2026-07-16_0908.md` | Owner confirmed integration-first architecture — the app must integrate with all kinds of tools; candidate connector list drafted |
| 2026-07-16 | accounting, QuickBooks, Excel, connector priority, data migration | `decisions-learnings/Key-Decisions-2026-07-16_0943.md` | ~~QuickBooks priority 1, Excel priority 2~~ **SUPERSEDED by 0959 entry** |
| 2026-07-16 | accounting, Excel, QuickBooks dropped, WhatsApp, calls, messaging | `decisions-learnings/Key-Decisions-2026-07-16_0959.md` | Owner revised: Excel ONLY for accounting (QuickBooks dropped); WhatsApp + calls confirmed as communication channels — Excel import/export is now priority 1, WhatsApp priority 2 |
| 2026-07-16 | public product, pricing, lifetime access, login, payments, vision | `decisions-learnings/Key-Decisions-2026-07-16_1007.md` | Owner redefined the product: public app (login required), data-in → results-out core tool, $30 one-time lifetime access; core tool definition is the blocking open question |
| 2026-07-16 | core tool, calculators, 2D drawings, renders, structural, geotechnical, disclaimers, release phasing | `decisions-learnings/Key-Decisions-2026-07-16_1019.md` | Core tool fully defined: all calculators + 2D drawings + renders + structural drawings + geotech report; engineering outputs must carry licensed-engineer-review disclaimers; 3-release phasing set |

---

## Keyword Reference

- **Vision & Goals:** Decisions about project vision, goals, success metrics
- **Audience & Market:** Decisions about target users, market positioning
- **Architecture:** Decisions about system/business/product design
- **Technology Stack:** Decisions about tech choices (software projects)
- **Process Design:** Decisions about operational workflows and org structure
- **Release & Phasing:** Decisions about launch phases and milestones
- **Dependencies:** Decisions about institutional dependencies (marketing, legal, finance, security, etc.)
- **Constraints:** Decisions about budget, timeline, or technical constraints

---

## Recent Decisions

- **2026-07-16:** Project staged autonomously as a **Software** project. Vision, target users, and candidate epics were AI-drafted and are **pending owner review** — see `decisions-learnings/Key-Decisions-2026-07-16_0728.md`.
- **2026-07-16 (later):** Owner confirmed the app should **integrate with all kinds of tools** → integration-first, API-first architecture with connector modules — see `decisions-learnings/Key-Decisions-2026-07-16_0908.md`.
- **2026-07-16 (1019, CURRENT — CORE TOOL DEFINED):** Owner confirmed the full output set: **material quantities, cost estimate, labor/time estimate, 2D drawings, renders, structural drawings, geotechnical report (from soil type)**. Engineering outputs (structural/geotech) will be watermarked "preliminary — requires licensed engineer review" with legal sign-off before their release. Phasing: R1 = calculators + payment + exports; R2 = drawings/renders; R3 = engineering outputs. Open: management features (Epic 8), market/country + building codes, Release-1 construction types — see `decisions-learnings/Key-Decisions-2026-07-16_1019.md`.
- **2026-07-16 (1007 — PRODUCT DIRECTION):** Owner redefined the product: **a public Fatalibuilders app** — anyone can log in, insert construction data, and get results, for a **one-time $30 lifetime-access payment**. Vision rewritten; epics restructured (Accounts & Payment / Core Tool / Output & Sharing / Product Site; management features parked as Epic 5). **Blocking question: define exactly what data goes in and what results come out** — see `decisions-learnings/Key-Decisions-2026-07-16_1007.md`.
- **2026-07-16 (0959):** Owner revised the accounting decision: **Excel ONLY — QuickBooks dropped.** The app becomes the system of record for job finances, with Excel import/export as integration priority 1. **WhatsApp + phone calls** confirmed as communication channels → WhatsApp is priority 2 (wa.me links first, Business API later), tap-to-call throughout. Still open: photo/document storage, scheduling method — see `decisions-learnings/Key-Decisions-2026-07-16_0959.md`.
- ~~**2026-07-16 (0943):** Excel + QuickBooks; QuickBooks connector priority 1.~~ **Superseded by 0959.**
