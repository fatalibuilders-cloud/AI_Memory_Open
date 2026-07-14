# Key Decisions — AITrader (Staging)

**Scope:** Decisions made during AITrader staging. Read this index before starting new staging work; drill into a detail file only when its keyword matches your current task.

---

## Keyword Index

| Keyword | Decision / Topic | Detail File | Date |
|---------|-----------------|-------------|------|
| regulatory, RIA, broker-dealer, custody, compliance | ~~Pursue RIA + third-party custodian structure~~ — **SUPERSEDED**, see EA license entry below | `decisions-learnings/2026-07-14_regulatory-path.md` | 2026-07-14 |
| business model, EA, expert advisor, MT5, MetaTrader, Exness, licensing, fee model | Pivot to selling AITrader as a licensed MT5 Expert Advisor (~$300 flat one-time fee); customers keep custody of their own funds at their own broker | `decisions-learnings/2026-07-14b_ea-license-business-model.md` | 2026-07-14 |

---

## Latest Decisions Summary

**2026-07-14 (later same day):** Pivoted from the RIA/discretionary-management model to selling AITrader as a licensed MetaTrader 5 Expert Advisor. Customers run the bot on their own funded Exness account; AITrader never holds customer funds. Fee is a flat one-time ~$300 license, not performance-contingent. This substantially lowers regulatory burden but shifts target market to non-US (Exness doesn't serve US clients) and makes licensing/anti-piracy and marketing-claim compliance the key open risks. See detail file for follow-ups.

**2026-07-14 (earlier, superseded):** Originally selected RIA + third-party broker-dealer/custodian as the regulatory structure for autonomous retail trading of pooled client funds. Superseded by the EA-license pivot above — kept in the record for context, not to be acted on.

---

## File Chronology

| File | Date | Session Focus |
|------|------|---------------|
| `2026-07-14_regulatory-path.md` | 2026-07-14 | Initial staging session — project intake, regulatory structure decision (superseded) |
| `2026-07-14b_ea-license-business-model.md` | 2026-07-14 | Follow-up session — business model pivot to MT5 EA licensing |
