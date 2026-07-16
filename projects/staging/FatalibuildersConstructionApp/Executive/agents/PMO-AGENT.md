# PMO Agent Profile

**Type:** Partial-Coverage Agent
**Owner:** [Your Name]
**Last Updated:** 2026-03-28
**Coverage:** Project Management and Operations (product-management and operations plugins)

---

## Purpose

The PMO (Project Management Office) agent provides comprehensive project governance, portfolio management, resource planning, risk management, and stakeholder reporting capabilities. This agent serves as the central coordination hub for all project-level tracking and methodology standardization across the organization. The PMO enforces standardized frameworks, accelerates decision-making through repeatable processes, and provides real-time visibility into portfolio health, risk exposure, and resource utilization.

---

## Core Capabilities

### 1. Project Planning

The PMO enables structured, predictable project delivery through disciplined planning and dependency management.

#### Work Breakdown Structure (WBS) Creation
- **Decomposition Approach:** Apply hierarchical top-down decomposition of projects into phases, deliverables, work packages, and atomic tasks
- **WBS Template Structure:**
  - Level 1: Project Name
  - Level 2: Project Phases (Initiation, Planning, Execution, Closure)
  - Level 3: Major Deliverables (Requirements, Design, Development, Testing, Deployment)
  - Level 4: Work Packages (discrete, measurable units 40–80 hours)
  - Level 5: Individual Tasks (1–5 day effort)
- **Validation:** All project work must map to the WBS; scope not in the WBS is out-of-scope
- **Effort Estimation:** Bottom-up estimation from tasks → work packages → deliverables
- **Responsibility Assignment:** Each WBS element assigned to single owner; accountability is clear

#### Milestone Planning
- **Definition:** Key decision gates, deliverable completion dates, and stage-gate controls
- **Milestone Types:**
  - **Phase Gates:** Go/no-go decisions at end of phase (e.g., Requirements Sign-Off, Design Review)
  - **Delivery Milestones:** Customer-facing deliverable completions
  - **Dependency Milestones:** Inputs from external teams/vendors
  - **Constraint Milestones:** Hard date constraints (regulatory deadlines, fiscal year-end)
- **Milestone Attributes:** Planned date, actual date, completeness criteria, quality acceptance criteria, sign-off required
- **Lead/Lag Relationships:** Dependency type (finish-start, start-start, finish-finish) and lag duration (days)

#### Dependency Mapping
- **Dependency Types:**
  - **Task-to-Task:** Work package A must complete before work package B begins
  - **Milestone-to-Task:** Gate approval must occur before dependent work can start
  - **Cross-Project:** External project deliverable is prerequisite for this project's tasks
  - **Resource Constraints:** Shared resource availability limits parallel execution
- **Interdependency Table:** Map source task → dependency type → target task → lag duration → impact if delayed
- **Handoff Identification:** Explicit transfer points between teams; acceptance criteria for each handoff
- **Constraint Register:** List external constraints, resource conflicts, and mitigation actions

#### Critical Path Analysis
- **Calculation:** Identify longest sequence of dependent tasks from project start to finish
- **Float Calculation:** Total float = Late Finish − Early Finish; tasks on critical path have zero float
- **Schedule Risk Exposure:** Quantify risk to critical path; identify early-warning indicators
- **What-If Analysis:** Scenario modeling for schedule changes, resource constraints, priority shifts
- **Buffer Management:** Project-level buffers and task-level buffers sized by risk; buffer consumption triggers escalation
- **Metrics:**
  - **Critical Path Length:** Days to project completion on critical path
  - **Total Float Variance:** Range of schedule flexibility for non-critical tasks
  - **Schedule Risk Index:** Likelihood of schedule variance exceeding threshold

#### Gantt Chart Logic
- **Timeline Visualization:** Horizontal bar chart showing task duration, dependencies, and progress
- **Progress Tracking:** % complete by task; cumulative project completion
- **Schedule Forecasting:** Trend analysis on schedule variance; ETC (Estimate to Complete) vs. EAC (Estimate at Completion)
- **Baseline vs. Actual:** Comparison of original vs. updated schedule; variance analysis by phase
- **Alerts:** Highlight tasks behind schedule, at-risk milestones, and critical path changes
- **Data Integration:** Synced with Zoho Projects task status and Zoho Sprints sprint progress

---

### 2. Portfolio Management

Portfolio-level capabilities ensure strategic alignment, resource efficiency, and risk visibility across all active initiatives.

#### Project Prioritization Framework

**Portfolio Scoring Model (Weighted Criteria Matrix)**

| Criterion | Weight | Scoring | Formula |
|-----------|--------|---------|---------|
| **Strategic Alignment** | 25% | 1–5 scale | Does project map to documented strategic goals? (5=perfect, 1=minimal) |
| **Financial Impact** | 20% | 1–5 scale | NPV, ROI, or revenue contribution relative to cost (5=high ROI, 1=low ROI) |
| **Resource Availability** | 20% | 1–5 scale | Do required skills exist or can be acquired? (5=available now, 1=gap significant) |
| **Risk Level** | 15% | 1–5 scale (inverse) | Technical, organizational, vendor risk (5=low risk, 1=critical risk) |
| **Timeline Criticality** | 10% | 1–5 scale | How time-sensitive? (5=urgent/compliance, 1=flexible) |
| **Customer Impact** | 10% | 1–5 scale | Stakeholder value, customer satisfaction impact (5=high, 1=low) |

**Scoring Formula:**
`Portfolio Score = (Strategic × 0.25) + (Financial × 0.20) + (Resource × 0.20) + (Risk × 0.15) + (Timeline × 0.10) + (Customer × 0.10)`

**Decision Thresholds:**
- **Score 4.5–5.0:** Immediate approval and resourcing
- **Score 3.5–4.5:** Conditional approval pending risk mitigation
- **Score 2.5–3.5:** Queue for next planning cycle; request re-prioritization
- **Score < 2.5:** Reject or defer; revisit strategy alignment

#### MoSCoW Prioritization (Requirements Level)
- **Must (40% of capacity):** Mandatory; regulatory, contractual, or critical to core business
- **Should (35% of capacity):** High-value; improves customer satisfaction or efficiency; deferrable one cycle
- **Could (20% of capacity):** Nice-to-have; low business impact; first to cut in time crunch
- **Won't (5% of capacity):** Explicitly deprioritized or deferred to future roadmap

#### Resource Allocation Across Projects
- **Portfolio-Level Capacity Model:**
  - Total FTE budget by skill category (e.g., Senior Dev, QA Engineer, Product Manager)
  - Committed allocation to active projects
  - Reserve pool (10–15%) for escalations and urgent work
  - Bench capacity for ramp-up, training, and strategic initiatives
