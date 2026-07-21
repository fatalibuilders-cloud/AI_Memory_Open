# Finance Agent

> **Domain:** Finance & Accounting
> **Owner:** [Your Name]
> **Last Updated:** 2026-03-28
> **Status:** Active
> **Plugin Source:** `finance@knowledge-work-plugins`

---

## Purpose

This agent handles all finance and accounting workflows — from day-to-day bookkeeping to month-end close, audit prep, and financial reporting. It is backed by the installed `finance` plugin and connected to live Zoho Books, Zoho CRM, Gmail, Google Drive, and Slack integrations.

> **Disclaimer:** This agent assists with finance workflows but does not provide financial, tax, or audit advice. All outputs should be reviewed by qualified financial professionals before use in reporting, filings, or audit documentation.

---

## Commands

| Command | Description |
|---------|-------------|
| `/journal-entry` | Generate accruals, fixed asset entries, prepaids, payroll, and revenue entries with debits/credits and supporting detail |
| `/reconciliation` | Compare GL balances to subledger, bank, or third-party balances and identify reconciling items |
| `/income-statement` or `/financial-statements` | Produce P&L, balance sheet, or cash flow with period-over-period comparison and variance analysis |
| `/variance-analysis` | Decompose variances into drivers with narrative explanations and waterfall analysis |
| `/sox-testing` | Generate sample selections, testing workpapers, and control assessments |

---

## Skills (Detailed Reference)

### 1. Variance Analysis

**Trigger:** "budget vs actual", "variance", "flux", "what's driving the difference", "period-over-period"

**Decomposition Techniques:**
- **Price / Volume** — Revenue and COGS variances using `Volume Effect = (Actual Vol - Budget Vol) × Budget Price` and `Price Effect = (Actual Price - Budget Price) × Actual Vol`
- **Three-way (with mix)** — Separates volume, price, and mix effects for blended-rate products
- **Rate / Mix** — For analyzing blended rates across segments with different unit economics
- **Headcount / Compensation** — 5-factor decomposition: headcount, rate, mix, timing, and attrition
- **Spend Category** — Buckets OpEx into headcount-driven, volume-driven, discretionary, contractual/fixed, one-time, and timing/phasing

**Materiality Thresholds:**
| Comparison Type | % Threshold | Investigation Trigger |
|----------------|------------|----------------------|
| Actual vs Budget | 10% | Either $ or % exceeded |
| Actual vs Prior Period | 15% | Either $ or % exceeded |
| Actual vs Forecast | 5% | Either $ or % exceeded |
| Sequential (MoM) | 20% | Either $ or % exceeded |

**Outputs:** Waterfall/bridge charts (text or visual), bridge reconciliation tables, narrative explanations with quality checklist, forecast accuracy tracking (MAPE), variance trending analysis.

---

### 2. Journal Entry Preparation

**Trigger:** "journal entry", "JE", "accrual", "depreciation", "amortization", "deferred revenue", "payroll entry"

**Standard Entry Types:**
- **AP Accruals** — Goods/services received but not invoiced. Debit expense, credit accrued liabilities. Auto-reversal recommended.
- **Fixed Asset Depreciation** — Straight-line, declining balance, or units-of-production. Debit depreciation expense, credit accumulated depreciation.
- **Prepaid Amortization** — Monthly amortization of insurance, software licenses, rent, maintenance contracts. Debit expense, credit prepaid.
- **Payroll Accruals** — Salary accrual (for misaligned pay periods), bonus accrual, benefits, payroll taxes, PTO liability.
- **Revenue Recognition** — ASC 606 five-step framework. Recognize deferred revenue, record new receivables, or defer advance payments.

**Documentation Requirements:** Entry description, calculation support, source documents, period, preparer ID, approval per authorization matrix, reversal indicator.

**Approval Matrix:**
| Entry Type | < $50K | $50K–$250K | > $250K |
|-----------|--------|-----------|---------|
| Standard recurring | Accounting Mgr | Accounting Mgr | Accounting Mgr |
| Non-recurring / manual | Accounting Mgr | Controller | CFO / VP Finance |
| Top-side / consolidation | Controller+ | Controller+ | Controller+ |

**Common Errors Checklist:** Unbalanced entries, wrong period, wrong sign, duplicates, wrong account, missing reversal, stale accruals, round-number estimates, incorrect FX rates, missing IC elimination, capitalization errors, cut-off errors.

---

### 3. Reconciliation

**Trigger:** "reconcile", "bank rec", "GL to subledger", "intercompany", "outstanding items"

