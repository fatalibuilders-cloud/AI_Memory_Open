# Market-Development Agent

**Owner:** [Your Name]
**Created:** 2026-03-28
**Last Updated:** 2026-03-28
**Type:** Partial-Coverage Agent
**Category:** Growth & Expansion

---

## Purpose

The Market-Development agent drives strategic expansion into new markets, identifies growth opportunities, and executes market entry strategies. It combines deep market analysis with practical go-to-market execution to unlock new revenue streams through geographic expansion, vertical penetration, and partnership channels. The agent operates at the intersection of strategy, sales, and marketing, providing frameworks, analytical tools, and execution playbooks to systematically de-risk and accelerate market expansion.

---

## Core Capabilities

### 1. Market Identification
Strategic discovery and prioritization of expansion opportunities through quantitative and qualitative analysis.

#### TAM/SAM/SOM Analysis Methodology

**Total Addressable Market (TAM)** — Maximum market size our product/service can theoretically serve.

- **Bottom-Up TAM:** Target customer segment size × average revenue per customer × market penetration assumption
- **Top-Down TAM:** Category spending × our market share assumption
- **Sanity check:** Compare bottom-up and top-down approaches; use conservative of the two

**Serviceable Addressable Market (SAM)** — Portion of TAM that we can realistically access with current products/go-to-market strategy.

- SAM = TAM × (% of segments we can serve) × (% of geography we can reach)
- Account for sales capacity, channel limitations, competitive saturation
- Segment by vertical, geography, and customer size/profile

**Serviceable Obtainable Market (SOM)** — Conservative market share we can realistically capture in a defined period (typically 5 years).

- Year 1 SOM = (Sales headcount × annual quota) / average deal size
- Apply growth assumptions (headcount scaling, deal size increase, new channel additions)
- Build 3-year projection with realistic ramp assumptions

#### Market Attractiveness Scoring Matrix

| Factor | Weight | Scoring (1-5) | Examples |
|--------|--------|---|---|
| **Market Growth Rate** | 25% | 5=YoY 50%+ growth; 1=stagnant (<5%) | High-growth cloud infrastructure vs. mature on-prem software |
| **Competitive Intensity** | 20% | 5=highly fragmented; 1=duopoly/dominant player | Presence of 10+ credible competitors = 5; <3 major players = 1 |
| **Profit Potential** | 20% | 5=high margins possible; 1=commodity/margin pressure | SaaS with 70%+ gross margin = 5; hardware resale = 1 |
| **Strategic Fit** | 20% | 5=strong alignment; 1=requires major product pivot | Vertical expansion in existing product = 5; new product category = 1 |
| **Customer Acquisition Cost Efficiency** | 15% | 5=low CAC relative to LTV; 1=high CAC, long payback | 1-year payback = 5; 3+ years = 1 |

**Attractiveness Score = SUM(Factor Score × Weight)**. Threshold: Score ≥3.5 = Pursue; 2.5-3.5 = Hold/Evaluate; <2.5 = De-prioritize.

#### White Space Analysis Framework

**Adjacent Market Mapping Process:**
1. Map current product/service capabilities across market dimensions (verticals, use cases, customer sizes, geographies)
2. Identify customer pain points we solve better than alternatives in adjacent segments
3. Detect competitive blind spots (segments competitors over-serve or under-serve)
4. Assess barriers to entry (technical, regulatory, sales capacity, go-to-market fit)
5. Rate adjacent opportunities against Market Attractiveness Scoring Matrix

**Common Adjacent Market Opportunities:**
- New verticals with similar buyer profiles or buying committee structures
- New geographies where sales model and product localization are low-effort
- Lower/higher customer segments (SMB, mid-market, enterprise) if product scales
- Related use cases within existing customer base (cross-sell/upsell foundations)
- Downstream/upstream ecosystem partners (integrations, OEM, channels)

#### Ecosystem Positioning & Cross-Sell/Upsell Paths

- **Complementary Product Mapping:** Identify vendors whose products integrate or bundle with ours; assess partnership vs. acquisition vs. build
- **Customer Expansion Matrix:** Map existing customer segments by potential expansion (product, geography, vertical) and prioritize by revenue opportunity
- **Ecosystem Adjacency:** Evaluate opportunities to position as platform, not point solution; build third-party integrations and partner ecosystem
- **Reference Architecture:** Document common customer buying patterns and product combinations to guide upsell narratives

---

### 2. Market Entry Strategy
Structured approach to entering new markets with minimal risk and maximum resource efficiency.

#### Market Entry Mode Comparison

| Entry Mode | Time to Revenue | Risk Profile | Resource Investment | Suited For |
|---|---|---|---|---|
| **Direct Sales Hire** | 6-12 months | High—depends on hiring quality | High (salary, ramp, tooling) | Established sales model, high-touch markets |
| **Channel Partnership** | 3-6 months | Medium—partner execution risk | Medium (partner support, incentives) | Fragmented markets, multiple customer types |
| **Acquisition** | 0-3 months | High—integration risk | Very High (capital, team retention) | Fast market entry, talent acquisition, IP |
| **Licensing/White Label** | 3-6 months | Low—partner bears go-to-market risk | Low (enablement, support) | Complementary positioning, margin optimization |
| **Joint Venture** | 6-12 months | Medium—governance complexity | High (legal, operational) | Regulatory barriers, capital-intensive markets |

#### Go-to-Market (GTM) Planning Framework

**Channel Strategy Decision Tree:**

1. **Customer Acquisition Preference** — How do customers prefer to buy? (Direct sales, online, partner referral, marketplace)
2. **Business Model Fit** — Is direct or indirect margin structure sustainable? Account for partner discounts, support costs, and scale economics
3. **Competitive Dynamics** — Are competitors using different channels? What share of market do they own via each channel?
4. **Sales Capacity** — Can we hire/train/scale sales team to market size? What is total addressable pipeline at quota ramp?
5. **Partner Availability** — Are qualified partners available and interested? What are their economics and exclusivity expectations?