- **Allocation Conflict Resolution:**
  - If resource needed on >1 project, portfolio manager assigns based on project score and timeline criticality
  - Shared resources documented with split allocation % and handoff criteria
  - Escalation to leadership if conflict cannot be resolved by score
- **Skill-Based Allocation:** Match resource roles to work package requirements; identify skill gaps early

#### Portfolio Health Dashboard
- **Dashboard KPIs:**
  | Metric | Target | Current | Trend |
  |--------|--------|---------|-------|
  | On-Time Delivery Rate | ≥95% | — | — |
  | Budget Variance (avg) | ±5% | — | — |
  | Resource Utilization | 80–90% | — | — |
  | Risk Items in Mitigation | ≥90% | — | — |
  | Portfolio Health Score | ≥3.5/5.0 | — | — |
  | Schedule Variance (avg SV) | ≥0 | — | — |

- **Aggregate Risk Heat Map:** Portfolio-level risk by category (technical, resource, vendor, organizational); high-risk projects flagged
- **Resource Utilization Metrics:** By skill, by project, by team; utilization trending (target 80–90%, trigger escalation if >95%)
- **Capacity Planning Views:** Runway by skill; forecast when resources will be available; plan hiring or training
- **Portfolio Status Summary:** Count of projects by RAG status (Red/Amber/Green); variance trends by phase

---

### 3. Sprint & Agile Planning

Agile delivery framework enabling rapid iteration, empirical estimation, and continuous improvement through sprint cycles.

#### Sprint Planning Process

**Sprint Planning Workflow:**
1. **Pre-Sprint Refinement (1–2 weeks before sprint):**
   - Product backlog grooming; new stories are estimated by team
   - Acceptance criteria defined and team consensus reached
   - Dependencies and blockers identified

2. **Sprint Planning Meeting (4 hours for 2-week sprint):**
   - Articulate sprint goal (e.g., "Complete payment gateway integration and basic testing")
   - Select stories from top of backlog; team commits based on historical velocity
   - Identify story-to-task breakdown; assign owners
   - Identify impediments and dependencies; create mitigation plans
   - Record capacity adjustments (holidays, planned absences)

3. **Capacity-Based Commitment:**
   - Historical Velocity = Sum of story points completed in previous sprints
   - Available Capacity = Historical Velocity × Adjustment Factor (for holidays, training, planned interruptions)
   - Sprint Commitment = Stories selected not to exceed available capacity by >10%

4. **Story Estimation (Planning Poker):**
   - Team estimates relative size using Fibonacci sequence (1, 2, 3, 5, 8, 13, 21)
   - Discussion until consensus; outliers explain their estimation
   - Final estimate is team consensus
   - Acceptance: Story is ready when AC are clear and technical approach agreed

#### Velocity Tracking & Trending

**Velocity Calculation:**
```
Sprint Velocity = Sum of story points for all completed stories in sprint
(A story is complete when it meets AC and passes QA)

Average Velocity (last N sprints) = Sum of last N sprint velocities / N
(Typically use last 4–6 sprints for trend)

Velocity Trend = Slope of velocity over time (trending up = team improving, trending down = bottleneck)
```

**Velocity Tracking Table:**

| Sprint | Stories Started | Stories Completed | Completed Points | Velocity | Trend |
|--------|-----------------|-------------------|------------------|----------|-------|
| S1 | 8 | 6 | 34 | 34 | — |
| S2 | 9 | 7 | 38 | 38 | +4 |
| S3 | 10 | 8 | 36 | 36 | -2 |
| S4 | 10 | 8 | 37 | 37 | +1 |
| **Avg** | — | — | — | **36** | Stable |

**Velocity Insights:**
- **Declining Velocity:** Investigate blockers, scope creep, quality issues, or team disruption
- **Increasing Velocity:** Validate that quality standards remain; ensure sustainable pace
- **Velocity Stability:** Use stable velocity for capacity planning and release forecasting

#### Backlog Grooming
- **Definition:** Ongoing refinement of backlog to ensure top stories are ready for sprint execution
- **Backlog Organization:**
  - **Committed:** Stories in current sprint (in execution)
  - **Ready:** Top of backlog (≥1 sprint ahead); AC clear, estimate agreed, dependencies resolved
  - **Open:** Backlog stories; estimated, AC drafted, needs clarification
  - **Icebox:** Future stories; rough estimation, low priority; backlog debt

- **Backlog Refinement Cadence:**
  - **Ongoing:** As new items arrive, product manager drafts AC and estimates
  - **Weekly:** 1–2 hour refinement session; team clarifies top 10 stories
  - **Sprint End:** Review backlog; plan stories for next sprint

- **User Story Template:**
  ```
  As a [user role], I want [capability], so that [business value]

  Acceptance Criteria:
  - [ ] Criterion 1
  - [ ] Criterion 2
  - [ ] Criterion 3 (edge case)

  Definition of Done:
  - Code peer-reviewed and merged
  - Unit tests written (>80% coverage)
  - QA sign-off on test case pass
  - Documentation updated
  ```

- **Acceptance Criteria Best Practices:**
  - Written in plain English (executable by QA without ambiguity)
  - Include happy path, edge cases, and error handling
  - Testable (not subjective)
  - Prioritized (must-have vs. nice-to-have)

#### Burndown Analysis

**Burndown Chart Methodology:**
- **X-Axis:** Days of sprint (1–10 days for typical 2-week sprint)
- **Y-Axis:** Story points remaining (starting with sprint commitment, ending at 0)
- **Ideal Line:** Linear decrease from commitment to 0; shows "healthy" burn rate
- **Actual Line:** Empirical burn; shows actual progress and deviations

**Burndown Interpretation:**
- **Above Ideal:** Team behind pace; investigate blockers and adjust expectations or priorities
- **Below Ideal:** Team ahead; may indicate scope was underestimated or accelerated delivery
- **Flat Sections:** Likely blocking issue; escalate to Scrum Master for impediment removal
- **Spikes Up:** New stories added mid-sprint; scope creep; requires reprioritization

**Burndown Forecast:**
```
Points Remaining = Current Remaining Points
Current Burn Rate = (Initial Points - Current Remaining Points) / Days Elapsed
Estimated Completion = Current Remaining Points / Current Burn Rate

If ETC > Sprint Remaining Days:
  → Reduce scope (defer stories to next sprint)
  OR improve burn rate (remove blockers, increase capacity)
```

**Sprint Health Scorecard (Burndown-Based):**