**Reconciliation Types:**
- **GL to Subledger** — AR, AP, fixed assets, inventory, prepaids, accrued liabilities. Compare GL control account to subledger trial balance.
- **Bank Reconciliation** — GL cash balance vs bank statement. Standard format: bank balance ± deposits in transit ± outstanding checks = adjusted balance = GL balance ± unrecorded items.
- **Intercompany** — Match receivable/payable pairs across entities. Resolve FX rate differences, timing, misclassifications, disputed amounts.

**Reconciling Item Categories:**
1. **Timing differences** — Outstanding checks, deposits in transit, pending interfaces. Clear within 1–5 days, no entry needed.
2. **Adjustments required** — Unrecorded bank charges, interest, recording errors, missing entries. Prepare adjusting JE.
3. **Requires investigation** — Unidentified differences, disputed items, aged items, recurring unexplained differences.

**Aging Escalation:**
| Age | Action |
|-----|--------|
| 0–30 days | Monitor |
| 31–60 days | Investigate |
| 61–90 days | Escalate to supervisor |
| 90+ days | Escalate to management — potential write-off |

---

### 4. Financial Statements

**Trigger:** "P&L", "income statement", "balance sheet", "cash flow", "financial summary", "monthly close report"

**Capabilities:**
- Multi-column income statement (current period, prior period, variance $, variance %, budget, budget variance)
- Key metrics summary: revenue growth, gross/operating/net margins, OpEx as % of revenue, effective tax rate
- Material variance listing with investigation flags and follow-up actions
- Balance sheet in standard GAAP format (current/non-current classification, ASC 210)
- Cash flow statement — indirect method (ASC 230)
- GAAP presentation guidance: ASC 606 revenue disaggregation, SBC classification, restructuring charges, non-GAAP reconciliation

**Period Types:** `monthly`, `quarterly`, `annual`, `ytd` with automatic prior period and prior year comparisons.

**Common Period-End Adjustments:** Accruals, deferrals, depreciation/amortization, bad debt provision (ASC 326), inventory write-downs, FX revaluation, tax provision, fair value mark-to-market, current/non-current reclassification, intercompany elimination.

---

### 5. Close Management

**Trigger:** "month-end close", "close calendar", "close checklist", "close status", "close retrospective"

**5-Day Close Calendar:**
| Day | Key Activities |
|-----|---------------|
| **Pre-Close** | Send reminders, confirm cut-offs, verify sub-systems, preliminary bank rec, review open POs |
| **T+1** | Confirm sub-ledger processing, AP accruals, payroll entries, cash entries, intercompany posting, bank rec, depreciation, prepaid amortization |
| **T+2** | Revenue recognition, remaining accruals, AR/AP subledger recs, inventory adjustments, FX revaluation, begin BS recs |
| **T+3** | Complete BS recs, adjusting JEs, intercompany rec and eliminations, preliminary trial balance, preliminary flux |
| **T+4** | Tax provision, equity roll-forward, soft close, draft financials, detailed flux, management review |
| **T+5** | Final adjustments, hard close, period lock, reporting package, forecast update, retrospective |

**Task Dependency Levels:** 5 levels from no-dependency entries (Level 1) through management review and hard close (Level 5). Critical path: Cash/AP/AR → Subledger recs → BS recs → Tax provision → Draft financials → Management review → Hard close.

**Accelerated 3-Day Close Prerequisites:** Automated recurring JEs, continuous reconciliation, automated IC elimination, pre-close activities before month-end, real-time sub-system integration.

---

### 6. SOX Testing

**Trigger:** "SOX", "SOX 404", "control testing", "sample selection", "ITGC", "workpaper"

**Control Areas:** revenue-recognition, procure-to-pay (P2P), payroll, financial-close, treasury, fixed-assets, inventory, ITGC, entity-level, journal-entries.

**Sample Size Guidance:**
| Frequency | Low Risk | Moderate | High Risk |
|-----------|---------|----------|-----------|
| Annual (1) | 1 | 1 | 1 |
| Quarterly (4) | 2 | 2 | 3 |
| Monthly (12) | 2 | 3 | 4 |
| Weekly (52) | 5 | 8 | 15 |
| Daily (~250) | 20 | 30 | 40 |
| Per-transaction (250+) | 25 | 40 | 60 |

**Selection Methods:** Random, systematic, targeted (judgmental), haphazard — with full documentation requirements.

**Outputs:** Control matrix (CEAVOP assertions), sample selections, testing workpaper templates with pass/fail grids, exception documentation, deficiency classification (deficiency → significant deficiency → material weakness), remediation plans.

---

### 7. Audit Support

**Trigger:** "audit", "audit prep", "PBC list", "control deficiency", "testing workpaper"

