# Decision: Pivot to MT5 Expert Advisor License Model (Supersedes RIA/Custodian Structure)

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

AITrader will be sold as a **MetaTrader 5 Expert Advisor (EA)** — a licensed piece of trading software — rather than as a discretionary asset-management service. Customers open and fund their **own** trading account with a supported broker (Exness named as the primary target broker) and run the EA on their own MT5 terminal/VPS. AITrader never takes custody of, or discretionary authority over, customer funds. Pricing is a **flat one-time license fee of ~$300**, charged regardless of trading outcome.

## Context

This decision reverses the framing established in `2026-07-14_regulatory-path.md`, which assumed AITrader would hold trading authorization over pooled/individual client accounts at a US-based qualified custodian (an RIA structure). The founder specified Exness (an offshore forex/CFD broker that does not accept US clients) and MetaTrader 5 as the execution platform, and confirmed the fee is a flat one-time software payment, not performance-contingent. Both details are inconsistent with the RIA/custodian model and consistent with the much more common "sell an EA" business model used across the retail forex/CFD space.

## Why This Changes the Regulatory Picture

- **No custody, no discretion over pooled assets:** Customers keep their own broker account and their own funds at all times. AITrader is licensing software, not exercising investment discretion on the company's own authority over client assets in the way an RIA does.
- **Lighter, but not zero, regulatory exposure.** Selling automated trading systems/signals can still draw regulatory attention in some jurisdictions (e.g., CFTC/NFA scrutiny of forex "trading system" sellers who make performance guarantees, or investment-adviser characterization if the software is marketed as "advice" rather than a tool). The main practical risk to manage is **marketing language** — no claims of guaranteed profit, no cherry-picked performance claims, clear risk disclosures — not registration as an adviser.
- **Target market shifts.** Since Exness does not serve US clients, the realistic target market is international retail forex/CFD traders (Exness's actual footprint — Asia, Africa, Latin America, parts of Europe/Middle East), not the US retail investor base assumed in the original Document 1.
- **IP protection becomes a first-order concern.** EA piracy/cracking is common in this market; licensing/anti-tamper mechanics need real design attention.

## Alternatives Considered

1. **Original RIA + custodian discretionary management model** — superseded; doesn't fit the stated broker/platform choice or fee structure.
2. **Performance-based fee ($300 only if profitable)** — considered, rejected by founder in favor of flat one-time pricing, which also happens to keep the business further from "investment adviser" territory.

## Rationale

The EA-license model matches an enormous, well-precedented market (MT5 Expert Advisors sold via the official MQL5 Market, vendor websites, and affiliate/IB channels) with a much lower barrier to launch than RIA registration. It fits the founder's stated broker (Exness) and platform (MT5) choices directly.

## Open Items / Follow-ups

- Confirm with a lawyer (IP/commercial, not necessarily securities) that EA marketing copy and terms of service avoid language that could be read as investment advice or a profit guarantee, and that disclaimers meet the standards used by other MT5 EA vendors and the MQL5 Market's own content policy.
- Decide distribution channel(s): self-hosted site + license-key system, the official MQL5 Market, or both.
- Evaluate an Exness IB/affiliate partnership as a secondary revenue stream (commission per lot traded by referred users) in addition to the $300 license fee.
- **Note (superseded item):** the RIA registration / securities-attorney engagement from the prior decision is no longer the critical path under this model. A lighter-weight legal review (IP/ToS/disclaimers) replaces it — see updated `NextSteps.md`.