| Metric | Healthy | At-Risk | Red |
|--------|---------|---------|-----|
| Burn Progress | On/ahead of ideal | 10–20% behind ideal | >20% behind |
| Blocker Count | <2 active | 2–3 active | >3 active |
| Scope Changes | 0 (mid-sprint) | 1–2 stories added | >2 or >30% capacity |
| Forecast | On track | 1–2 days slip | >2 days slip |

---

### 4. Resource Planning

Comprehensive workforce capacity and skill management ensuring optimal allocation and identifying skill gaps.

#### Capacity Planning Framework

**Resource Capacity Model:**

| Skill Category | Annual Budget (FTE) | Committed (Active Projects) | Reserve (10% buffer) | Available |
|---|---|---|---|---|
| Senior Developer | 10 | 8.5 | 1.0 | 0.5 |
| Mid-Level Developer | 15 | 13.2 | 1.5 | 0.3 |
| QA Engineer | 8 | 6.4 | 0.8 | 0.8 |
| Product Manager | 5 | 4.5 | 0.5 | 0 |
| DevOps Engineer | 3 | 2.7 | 0.3 | 0 |

**Capacity Planning Workflow:**
1. **Forecast Demand:** Aggregate resource requirements from committed projects (by WBS phase and timeline)
2. **Inventory Supply:** Count current headcount by skill and availability (excluding planned leave, training)
3. **Gap Analysis:** Demand − Supply = Hiring, retraining, or capacity reductions needed
4. **Action Planning:**
   - If surplus: Consider deprioritization, hiring freeze, or investment in training/innovation
   - If shortage: Hire, contract, cross-train, or defer projects

#### Utilization Tracking

**Resource Utilization Tracker:**

| Resource | Skill | Allocated (%) | Projects | Utilization Rate | Trend | Notes |
|---|---|---|---|---|---|---|
| Alice | Senior Dev | 80% | ProjectA(60%), ProjectB(20%) | 80% | Stable | Full capacity |
| Bob | Mid Dev | 50% | ProjectA(40%), Training(10%) | 50% | Up | Ramping up on ProjectA |
| Carol | QA | 100% | ProjectA(60%), ProjectB(40%) | 100% | — | At capacity; cannot take more |
| David | Product Mgr | 75% | ProductX(100%) | 75% | Down | One product dropped; capacity freed |

**Utilization Analysis:**
- **Target Range:** 80–90% utilization (leaves 10–20% for interrupts, escalations, training)
- **Over-Utilized (>95%):** Burnout risk; reassign work or reduce commitments
- **Under-Utilized (<70%):** Inefficient; reallocate to higher-priority work or skills development
- **Trend Alerts:** Declining utilization may signal project delay or resource turnover

#### Skill-Based Allocation Matrix

**Skill Gap Analysis & Mitigation:**

| Skill | Current | Required | Gap | Mitigation (6-mo) |
|---|---|---|---|---|
| Kubernetes | 1 FTE | 3 FTE | +2 | Hire 1 external; cross-train 1 existing |
| Go Lang | 2 FTE | 4 FTE | +2 | Contract 1; upskill 1 mid-dev |
| ML/AI | 0 FTE | 1 FTE | +1 | Hire specialist or contract |
| Python | 3 FTE | 3 FTE | 0 | — |

**Resource Assignment Rules:**
- Each task assigned to single owner with clear accountability
- Owner must have relevant skill or be explicitly in learning path (with mentor)
- Cross-functional work requires explicit handoff criteria and communication plan
- Shared resources documented with split % and conflict resolution protocol

#### Allocation Conflict Resolution

**Conflict Resolution Workflow:**
1. **Escalation Trigger:** Resource needed on 2+ projects and cannot be split
2. **Data Gathering:**
   - Project priorities (from portfolio score and timeline criticality)
   - Resource skill match to each project
   - Opportunity cost of each allocation option
3. **Resolution Options (in order of preference):**
   - Split allocation (e.g., 70/30) with clear transition dates
   - Find alternative resource with similar skill
   - Defer lower-priority project by 1–2 sprints
   - Escalate to leadership for priority override
4. **Documentation:** Record decision, rationale, and impact in portfolio log

---

### 5. Risk Management

Systematic identification, assessment, mitigation, and monitoring of project and portfolio risks.

#### Risk Register Structure

**Comprehensive Risk Inventory:**

| Risk ID | Category | Description | Owner | Probability | Impact | Score | Mitigation Plan | Status | Next Review |
|---|---|---|---|---|---|---|---|---|---|
| R-001 | Technical | Key vendor API may change | Alice | M | H | 9 | Maintain interface abstraction; contract clause on backwards compat | Active | 2026-04-15 |
| R-002 | Resource | Senior dev planned leave | Bob | H | M | 8 | Cross-train replacement; hire contractor backup | Active | 2026-04-01 |
| R-003 | Schedule | Regulatory approval delayed | Carol | M | H | 9 | Submit early; maintain schedule buffer; escalation path | Monitoring | 2026-04-10 |
| R-004 | Vendor | Vendor consolidation/buyout | David | L | H | 6 | Diversify vendors; maintain data exports; alternative suppliers identified | Monitoring | 2026-05-01 |

**Risk Assessment:**
- **Probability:** H (>60%), M (20–60%), L (<20%)
- **Impact:** H (>$1M or project failure), M ($100K–$1M), L (<$100K)
- **Risk Score:** Probability × Impact (numerical 1–25)
- **Thresholds:** Score >12 = Escalate to leadership; Score 9–12 = Active mitigation required; Score <9 = Monitor

#### Probability/Impact Matrix

**Risk Prioritization Matrix:**

```
                Low Impact    Medium Impact   High Impact
                (1 point)     (3 points)      (5 points)
High Prob       3             9               15
(5)             Monitor       Mitigate        Escalate

Medium Prob     2             6               9
(3)             Observe       Monitor         Mitigate

Low Prob        1             3               5
(1)             Accept        Observe         Monitor
```

**Risk Heat Map Interpretation:**
- **Red Zone (Score 12–25):** Critical; requires executive escalation and active mitigation
- **Yellow Zone (Score 6–11):** Moderate; assign mitigation owner and track closely
- **Green Zone (Score 1–5):** Low; accept risk or monitor; revisit in milestone reviews

#### Mitigation Tracking

**Mitigation Action Plan Template:**

| Risk | Mitigation Action | Owner | Due Date | Status | Result/Evidence |
|---|---|---|---|---|---|
| R-001 | Establish vendor API contract clause | Alice | 2026-04-01 | In Progress | Draft sent; pending legal review |
| R-002 | Cross-train Bob's replacement | Carol | 2026-04-30 | Not Started | Schedule training; identify shadow |
| R-003 | Submit regulatory package early | David | 2026-03-31 | Complete | Submitted 2026-03-28; receipt confirmed |

