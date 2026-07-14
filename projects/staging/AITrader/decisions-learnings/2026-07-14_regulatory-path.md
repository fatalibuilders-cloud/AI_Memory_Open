# Decision: Regulatory Path for Autonomous Retail Trading

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

AITrader will pursue an **RIA (Registered Investment Adviser) + third-party broker-dealer/custodian** structure rather than becoming its own broker-dealer. AITrader will hold trading authorization (limited power of attorney) over client accounts held at a regulated custodian; it will never directly custody client funds.

## Context

The founder selected "fully autonomous trading on users' behalf" as AITrader's execution model, targeting retail investors. Discretionary trading of client accounts without per-trade approval constitutes investment advisory activity under the Investment Advisers Act of 1940, which is the single largest regulatory and timeline gate on the project.

## Alternatives Considered

1. **Become a broker-dealer directly** — rejected for now: far higher capital, licensing (FINRA membership), and compliance burden than an RIA; only revisit if a compelling reason emerges (e.g., wanting to control execution/order routing directly).
2. **Signal/recommendation-only model (user clicks "execute")** — considered but rejected because the founder explicitly wants full autonomy; noted as a fallback "Phase 0" option if RIA registration timeline becomes a blocker (could launch as an advisory tool first, add discretionary trading once registered).
3. **Managed fund/pooled vehicle structure** — not selected; adds fund-formation complexity (private fund rules, accredited-investor limits) that doesn't fit the "retail" target market as well as separately managed accounts would.

## Rationale

RIA + third-party custodian is the standard, well-precedented structure used by existing robo-advisors and algorithmic-trading platforms (e.g., Wealthfront, Betterment, various API-driven quant platforms). It avoids broker-dealer registration entirely by using an existing broker-dealer's API for execution, which is materially faster and cheaper to stand up than a full broker-dealer buildout.

## Open Items / Follow-ups

- Engage a securities attorney to confirm state vs. SEC RIA registration threshold and jurisdiction plan before further build investment.
- Select a broker-dealer/custodian partner (e.g., Alpaca Securities, Interactive Brokers, Tradier) — evaluate API capabilities, fee splits, and whether they support the intended asset classes (equities/options/crypto).
- Consider a "Phase 0" signal-only launch (no discretionary authority) if RIA registration timeline threatens the release schedule.
