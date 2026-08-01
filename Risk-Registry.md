# Risk Registry — AI Memory System (Root Level)

> **SCOPE:** This file tracks risks to the **AI Memory system itself** — data integrity, standard compliance, infrastructure reliability, and cross-project coordination risks. This is NOT a project-level file. Project-specific risks live in each project's own `Risk-Registry.md`.

**Last Updated:** 2026-08-01

---

## Active Risks

| ID | Risk | Severity | Likelihood | Impact | Mitigation | Status |
|----|------|----------|------------|--------|------------|--------|
| R-ROOT-001 | Standards drift — local copies in project folders diverge from root-level master copies | High | Medium | Standards applied inconsistently across projects | Root copies are authoritative. When updating a standard, update root first, then propagate to all project `Standards and Policy/` folders. Closure protocol must verify sync. | Active |
| R-ROOT-002 | Financial loss from `deriv-crypto-bot` trading real money | Critical | Medium | Direct, unrecoverable loss of owner funds; unattended operation means losses can accumulate without anyone watching | Demo account is the default and a real-money account is refused unless `DERIV_ALLOW_REAL_MONEY=true`; the check fails closed. `DAILY_LOSS_LIMIT` halts trading for the UTC day and the halt persists across restarts. Stake is capped at `MAX_STAKE_FRACTION` of balance and at the remaining daily budget. `KILL_SWITCH` file stops trading within one cycle. Owner must dry-run and demo before going live. | Active |
| R-ROOT-003 | `deriv-crypto-bot` strategy has no demonstrated edge | High | High | The strategy may be unprofitable in a way nobody detects until money is lost | **Mitigation strengthened 2026-08-01:** a backtester now exists (`deriv_bot/backtest.py`) that replays history through the same strategy and risk code, and reports win rate against the **breakeven win rate** implied by the payout. On a synthetic random walk the default settings correctly produce a 51.4% win rate and a net loss. The risk is *not* closed: no real Deriv history has been replayed yet, and the payout ratio in any backtest is an assumption, not a measurement. Owner must backtest real data across several periods and symbols before treating the strategy as viable. | Active |
| R-ROOT-005 | Backtest results are over-trusted | Medium | Medium | A favourable backtest is mistaken for evidence of profitability, prompting real-money use | The backtester states its assumptions in the report itself, flags results within 2 points of breakeven as MARGINAL, and prints "one period is not evidence" on every run. Payout ratio, spread, slippage, and intra-candle movement are all unmodelled and all bias results optimistically. | Active |
| R-ROOT-004 | Deriv API token leaked via commit | High | Low | A token with trade scope allows a third party to trade the owner's account | `.env` is git-ignored in the bot folder; `.env.example` ships with an empty token; the config object redacts the token from all logging. Guidance restricts the token to Read + Trade scopes — never Payments or Admin — so a leak cannot move funds out. | Active |

---

## Risk Severity Guide

- **Critical:** Immediate threat to system integrity or data loss
- **High:** Significant impact on operational effectiveness if realized
- **Medium:** Manageable impact, but should be addressed within 1-2 sessions
- **Low:** Minor inconvenience, tracked for awareness

---

*This is a root-level system file. It tracks risks to the AI Memory system, NOT individual projects.*