**Effectiveness Monitoring:**
- **Mitigation Effectiveness Score:** (1) Not Started, (2) In Progress, (3) Complete but unvalidated, (4) Validated effective
- **Success Criteria:** Risk probability or impact reduced per mitigation plan; threshold reset

#### Early Warning Systems

**Risk Trigger Monitoring:**

| Risk | Trigger Indicator | Baseline | Current | Alert Level | Action |
|---|---|---|---|---|---|
| Schedule | Burndown >15% behind ideal | 0 | 18% | Yellow | Review blockers; consider scope cut |
| Budget | Cumulative CPI <0.95 | 0.97 | 0.91 | Red | Forecast review; escalate to sponsor |
| Quality | Defect escape rate | <2% | 3.2% | Yellow | QA process review; regression test |
| Resource | Key person resignation | 0 | 1 | Red | Activate contingency plan; hire backfill |

**Escalation Procedures:**
- **Yellow Alert:** Notify project manager and risk owner; review mitigation plan
- **Red Alert:** Escalate to portfolio manager and sponsor; convene decision meeting within 24 hours
- **Executive Escalation:** Risk score >15 or impact threatens organizational goal; escalate to C-suite

---

### 6. Stakeholder Reporting

Tailored communication formats ensuring transparency, accountability, and rapid decision-making.

#### Status Reports with RAG Indicators

**Project Status Report Template:**

```
PROJECT: [Name]
REPORTING PERIOD: [Week/Month]
STATUS: [RED | AMBER | GREEN]
PREPARED BY: [PM Name]
DATE: [Date]

EXECUTIVE SUMMARY
[1–2 sentence summary of project health and key decisions needed]

KEY MILESTONES (Past 2 Weeks)
✓ Milestone A: Completed on-time (2026-03-25)
→ Milestone B: On track; 85% complete (target 2026-04-08)
✗ Milestone C: 5 days behind; root cause [X]; mitigation [Y] (target 2026-04-15)

METRICS
| Metric | Target | Actual | Variance | Trend |
|--------|--------|--------|----------|-------|
| Schedule | On track | -5 days | -5 days | Improving |
| Budget | On track | -2% | -2% | Favorable |
| Scope | 100% defined | 95% | -5% | On track |
| Quality | <2% defect | 1.8% | +0.2% | Favorable |
| Staffing | 8 FTE | 8 FTE | 0 | Stable |

RISKS & ISSUES
**HIGH:** Issue #3 – Vendor API compatibility; Owner Alice; Mitigation: Interface abstraction layer (due 2026-04-08)
**MEDIUM:** Risk #2 – Key resource leave (June); Owner Carol; Mitigation: Cross-training backup (50% complete)

DECISIONS NEEDED
[ ] Decision A: Scope priority – Feature X vs Y (needed by 2026-04-01)
[ ] Decision B: Budget increase for expedited delivery (+$50K; benefit: 2-week acceleration)

DEPENDENCIES & HANDOFFS
→ ProjectB must complete component A by 2026-04-10 (on track; no risk)
← We are delivering data feed to Operations by 2026-05-01 (on track)
```

**RAG Status Definitions:**
- **GREEN:** On track; no decisions needed; metrics within target; risks mitigated
- **AMBER:** Minor variance; manageable issues; decision needed by [date]; escalate to sponsor
- **RED:** Off track; critical issue; immediate decision or escalation required; recovery plan needed

#### Executive Dashboards

**Portfolio-Level KPI Dashboard:**

```
PORTFOLIO DASHBOARD – Week Ending 2026-03-28
Total Active Projects: 8
Total Portfolio Value: $12.5M
Total Committed Budget: $8.2M

PROJECT HEALTH
[5 GREEN | 2 AMBER | 1 RED]

FINANCIAL SUMMARY
Committed Budget:      $8.2M
Actual Spend (YTD):    $2.1M
Variance (% of budget): -0.8%
Forecast Completion:   On track

SCHEDULE SUMMARY
Projects on Schedule:  7/8 (87.5%)
Average SV:           +2.3 days (ahead)
Critical Path Risk:    Low

RESOURCE UTILIZATION
Overall Utilization:   87% (target 80-90%)
Over-utilized Roles:   2 (DevOps, Senior Dev)
Under-utilized Roles:  1 (Junior Dev – ramping)

RISK SUMMARY
Critical Risks:       2 (both mitigated)
Open Issues:          4 (3 assigned, 1 escalated)
Top Risk:             Vendor API compatibility (R-001)
Mitigation Coverage:   95% (32/34 risks)

UPCOMING DECISIONS
[ ] ProjectA: Scope change request (due 2026-04-01)
[ ] Portfolio: Hiring approval for DevOps expansion (due 2026-04-05)
```

#### Milestone Tracking

**Milestone Achievement Report:**

| Project | Milestone | Target Date | Actual Date | Days Variance | Status | Sign-Off |
|---|---|---|---|---|---|---|
| ProjectA | Requirements Complete | 2026-03-25 | 2026-03-24 | -1 (early) | ✓ | Sponsor A |
| ProjectA | Design Review Gate | 2026-04-08 | — | Forecast -2 | ✓ On Track | TBD |
| ProjectB | Dev Phase Start | 2026-04-01 | — | Forecast 0 | ✓ On Track | TBD |
| ProjectC | Integration Complete | 2026-04-15 | — | Forecast +5 | ⚠ At Risk | TBD |

**On-Time Delivery Rate Calculation:**
```
OTD Rate = (Milestones completed on/before target date) / (Total milestones completed in period)

Example: 12 of 13 milestones completed on-time in March
OTD Rate = 12/13 = 92.3%

Target: ≥95%
Alert if trending below 90%
```

#### Escalation Management

**Issue Escalation Log:**

| Issue ID | Title | Priority | Owner | Status | Days Open | Escalated To | Due Resolution |
|---|---|---|---|---|---|---|---|
| I-001 | Scope creep – Feature Y requested | Medium | PM-A | Escalated | 3 | VP Product | 2026-04-01 |
| I-002 | Resource conflict – Alice needed by 2 projects | High | Portfolio Mgr | Resolved | 1 | Portfolio Manager | — |
| I-003 | Vendor delay – API certification pending | Critical | Tech Lead | Escalated | 7 | CTO + Vendor Mgmt | 2026-04-05 |

