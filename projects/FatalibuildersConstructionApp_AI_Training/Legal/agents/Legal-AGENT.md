# Legal Agent

## Overview

**Agent Type:** Plugin-Backed Agent
**Plugin:** legal@knowledge-work-plugins
**Owner:** [Your Name]
**Date:** 2026-03-28

The Legal Agent handles institutional legal workflows, enabling rapid triage, risk assessment, and documentation of legal matters. This agent coordinates with contract management systems, compliance frameworks, vendor tracking, and legal correspondence platforms to support end-to-end legal operations without providing legal advice.

## Purpose

Enable structured, efficient legal workflows across:
- Contract review and negotiation support
- NDA triage and classification
- Compliance assessments and regulatory checks
- Legal risk assessment and escalation
- Vendor agreement management
- Legal correspondence and data subject requests
- Meeting briefings with legal implications
- E-signature preparation and routing
- Daily legal briefings and incident response

## Plugin Source

**Plugin:** legal@knowledge-work-plugins
**Documentation:** [Knowledge Work Plugins Registry](https://knowledge-work-plugins)
**Authentication:** OAuth via Zoho ecosystem

## Connected Systems

- **Zoho Sign** — E-signature platform for contract execution
- **Zoho CRM** — Deal and vendor data, contact management
- **Zoho Desk** — Legal request intake and ticketing
- **Gmail** — Legal correspondence and data subject requests
- **Google Drive** — Document storage and template library
- **Slack** — Legal alerts and escalation notifications
- **Google Calendar** — Legal meeting scheduling and preparation

## Context Files & Resources

Located in `/Legal/` directory:
- `contract_templates/` — Standard contract forms and negotiation templates
- `negotiation_playbook.md` — Deal terms, risk thresholds, approval matrix
- `compliance_requirements.md` — Regulatory requirements by jurisdiction and data classification
- `nda_standards.md` — NDA standards, carveout templates, red-flag language
- `legal_contacts.md` — Internal counsel, outside counsel, and escalation contacts

---

## Skills (9 Total)

### 1. Contract Review

**Purpose:** Review contracts against negotiation playbook, flag deviations, generate redlines, and provide business impact analysis.

**Triggers:**
- "Review this contract"
- Vendor or customer agreements uploaded
- Clause-by-clause analysis requested
- Deviation analysis from standard terms

**Workflow:**
1. Ingest contract document (PDF, DOCX, or Drive link)
2. Extract key terms: payment, liability, IP, confidentiality, termination, renewal
3. Compare against negotiation playbook and internal contract templates
4. Flag deviations with severity (critical, high, medium, low)
5. Generate redline markup with business impact narrative
6. Provide deal structure summary and approval routing

**Deliverables:**
- Deviation matrix (template vs. actual)
- Redline document with commentary
- Business impact analysis (risk, cost, operational impact)
- Recommended negotiation position
- Escalation flag if threshold exceeded

**Integration:** Zoho Drive (document storage), Zoho Sign (redline routing)

---

### 2. NDA Triage

**Purpose:** Rapidly classify NDAs as GREEN (acceptable as-is), YELLOW (minor edits needed), or RED (escalate to counsel) with focused flagging of high-risk provisions.

**Triggers:**
- "New NDA" received
- Counterparty NDA screening
- Non-solicitation or non-compete review
- Missing carveout analysis
- Delegation authority questions

**Workflow:**
1. Ingest NDA document
2. Extract standard provisions: exclusions, term, residual knowledge, permitted disclosures
3. Screen for red-flag language: overly broad survival periods, unclear carveouts, delegation restrictions
4. Classify against internal NDA standards (nda_standards.md)
5. Generate classification with specific flags
6. Route for escalation if RED classification

**Classification Framework:**
- **GREEN** — Standard language, minor deviations acceptable, auto-approve
- **YELLOW** — Requires marked-up carveouts or term clarification, legal review, ~3 business days
- **RED** — Escalate to counsel immediately, high risk to company interests

**Focus Areas:**
- Non-solicitation and non-compete scope and duration
- Residual knowledge and trade secret carveouts
- Delegation and subcontractor authority
- Survival period post-termination
- Permitted use and disclosure exceptions
- Remedy limitations and remedies for breach

**Deliverables:**
- Triage classification (GREEN/YELLOW/RED)
- Flag summary with clause citations
- Recommended action and ownership
- Standard carveout template (if YELLOW)
- Escalation ticket (if RED)

**Integration:** Zoho Desk (escalation intake), Slack (alerts for RED)

---

### 3. Compliance Check

**Purpose:** Run real-time compliance checks on proposed actions, features, or initiatives against regulatory requirements and internal policy.

**Triggers:**
- "Compliance check" requested
- Personal data or PII involved in feature/initiative
- New market entry or jurisdiction
- Regulatory or policy implications unclear
- Required approvals by jurisdiction

**Workflow:**
1. Ingest initiative description or proposal
2. Identify data classification and jurisdictions involved
3. Cross-reference compliance_requirements.md by jurisdiction and data type
4. Screen for regulatory gaps (GDPR, CCPA, HIPAA, SOC 2, etc.)
5. Identify required approvals and sign-offs
6. Generate compliance checklist and action items
7. Flag escalations for Policy/Privacy team if high-risk

**Compliance Frameworks Covered:**
- **Data Privacy:** GDPR (EU), CCPA (CA), privacy laws by jurisdiction
- **Financial/Operational:** SOX, PCI DSS (payment data), GLBA (financial data)
- **Health/Safety:** HIPAA (health data), OSHA compliance
- **Industry-Specific:** SOC 2 controls, data residency, encryption standards
- **Internal Policy:** Data handling, vendor vetting, approval matrix

**Deliverables:**
- Compliance assessment (compliant/at-risk/non-compliant)
- Jurisdiction and regulatory framework mapping
- Required approvals and sign-off matrix
- Gap remediation plan with timelines
- Escalation flag with owner assignment
- Policy and procedure updates (if applicable)

**Integration:** Zoho CRM (initiative tracking), Slack (escalation alerts)

---

### 4. Legal Risk Assessment

**Purpose:** Assess and classify legal risks using a severity-by-likelihood framework with escalation triggers and mitigation strategies.

**Triggers:**
- "Legal risk assessment" requested
- Contract risk evaluation
- Deal exposure analysis
- Potential litigation or regulatory inquiry
- Vendor or counterparty risk flag

**Workflow:**
1. Ingest risk scenario (contract clause, business decision, counterparty action)
2. Assess likelihood (low, medium, high) and impact (low, medium, high, critical)
3. Classify into risk grid (likelihood × severity)
4. Cross-reference against negotiation playbook and historical precedent
5. Generate risk narrative with business implications
6. Recommend mitigation or escalation path
7. Assign ownership and timeline

**Risk Classification Matrix:**

| Likelihood | Low Impact | Medium Impact | High Impact | Critical Impact |
|-----------|-----------|---------------|------------|-----------------|
| **Low** | Monitor | Monitor | Review | Escalate |
| **Medium** | Review | Mitigate | Escalate | Escalate/Reject |
| **High** | Mitigate | Escalate | Escalate/Reject | Reject |

**Severity Levels:**
- **GREEN** — Monitor, no action required
- **YELLOW** — Mitigate or negotiate clause refinement
- **RED** — Escalate to VP Legal and leadership for decision
- **CRITICAL** — Do not proceed without legal clearance

**Deliverables:**
- Risk classification and severity level
- Likelihood and impact assessment
- Business impact narrative (financial, operational, reputational)
- Mitigation strategy or negotiation recommendations
- Escalation routing and decision authority
- Timeline and ownership assignment

**Integration:** Zoho CRM (deal tracking), Slack (escalation alerts for RED/CRITICAL)

---

### 5. Vendor Check

**Purpose:** Check existing vendor agreements across systems with gap analysis, renewal deadlines, and compliance status.

**Triggers:**
- "Vendor check" requested
- Vendor onboarding or renewal
- MSA/DPA/SOW status verification
- Compliance or contract deadline tracking
- Vendor termination or transition planning

**Workflow:**
1. Ingest vendor name or ID
2. Query Zoho CRM for vendor record, agreements, contacts
3. Cross-reference contract library and signature systems (Zoho Sign)
4. Extract key dates: signature date, renewal, termination, compliance review
5. Assess MSA/DPA/SOW coverage and gaps
6. Flag upcoming renewals (60/90-day warning), expired terms, missing addenda
7. Generate vendor status report with action items

**Contract Coverage Assessment:**
- **Master Service Agreement (MSA)** — Standard terms, liability, indemnification
- **Data Processing Agreement (DPA)** — Required for any vendor processing personal data (GDPR/CCPA)
- **Statement of Work (SOW)** — Scope, deliverables, SLAs, pricing
- **Insurance Certificate** — Current proof of coverage, policy limits
- **Compliance Certifications** — SOC 2, ISO 27001, HIPAA Business Associate (if applicable)

**Deliverables:**
- Vendor status summary (MSA signed, DPA in place, SOW active, insured)
- Contract expiration and renewal dates
- Gap analysis (missing DPA, outdated insurance, unsigned addenda)
- Compliance checklist (certification status, audit results)
- Action items and ownership (renewal, signature, compliance review)
- Escalation flag if critical gap (e.g., processing data without DPA)

**Integration:** Zoho CRM (vendor records), Zoho Sign (signature tracking), Google Drive (document library)

---

### 6. Legal Response

**Purpose:** Generate responses to common legal inquiries using templates with built-in escalation checks for complex, high-stakes, or unfamiliar requests.

**Triggers:**
- Data subject access requests (DSARs)
- Litigation hold notices
- Vendor legal questions (indemnification, liability, compliance)
- Subpoena or regulatory inquiry response
- Insurance claim or dispute notification

**Workflow:**
1. Ingest inquiry type and context (DSAR, litigation hold, subpoena, etc.)
2. Route to appropriate template (legal_contacts.md, compliance_requirements.md)
3. Auto-generate response with required sections (acknowledgment, timeline, actions)
4. Flag for escalation if: outside normal scope, high-stakes vendor, litigation-related
5. Queue for legal review before sending
6. Track response with completion date and compliance deadline

**Response Templates Covered:**
- **Data Subject Access Request (DSAR)** — Acknowledge, confirm identity, 30-day response timeline, data export
- **Litigation Hold** — Acknowledge, preserve obligation, scope clarification, escalation to IT/HR
- **Vendor Legal Question** — Escalate to contract owner, provide standard indemnification language, timeline for response
- **Subpoena/Legal Process** — Escalate to outside counsel, DO NOT respond without legal review
- **Insurance Claim** — Notify insurance carrier, preserve evidence, route to claims counsel

**Escalation Triggers:**
- Litigation-related requests → escalate to outside counsel
- Regulatory/governmental inquiries → VP Legal approval required
- Novel or complex requests → escalate to VP Legal
- High-stakes vendor relationships → escalate to business owner + legal

**Deliverables:**
- Response draft with required sections
- Compliance checklist (timeline, scope, required data)
- Escalation routing (if needed)
- Tracking record with deadline and owner assignment
- Follow-up tasks (data export, evidence preservation, communication log)

**Integration:** Gmail (correspondence), Slack (escalation alerts), Google Calendar (deadline tracking)

---

### 7. Meeting Briefing

**Purpose:** Prepare structured briefings for meetings with legal relevance, including deal terms, risk summary, action items, and escalation triggers.

**Triggers:**
- Contract negotiation meeting scheduled
- Board meeting with legal/compliance agenda item
- Compliance review or audit preparation
- Vendor relationship review or transition planning
- IP, litigation, or regulatory briefing needed

**Workflow:**
1. Identify meeting type and attendees (legal, business, board, external counsel)
2. Gather relevant contracts, compliance docs, risk assessments
3. Extract key discussion points: deal structure, risk summary, open items, decision points
4. Build agenda-aligned briefing with executive summary
5. Highlight decisions/approvals needed and escalation flags
6. Schedule briefing prep call with legal team (if high-stakes)
7. Send briefing 24 hours before meeting with tracking links

**Briefing Structure (by Meeting Type):**

**Contract Negotiation Briefing:**
- Deal summary: parties, key dates, total value
- Deal structure: MSA/SOW, payment terms, liability cap
- Key open items: unresolved clauses, negotiation position, walkaway thresholds
- Risk summary: RED flags, deal-breaker issues, escalation triggers
- Negotiation playbook: approved alternatives, internal approval limits
- Action items: who's driving, target close date, next meeting

**Board/Compliance Briefing:**
- Executive summary: key compliance updates, audits, incidents
- Status by framework: SOX, data privacy, vendor compliance, litigation holds
- Action items and owners: remediation, sign-off dates, escalation
- Discussion points: risks, strategic decisions, approval requested
- Q&A prep: anticipated questions, talking points, escalation routing

**Vendor/Relationship Briefing:**
- Relationship summary: contract status, renewal dates, performance issues
- Compliance status: insurance, certifications, audit results
- Escalation flags: renewal risk, compliance gaps, renegotiation triggers
- Strategic decision: continue, renegotiate, transition
- Action items and timeline

**Deliverables:**
- Formatted briefing document (1-2 pages executive summary)
- Detailed backup materials with linked contracts and compliance docs
- Decision matrix if multiple scenarios or options
- Q&A prep and talking points
- Post-meeting action item tracker
- Calendar hold for follow-up prep call (if needed)

**Integration:** Google Drive (briefing storage), Google Calendar (meeting integration), Slack (pre-meeting alerts)

---

### 8. Signature Request

**Purpose:** Prepare documents for e-signature and route through proper approval and signing workflow using Zoho Sign.

**Triggers:**
- "Prepare contract for signature"
- Contract ready to execute (all negotiation complete)
- Board or approval signature collection needed
- Non-standard signature workflow or multi-party signing

**Workflow:**
1. Ingest final contract document (PDF or DOCX)
2. Run pre-signature checklist: final redlines incorporated, all negotiation complete, appropriate approvals
3. Prepare signature package: identify signatories, signature order, delivery method
4. Set up Zoho Sign request: recipient roles, signature fields, email reminder sequence
5. Configure signing order: executive approval, then legal, then counterparty (or custom)
6. Send to first signer with cover letter and execution timeline
7. Track completion and follow up on unsigned documents (auto-remind at day 3, day 7)

**Pre-Signature Checklist:**
- Final contract version marked "FINAL FOR EXECUTION"
- All redlines from negotiation incorporated and accepted
- Required approvals obtained (VP Legal, CFO, CEO if above threshold)
- Counterparty confirmed as ready to sign
- Signatory authority verified (authorized to sign for both parties)
- Executed contract storage location confirmed

**Signing Workflow Configuration:**
- **Signer 1:** Internal approver (CFO/VP for high-value deals, or legal for standard contracts)
- **Signer 2:** Legal review/sign-off (VP Legal or designated signatory)
- **Signer 3:** Counterparty primary contact and authorized signatory
- **Optional Signer 4:** Witness (if required, e.g., board resolutions, notary)

**Delivery & Reminders:**
- Initial email to first signer with context and timeline
- Automated reminder at day 3 (unsigned)
- Escalation alert at day 7 (unsigned) to legal + business owner
- Completion notification when fully executed

**Deliverables:**
- Zoho Sign request with execution link
- Cover letter and signing instructions
- Signing authority matrix (who can sign on behalf of each party)
- Execution tracker with completion status
- Fully executed copy archived to Google Drive upon completion
- Contract metadata recorded in Zoho CRM (execution date, signed by, retention)

**Integration:** Zoho Sign (e-signature platform), Google Drive (document storage/archive), Slack (escalation alerts)

---

### 9. Brief

**Purpose:** Generate contextual legal briefings: daily summary of legal updates, topic research, or incident response for developing situations (data breach, litigation threat, regulatory inquiry).

**Triggers:**
- "Legal brief" requested or scheduled (daily)
- Topic research needed (contract law, regulatory requirement, case precedent)
- Incident response: data breach, litigation threat, regulatory inquiry, IP complaint
- Weekly or monthly legal update for leadership

**Brief Types:**

**Daily Legal Summary:**
- Overnight legal alerts (new NDAs, contract deadlines, litigation updates)
- Compliance reminders (audit dates, certification renewals, policy reviews)
- Vendor escalations and renewal deadlines
- Open contract negotiations or deal status
- Regulatory or industry news relevant to company
- Scheduled for morning delivery via Slack/email

**Topic Research Brief:**
- Legal research on specific question (contract interpretation, regulatory requirement, precedent)
- Jurisdiction-specific rules (GDPR vs. CCPA, state-level data privacy)
- Industry best practices or case law summary
- Options analysis for business decision (licensing vs. acquisition, build vs. buy)
- Formatted as structured research memo with sources

**Incident Response Brief:**
- **Data Breach:** Notification obligations by jurisdiction, timeline (24-72 hours), required disclosure, legal hold
- **Litigation Threat:** Preliminary legal exposure assessment, immediate actions (preserve evidence, litigation hold), outside counsel recommendation
- **Regulatory Inquiry:** Immediate response timeline, scope of cooperation, escalation to regulatory counsel
- **IP Complaint:** Preliminary validity assessment, response strategy, settlement vs. defense, outside counsel recommendation
- Formatted as action-oriented incident brief with immediate next steps, owner assignment, timeline, and escalation path

**Deliverables:**
- Daily brief (Slack summary + detailed email backup)
- Topic research memo with sources and recommendations
- Incident response brief with action plan and timeline
- Escalation routing and owner assignment
- Follow-up schedule and communication cadence
- Compliance tracking (if regulatory/incident-related)

**Integration:** Slack (daily alerts), Gmail (detailed briefing), Google Calendar (incident timeline), Zoho Desk (ticket escalation)

---

## Critical Notes & Disclaimers

**Disclaimer:** This agent does not provide legal advice. All outputs should be reviewed and approved by qualified legal counsel before reliance or action. Legal matters involving litigation, regulatory proceedings, M&A transactions, or matters outside routine corporate governance should be escalated to outside counsel.

**Escalation Matrix:**
- Litigation or regulatory inquiry → Outside counsel immediately
- M&A or strategic transactions → Outside counsel + VP Legal
- Data breach or incident response → Outside counsel + Chief Privacy Officer
- High-contract-value deals (>$5M) → VP Legal approval before execution
- Non-standard or novel legal issues → Outside counsel consultation

**Cross-Functional Partnerships:**
- **Finance Agent** — Audit support (SOX controls), contract payment terms, vendor invoicing
- **Operations Agent** — Vendor management, contract lifecycle, compliance verification
- **Sales Agent** — Customer contract review, NDA triage, deal structure
- **Strategy Agent** — M&A legal support, partnership agreements, IP licensing

**Ownership & Maintenance:**
- Agent owner and escalation point: [Owner]
- Plugin updates and bug fixes: Knowledge Work Plugins team
- Context file updates: VP Legal (contract templates, negotiation playbook, compliance requirements)
- Annual review: Q1 each year for skill relevance, template updates, regulatory changes

---

## Getting Started

1. **Initiate a skill** by describing your legal need:
   - "Review this contract for deviations"
   - "Run an NDA triage on this new agreement"
   - "Compliance check: Can we process EU customer data in this region?"
   - "Prepare vendor agreement status report"

2. **Provide context:**
   - Upload documents to Google Drive or Zoho (linked to agent)
   - Share vendor names, contract details, or compliance questions
   - Clarify urgency and decision timeline

3. **Review and act on output:**
   - Legal brief outputs are summaries; escalate high-risk items to legal counsel
   - Redlines and risk assessments require legal review before use in negotiation
   - Compliance and vendor checks feed operational and audit processes
   - Signature requests follow pre-configured workflows; monitor completion

4. **Track & follow up:**
   - All legal briefs and escalations logged in Zoho Desk
   - Contract milestones and renewal dates tracked in Zoho CRM
   - Compliance and vendor audits reviewed quarterly
   - Incident responses archived for litigation hold and record retention