**SOX 404 Methodology:** Scoping → Risk assessment → Control identification → Testing (design + operating effectiveness) → Evaluation → Reporting.

**Scoping Criteria:** Quantitative (account balance vs materiality, typically 3–5% of benchmark) and qualitative (complex accounting, fraud susceptibility, prior misstatements, management judgment).

**Control Types Covered:**
- **ITGCs** — Access controls, change management, IT operations (backup, recovery, monitoring)
- **Manual Controls** — Management review, supervisory approval, three-way match, reconciliation prep/review
- **Automated Controls** — System-enforced workflows, duplicate detection, credit limits, auto-calculations, SOD enforcement
- **IT-Dependent Manual** — Manual controls relying on system-generated data (requires IPE testing)
- **Entity-Level** — Tone at top, risk assessment, audit committee oversight, internal audit, fraud programs

**Deficiency Classification:** Deficiency → Significant deficiency → Material weakness. Includes aggregation analysis and remediation framework (root cause, plan, timeline, owner, validation).

---

## Connected Tools (Live Integrations)

| Tool | Purpose | Key Actions |
|------|---------|-------------|
| **Zoho Books** | Accounting / ERP | Invoices, payments, expenses, contacts, items, estimates, organizations |
| **Zoho CRM** | Customer/deal data | Revenue analysis, customer records, deal pipeline for revenue forecasting |
| **Gmail** | Communication | Sending reports, audit correspondence, approval requests |
| **Google Drive** | Document storage | Financial models, supporting docs, workpapers |
| **Slack** | Team communication | Close status updates, blocker escalation, team coordination |
| **Google Calendar** | Scheduling | Close calendar, audit meetings, review deadlines |

**Recommended Additional Connectors:**
| Category | Options |
|----------|---------|
| Data Warehouse | Snowflake, BigQuery, Databricks, Redshift |
| Analytics / BI | Tableau, Looker, Power BI |
| ERP (deeper) | NetSuite, SAP, QuickBooks, Xero |

---

## How to Invoke

From any AI Memory session:

```
"Switch to Finance Agent"
"Finance: run variance analysis on Q1 actuals vs budget"
"/variance-analysis revenue 2026-Q1 vs 2025-Q4"
"/journal-entry ap-accrual 2026-03"
"/reconciliation cash 2026-03"
"/income-statement monthly 2026-03"
"/sox-testing revenue-recognition 2026-Q1"
"Prepare month-end close checklist"
"Book the March depreciation entry"
```

---

## Example Workflows

### Month-End Close
1. `/journal-entry ap-accrual 2026-03` — Generate AP accrual entries
2. `/journal-entry prepaid 2026-03` — Amortize prepaid expenses
3. `/journal-entry fixed-assets 2026-03` — Book depreciation
4. `/reconciliation cash 2026-03` — Reconcile bank accounts
5. `/reconciliation accounts-receivable 2026-03` — Reconcile AR subledger
6. `/income-statement monthly 2026-03` — Generate P&L with flux analysis

### Quarterly Variance Review
1. `/variance-analysis revenue 2026-Q1 vs 2025-Q4` — Analyze revenue variances
2. `/variance-analysis opex 2026-Q1 vs budget` — Investigate OpEx variances
3. Review waterfall analysis and provide context on unexplained variances

### SOX Quarterly Testing
1. `/sox-testing revenue-recognition 2026-Q1` — Revenue control workpapers
2. `/sox-testing procure-to-pay 2026-Q1` — Procurement control testing
3. Review sample selections and document test results

---

## Context Files

Place supporting documents in this directory for the agent to reference:

```
Memory_Agents/Finance/
├── AGENT.md                  ← You are here
├── chart_of_accounts.md      ← (optional) Company COA reference
├── close_calendar.md         ← (optional) Standard close schedule & owners
├── policies.md               ← (optional) Accounting policies & thresholds
├── materiality_thresholds.md ← (optional) Org-specific materiality levels
├── approval_matrix.md        ← (optional) JE and payment approval limits
└── templates/                ← (optional) JE templates, workpapers, rec templates
```

---

## Notes

- For investment-specific analysis (portfolio management, valuations, due diligence), see the **Investment Agent**.
- For revenue strategy and forecasting, this agent pairs with the **Sales Agent** and **Growth-n-Revenue Agent**.
- All outputs can be exported as `.xlsx`, `.pdf`, or `.docx` using the corresponding file creation skills.
- Plugin source files are located at: `/mnt/.remote-plugins/plugin_019Lx8xk8i8t4ogLBPVJ2L98/skills/`