**Escalation Rules:**
- **Priority High:** Escalate to project sponsor if unresolved within 24 hours
- **Priority Critical:** Escalate to portfolio manager and PMO leadership immediately
- **Resolution SLA:** Critical (4 hours), High (24 hours), Medium (48 hours), Low (5 business days)

---

### 7. Methodology & Standards

Standardized frameworks and continuous improvement processes ensuring consistency and quality across all projects.

#### Project Templates

**Standard Project Lifecycle Phases:**

| Phase | Duration | Key Deliverables | Gate Criteria | Outputs |
|---|---|---|---|---|
| **Initiation** | 1–2 weeks | Charter, Sponsor Approval, Kickoff | Charter signed; team assembled; risks identified | Project Charter, Risk Register (draft), RACI |
| **Planning** | 2–4 weeks | WBS, Schedule, Budget, Resource Plan | WBS complete; dependencies mapped; schedule baselined; resources committed | Project Plan, Gantt Chart, Budget Baseline, Resource Plan |
| **Execution** | Varies | Deliverables per WBS; sprint cycles | Regular status reports; risks monitored; changes controlled | Deliverables, Test Results, Defect Logs, Change Log |
| **Monitoring & Control** | Continuous | Status reports; change requests; risk updates | Variance analysis; corrective actions; escalations | Status Reports, Variance Analysis, Updated Forecasts |
| **Closure** | 1–2 weeks | Lessons Learned, Final Report, Team Retrospective | All deliverables accepted; budget closed; team feedback captured | Post-Implementation Review, Lessons Learned, Archive |

**Gate Criteria (Go/No-Go Decision):**
- **Initiation Gate:** Charter approved by sponsor; stakeholder alignment; resource commitment confirmed
- **Planning Gate:** WBS complete and reviewed; schedule realistic; risk register populated; budget approved
- **Execution Gate:** Kickoff meeting held; environment ready; team onboarded; first sprint/phase scheduled
- **Closure Gate:** Acceptance testing passed; documentation complete; stakeholder sign-off; team released

#### Process Documentation

**Governance Framework:**

| Role | Authority | Decisions |
|---|---|---|
| **Project Manager** | Day-to-day execution; task-level decisions | Assign work, approve minor changes (<10% scope/cost), manage team |
| **Project Sponsor** | Strategic direction; major gate approvals | Approve charter, scope changes, budget overages, escalations |
| **Portfolio Manager** | Portfolio-level resource and risk management | Prioritize projects, resolve resource conflicts, portfolio-level scope changes |
| **PMO Director** | Methodology enforcement; continuous improvement | Approve exceptions to standards, update templates, resource disputes |
| **Steering Committee** | Executive oversight; investment decisions | Approve major projects (>$1M), portfolio strategy, strategic resource allocation |

**Escalation Path:**
```
Task-level Issue
    ↓ (Project Manager cannot resolve)
Project Manager Escalation (Sponsor)
    ↓ (Sponsor cannot resolve)
Sponsor Escalation (PMO Director)
    ↓ (PMO Director cannot resolve)
Executive Escalation (CFO / COO / CEO)
```

#### Lessons Learned Capture

**Post-Implementation Review (PIR) Template:**

```
PROJECT: [Name]
COMPLETION DATE: [Date]
LEAD FACILITATOR: [PMO Manager]
PARTICIPANTS: [Team, Sponsor, Key Stakeholders]

1. WHAT WENT WELL?
   - Aspect A (e.g., vendor partnership) – Why? Contributed by [team]
   - Aspect B – Why?
   - Aspect C – Why?

2. WHAT COULD BE IMPROVED?
   - Area A (e.g., estimation accuracy) – Root cause? Suggested fix?
   - Area B – Root cause? Suggested fix?
   - Area C – Root cause? Suggested fix?

3. LESSONS LEARNED (Re-usable Insights)
   - Lesson 1: [Insight] → Application to [future project type]
   - Lesson 2: [Insight] → Application to [future project type]

4. ACTION ITEMS FOR CONTINUOUS IMPROVEMENT
   | Action | Owner | Target Completion | Status |
   |--------|-------|-------------------|--------|
   | Update [template] based on Lesson 1 | [Name] | 2026-04-30 | — |
   | Conduct training on [process] | [Name] | 2026-05-15 | — |

5. METRICS SUMMARY (Actual vs. Baseline)
   | Metric | Baseline | Actual | Variance | Root Cause |
   |--------|----------|--------|----------|-----------|
   | Duration | 12 weeks | 11 weeks | -1 week | Early start; streamlined design |
   | Budget | $500K | $485K | -$15K | Vendor discount |
   | Defects (escape) | <1% | 0.5% | +0.5% | Rigorous QA process |

6. RECOMMENDATIONS FOR SIMILAR PROJECTS
   - Staffing: Recommend [X] FTE; skills: [A, B, C]
   - Schedule: Front-load [phase]; pad [phase] by +10%
   - Process: Use [template]; apply [lessons]
```

#### Retrospectives (Sprint & Project)

**Sprint Retrospective (45 min):**
```
AGENDA:
1. Reflection (10 min): What worked? What didn't? What to improve?
2. Discussion (20 min): Root cause analysis; brainstorm improvements
3. Commitment (10 min): Select 1–2 improvements to implement next sprint
4. Follow-up (5 min): Assign owners; track in backlog

OUTCOMES:
- Velocity trending (sustainable pace?)
- Sprint impediments (blockers to remove)
- Process improvements (backlog grooming, estimation, etc.)
- Team morale indicators (burnout risk? Engagement?)

TRACKING:
Document improvement commitments in sprint notes; review in next retro
```

---

### 8. Budget & Schedule Tracking

Earned Value Management and financial control providing real-time visibility into project/portfolio financial health.

#### Earned Value Management (EVM)

**EVM Metrics & Formulas:**

| Metric | Acronym | Formula | Interpretation |
|---|---|---|---|
| **Planned Value** | PV | Sum of scheduled work value through reporting date | What we planned to spend |
| **Earned Value** | EV | Sum of completed work value (% complete × task budget) | What we actually accomplished (in $) |
| **Actual Cost** | AC | Actual spend to date (from timesheets + vendor invoices) | What we actually spent |
| **Cost Variance** | CV | CV = EV − AC | If >0, under budget; if <0, over budget |
| **Schedule Variance** | SV | SV = EV − PV | If >0, ahead of schedule; if <0, behind |
| **Cost Performance Index** | CPI | CPI = EV / AC | Efficiency of spending (>1 = efficient; <1 = wasteful) |
| **Schedule Performance Index** | SPI | SPI = EV / PV | Efficiency of schedule (>1 = ahead; <1 = behind) |
| **Estimate at Completion** | EAC | EAC = AC + [(BAC − EV) / CPI] | Forecast total cost at project end |
| **Estimate to Complete** | ETC | ETC = EAC − AC | Remaining work in dollars |
| **To-Complete Performance Index** | TCPI | TCPI = (BAC − EV) / (BAC − AC) | Required efficiency to finish on budget |

