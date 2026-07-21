# Risk Registry — FatalibuildersConstructionApp

> **Purpose:** Consolidated risk summary. Indexes all risk reports and categorizes active risks by severity. Check during session init (open.md step 7); update during closure. Detail reports live in `Security/`.

---

## AI Instructions

- **Init:** check Critical/High risks affecting planned work; read the referenced `Security/` report if relevant.
- **Closure:** log new risks as `Security/Risk-Report-[YYYY-MM-DD]_[HHMM].md`; recategorize; mark resolutions; sync the `## Risk Mitigation` section of NextSteps.md.

**Severity:** Critical = stop-everything · High = address within 1-2 sessions · Medium = within the release cycle · Low = tracked.

---

## Active Risks Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 2 |
| Medium | 3 |
| Low | 0 |

**Total Active Risks:** 5 *(carried from the approved staging risk register, 2026-07-16)*

---

## Critical Risks

*None.*

## High Risks

**RISK-001 — Engineering outputs used without professional review** *(Category: Compliance/Safety · applies to Release 3.0)*
Auto-generated structural drawings or geotech reports used directly in construction could endanger buildings and expose Fatali Builders to liability.
**Mitigation:** watermark + code-profile stamp + engineer-review disclaimer on every generated document (architecture §4); legal review is a GATE before R3 ships; owner-engineer validates all rule-sets. **Owner:** [AI+Human]. **Status:** Open (mitigations designed; enforced at R3 planning by plan-release.md).

**RISK-002 — Calculator accuracy damages brand trust** *(Category: Data/Quality · applies to Release 1.0)*
Wrong quantities or costs would undermine the product and the Fatalibuilders brand.
**Mitigation:** every engine unit-tested against owner-validated worked examples before story sign-off (CORE-5.0/5.1/5.2 acceptance criteria); residential-only R1 scope; engine versioning. **Owner:** [AI+Human]. **Status:** Open (mitigations embedded in R1 stories).

## Medium Risks

**RISK-003 — Lifetime $30 pricing vs. ongoing hosting costs** *(Category: Financial)*
LTV capped at $30 while costs continue.
**Mitigation:** serverless/low-fixed-cost stack (<$50/month target); advisor guardrails (launch-offer framing, future pro tier, willingness-to-pay validation). **Owner:** [AI+Human]. **Status:** Open.

**RISK-004 — Payment failures in launch market** *(Category: Infrastructure)*
Card-only checkout would exclude much of the Kenyan market; gateway misconfiguration blocks revenue.
**Mitigation:** dual stack (merchant-of-record cards + M-Pesa); sandbox-tested before launch (CORE-3.x); go-live smoke test (CORE-8.2). **Owner:** [AI+Human]. **Status:** Open.

**RISK-005 — Scope creep delaying revenue** *(Category: Delivery)*
Seven output types + management features invite endless R1 expansion.
**Mitigation:** R1 fixed to Epics 1-4 + 7 of the release file; drawings/engineering/management phased to R2-R4; plan-release.md enforces explicit deferral. **Owner:** [AI]. **Status:** Open.

## Low Risks

*None.*

---

## Keyword Index

| Keyword | Files |
|---------|-------|
| engineering liability, disclaimers, structural, geotech | This file RISK-001; staging `Key-Decisions-2026-07-16_1019.md` |
| calculator accuracy, worked examples | This file RISK-002; release file CORE-5.x |
| pricing, unit economics, lifetime | This file RISK-003; staging `Key-Decisions-2026-07-16_1007.md` |
| payments, M-Pesa, checkout | This file RISK-004; release file CORE-3.x |
| scope, phasing | This file RISK-005 |

---

## Report Chronology

| Date | File | Focus | Risks Added | Risks Resolved |
|------|------|-------|-------------|----------------|
| 2026-07-16 | *(initialized from staging risk register — no separate report file)* | Founding risks | 5 | 0 |

---

*Last updated: 2026-07-16 — initialized by PROJECT_MEMORY_INIT.md*
