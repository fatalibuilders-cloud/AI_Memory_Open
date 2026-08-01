# Risk Registry — AI Memory System (Root Level)

> **SCOPE:** This file tracks risks to the **AI Memory system itself** — data integrity, standard compliance, infrastructure reliability, and cross-project coordination risks. This is NOT a project-level file. Project-specific risks live in each project's own `Risk-Registry.md`.

**Last Updated:** 2026-08-01

---

## Active Risks

| ID | Risk | Severity | Likelihood | Impact | Mitigation | Status |
|----|------|----------|------------|--------|------------|--------|
| R-ROOT-001 | Standards drift — local copies in project folders diverge from root-level master copies | High | Medium | Standards applied inconsistently across projects | Root copies are authoritative. When updating a standard, update root first, then propagate to all project `Standards and Policy/` folders. Closure protocol must verify sync. | Active |
| R-ROOT-002 | Financial loss from `deriv-crypto-bot` trading real money | Critical | Medium | Direct, unrecoverable loss of owner funds; unattended operation means losses can accumulate without anyone watching | Demo account is the default and a real-money account is refused unless `DERIV_ALLOW_REAL_MONEY=true`; the check fails closed. `DAILY_LOSS_LIMIT` halts trading for the UTC day and the halt persists across restarts. Stake is capped at `MAX_STAKE_FRACTION` of balance and at the remaining daily budget. `KILL_SWITCH` file stops trading within one cycle. Owner must dry-run and demo before going live. | Active |
| R-ROOT-003 | `deriv-crypto-bot` strategy is unvalidated — no backtesting exists | High | High | The strategy may be unprofitable in a way nobody would detect until money is lost | Documented explicitly in the bot README's limitations section and in NextSteps. Backtesting is queued as Medium Priority. Until it exists, treat the strategy as unproven rather than merely untuned. | Active |
| R-ROOT-004 | Deriv API token leaked via commit | High | Low | A token with trade scope allows a third party to trade the owner's account | `.env` is git-ignored in the bot folder; `.env.example` ships with an empty token; the config object redacts the token from all logging. Guidance restricts the token to Read + Trade scopes — never Payments or Admin — so a leak cannot move funds out. | Active |

---

## Risk Severity Guide

- **Critical:** Immediate threat to system integrity or data loss
- **High:** Significant impact on operational effectiveness if realized
- **Medium:** Manageable impact, but should be addressed within 1-2 sessions
- **Low:** Minor inconvenience, tracked for awareness

---

*This is a root-level system file. It tracks risks to the AI Memory system, NOT individual projects.*