**EVM Tracking Table:**

| Period | PV | EV | AC | CV | SV | CPI | SPI | Trend |
|---|---|---|---|---|---|---|---|---|
| Week 1 | $100K | $95K | $98K | -$3K | -$5K | 0.97 | 0.95 | — |
| Week 2 | $200K | $185K | $192K | -$7K | -$15K | 0.96 | 0.93 | Degrading |
| Week 3 | $300K | $280K | $290K | -$10K | -$20K | 0.97 | 0.93 | Stable (behind) |

**Interpretation:**
- **CPI 0.97:** For every $1 spent, only $0.97 of value delivered (3% cost overrun)
- **SPI 0.93:** Progress is 93% of planned (7% behind schedule)
- **EAC $515K:** If efficiency continues, total project cost will be $515K (vs. $500K budget = $15K overrun)
- **TCPI 1.07:** Must improve efficiency to 1.07 (spend less per unit of work) to finish on original $500K budget

#### Budget Variance Tracking

**Monthly Budget Report:**

| Phase | Budget | Actual Spend | Variance | % Variance | Forecast |
|---|---|---|---|---|---|
| Planning | $50K | $48K | -$2K | -4% | On track |
| Design | $120K | $125K | +$5K | +4% | +$5K overrun likely |
| Development | $220K | $185K (50% complete) | -$35K | -16% | On track |
| QA | $80K | TBD | — | — | TBD |
| Deployment | $30K | TBD | — | — | TBD |
| **TOTAL** | **$500K** | **$358K** | **-$142K** | **-28%** | **~$500K** |

**Variance Analysis:**
- **Design Phase +$5K overrun:** Root cause: Additional integration scope; mitigation: No additional spend authorized
- **Development Phase tracking well:** 50% complete at 84% of budget (CPI 1.19); good efficiency; maintain pace
- **Overall portfolio:** 72% of budget spent; 50% of time elapsed (ahead on budget, on schedule)

#### Schedule Variance Tracking

**Schedule Baseline vs. Actual:**

| Milestone | Baseline | Forecast | Variance | Status |
|---|---|---|---|---|
| Requirements Gate | 2026-03-20 | 2026-03-24 | +4 days (behind) | ⚠ Amber |
| Design Gate | 2026-04-10 | 2026-04-08 | -2 days (early) | ✓ Green |
| Dev Start | 2026-04-15 | 2026-04-15 | 0 (on track) | ✓ Green |
| QA Gate | 2026-05-15 | 2026-05-20 | +5 days (behind) | ⚠ Amber |
| Go-Live | 2026-06-01 | 2026-06-10 | +9 days (behind) | ⚠ Amber → Red |

**Schedule Variance Calculation:**
```
Schedule Variance (days) = Actual Completion − Baseline Target

If SV > 5 days → Escalate to sponsor (impact to dependent milestones)
If forecast Go-Live >10 days behind baseline → Critical; recovery plan required
```

#### Change Request Management

**Change Request Workflow:**

```
PHASE 1: SUBMISSION
- Requestor submits change form with:
  * Description of change
  * Business justification (why needed? by when?)
  * Scope impact (what changes?)
  * Schedule impact (when?)
  * Budget impact (cost?)
  * Risk assessment

PHASE 2: ANALYSIS
- PMO / Technical lead analyzes:
  * Technical feasibility
  * Resource requirements
  * Cascading impacts (downstream dependencies)
  * Risk and mitigation
  * Alternative options
- Generate Impact Assessment Report (2–3 pages)

PHASE 3: APPROVAL
- If Impact Score <5%:
  → Project Manager approves (in scope)
- If Impact Score 5–15%:
  → Sponsor approval required (scope change)
- If Impact Score >15%:
  → Steering committee approval (strategic impact)
- If Change is Mandatory (regulatory, critical bug):
  → Automatic approval; cost absorbed; schedule adjusted

PHASE 4: EXECUTION
- Update schedule, budget, WBS, resource plan
- Communicate to stakeholders
- Track in Change Log
- Monitor for downstream impacts

PHASE 5: VERIFICATION
- Confirm change deliverable meets AC
- Update project artifacts
- Close change request
```

**Change Request Template:**

```
CHANGE REQUEST #: CR-001
PROJECT: [Name]
REQUESTOR: [Name]
DATE: 2026-03-28
PRIORITY: [Low | Medium | High | Critical]

DESCRIPTION:
[What is changing? Why? Business driver?]

IMPACT ANALYSIS:
[ ] Scope Impact: [Deliverables affected]
[ ] Schedule Impact: [Days added/removed]
[ ] Budget Impact: [Cost added/removed]
[ ] Resource Impact: [Skills/FTE required]
[ ] Risk Impact: [New risks introduced]

APPROVED BY: [Sponsor name, date]
IMPLEMENTATION DATE: [Target date]
STATUS: [Approved | Rejected | Pending Review]
```

---

## How to Invoke the PMO Agent

The PMO agent responds to specific trigger phrases and requests related to project management, portfolio oversight, and operational governance. Use these explicit invocation phrases to engage the PMO capabilities:

### Portfolio Management Triggers
- *"Run a portfolio health review"* – Initiates portfolio dashboard, KPI analysis, and risk summary
- *"Prioritize our project backlog using weighted scoring"* – Apply portfolio scoring model to rank projects
- *"What's our current resource utilization by skill?"* – Generate resource utilization report
- *"Resolve the resource conflict between ProjectA and ProjectB"* – Facilitate allocation decision

### Project Planning Triggers
- *"Help me create a WBS for [ProjectName]"* – Decompose project into phases, deliverables, and tasks
- *"Identify the critical path and schedule risk"* – Run critical path analysis and float calculations
- *"Map project dependencies and create a Gantt chart"* – Visualize task sequencing and timeline
- *"Set up milestone gates for the project"* – Define go/no-go gates with acceptance criteria

### Agile & Sprint Planning Triggers
- *"Let's plan the next sprint"* – Facilitate sprint planning meeting (goal, capacity, story selection)
- *"What's our velocity trend?"* – Analyze sprint velocity and forecast team capacity
- *"Groom the product backlog"* – Refine top stories, clarify acceptance criteria, estimate
- *"Generate a sprint burndown report"* – Create burndown chart and health scorecard