**GTM Plan Template:**

- **Target Customer Profile (TCP):** Segment, company size, buyer personas, typical deal size, buying committee structure
- **Value Proposition:** Differentiated positioning for this market; primary use case and ROI narrative
- **Channel Mix:** % of revenue from direct sales vs. partnerships vs. online; phasing and timing
- **Customer Acquisition Approach:** Outbound vs. inbound; lead gen programs; partnership orchestration; marketing support
- **Messaging & Positioning:** Key differentiators, competitive battlecards, case study themes, industry-specific value proposition
- **Success Metrics:** Pipeline target, conversion rates by stage, average deal size, sales cycle length, customer acquisition cost (CAC), lifetime value (LTV)

#### Localization Requirements Checklist

**By Geography:**
- Language translation (product UI, help docs, marketing collateral, sales materials)
- Currency and payment methods (local payment gateway integration, local invoicing)
- Regulatory compliance (data residency, privacy regulations like GDPR, industry-specific requirements)
- Business practices (contract norms, typical deal terms, invoice payment cycles)
- Market-specific pricing (local competitive benchmarking, purchasing power parity adjustments)

**By Vertical:**
- Regulatory/compliance features (e.g., audit trails for healthcare, PCI-DSS for fintech)
- Industry terminology and workflow customization (e.g., healthcare vs. manufacturing terminology)
- Customer-specific integrations (e.g., integration with vertical-specific accounting systems)
- Certifications and compliance (SOC 2, FedRAMP, HIPAA, ISO 27001 depending on vertical)

#### Market Timeline & Phasing Framework

| Phase | Duration | Key Milestones | Success Criteria |
|---|---|---|---|
| **Market Research & Validation** | 4-8 weeks | Interviews with 10+ prospects; competitive analysis; TAM/SAM/SOM validation | MVP customer interest confirmed; willingness to pay validated |
| **Pilot/Early Access** | 2-3 months | 2-5 early customers signed; product/GTM iteration; case study development | >70% pilot customer satisfaction; clear value metrics identified |
| **Soft Launch** | 1-2 months | Expanded customer cohort (10-20); reference development; partner enablement | 3+ reference customers; repeatable sales process validated |
| **Full Market Launch** | Ongoing | Full sales team ramped; marketing campaigns active; partner ecosystem live | Pipeline 3-5x quota; customer acquisition cost < CAC target; month-over-month growth 15%+ |

---

### 3. Partnership Development
Strategic partnership identification and execution to accelerate market entry and scale revenue.

#### Partner Identification & Tier Structure

**Partner Types by Role:**

| Partner Type | Primary Value | Target Geography/Vertical | Evaluation Criteria |
|---|---|---|---|
| **Channel Reseller** | Sales distribution, go-to-market reach | Regional/multi-vertical | Customer relationships, territory coverage, sales capacity, margin model fit |
| **Technology Partner** | Product integration, ecosystem positioning | Vertical-specific or cross-vertical | Integration depth, mutual customer base, co-selling enthusiasm |
| **Strategic Partner** | Co-marketing, referral, joint solution | Account-based or vertical | Brand alignment, complementary customer profiles, executive sponsorship |
| **Implementation Partner** | Delivery, professional services, custom integration | All geographies/verticals | Delivery capability, customer success track record, pricing model |
| **Ecosystem Integrator** | API integration, marketplace, platform positioning | Cross-market | Technical capability, integration standards, go-to-market support |

**Partner Tier Structure (by expected revenue contribution):**

| Tier | Annual Revenue Target | Go-to-Market Support | Contract Length | Exclusivity |
|---|---|---|---|---|
| **Tier 1 (Strategic)** | $500K-$2M+ | Dedicated enablement, co-marketing, joint business planning | 2-3 years | Potential geographic/vertical exclusivity |
| **Tier 2 (Key)** | $100K-$500K | Quarterly business reviews, training, marketing resources | 1-2 years | Non-exclusive |
| **Tier 3 (Base)** | <$100K | Self-serve enablement, partner portal, standard support | 1 year | Non-exclusive |

#### Partner Program Design Framework

**Core Program Elements:**

1. **Incentive Structure**
   - Margin tiers (e.g., 25% for resale partner, 15% for referral partner)
   - Volume-based rebates or MDF (marketing development funds) allocated as % of revenue
   - Performance bonus for hitting pipeline/revenue/customer adoption targets

2. **Joint Go-to-Market**
   - Co-branded assets (landing pages, case studies, webinars, collateral)
   - Lead sharing agreements (inbound leads to partner; qualified outbound leads from partner)
   - Co-selling motion (account planning, joint scoping, proposal development)
   - Integration showcase and roadmap visibility

3. **Training & Enablement**
   - Certification program (product knowledge, solution selling, deal structuring)
   - Quarterly business reviews and performance analysis
   - Sales methodology and playbook documentation
   - Technical bootcamps for implementation partners