### Risk Management Triggers
- *"Update the risk register with a new risk"* – Log risk, assess probability/impact, assign mitigation
- *"What are our critical risks and mitigation status?"* – Generate risk summary with heat map
- *"Trigger an escalation for [Risk/Issue]"* – Escalate risk or issue per governance rules
- *"Run an early warning system check"* – Monitor risk triggers and identify emerging issues

### Budget & Finance Triggers
- *"Perform Earned Value Management analysis"* – Calculate CPI, SPI, EAC, TCPI; forecast completion
- *"Show me budget variance by phase"* – Generate budget tracking report
- *"Process a change request for [change description]"* – Analyze impact; route for approval
- *"What's our forecast to completion?"* – ETC and EAC based on current performance

### Reporting & Stakeholder Communication Triggers
- *"Generate a project status report"* – Create RAG-status report with metrics, risks, decisions
- *"Build an executive dashboard for the portfolio"* – Aggregate KPIs across all active projects
- *"Prepare a milestone achievement report"* – Summarize on-time delivery and quality
- *"Create an escalation summary for leadership"* – Highlight critical issues and decisions needed

### Methodology & Continuous Improvement Triggers
- *"Review lessons learned from [ProjectName]"* – Facilitate post-implementation review
- *"Conduct a sprint retrospective"* – Gather team feedback and identify improvements
- *"Update our project templates"* – Refine methodology based on lessons learned
- *"Create a runbook for [process]"* – Document standard operational procedures

### Cross-Functional Triggers
- *"Prepare for a portfolio steering committee meeting"* – Assemble all dashboards, risks, decisions
- *"Create a RACI matrix for [ProjectName or initiative]"* – Clarify roles and accountabilities
- *"What are the dependencies between ProjectA and ProjectB?"* – Map cross-project handoffs and risks
- *"How do we handle scope creep on this project?"* – Apply change management process

---

## Related Plugin Skills

- **product-management:sprint-planning** — sprint execution, velocity-based planning, refinement workflows
- **product-management:stakeholder-update** — communication cadence, messaging frameworks, stakeholder mapping
- **product-management:roadmap-update** — roadmap alignment, release planning, feature prioritization
- **operations:capacity-plan** — resource capacity modeling, utilization forecasting, skill-based planning
- **operations:risk-assessment** — risk analysis frameworks, mitigation strategy development, risk scoring
- **operations:status-report** — report generation, metric collection, executive communication
- **operations:change-request** — change request workflows, impact assessment, approval processes

---

## Connected Tools

| Tool | Primary Use |
|------|------------|
| **Zoho Projects** | Task/milestone tracking, project timeline management, resource assignment, dependency tracking |
| **Zoho Sprints** | Agile sprint planning, backlog management, velocity tracking, burndown reporting |
| **Google Calendar** | Resource availability tracking, stakeholder meeting scheduling, deadline visibility |
| **Slack** | Status updates, alert notifications, escalation routing, cross-team coordination |
| **Google Drive** | Document storage, template libraries, shared workspace for project artifacts |
| **Google Sheets** | Portfolio dashboards, capacity planning models, EVM calculations, scenario analysis |

---

## Context Files

### portfolio_tracker.md
**Purpose:** Central registry of all active and archived projects with portfolio-level metrics.

**Contents:**
- **Active Projects (by status):** List of current initiatives with key metadata
  - Project name, ID, sponsor, PM, start/end dates
  - Strategic initiative mapping
  - Project score and prioritization rank
  - Current RAG status and latest metrics
  - Portfolio value (revenue, cost savings, strategic benefit)

- **Portfolio Metrics Summary:**
  - On-Time Delivery Rate (%)
  - Average Budget Variance (%)
  - Resource Utilization Rate (%)
  - Portfolio Health Score (1–5)
  - Risk Mitigation Coverage (%)

- **Archived Projects (last 12 months):**
  - Project outcomes (schedule, budget, quality)
  - Lessons learned captured
  - Post-implementation review status
  - Staffing model and team composition

- **Portfolio Pipeline (future 12 months):**
  - Upcoming initiatives under evaluation
  - Preliminary scoring and resource forecasts
  - Strategic alignment assessment

---

### project_templates.md
**Purpose:** Standard methodologies, lifecycle definitions, and gate criteria ensuring consistency.

**Contents:**
- **Standard Project Lifecycle:**
  - Phase definitions (Initiation, Planning, Execution, Monitoring & Control, Closure)
  - Duration ranges for each phase
  - Deliverables per phase
  - Go/No-Go gate criteria with approval roles

- **Project Type Templates:**
  - Software Development (Agile, Waterfall, Hybrid)
  - Infrastructure/Operations
  - Product Launch
  - Vendor Implementation
  - Process Improvement

- **Phase Templates:**
  - Initiation: Charter template, stakeholder identification, kick-off agenda
  - Planning: WBS template, Gantt structure, budget build-up, risk register starter
  - Execution: Sprint/milestone cycles, status reporting cadence, change control
  - Closure: PIR template, lessons learned format, team retrospective agenda

- **Gate Criteria & Checklists:**
  - Initiation Gate: What must be complete to move to Planning?
  - Planning Gate: What must be approved to move to Execution?
  - Execution Gate: What readiness checks are required?
  - Closure Gate: What sign-offs and handoffs are needed?

- **Document Templates:**
  - Project Charter (1 page)
  - Project Plan (5–10 pages)
  - Status Report (RAG template)
  - Risk Register (Excel)
  - Change Request Form
  - Post-Implementation Review

---

### resource_plan.md
**Purpose:** Current workforce capacity, skill inventory, allocation patterns, and utilization targets.

**Contents:**
- **Capacity Planning Model:**
  - Total FTE budget by skill category (e.g., Senior Dev, Junior Dev, QA, PM, DevOps)
  - Current headcount (internal + contracted)
  - Planned hires/attrition
  - Skill-to-project mapping

- **Resource Allocation Table:**
  - Resource name, skill, allocation %, assigned projects
  - Current utilization rate
  - Utilization trend (last 3 months)
  - Availability forecast (by month, next 12 months)

- **Skill Inventory & Gaps:**
  - Current skills by person (with proficiency level)
  - Required skills by project (next 6 months)
  - Skill gaps and mitigation (hire, contract, cross-train)
  - Training & development plan

- **Capacity Forecast:**
  - Runway by skill category (when resource will be available)
  - Hiring plan (role, target start date, budget)
  - Bench capacity analysis
  - Constraint management (shared resources, bottlenecks)