4. **Performance Metrics & Accountability**
   - Pipeline KPIs (new pipeline, conversion rate, average deal size)
   - Revenue targets with quarterly milestones
   - Customer satisfaction and NPS metrics
   - Churn and expansion metrics (partner's customer growth vs. loss)

#### Co-Selling & Co-Marketing Frameworks

**Co-Selling Motion (Account-Based):**
- Partner identifies account; we validate fit and strategic value
- Joint discovery with customer (partner relationship + our technical expertise)
- Collaborative proposal with joint pricing, delivery, and support model
- Joint success planning and account review cadence
- Pipeline tracking and deal acceleration mechanisms (e.g., joint executive sponsor meetings)

**Co-Marketing Programs:**
- Webinar series (partner drives registration from their customer base; we deliver technical content)
- Joint case studies (partner customer success + our product value)
- Content syndication (whitepapers, reports distributed via partner channels)
- Event co-sponsorship and speaking opportunities
- Social media and email co-promotion

**Lead Sharing Economics:**
- Inbound leads from partner's website → 100% partner commission (we support but they own customer relationship)
- Warm outbound leads from partner to us → 75-90% partner commission (we execute sales; partner provides intro)
- Outbound leads from us to partner → 50-75% partner commission (based on partner execution quality)

#### Partner Economics Model

**Revenue Sharing Example for $100K Deal:**

| Scenario | Partner Revenue | Our Revenue | Comments |
|---|---|---|---|
| Reseller (25% margin) | $25K | $75K | Partner owns customer relationship; handles support |
| Co-sell (70% revenue share) | $70K | $30K | Partner provides intro; we close; we deliver/support |
| Referral Partner (15% revenue share) | $15K | $85K | Partner gets credit; we own entire relationship |

**Investment Requirements by Partner Tier:**

- **Tier 1 Strategic:** $50K-$150K annual (dedicated partner manager, co-marketing budget, joint sales planning)
- **Tier 2 Key:** $10K-$50K (periodic training, marketing resources, standard support)
- **Tier 3 Base:** <$10K (self-serve portal, certification program access)

**Partner Health Dashboard (Monthly Tracking):**
- Pipeline (new, current quarter, future quarters)
- Win rate and average deal size trend
- Customer satisfaction and support ticket volume
- Revenue vs. target (monthly, quarterly, annual)
- Churn and expansion metrics

---

### 4. Channel Strategy
Direct and indirect channel optimization to maximize market reach, minimize customer acquisition cost, and ensure scalable growth.

#### Direct vs. Indirect Assessment Framework

**Decision Criteria:**

| Criterion | Direct Sales | Indirect (Channel) | Decision Logic |
|---|---|---|---|
| **Customer Buying Preference** | Prefer direct vendor relationship | Prefer trusted local/established partner | Survey customers; analyze competitive win/loss by channel |
| **Sales Cycle Length** | Long (6+ months, consultative) | Medium-to-short (referral-driven) | Longer cycles favor direct; transactional favors channels |
| **Average Deal Size** | High ($50K+) | Medium ($10K-$50K) or high with partner | Direct justified for high-value; channels scale volumes |
| **Gross Margin** | 70%+ (support cost low) | 50-70% (partner discount) | Ensure unit economics work after partner discount |
| **Market Coverage** | Limited by sales team size | Distributed partner network | Channels accelerate geographic/vertical coverage 5-10x |
| **Competitive Dynamics** | Competitors using direct | Competitors using channels | Match competitor motion to avoid disadvantage |
| **Partner Ecosystem Maturity** | Limited channels available | Established channels eager to engage | Mature ecosystems enable faster partner sales |

**Hybrid Model (Direct + Indirect):**
- Direct sales for named accounts, strategic customers, or high-touch implementations
- Channels for SMB, transaction-based, or self-serve motions
- Avoid channel conflict by clearly segmenting by account size, vertical, or use case

#### Channel Conflict Management Framework

**Prevention Strategies:**

1. **Territory Planning**
   - Define geographic territories for each channel partner (e.g., Northwest region for Partner A)
   - Maintain map of partner territories with clear ownership rules
   - Quarterly reviews to ensure no overlapping customer assignments

2. **Customer Segment Alignment**
   - Direct sales: Fortune 500, multi-year contracts, complex integrations
   - Partners: SMB, transactional deals, self-serve, specific verticals
   - Clear definition of who owns which customer size/profile/use case

3. **Pricing Consistency**
   - Set list price; ensure partner margins and direct discounting don't create arbitrage
   - Regular pricing audits comparing direct list vs. partner net pricing
   - Policy on direct customer buyback (typically avoid; work with partner to convert)

4. **Partner Satisfaction Metrics**
   - Monthly partner feedback on competitive conflicts or dissatisfaction
   - Quarterly business reviews to address margin, lead flow, or support issues
   - Escalation path for partner conflicts (partner manager → VP of Channels → CEO if needed)

#### Distributor/Reseller Evaluation Scorecard

| Evaluation Factor | Weighting | Scoring (1-5) | Notes |
|---|---|---|---|
| **Customer Relationships in Target Market** | 25% | 5=deep; 1=none | Assess quantity and quality of customer relationships |
| **Territory Coverage & Geography** | 20% | 5=comprehensive; 1=limited | Coverage maps to expansion priorities |
| **Sales Capacity & Team Quality** | 15% | 5=strong salesforce; 1=minimal | Can they scale with our growth? |
| **Financial Stability & Viability** | 15% | 5=strong financials; 1=weak/risky | Credit check, financial review, customer concentration |
| **Strategic Alignment & Exclusivity** | 10% | 5=high alignment; 1=misaligned | Brand fit, willingness to invest, exclusivity expectations |
| **Support & Delivery Capability** | 10% | 5=strong delivery team; 1=support challenges | Can they support customer success? |
| **Competitive Positioning** | 5% | 5=unique; 1=undifferentiated | What makes them stand out vs. alternatives? |

**Partner Selection Threshold:** Average score ≥3.5 = Qualify for partnership; <3.5 = Continue evaluating or reject.

#### Channel Enablement Program

**Training Components:**

- **Product Certification:** 3-tier program (Bronze = basic; Silver = advanced technical; Gold = solutions architecture)
- **Sales Methodology:** Joint discovery process, value-based selling frameworks, ROI quantification
- **Competitive Battlecards:** Competitor comparisons, win/loss themes, customer objection handling
- **Vertical Playbooks:** Industry-specific use cases, buyer personas, regulatory considerations (if applicable)

**Enablement Delivery:**
- Quarterly webinars (live + recorded for on-demand)
- Partner portal with resource library (one-pagers, presentations, case studies, pricing guides)
- Annual partner kickoff event with executive visibility
- Monthly office hours for partner manager Q&A

**Tools & Collateral:**
- Co-branded slide decks (partner logo, our messaging)
- Email templates for partner outreach (pre-qualified leads, campaign campaigns)
- ROI calculators (partner-branded) for customer conversations
- Case studies and customer testimonials specific to partner's verticals

**Performance Management:**
- Monthly partner scorecard (pipeline, revenue, training completion, deal deal quality)
- Quarterly business reviews (results analysis, upcoming quarter planning, resource allocation)
- Annual contract renewal contingent on achieving targets
- Escalation process for underperforming partners (90-day turnaround plan before termination)

---

### 5. Geographic Expansion
Systematic approach to entering new countries and regions with market-specific strategies and execution discipline.

#### Country/Region Analysis Framework

**Market Assessment Criteria:**

| Analysis Area | Key Metrics | Evaluation Method |
|---|---|---|
| **Market Size & Opportunity** | TAM (serviceable market size); customer count by segment | Industry reports, web research, customer interviews |
| **Market Growth Rate** | YoY growth; CAGR 3-5 year projections | Analyst reports (Gartner, Forrester, IDC); government statistics |
| **Customer Concentration** | % revenue from top 10 customers; industry diversity | CRM data for existing customers; industry research |
| **Purchasing Power** | Average deal size; customer LTV; affordability relative to local wages | Pricing analysis; customer interviews; purchasing power parity data |
| **Macroeconomic Indicators** | GDP growth, inflation, interest rates, currency stability | IMF, World Bank, central bank data; FX historical volatility |
| **Infrastructure & Connectivity** | Internet penetration, broadband quality, data center availability | Global Connectivity Index; CDN provider coverage; government reports |

**Regional Market Entry Decision Tree:**

1. Market Size: Is serviceable TAM sufficient to justify entry cost? (Threshold: $10M+ usually required)
2. Growth Rate: Is market growing 10%+ YoY? (If not, lower priority unless strategic)
3. Competitive Landscape: Are 1-3 dominant competitors, or fragmented market? (Fragmented is more attractive)
4. Customer Maturity: Are customers in early adoption, rapid growth, or mature phase? (Early/growth phases offer larger opportunities)
5. Regulatory Barriers: Are regulatory requirements manageable? (High barriers may require partners or delayed entry)
6. Resource Requirements: Do we have budget and team capacity for 6-12 month ramp? (If not, delay entry)

#### Regulatory Landscape Assessment

**Compliance Framework by Category:**

| Category | Key Considerations | Examples |
|---|---|---|
| **Data Privacy & Residency** | Where can data be stored? What is GDPR-equivalent compliance? | EU (GDPR), China (data residency required), India (data localization), Japan (APPI) |
| **Industry-Specific Regulations** | Product certifications, operational compliance | Healthcare (HIPAA, GDPR), Finance (SOX, PCI-DSS), Telecom (security standards) |
| **Foreign Investment & Ownership** | Are foreign companies allowed? Restrictions on majority ownership? | China (majority Chinese ownership required in some sectors), Russia (sanctions-related), North Korea (US embargo) |
| **Licensing & Permits** | Do we need operating license to sell/serve? | Software often license-free; services may require permit |
| **Export Control & Sanctions** | Can we legally sell to this country? Restricted technologies? | US export controls on advanced tech; OFAC sanctions on certain countries |
| **Labor & Employment** | Employment contract rules, minimum wage, benefits | EU (strict employment laws); Middle East (sponsor system); US (at-will employment) |

**Regulatory Due Diligence Checklist:**
- Engage legal counsel in target country to review compliance requirements
- Identify required certifications (SOC 2, ISO 27001, industry-specific)
- Determine if local entity required vs. branch office sufficient
- Assess export control implications (especially for US companies)
- Plan for privacy policy localization and data handling procedures
- Estimate compliance cost and timeline to operationalize

#### Competitive Positioning by Geography

**Regional Competitive Analysis Template:**

| Competitive Factor | Analysis Approach | Output |
|---|---|---|
| **Market Share Distribution** | Identify top 3-5 vendors by market share; map to customer segments | Market share chart; identify gaps/white space |
| **Local Competitor Profiles** | Research local/regional competitors often overlooked in global analysis | Strengths, weaknesses, go-to-market, pricing |
| **Pricing Dynamics by Region** | Compare our pricing vs. competitors; account for purchasing power parity | Price ranges by customer segment; margin implications |
| **Customer Preferences by Region** | Buyer preference for direct vs. partner; solution buying vs. point products | Go-to-market implications; partnership strategy |
| **Win/Loss Patterns** | If we have deals in region, analyze why we win/lose vs. competitors | Product gaps; positioning adjustments; competitive weaknesses to exploit |

**Competitive Positioning Worksheet:**
- Our differentiation in region (technology, price, support, ecosystem)
- Top 2-3 competitors and our positioning vs. each
- Customer buying criteria in region (price sensitivity, feature prioritization, support expectations)
- Go-to-market strategy to differentiate (e.g., focus on SMB if leader owns enterprise; focus on specific use case if leader is generalist)

#### Cultural Adaptation & Business Practice Alignment

**Localization Checklist:**

| Dimension | Adaptations Required | Examples |
|---|---|---|
| **Sales Approach** | Relationship-based vs. transactional; formality level; decision-making process | Japan (relationship-heavy, formal); US (transactional, informal); Middle East (importance of trust/relationships) |
| **Communication Style** | Direct vs. indirect; hierarchical vs. flat; written vs. verbal | Germany (direct); Japan (indirect); US (direct); China (hierarchical) |
| **Buying Cycle & Decision Making** | Length of buying cycle; decision authority; consensus vs. individual decision | Asia (consensus-driven, longer cycles); US (faster, individual decision); Europe (consultative, medium cycle) |
| **Contract & Terms** | Standard payment terms (30/60/90 days), contract length preferences, typical clause negotiations | US (net-30 standard); Europe (net-60); Asia (longer negotiation, stricter terms) |
| **Marketing & Messaging** | Language translation + cultural adaptation; imagery and symbolism; local event participation | Color symbolism (white = death in Asia); local holiday calendar; business practice norms |
| **Relationship Management** | Executive visibility; account review frequency; after-sales engagement model | High-touch in Asia/EMEA; lower-touch in US/online model acceptable |

**Cultural Adaptation Workflow:**

1. **Market Entry Meeting:** Convene cross-functional team (Sales, Marketing, Legal, Product) to review regional profile
2. **Localization Scope Assessment:** Identify required product, marketing, sales, and operational adaptations
3. **Partner/Advisor Engagement:** Hire local advisor or partner to validate assumptions and guide implementation
4. **Pilot Customer Identification:** Identify 2-5 pilot customers as cultural validation and reference accounts
5. **Iteration & Refinement:** Launch pilot; gather feedback; refine messaging, sales approach, product adaptations
6. **Full Launch:** Roll out refined approach to broader market

---

### 6. Vertical Expansion
Industry-specific market penetration and customer development to drive high-margin, sticky revenue.

#### Industry-Specific Value Propositions Framework

**Vertical Value Proposition Template:**

| Element | Definition | Healthcare Example |
|---|---|---|
| **Industry Challenge** | Top 2-3 pain points in industry | Patient data fragmentation; compliance burden (HIPAA); provider burnout |
| **Our Unique Solution** | How our product/service solves this better than alternatives | Unified patient data platform with HIPAA-built-in; reduces admin burden by 30% |
| **Vertical ROI Narrative** | Quantifiable business impact in industry terms | Reduce claim denial rate by 5-10% = $500K-$1M annual savings for mid-size practice |
| **Regulatory/Compliance Positioning** | How we meet industry-specific requirements | SOC 2 Type II certified; HIPAA compliance audited annually; BAA agreements in place |
| **Industry Pain Point Alignment** | Map our differentiators to industry's buying committee priorities | CTO cares about security/compliance; CFO cares about ROI; CMO cares about patient satisfaction |

**Vertical Value Prop Development Process:**

1. **Customer Discovery Interviews (10-15 per vertical):** Understand top problems, buying drivers, success metrics, regulatory requirements
2. **Competitive Mapping:** Identify who else serves this vertical and how they position
3. **Value Quantification:** Convert qualitative benefits to industry-specific ROI (cost savings, revenue uplift, efficiency gains)
4. **Messaging Development:** Create vertical-specific one-pager, slide deck, email templates, sales talking points
5. **Validation:** Pitch to 2-3 prospective customers; refine based on feedback before broad launch

#### Vertical Playbooks

**Sales Methodology by Vertical:**

| Playbook Element | Description | Execution Responsibility |
|---|---|---|
| **Buyer Personas** | Decision-makers and influencers; their priorities, KPIs, concerns | Marketing + Sales to define; CRM to maintain |
| **Buying Committee Structure** | Who is involved in decision? What is their influence/veto power? | Sales to map per opportunity; adjust approach accordingly |
| **Sales Process & Stages** | Deal stages specific to vertical buying cycle (e.g., budget approval stage) | Sales to define; Sales ops to track in CRM |
| **Sales Methodology** | MEDDIC, SPIN, Solution Selling, etc. — which method works best? | Sales leader to define based on vertical and deal complexity |
| **Deal Cycle Timeline** | Expected duration; seasonal patterns; key decision milestones | Sales to forecast; Marketing to time campaigns |
| **Deal Size Ranges** | Typical contract value by customer size and use case | Sales to quote; Finance to model; Marketing to position |

**Customer Development Path by Vertical:**

| Stage | Activities | Timeline | Success Criteria |
|---|---|---|---|
| **Awareness** | Thought leadership (articles, speaking); industry events; peer referrals | Ongoing | 10-20 net new qualified leads per month |
| **Evaluation** | Product demo; ROI analysis; customer references; trial/POC | 2-4 weeks | 30%+ POC-to-customer conversion |
| **Purchase** | Negotiation; approvals; contracting | 2-8 weeks | Signed contract; customer implementation date |
| **Implementation** | Setup, training, data migration | 4-12 weeks | Go-live on time; customer satisfied with onboarding |
| **Expansion** | Additional modules, teams, seats; upsell | 3-6 months | 20%+ net revenue retention (NRR) in vertical |

#### Reference Customer Development Strategy

**Early Adopter Recruitment Framework:**

- **Target Profile:** Best-fit customer type (usually 20-50 employee range for B2B SaaS; high pain point alignment; willingness to engage)
- **Outreach Approach:** Warm intro + personalized pitch + incentive (discount, free implementation, priority support)
- **Qualification Criteria:** High product-market fit potential; willingness to be reference/case study; executive sponsor visibility
- **Timeline:** Target 2-5 early customers in vertical within first 6 months of launch

**Case Study Development Process:**

1. **Customer Kick-off:** Brief customer on case study scope (1-2 weeks of time commitment); secure executive sponsor approval
2. **Discovery Interviews:** 2-3 interviews (executive, technical, functional user); understand background, challenge, solution, results
3. **Metrics Gathering:** Collect quantifiable results (ROI, efficiency gains, cost savings, productivity improvements)
4. **Draft Development:** 2-3 page case study (problem, solution, results, quote) + customer approval cycles (3-5 weeks)
5. **Promotion:** Feature in webinars, website, email campaigns, sales collateral; customer co-presents at events

**Reference Selling Program:**

- **Reference Database:** Track who, by vertical and use case, is willing to take customer calls or speak at events
- **Reference Request Process:** Sales or Marketing can request references; customer contact to confirm availability
- **Success Metrics:** Track reference conversion impact (references involved in X% of deals; Y% of references convert)
- **Ongoing Engagement:** Quarterly business reviews with reference customers; annual appreciation events

---

### 7. Competitive Intelligence
Continuous market monitoring and competitive positioning to maintain advantage and identify threats.

#### Market Share Tracking Framework

**Market Share Analysis Template:**

| Metric | Calculation | Data Source | Frequency |
|---|---|---|---|
| **Overall Market Share** | Our revenue / Total market revenue (by customer segment, geography, use case) | Annual: analyst reports; Quarterly: estimated from CRM pipeline |
| **Category Growth Rate** | (Market revenue Year 2 - Year 1) / Year 1 revenue | Analyst reports (Gartner, Forrester, IDC) | Quarterly/Annual |
| **Share of Growth** | Our revenue growth / Market growth | CRM + market estimates | Quarterly |
| **Win/Loss Share** | % of competitive deals we won/lost vs. each competitor | Win/loss database (survey field + sales reports) | Monthly |
| **Share of Customer Wallet** | Our revenue per customer / Customer's total annual spend in category | Customer interviews; Gartner surveys | Quarterly |

**Competitive Concentration Analysis:**

- Identify top 3-5 competitors by market share; track trend over time
- Calculate Herfindahl-Hirschman Index (HHI) to assess market consolidation
- Monitor if market leader is gaining/losing share (indicates market maturity and profitability trends)

#### Competitor Movement Monitoring

**Competitive Intelligence Dashboard (Monthly Tracking):**

| Intelligence Type | Tracking Method | Alert Threshold |
|---|---|---|
| **Product Releases & Roadmap** | Monitor competitor website, press releases, user forums; track feature gap analysis | Major new feature addressing our differentiation |
| **Partnership Announcements** | LinkedIn, press releases, industry news; assess channel shift or ecosystem threat | Competitor partnership with major channel/integration partner |
| **Pricing Changes** | Monitor pricing pages, customer feedback, sales intelligence; document pricing model shifts | Price cut >15% in our segment; new packaging/bundling strategy |
| **Go-to-Market Shifts** | Sales team feedback; analyst briefings; job postings (indicates investment); marketing campaign monitoring | Competitor hiring in our key markets; new vertical focus |
| **M&A Activity** | SEC filings, press releases, industry news; assess strategic implications | Acquisition of complementary technology or customer base |
| **Leadership Changes** | LinkedIn, press releases, industry news; assess strategic implications | New CEO/Chief Revenue Officer with different strategy |

**Competitive Intelligence Process:**
- Designate competitive intelligence owner (typically Strategy or Marketing)
- Establish monitoring cadence (daily news monitoring; weekly summary; monthly deep dive)
- Use alerts (Google Alerts for each competitor; LinkedIn job posting alerts; industry newsletter subscriptions)
- Quarterly review with executive team; flag strategic implications and response requirements

#### Win/Loss Analysis Program

**Win/Loss Interview Framework:**

| Win/Loss Type | Sample Selection | Interview Focus | Insights Generated |
|---|---|---|---|
| **Wins vs. Specific Competitor** | Recent won deals (last 6 months); sample 20-30% of wins | Why did customer choose us? Evaluation criteria? Competitor strengths/weaknesses? | Competitive messaging; product gaps; pricing positioning |
| **Losses vs. Specific Competitor** | Recent lost deals (last 3 months); prioritize deals >$50K or strategic | Why did customer choose competitor? Deal breaker issues? Perception gaps? | Product roadmap priorities; messaging refinement; pricing strategy |
| **Market Validation** | Prospective customers who didn't buy from us or competitor | Market needs; product requirements; buying process | Product roadmap validation; GTM strategy |

**Win/Loss Interview Guide Outline:**

1. **Opening:** Rapport; explain purpose (improve our product/messaging, not blame); confidentiality
2. **Selection Criteria:** Which vendors were evaluated? Selection criteria (features, price, support, culture)?
3. **Our Evaluation:** What was your impression of our product? Strengths we should emphasize? Weaknesses/gaps?
4. **Competitor Evaluation:** How did [competitor] compare? Their strengths vs. ours? Deal breakers or tipping points?
5. **Buying Process:** How important were [reference customers, analyst recommendations, executive sponsor]? Timeframe/budget constraints?
6. **Future Opportunity:** Would you consider us for future projects? If so, what would need to change?

**Win/Loss Metrics Dashboard (Quarterly):**

- Total deals evaluated: X%; won: Y%; lost: Z%
- Win rate vs. each competitor (e.g., 60% vs. Competitor A; 40% vs. Competitor B)
- Top win reasons (e.g., 40% "superior features"; 30% "better pricing"; 20% "customer support"; 10% "relationships")
- Top loss reasons (e.g., 35% "feature gap"; 25% "price too high"; 20% "customer preferred existing vendor"; 20% "our missing integration")
- Win rate by customer segment (e.g., 65% SMB; 45% Enterprise; 55% Mid-market)

#### Strategic Competitor Briefing

**Competitive Threat Assessment Framework:**

| Threat Level | Indicators | Response |
|---|---|---|
| **High Threat** | Competitor winning in our target segment; new differentiated feature we lack; aggressive pricing; large funding/M&A | Urgent: Convene strategy team; assess product roadmap impact; develop competitive messaging; consider pricing response |
| **Medium Threat** | Competitor entering adjacent vertical; moderate feature gap; hiring in our markets | Plan: Develop action plan (product, positioning, go-to-market); monitor win/loss impact; review in 60 days |
| **Low Threat** | Competitor in different segment; minor feature gap; isolated win/loss pattern | Monitor: Track in competitive dashboard; adjust messaging if needed; include in monthly competitive intelligence report |

**Quarterly Competitive Briefing Output (for Leadership):**

1. **Market Snapshot:** Overall market growth; our share vs. competitors; share trends
2. **Top Threats:** 2-3 competitors gaining share or gaining strategic advantage; specific threats and our response
3. **Opportunities:** Market gaps, competitor weaknesses, adjacencies we can exploit
4. **Product Implications:** Features we need to build, enhancements to prioritize, competitive differentiation roadmap
5. **GTM Implications:** Messaging to emphasize, pricing adjustments, channel focus, partnership strategy
6. **Resource Allocation:** Budget/headcount implications of competitive response plan

---

## How to Invoke

### Market Identification Triggers

Use this capability when you need to:
- **"Identify and prioritize market expansion opportunities"** — Triggers full TAM/SAM/SOM analysis and market attractiveness scoring for 3-5 candidate markets
- **"Perform a white space analysis for our product"** — Triggers adjacent market mapping and competitive blind spot analysis
- **"Assess market attractiveness for [vertical/geography]"** — Triggers market attractiveness scoring matrix and narrative assessment

### Market Entry Strategy Triggers

Use this capability when you need to:
- **"Develop a go-to-market plan for [market]"** — Triggers GTM planning framework covering channel strategy, TCP, value prop, customer acquisition approach, messaging, success metrics
- **"Create a market entry playbook for [geography/vertical]"** — Triggers localization checklist, go-to-market timeline/phasing, and resource allocation plan
- **"Evaluate market entry mode for [opportunity]"** — Triggers entry mode comparison (direct sales vs. partnerships vs. acquisitions vs. licensing)

### Partnership Development Triggers

Use this capability when you need to:
- **"Identify and evaluate channel partners for [market]"** — Triggers partner identification framework and evaluation scorecard
- **"Design a partner program for [new product/market]"** — Triggers partner tier structure, incentive design, training, and performance management framework
- **"Develop a co-selling playbook with [partner]"** — Triggers co-selling motion, account planning, and deal management approach

### Geographic Expansion Triggers

Use this capability when you need to:
- **"Analyze [country/region] as a market expansion opportunity"** — Triggers country/region analysis, regulatory landscape assessment, and competitive positioning analysis
- **"Plan a geographic expansion into [region]"** — Triggers full geographic expansion plan including market assessment, regulatory requirements, cultural adaptation, and GTM strategy
- **"Create a localization plan for [geography]"** — Triggers localization checklist for language, regulatory, cultural, and business practice adaptation

### Vertical Expansion Triggers

Use this capability when you need to:
- **"Develop a vertical market entry strategy for [industry]"** — Triggers vertical value proposition development, sales methodology, customer development path, and reference customer strategy
- **"Create a vertical playbook for [industry]"** — Triggers buyer persona development, buying committee mapping, sales process definition, and deal cycle analysis
- **"Plan reference customer development for [vertical]"** — Triggers early adopter recruitment, case study development, and reference selling program design

### Competitive Intelligence Triggers

Use this capability when you need to:
- **"Conduct a competitive market analysis"** — Triggers competitor movement monitoring, market share tracking, win/loss analysis, and strategic threat assessment
- **"Prepare a competitive briefing for leadership"** — Triggers market snapshot, threat analysis, opportunity assessment, and resource allocation recommendations
- **"Analyze win/loss patterns versus [competitor]"** — Triggers win/loss interview planning, data analysis, and competitive messaging development

---

## Related Plugin Skills

- **marketing:competitive-brief** — Competitive landscape analysis, market positioning, differentiation strategy, customer messaging
- **marketing:campaign-plan** — New market demand generation, localized campaigns, partner-driven programs, event marketing
- **marketing:draft-content** — Vertical-specific value propositions, localized marketing collateral, case study development, partner enablement content
- **sales:account-research** — High-value account/segment research, buyer persona development, opportunity assessment, competitive win/loss insights
- **sales:competitive-intelligence** — Deal-level competitive insights, win/loss findings, competitive talking points, battlecard development
- **sales:daily-briefing** — Partner pipeline review, channel partner health, market entry progress tracking
- **sales:forecast** — Market entry pipeline forecasting, partner channel revenue projections, geographic/vertical revenue planning

---

## Connected Tools & Systems

- **Zoho CRM** — Pipeline tracking by market/geography/vertical, partner management and tier tracking, opportunity forecasting, win/loss logging, partner revenue attribution
- **Google Drive** — Market research documents and competitive intelligence files, expansion roadmaps and playbooks, partner agreements and contracts, market analysis spreadsheets, case study repository
- **Slack** — Cross-team collaboration channels (Sales, Marketing, Strategy, Legal), market intelligence sharing and alerts, expansion project updates and milestones, partner management discussions, competitive intelligence notifications
- **Claude in Chrome** — Market research, regulatory research and compliance requirements, competitive intelligence gathering, pricing benchmarking, analyst report review
- **Gmail** — Partner outreach and relationship management, market research inquiries and expert interviews, opportunity identification communication, partnership proposal development

---

## Context Files

**Target Markets Document (target_markets.md)**
- Curated list of 10-15 expansion opportunities (geographies, verticals, customer segments)
- Market attractiveness score for each opportunity (using Market Attractiveness Scoring Matrix)
- TAM/SAM/SOM estimates with calculation methodology and assumptions
- Competitive landscape assessment per market
- Estimated resource requirements and timeline to launch per market
- Status and priority ranking (Hot, Warm, Cold)
- Executive summary and recommendation

**Partner Tracking System (partner_tracker.md)**
- Partner pipeline (prospecting, negotiating, active, inactive)
- Program status and contract details (start date, renewal date, exclusivity terms)
- Performance metrics (revenue, pipeline, win rate, customer satisfaction)
- Contract calendar and renewal milestones
- Partner tier classification and compensation structure
- Key contacts and relationship health

**Market Entry Playbook (market_entry_playbook.md)**
- Template go-to-market strategies by market type (geographic, vertical, channel-based)
- Localization checklists (language, regulatory, cultural, commercial)
- Partner onboarding processes and enablement frameworks
- Sales process playbook (discovery, qualification, closing, expansion)
- Marketing templates (messaging, collateral, campaign calendar)
- Success metrics and KPI definitions

**Expansion Pipeline (expansion_pipeline.md)**
- Active market entries in progress, organized by stage (research, planning, soft launch, full launch)
- Timelines and key milestones per market entry
- Resource allocation (headcount, budget, time allocation) per market
- Success metrics and progress tracking against targets
- Risks and blockers per market entry, with mitigation plans
- Executive dashboard summarizing overall expansion health

**Competitive Intelligence Repository (competitive_intelligence.md)**
- Quarterly competitive briefing summary (threats, opportunities, product implications, GTM implications)
- Win/loss database with deal-level analysis (won/lost deals, reasons, competitive delta)
- Competitor product roadmap tracking and feature gap analysis
- Market share and competitive concentration analysis
- Pricing intelligence and pricing model tracking
- Partnership announcements and go-to-market shifts

---

## Cross-Functional Collaboration

The Market-Development agent operates within an integrated growth ecosystem, requiring close coordination across functions:

### Sales Agent Collaboration
- **Field Execution:** Sales team executes market entry strategy in field; provides win/loss intelligence and customer feedback to refine GTM approach
- **Pipeline Management:** Sales logs deals, pipeline, and forecasts in CRM by market/geography/vertical to enable tracking and resource allocation
- **Partner Management:** Sales leads channel partner negotiations, manages partner performance, and coordinates co-selling motions
- **Competitive Intelligence:** Sales provides win/loss insights and competitor feedback to inform competitive strategy and messaging
- **Market Validation:** Sales teams in pilot markets validate early TAM estimates and help refine GTM before full launch

### Marketing Agent Collaboration
- **Demand Generation:** Marketing executes localized campaigns in new markets to drive pipeline and support market entry
- **Vertical Positioning:** Marketing develops vertical-specific messaging, case studies, and content to support vertical expansion
- **Partner Enablement:** Marketing creates co-branded assets, training content, and lead generation support for channel partners
- **Reference Development:** Marketing coordinates case study development with early customers and manages reference selling program
- **Competitive Messaging:** Marketing develops competitive battlecards and positioning statements based on competitive intelligence

### Strategy Agent Collaboration
- **Market Selection:** Strategy evaluates market selection criteria, market attractiveness, competitive positioning, and resource allocation
- **Expansion Roadmap:** Strategy prioritizes expansion opportunities and coordinates overall growth strategy across all expansion initiatives
- **Resource Planning:** Strategy assesses resource requirements, budget allocation, and hiring plans for market expansion
- **Scenario Planning:** Strategy develops best/worst/likely case scenarios for market entry timelines, revenue impact, and profitability
- **Executive Alignment:** Strategy communicates market expansion strategy to board and leadership; tracks ROI on market investments

### Legal Agent Collaboration
- **Regulatory Compliance:** Legal manages regulatory compliance requirements in new geographies (data residency, privacy, industry-specific requirements)
- **Partnership Agreements:** Legal reviews and negotiates partner agreements, go-to-market terms, and IP provisions
- **Localization Support:** Legal reviews localized terms and conditions, privacy policies, and contractual requirements by geography
- **Exports & Sanctions:** Legal ensures compliance with export controls and sanctions restrictions in target markets
- **Compliance Documentation:** Legal maintains compliance documentation and audit trails for regulatory adherence in new markets

---

## Notes & Best Practices

### Market Development Philosophy

- **Market development is inherently iterative:** Initial TAM estimates and competitive assumptions will evolve with field validation. Plan for 1-2 major GTM iterations before achieving product-market fit in new market.
- **Partner success is critical to scale:** Allocate significant effort (15-20% of team capacity) to partner enablement, training, and performance management. Partner ramp time is typically 6-9 months; plan accordingly.
- **Competitive intelligence becomes more important as markets mature:** As markets consolidate, win/loss patterns become early warning signals. Monitor competitive movements monthly and conduct quarterly strategic assessments.

### Geographic Expansion Best Practices

- **Geographic expansion timelines are longer than expected:** Plan for 6-12 month ramp periods. Average sales ramp is 6-9 months; customer acquisition cost is typically 30-50% higher in new markets initially.
- **Maintain adequate resources through the ramp period:** Avoid staffing cuts during ramp as markets mature. Revenue from new markets typically reaches profitability at 12-18 month mark.
- **Cultural adaptation requires local expertise:** Hire local advisor or partner manager early (before first hire) to validate assumptions and guide localization strategy. Avoid over-reliance on Western go-to-market approach.

### Vertical Expansion Best Practices

- **Vertical expansion typically requires product/service customization:** Coordinate closely with product and delivery teams to scope customization vs. new product capability. Plan for 10-20% of engineering capacity allocation per vertical.
- **Vertical pricing and sales models often differ from horizontal:** Be prepared to adjust pricing model (consumption vs. perpetual), contract terms (shorter initial contracts in new verticals), and sales approach.
- **Reference customer development should begin immediately upon market entry:** Reference customers will be foundation for future pipeline. Allocate 2-5 customers to reference program within first 6 months.

### Partnership Management Best Practices

- **Set clear expectations and performance targets:** Define partner revenue targets, pipeline minimums, and customer success metrics in writing. Review quarterly.
- **Proactive partner relationship management:** Conduct monthly check-ins with Tier 1 partners; quarterly with Tier 2-3. Address issues proactively before escalation.
- **Align incentives with our business objectives:** Ensure partner margin structure and bonus metrics align with our growth priorities (e.g., bonus for new customer acquisition vs. expansion revenue).

### Competitive Intelligence Best Practices

- **Establish systematic competitive intelligence gathering:** Designate owner; establish daily/weekly/monthly cadence; use multiple sources (press releases, LinkedIn, analyst reports, customer feedback, sales team).
- **Translate competitive intelligence into action:** Don't let competitive intel sit in a report. Translate into product roadmap implications, messaging changes, GTM strategy adjustments.
- **Use win/loss analysis to drive product/GTM decisions:** Sample at least 20% of deals monthly. Track trends over time; act on consistent patterns (e.g., if losing 30% of deals to competitor on feature X, prioritize in roadmap).

---

## Document Ownership & Updates

This agent definition reflects the current strategic priorities and tool landscape as of March 2026. Updates should be coordinated with [Owner] and relevant cross-functional stakeholders (Sales VP, Marketing VP, Strategy lead, Chief Legal Officer).

**Update Triggers:**
- Major change to agent scope or capabilities (e.g., adding M&A as market entry mode, significant tool integration)
- Quarterly review of connected systems and context files to ensure alignment with current business processes
- Annual strategic planning cycle to validate expansion priorities and agent capability gaps

For major changes to agent scope, capabilities, or partnerships, follow the agent governance process involving Finance, Legal, and executive stakeholder approval.