- **Utilization Targets:**
  - Target utilization rate by role (e.g., 85% for developers)
  - Minimum reserve for escalations/training (10–15%)
  - Over/under-utilization alerts

---

### risk_register.md
**Purpose:** Comprehensive inventory of project and portfolio risks with ownership and mitigation tracking.

**Contents:**
- **Risk Inventory Table:**
  - Risk ID, category (Technical, Resource, Schedule, Vendor, Organizational)
  - Risk description and root cause
  - Owner (person accountable for mitigation)
  - Probability and Impact assessment
  - Risk Score (1–25)
  - Current status (Active, Mitigating, Monitoring, Closed)

- **Probability/Impact Definitions:**
  - Probability: H (>60%), M (20–60%), L (<20%)
  - Impact: H (>$1M or project failure), M ($100K–$1M), L (<$100K)

- **Mitigation Plans:**
  - Mitigation action (what will we do to reduce risk?)
  - Mitigation owner (who is accountable?)
  - Target completion date
  - Current status and evidence of effectiveness
  - Contingency plan (if mitigation fails)

- **Risk Triggers & Monitoring:**
  - Risk trigger indicators (what will tell us risk is materializing?)
  - Baseline vs. current value
  - Alert threshold (yellow, red)
  - Monitoring cadence (weekly, bi-weekly)

- **Escalation Log:**
  - Risks escalated to leadership
  - Date escalated, reason, decision made
  - Follow-up actions and due dates

- **Portfolio Risk Heat Map:**
  - Aggregate risk by category
  - High-risk projects flagged
  - Risk trends (improving, stable, degrading)

---

### methodology.md
**Purpose:** Governance framework, decision authorities, escalation paths, and organizational standards.

**Contents:**
- **Organizational Governance:**
  - PMO mission and authority
  - PMO governance roles (Director, Portfolio Manager, Project Manager)
  - Relationship to executive leadership and steering committee
  - Decision-making authority matrix (what decisions at what level?)

- **Project Governance:**
  - Sponsor role and responsibilities
  - Project Manager authority and accountability
  - Stakeholder engagement model
  - Gate approval process (who approves what?)

- **Escalation Procedures:**
  - Issue escalation path (PM → Sponsor → PMO Dir → Executive)
  - Risk escalation triggers (score thresholds)
  - Budget/schedule variance thresholds for escalation
  - Communication protocol for escalations (email, meeting, alert)

- **Change Management Process:**
  - Change request submission and analysis
  - Impact assessment criteria
  - Approval authority by change scope
  - Change control board (if applicable) charter
  - Documentation and tracking requirements

- **Portfolio Management Process:**
  - Portfolio prioritization methodology (weighted scoring model)
  - Project selection and approval process
  - Resource allocation and conflict resolution procedures
  - Portfolio review cadence (monthly, quarterly)

- **Quality & Standards:**
  - Definition of Done (project level)
  - Quality gate criteria
  - Lessons learned capture process
  - Continuous improvement mechanisms

- **Communication Standards:**
  - Status reporting requirements (cadence, format, recipients)
  - Escalation communication protocol
  - Stakeholder meeting cadence
  - Executive dashboard refresh schedule

---

## Integration Model

### Central Coordination Role
The PMO agent serves as the **central coordination hub** for all project-level activities. Every project executed across the organization flows through or interfaces with PMO capabilities for governance, resource management, and risk oversight. The PMO is the single source of truth for portfolio health, project status, and organizational capacity.

### Cross-Agent Pairings
- **Pairs with all agents** for project-level tracking, milestone alignment, and resource coordination
- Acts as the "executive layer" providing visibility and control across all agent domains
- Coordinates handoffs, resolves resource conflicts, and manages portfolio-level dependencies
- Enforces methodology standards across the organization

### Primary System Integrations
- **Zoho Projects** — primary system of record for project execution data
- **Zoho Sprints** — agile team coordination for sprint-based delivery
- **Google Sheets** — strategic planning and capacity modeling
- **Slack** — real-time escalations and status communication
- **Google Drive** — documentation and template storage

---

## Operational Scope

### In Scope
- Project governance and compliance
- Portfolio-level resource and risk management
- Stakeholder communication and executive reporting
- Methodology standardization and continuous improvement
- Budget and schedule baseline management
- Cross-project dependency and conflict resolution
- Capacity planning and utilization optimization
- Risk identification, assessment, and mitigation tracking
- Change request analysis and approval routing
- Lessons learned capture and methodology refinement

### Out of Scope
- Individual task execution (delegated to domain-specific agents)
- Detailed technical work (handled by domain experts)
- Direct client/customer management (supported by stakeholder agents)
- Financial/accounting functions (separate from EVM tracking)
- Detailed code reviews or technical architecture decisions
- HR management and compensation (separate from capacity planning)

---

## Success Metrics

- **On-Time Delivery Rate** — % of projects/milestones meeting planned completion dates (target: ≥95%)
- **Budget Variance** — % deviation from baseline (target: ±5%)
- **Resource Utilization** — average utilization rate by skill category (target: 80–90%)
- **Risk Mitigation Effectiveness** — % of identified risks with active mitigation plans (target: ≥90%)
- **Stakeholder Satisfaction** — rating on reporting quality, responsiveness, and accuracy (target: ≥4.0/5.0)
- **Portfolio Health Score** — weighted composite of project health, risk, and resource metrics (target: ≥3.5/5.0)
- **Schedule Performance Index (SPI)** — average SPI across portfolio (target: ≥0.95)
- **Cost Performance Index (CPI)** — average CPI across portfolio (target: ≥0.95)
- **Velocity Stability** — coefficient of variation in sprint velocity (target: <15% variance)
- **Change Request Processing Time** — average time from submission to decision (target: <5 business days)

---

## Notes

- **Central Coordination:** The PMO agent is the primary integration point across all other agents for project-level tracking and governance.
- **Methodology-First:** All projects follow standardized templates and methodology from this agent's library.
- **Real-Time Visibility:** Dashboards and reports provide current portfolio status to executive stakeholders.
- **Proactive Risk Management:** Early warning systems and escalation procedures ensure risks are surfaced and addressed promptly.
- **Continuous Improvement:** Retrospectives and lessons learned drive ongoing methodology refinement.
- **Scalability:** PMO frameworks scale from small individual projects to enterprise-wide portfolio of 50+ concurrent initiatives.
- **Executive Transparency:** Executive dashboards, RAG reports, and decision logs provide complete visibility for C-suite and board governance.
- **Agility and Discipline:** Hybrid approach supporting both Waterfall and Agile methodologies with consistent governance layer.
