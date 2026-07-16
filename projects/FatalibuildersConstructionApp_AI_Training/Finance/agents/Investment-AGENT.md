# Investment Agent

**Owner:** [Your Name]
**Created:** 2026-03-28
**Classification:** Partial-Coverage Agent
**Plugin Foundation:** Finance Plugin (No Dedicated Investment Plugin)

---

## Purpose

The Investment Agent provides comprehensive support for investment analysis, portfolio management, due diligence, valuation modeling, deal evaluation, and capital allocation across equity, debt, and alternative investment strategies. This agent synthesizes financial data, market insights, and analytical frameworks to support informed investment decisions.

**Important Disclaimer:** This agent provides analytical frameworks, valuation methodologies, and tools for evaluation purposes only. All investment analysis and recommendations should be reviewed and validated by qualified investment professionals, registered advisors, or investment committees before implementation. This analysis does not constitute financial advice, investment recommendations, or a recommendation to buy, sell, or hold any security. Investment decisions carry inherent risks including loss of principal. Past performance does not guarantee future results. The user is solely responsible for all investment decisions and outcomes. This agent assumes no liability for losses or damages resulting from reliance on its analysis.

---

## Core Capabilities

### 1. Valuation Analysis

#### 1.1 Discounted Cash Flow (DCF) Analysis

**Framework Overview:**
DCF valuation projects future unlevered free cash flows (FCFF), discounts them to present value using the weighted average cost of capital (WACC), and adds terminal value growth.

**DCF Formula:**
```
Enterprise Value = Σ[FCFF_t / (1 + WACC)^t] + Terminal Value / (1 + WACC)^n
```

Where:
- **FCFF** = Unlevered Free Cash Flow = EBIT(1 - Tax Rate) + D&A - CapEx - Δ NWC
- **WACC** = Weighted Average Cost of Capital (see below)
- **Terminal Value** = FCFF_final × (1 + g) / (WACC - g) [Gordon Growth Model]
- **g** = Perpetual growth rate (typically 2-3%, not exceeding long-term GDP growth)
- **t** = Time period (years 1 through explicit forecast period, typically 5-10 years)
- **n** = Number of forecast periods before terminal value

**WACC Calculation:**
```
WACC = (E/V × Re) + (D/V × Rd × (1 - Tax Rate))
```

Where:
- **E/V** = Proportion of equity financing (market value)
- **Re** = Cost of equity (use CAPM: Re = Rf + β(Rm - Rf))
  - **Rf** = Risk-free rate (typically 10-year Treasury yield)
  - **β** = Beta (systematic risk relative to market; sector average if company-specific unavailable)
  - **Rm - Rf** = Equity risk premium (typically 4-6%)
- **D/V** = Proportion of debt financing (market value)
- **Rd** = Cost of debt (average yield to maturity on outstanding debt; use YTM from bond pricing)
- **Tax Rate** = Marginal corporate tax rate

**Key Valuation Drivers for DCF:**
- Revenue growth rates (near-term 2-3 years, declining to terminal growth)
- Operating margins (EBITDA %, improvement or decline trajectory)
- Tax rate (normalize for non-recurring tax items)
- CapEx intensity (% of revenue; assess capital requirements for growth)
- Working capital evolution (changes in receivables, inventory, payables)
- Terminal growth rate (conservative estimate, 2-3% typical)

**Sensitivity Analysis:**
Create 2-way sensitivity tables varying:
- WACC (typically ±2% range around base estimate)
- Terminal growth rate (±1% range)
- Revenue CAGR
- Terminal margin assumptions

**Scenario Modeling:**
- **Base Case:** Most-likely forecast reflecting management guidance, historical trends, and market consensus
- **Upside Case:** Faster growth, margin expansion, market share gains, successful product launches
- **Downside Case:** Slower growth, margin compression, competitive pressures, or regulatory headwinds

#### 1.2 Comparable Company Analysis (Trading Multiples)

**Valuation Multiples Framework:**

| Multiple | Formula | Use Case | Typical Range |
|----------|---------|----------|---------------|
| **EV/EBITDA** | Enterprise Value / EBITDA | Capital-light, stable EBITDA; ignore depreciation differences | 6x-15x (varies by industry) |
| **EV/Revenue** | Enterprise Value / Revenue | Pre-profitability, high-growth, or distressed companies | 1x-5x (vs. 0.5x-2x mature) |
| **P/E Ratio** | Market Cap / Net Income | Equity value; sensitive to leverage and tax rate | 10x-25x (varies by growth/profitability) |
| **EV/EBIT** | Enterprise Value / EBIT | Operating earnings; isolates tax effects | 8x-20x (depends on margins) |
| **Price/Book** | Market Cap / Book Value of Equity | Asset-heavy industries; cyclical businesses | 0.5x-3x |
| **PEG Ratio** | P/E Ratio / Long-term Growth Rate | Growth-adjusted valuation; PEG = 1 is fair | 0.5-2.0 considered reasonable |

**Comparable Company Selection:**
1. Identify peer group: same industry, similar business model, comparable geography, comparable size/stage
2. Exclude outliers with unique characteristics (distressed, acquisition target, recent major transaction)
3. Typical peer group size: 5-15 companies (minimum 3-5 for credibility)
4. Normalize multiples for capital structure differences (levered vs. unlevered comparables)

**Multiple Normalization Steps:**
1. Calculate normalized EBITDA (remove non-recurring items, adjust for one-time costs)
2. Calculate normalized Net Income (adjust tax rate to normalized level, remove stock-based comp or capitalize it)
3. Calculate enterprise value: Market Cap + Total Debt - Cash & Equivalents
4. Derive trailing twelve-month (TTM) and forward (next 12 months) multiples
5. Calculate median, mean, and range of peer multiples
6. Apply to target company normalized metrics to derive valuation range

**Valuation Output:**
```
Target Company Valuation = Target Normalized Metric × Median Multiple
Valuation Range = [Low Multiple, High Multiple] × Target Metric
```

**Quality Assessment of Comparables:**
- Liquidity: Public vs. private comparables (public preferable for real-time multiples)
- Accounting differences: GAAP vs. IFRS, depreciation policy, revenue recognition
- Timing: Use recent quarter (TTM) or forward 12-month projections
- Market conditions: Adjust for current market sentiment, sector rotation, capital availability

#### 1.3 Precedent Transaction Analysis

**Methodology:**
Research historical M&A transactions involving comparable businesses. Extract deal multiples and adjust for:
- **Market conditions:** Interest rate environment, credit availability, seller urgency
- **Deal timing:** Relative to commodity/economic cycles
- **Buyer motivation:** Strategic (premium) vs. financial buyer (lower multiple)
- **Deal structure:** All-cash vs. earn-out, debt assumptions, seller financing
- **Synergies:** Buyer anticipated cost synergies or revenue synergies

**Precedent Transaction Multiples:**

| Multiple | Typical M&A Range | Application |
|----------|-------------------|-------------|
| **EV/EBITDA** | 7x-16x (vs. 6x-15x trading) | Most common; reflects acquisition price inflation |
| **EV/Revenue** | 1.5x-6x (vs. 1x-5x trading) | Growth companies, SaaS (higher multiples) |
| **Deal Price / EBIT** | 8x-22x | Less common; sensitive to leverage |

**Sources for Precedent Data:**
- Bloomberg terminal (deal search, comps module)
- Capital IQ (S&P Global)
- Mergermarket (M&A intelligence)
- PitchBook (private company transactions)
- Public filings (8-K current reports, proxy statements for disclosed prices)

**Valuation Range from Precedent Transactions:**
```
Target Enterprise Value = [Low Multiple, Median, High Multiple] × Normalized EBITDA
Apply to current normalized earnings (not at acquisition date earnings)
Adjust for changes in market conditions, leverage environment, company profile
```

**Adjustment Factors:**
- **Time lag:** Adjust for multiple expansion/contraction since transaction date
- **Size:** Larger deals often command premium multiples (better liquidity)
- **Strategic buyer premium:** Add 20-40% vs. financial buyer baseline
- **Sector cyclicality:** Adjust for commodity price changes, interest rate movements

#### 1.4 Sum-of-the-Parts (SOTP) Valuation

**Framework:**
Segment business by division, geography, or business line. Value each independently using appropriate methodology (DCF, trading multiples, or precedent transactions). Aggregate for total enterprise value.

**SOTP Structure:**
```
Enterprise Value = Value(Division A) + Value(Division B) + ... + Value(Division N)
Equity Value = Enterprise Value - Net Debt + Non-Operating Assets
```

**Application:**
- Conglomerates with distinct business units
- Transition periods (e.g., company exiting a division)
- Tax restructuring analysis
- Strategic break-up valuations

**Segment Valuation Approach:**
- Apply division-specific growth rates, margins, CapEx needs
- Use divisional peers (not parent company peers) for comparable multiples
- Allocate corporate overhead by division (typical 3-8% of revenue)
- Model stand-alone tax rates by division (may differ from consolidated rate)
- Apply discount to account for loss of scale, overhead inflation when spun out

#### 1.5 Leveraged Buyout (LBO) Modeling Basics

**LBO Model Framework:**
Build a model projecting returns to equity investors in a debt-financed acquisition. Key outputs: IRR, MOIC, and debt paydown schedule.

**LBO Model Components:**

1. **Sources and Uses of Funds:**
   ```
   Uses: Purchase Price + Transaction Fees + Debt Paydown
   Sources: Debt Financing + Equity Investment + Cash on Hand
   Leverage (Debt/EBITDA) at closing: 4x-6x (typical LBO range)
   ```

2. **Debt Structure:**
   ```
   Term Loan A + Term Loan B + Senior Secured Notes + Subordinated Debt
   Repayment: Mandatory from cash flow; optional if excess cash available
   Amortization: Term Loan A (typically 5-6 year term, 1-2% annual mandatory amortization)
   Term Loan B (typically 6-7 year term, <1% annual amortization)
   Interest: Floating (SOFR/LIBOR + Spread) or fixed notes
   ```

3. **Cash Flow Waterfall (Annual):**
   ```
   EBITDA
   - Interest Expense
   - Taxes (normalized tax rate)
   - CapEx (maintenance + growth capex)
   - Δ Working Capital
   = Free Cash Flow Available for Debt Repayment
   ```

4. **Debt Paydown Schedule:**
   ```
   Mandatory Amortization: [Annual] = Loan Balance × Amortization %
   Optional Prepayment: Excess FCF applied to debt reduction (optional)
   Ending Debt Balance = Beginning Balance - Mandatory - Optional Paydown
   Debt/EBITDA Ratio: Track throughout hold period for covenant compliance
   ```

5. **Exit Scenario & Equity Return:**
   ```
   Exit Enterprise Value (Year 4-7 typically)
   - Remaining Debt Balance at Exit
   = Equity Value at Exit

   IRR = (Equity Value at Exit / Equity Investment at Entry)^(1/Hold Years) - 1
   MOIC = Equity Value at Exit / Equity Investment at Entry
   ```

6. **Return Sensitivity:**
   Create sensitivity tables showing IRR and MOIC across:
   - Exit EBITDA multiples (6x-10x range typical)
   - Hold period duration (3-7 years)
   - EBITDA growth trajectory
   - Debt paydown assumptions

---

### 2. Due Diligence Frameworks

#### 2.1 Financial Due Diligence Checklist

**Historical Financial Review:**
- [ ] Obtain 3-5 years audited/reviewed financial statements (IS, BS, CF)
- [ ] Verify clean audit opinions; note any qualifications or going concern warnings
- [ ] Obtain management accounts (unaudited) for most recent quarters; reconcile to year-end
- [ ] Review footnote disclosures, accounting policy summaries, related party transactions
- [ ] Identify any restatements, material misstatements, or changes in accounting policies

**Trend Analysis & Normalization:**
- [ ] Calculate historical revenue CAGR by segment; identify inflection points or declines
- [ ] Analyze gross margin evolution; identify pricing pressure, cost inflation, or mix shift
- [ ] Review operating expense base; separate fixed vs. variable costs
- [ ] Identify and quantify non-recurring items (one-time costs, asset sales, litigation)
- [ ] Calculate normalized EBITDA (add back non-recurring items, stock-based comp, restructuring)

**Working Capital Assessment:**
- [ ] Calculate Days Sales Outstanding (DSO) = (Receivables / Revenue) × 365
- [ ] Calculate Days Inventory Outstanding (DIO) = (Inventory / COGS) × 365
- [ ] Calculate Days Payable Outstanding (DPO) = (Payables / COGS) × 365
- [ ] Cash Conversion Cycle (CCC) = DSO + DIO - DPO; identify trends and seasonality
- [ ] Calculate net working capital requirement by year; identify normalized level
- [ ] Assess consistency of working capital accounting (e.g., revenue timing, accrual policy)

**Accounting Policy Review:**
- [ ] Revenue recognition policy (point in time vs. performance obligations, deferral patterns)
- [ ] Inventory valuation (FIFO vs. LIFO; write-down policies)
- [ ] Depreciation & amortization policy (useful lives; consistent with peers?)
- [ ] Provisions & accruals (reserves adequacy; historical over/under reserves)
- [ ] Capitalize vs. expense policy (R&D capitalization, lease accounting under ASC 842)
- [ ] Related party transactions (pricing, substance, arm's length nature)

**Quality of Earnings (QOE) Analysis:**

| Adjustment Category | Assessment | Red Flags |
|---------------------|------------|-----------|
| **Non-Recurring Revenue** | Are significant one-time contracts included? | Large year-end deals; non-recurring licensing |
| **Cost Structure** | Is cost base sustainable or inflated by cost-cutting? | Deferred maintenance; understaffed operations |
| **Operating Leverage** | Can company scale revenue without proportional cost growth? | Fixed cost base sufficient for growth targets |
| **Seasonality** | What is normalized run-rate absent seasonal peaks/troughs? | High Q4 concentration; seasonal cash flow swings |
| **Stock-Based Comp** | How material is SBC? Non-recurring or ongoing? | SBC >5-10% of operating expenses |
| **Extraordinary Items** | Gains on asset sales, litigation settlements, insurance proceeds? | Distort normalized profitability if material |

#### 2.2 Red Flag Identification

**Revenue Quality Red Flags:**

| Red Flag | Implication | Follow-up |
|----------|-------------|-----------|
| Receivables growing faster than revenue | Loosened credit terms or uncollectible sales | Request aging analysis; review credit policies; test recent collections |
| Revenue concentration in large customers | Customer loss risk; pricing power limited | Obtain customer contracts; assess switching cost; request financial statements of top 3 customers |
| Unusual year-end revenue surges | Potential channel stuffing or aggressive revenue recognition | Review Q4 vs. prior quarter trends; obtain sales contracts; review returns in subsequent period |
| Revenue from new product lines unexplained | New market; customer concentration risk | Analyze customer retention; contract terms; ASP; renewal rates |
| Significant change in customer mix or geography | Market shift or customer exit | Analyze by-customer revenue trends; geographic exposure; contract renewal status |

**Cost Structure Red Flags:**

| Red Flag | Implication | Follow-up |
|----------|-------------|-----------|
| Declining gross margins with stable revenue | Pricing pressure, unfavorable mix, or cost inflation | Analyze by-product/customer profitability; pricing trends; input cost movement |
| Rising operating expenses without revenue growth | Inefficient cost control or revenue recognition issue | Review OpEx by category; benchmark vs. peers; validate revenue recognition |
| Significant supplier or vendor concentration | Supply chain risk; pricing leverage | Obtain top supplier list; contract terms; assess alternative suppliers |
| Unexpected bonus or incentive accruals | Discretionary compensation; profit manipulation | Review bonus policy; historical payout patterns; reasonableness of accrual |

**Balance Sheet Red Flags:**

| Red Flag | Implication | Follow-up |
|----------|-------------|-----------|
| Rising inventory levels without revenue growth | Obsolescence risk; demand slowdown; supply chain buildup | Analyze inventory aging; turnover trends; assess for markdowns |
| Increasing allowance for doubtful accounts | Growing uncollectible receivables; customer credit deterioration | Review provision policy; historical bad debts; aged receivables analysis |
| Deferred revenue declining | Future revenue recognition at risk | Analyze deferred revenue by contract; assess renewal rates; customer health |
| Significant intangible assets or goodwill | Valuation risk; acquisition overpayment; impairment risk | Trace to prior acquisitions; assess underlying asset basis; impairment indicators |
| Rising debt levels with flat/declining EBITDA | Leverage risk; refinance risk; covenant violations | Review debt covenants; maturity schedule; refinance ability; leverage trends |

**Cash Flow Red Flags:**

| Red Flag | Implication | Follow-up |
|----------|-------------|-----------|
| Increasing accounts payable with declining payables turnover | Extended payment terms; strained vendor relationships | Analyze payment history; vendor concentration; DSO/DPO trends |
| Capital expenditure significantly below depreciation | Asset base aging; future maintenance CapEx risk | Assess asset age; maintenance schedule; capex timing; operating risk |
| Negative free cash flow despite positive net income | Quality of earnings concern; burn rate risk | Analyze working capital changes; CapEx sustainability; operating cash drivers |
| Large investing cash outflows for acquisitions | Integration risk; management focus distraction | Review acquisition contracts; purchase price allocation; synergy realization |

#### 2.3 Management Assessment

**Management Quality Framework:**

| Assessment Area | Key Questions | Information Sources |
|-----------------|----------------|---------------------|
| **Track Record** | Prior company exits, IPOs, or acquisitions? Outcome? Return multiples? | LinkedIn, PitchBook, company filings, reference calls |
| **Relevant Experience** | Years in industry? Similar business models? Domain expertise? | Background checks, board bios, investor materials |
| **Stability** | Turnover among leadership? Tenure of key functional heads? | Current org chart, historical changes, employee reviews |
| **Incentive Alignment** | Equity ownership? Board representation? Clawback provisions? | Equity schedule, option pool, vesting terms, employment agreements |
| **Communication** | Transparent, candid discussion of challenges? Realistic forecasts? | Reference calls, earnings call tone, investor updates |
| **Vision & Strategy** | Clear business plan? Defensible differentiation? Realistic milestones? | Business plan, investor pitch, quarterly updates, competitive positioning |

**Organizational Assessment:**
- Depth: Is there bench strength below CEO? Multiple leaders capable of running company?
- Functional coverage: CFO, CMO, COO, CTO in place or need backfill?
- Turnover: Key employee retention risk? Non-compete agreements in place?
- Advisory: Board effectiveness; experienced independent directors?

#### 2.4 Technology & Operations Due Diligence

**Technology Assessment (for software/tech companies):**

| Area | Assessment | Red Flags |
|------|-----------|-----------|
| **Architecture** | Scalable, modern tech stack? Cloud vs. on-premise? Monolith vs. microservices? | Outdated languages/frameworks; single-language dependencies; poor modularity |
| **Technical Debt** | Engineering time spent on debt vs. features? Debt quantified? | No test coverage; undocumented code; frequent outages; slow velocity |
| **Security** | Penetration testing? Data encryption? Incident response plan? SOC 2 Type II? | No security testing; data breaches; poor vulnerability management |
| **IP & Defensibility** | Patents filed? Trade secrets protected? IP assignment to company? | Unprotected proprietary code; employee IP disputes; imitable features |
| **Ops & Infrastructure** | Uptime SLAs? Disaster recovery? Backup systems? Scalability headroom? | Single points of failure; no disaster recovery; frequent outages; scaling limits |

**Operations Assessment:**
- Production capacity constraints? Bottlenecks?
- Supply chain dependencies? Geopolitical risk?
- Quality control systems? Defect rates?
- Outsourced manufacturing? Supplier concentration?
- Regulatory compliance (ISO, FDA, environmental)?

---

### 3. Portfolio Management Frameworks

#### 3.1 Modern Portfolio Theory & Asset Allocation

**Foundational Concepts:**

1. **Expected Return & Risk:**
   ```
   Portfolio Return = Σ(Weight_i × Expected Return_i)
   Portfolio Volatility = √[Σ(Weight_i^2 × σ_i^2) + 2×Σ(Weight_i × Weight_j × Cov(i,j))]
   ```

2. **Correlation & Diversification:**
   - **Correlation coefficient** ranges from -1 (perfect negative) to +1 (perfect positive)
   - Lower correlation = greater diversification benefit
   - Typical correlations: Stocks/Bonds (0.1-0.3), Stocks/Real Estate (0.4-0.6), Stocks/Commodities (0.0-0.2)

3. **Efficient Frontier:**
   - Set of portfolios that provide highest expected return for given risk level
   - Optimize by varying asset class weights
   - Higher return requires accepting higher volatility; diminishing returns at extremes

#### 3.2 Asset Allocation Framework

**Strategic Asset Allocation (SAA):**
Long-term target allocation reflecting risk tolerance, time horizon, and return objectives.

**Example SAA for Conservative Portfolio (Risk Tolerance = Moderate):**

| Asset Class | Target Allocation | Expected Return | Expected Volatility |
|-------------|------------------|-----------------|---------------------|
| Domestic Equities (Large Cap) | 30% | 8-10% | 12-15% |
| International Equities | 10% | 8-12% | 15-18% |
| Fixed Income (IG Bonds) | 35% | 4-5% | 5-7% |
| Real Estate (REITs) | 10% | 6-8% | 10-12% |
| Private Equity / Alternatives | 10% | 12-18% | 15-25% |
| Cash & Equivalents | 5% | 4-5% | 1-2% |
| **Portfolio Total** | **100%** | **~7-8%** | **~8-10%** |

**Tactical Asset Allocation (TAA):**
Short-term adjustments within strategic bands to capitalize on market opportunities or manage near-term risks.

**Example TAA Bands (± from SAA target):**
- Domestic Equities: 25%-35% (vs. 30% SAA)
- Fixed Income: 30%-40% (vs. 35% SAA)
- Alternatives: 8%-12% (vs. 10% SAA)

#### 3.3 Portfolio Construction Process

**Step 1: Define Investment Objectives**
- Return target (e.g., 8% annual return)
- Risk tolerance (e.g., max 15% portfolio volatility)
- Time horizon (e.g., 10-year investment period)
- Liquidity needs (e.g., $500K annual draw)
- Constraints (e.g., no single position >5%, no commodity exposure)

**Step 2: Identify Investment Universe**
- Asset classes available (equities, bonds, alternatives)
- Geographic markets (developed, emerging)
- Sectors / subsectors
- Manager availability (mutual funds, ETFs, separately managed accounts)

**Step 3: Select Investments**
- Screen for attractive valuations using DCF, multiples, yield analysis
- Assess fundamental quality (management, competitive position, financial stability)
- Evaluate manager quality (track record, process, capacity)

**Step 4: Optimize Allocation**
- Use Modern Portfolio Theory optimization (minimize volatility for target return)
- Stress test across historical return scenarios
- Test portfolio resilience in recession, inflation, rate increase environments

**Step 5: Monitor & Rebalance** (see Section 3.5)

#### 3.4 Sharpe Ratio & Risk-Adjusted Returns

**Sharpe Ratio Formula:**
```
Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Portfolio Volatility

Where:
- Portfolio Return = Expected return over analysis period
- Risk-Free Rate = Yield on US Treasury or benchmark (typically 10-year yield)
- Portfolio Volatility = Standard deviation of returns
```

**Interpretation:**
- Sharpe Ratio > 1.0 = Excellent risk-adjusted returns
- Sharpe Ratio 0.5-1.0 = Good risk-adjusted returns
- Sharpe Ratio < 0.5 = Suboptimal risk-adjusted returns
- Negative Sharpe Ratio = Return below risk-free rate (undesirable)

**Example Calculation:**
```
Portfolio annual return: 10%
Risk-free rate: 4%
Portfolio volatility: 12%
Sharpe Ratio = (10% - 4%) / 12% = 0.5

Interpretation: Portfolio generates 0.50 units of excess return per unit of risk taken.
Compare to alternative portfolio with Sharpe Ratio 0.6 → Better risk-adjusted returns.
```

**Use in Portfolio Construction:**
- Compare manager/strategy options on risk-adjusted basis
- Identify lowest-risk path to return target
- Determine optimal leverage (if applicable) to enhance returns

#### 3.5 Alpha & Beta Analysis

**Beta Definition:**
Beta measures systematic risk (non-diversifiable risk) relative to market benchmark.

```
β = Cov(Asset Return, Market Return) / Var(Market Return)

Interpretation:
- β = 1.0: Asset moves exactly with market (neutral systematic risk)
- β > 1.0: Asset more volatile than market (high systematic risk)
- β < 1.0: Asset less volatile than market (defensive characteristics)
- β = 0: Asset uncorrelated with market (pure alpha)
```

**Alpha Definition:**
Alpha measures excess return above what CAPM predicts based on beta.

```
α = Actual Return - [Rf + β(Rm - Rf)]

Where:
- Rf = Risk-free rate
- Rm = Market return
- β(Rm - Rf) = Beta-adjusted expected return

Interpretation:
- α > 0: Manager/strategy outperforming risk-adjusted expectation (skill or luck)
- α < 0: Manager/strategy underperforming risk-adjusted expectation
- α = 0: Returns in line with CAPM prediction (market efficient)
```

**Example:**
```
Asset annual return: 12%
Beta: 1.2
Risk-free rate: 4%
Market return: 10%

Expected return per CAPM = 4% + 1.2(10% - 4%) = 4% + 7.2% = 11.2%
Alpha = 12% - 11.2% = 0.8% (positive alpha; manager outperforming)
```

**Portfolio-Level Analysis:**
- Calculate weighted average beta of portfolio; target align to market risk appetite
- Measure aggregate alpha generation; assess if due to skill or sampling variation
- Separate alpha sources: stock selection, sector allocation, factor exposure

#### 3.6 Rebalancing Frameworks

**Rebalancing Trigger Options:**

| Trigger Type | Threshold | Frequency | Pros / Cons |
|--------------|-----------|-----------|-----------|
| **Percentage Drift** | Position deviates >1-3% from target | Event-driven | Low trading cost; may drift far before rebalancing |
| **Time-Based** | Quarterly or semi-annual | Calendar-based | Disciplined; predictable; may miss market opportunities |
| **Threshold-Based** | Position size >150% or <50% of target | Event-driven | Responsive; can result in frequent trading in volatile markets |
| **Calendar + Drift** | Quarterly unless drift >2% | Hybrid | Balanced approach; combines discipline with flexibility |

**Rebalancing Decision Tree:**

```
IF (Position Weight - Target Weight) > Drift Threshold
   THEN Execute rebalancing trade
   ELSE Monitor and hold

Rebalancing Logic:
- Overweight position → Reduce to target (take profits)
- Underweight position → Increase to target (add on weakness)
- Use cash inflows/outflows to minimize realized gains, taxes
```

**Rebalancing Math:**

```
Position to sell = (Current Weight - Target Weight) × Total Portfolio Value
Position to buy = (Target Weight - Current Weight) × Total Portfolio Value

Constraint: Σ(Positions to sell) = Σ(Positions to buy)
```

**Example:**
```
Portfolio Value: $1,000,000
Target allocation: 60% Equities, 40% Bonds

Current allocation:
- Equities: $700,000 (70%)
- Bonds: $300,000 (30%)

Rebalancing:
- Equities overweight by: 70% - 60% = 10%
- Amount to sell: 10% × $1,000,000 = $100,000
- Bonds underweight by: 30% - 40% = -10%
- Amount to buy: 10% × $1,000,000 = $100,000

New allocation:
- Equities: $700,000 - $100,000 = $600,000 (60%)
- Bonds: $300,000 + $100,000 = $400,000 (40%)
```

#### 3.7 Performance Attribution

**Return Decomposition:**
```
Total Return = Return from Allocation Decisions + Return from Security Selection + Return from Fees/Expenses

Allocation Effect = Σ[(Actual Weight - Target Weight) × (Sector Return - Total Return)]
Selection Effect = Σ[Target Weight × (Security Return - Sector Return)]
```

**Example Attribution Analysis:**

| Component | Contribution | Explanation |
|-----------|--------------|-------------|
| Strategic asset allocation | +0.8% | Overweight equities during market rally; underweight bonds during rate spike |
| Sector allocation | +0.3% | Overweight tech in growth phase |
| Security selection (equities) | +0.2% | Picked outperforming mega-cap tech stocks |
| Security selection (bonds) | -0.1% | High-yield positioning during credit spread widening |
| Cash drag / Fees | -0.4% | Cash position held for liquidity; management fees 0.3% |
| **Total Return** | **+0.8%** | vs. 0.5% benchmark return |

---

### 4. Deal Evaluation Tools

#### 4.1 Cap Table Modeling & Founder Dilution

**Cap Table Structure:**

| Investor | Shares | % Ownership | Price/Share | Investment | Valuation Post-Money |
|----------|--------|-------------|-------------|------------|----------------------|
| **Founder A** | 5,000,000 | 50% | $0.10 | $500,000 | $10,000,000 |
| **Founder B** | 3,000,000 | 30% | $0.10 | $300,000 | $10,000,000 |
| **Employee Options (Pool)** | 2,000,000 | 20% | $0.10 | - | $10,000,000 |
| **Total Pre-Seed** | **10,000,000** | **100%** | - | - | **$10M** |

**Series A Financing Example:**

```
Series A Scenario:
- Raising: $3M
- Price/share: $0.30 (3x Series A premium)
- Shares issued: 10M / $0.30 = 10,000,000 new shares

Post-Money Valuation = $3M / (A shares issued / Total shares after)
= $3M / (10M / 30M)
= $3M / 0.333
= $9M Pre-Money + $3M = $12M Post-Money

Dilution Analysis:
```

| Investor | Pre-Money Shares | Pre-Money % | Post-Money Shares | Post-Money % | Dilution |
|----------|-----------------|-------------|-------------------|------------|----------|
| Founder A | 5,000,000 | 50% | 5,000,000 | 16.7% | -33.3% |
| Founder B | 3,000,000 | 30% | 3,000,000 | 10% | -20% |
| Options Pool | 2,000,000 | 20% | 2,000,000 | 6.7% | -13.3% |
| Series A | - | - | 10,000,000 | 33.3% | +33.3% (new) |
| **Total** | **10,000,000** | **100%** | **20,000,000** | **100%** | - |

**Key Formulas:**

```
Pre-Money Valuation = (Investment / % Ownership) - Investment
Post-Money Valuation = Pre-Money + Investment
Founder Dilution % = (Shares Before - Shares After) / Shares Before

Ownership Retention After Round N:
% After = % Before × (Old Shares / Total Shares After)

Example (Founder A):
% After Series A = 50% × (5M / 20M) = 50% × 25% = 12.5% ❌ (Recalc: 5M / 20M = 25%, not 12.5%)
Actually: 5M / 20M = 25% directly
Wait - let me recalc the table above:
Founder A post-money = 5,000,000 / 30,000,000 = 16.67%
```

#### 4.2 SAFE & Convertible Note Modeling

**SAFE (Simple Agreement for Future Equity) Overview:**
Convertible instrument that operates like an option on future equity. Does not create debt or voting rights.

**Key SAFE Terms:**
- **Valuation Cap:** Maximum per-share price at which SAFE converts to equity in future round
- **Discount Rate:** % discount (e.g., 20%) on Series A price if valuation cap is not hit
- **Pro-Rata Rights:** Right to participate in future round to maintain ownership %

**SAFE Conversion Math:**

```
Scenario 1: Series A at $0.40/share with $2M SAFE, $1M valuation cap, no discount

Conversion at cap:
SAFE Conversion Price = $1M / $1M = $1.00 (minimum of cap and discounted price)
SAFE Shares = $2M SAFE / $1.00 = 2,000,000 shares (NOT $5M at $0.40)

Conversion advantage = $0.40 × 5M shares - $1.00 × 2M shares = $0 benefit
(Valuation cap advantageous if Series A price > cap valuation)
```

**Convertible Note Overview:**
Debt instrument with interest accrual. Converts to equity at future financing or on maturity/default.

**Convertible Note Conversion:**

```
Scenario: $2M convertible note, 10% annual interest, 3-year maturity, 25% discount, $5M Series A

At Series A:
Series A Price per Share = $1.00 (implies $5M valuation on some share count)
Discount = 25% → Conversion Price = $1.00 × (1 - 25%) = $0.75

Interest accrued (3 years) = $2M × 10% × 3 = $0.6M
Principal + Interest = $2M + $0.6M = $2.6M
Shares issued = $2.6M / $0.75 = 3,466,667 shares

If note matures without conversion:
Principal + Interest owed = $2.6M
Must be repaid in cash or converted
Conversion required if no liquidity event
```

**Comparison Table: SAFE vs. Convertible Note vs. Equity**

| Attribute | SAFE | Convertible Note | Preferred Stock |
|-----------|------|------------------|-----------------|
| **Debt?** | No | Yes | No |
| **Voting Rights?** | No | No | Yes (usually) |
| **Interest Accrual?** | No | Yes | Dividends (if declared) |
| **Time to Conversion** | Future round or expiration | Maturity or future round | Immediate |
| **Liquidation Priority** | Common (post-preferred) | Debt (first priority) | Preferred (after debt, before common) |
| **Founder Dilution** | Delayed | Delayed | Immediate |
| **Cost** | Low complexity | Moderate complexity | Highest complexity |

#### 4.3 Waterfall Distribution Analysis

**Exit Scenario: $100M Acquisition**

**Cap Table at Acquisition:**

| Investor | Shares | % | Liquidation Preference |
|----------|--------|---|------------------------|
| Series C (Preferred) | 10,000,000 | 25% | 1x non-participating |
| Series B (Preferred) | 8,000,000 | 20% | 1x non-participating |
| Series A (Preferred) | 12,000,000 | 30% | 1x non-participating |
| Common (Founders) | 10,000,000 | 25% | None |
| **Total** | **40,000,000** | **100%** | - |

**Original Investment Amounts:**
- Series C: $30M (paid $3.00/share for $30M investment)
- Series B: $15M (paid $1.88/share)
- Series A: $12M (paid $1.00/share)
- Founders: $1M (paid $0.10/share)

**Waterfall at $100M Acquisition:**

```
Proceeds Available: $100,000,000

Step 1: Pay off debt (none in this scenario)
Remaining: $100,000,000

Step 2: Distribute to preferred holders (in reverse order of series, per agreement)

Series C Preference: 1x non-participating
Max allocation: $30,000,000 (original investment)
Remaining after Series C: $100M - $30M = $70M

Series B Preference: 1x non-participating
Max allocation: $15,000,000
Remaining after Series B: $70M - $15M = $55M

Series A Preference: 1x non-participating
Max allocation: $12,000,000
Remaining after Series A: $55M - $12M = $43M

Step 3: Remaining proceeds to common pro-rata
Common shareholders entitled to: $43M on pro-rata basis (25% of cap table)
But they get full remainder since non-participating preferred → common gets full residual

Distribution:
- Series C: $30,000,000 (1x preference returned)
- Series B: $15,000,000 (1x preference returned)
- Series A: $12,000,000 (1x preference returned)
- Common (Founders): $43,000,000 (remaining + appreciation)
```

**Alternative Scenario: Participating Preferred (Series C)**

If Series C had 1x participating (return capital + pro-rata share of remaining):

```
Series C Preference: 1x participating
Step 1: Return $30M capital
Remaining: $70M

Step 2: Distribute remaining pro-rata by ownership %
Series C owns 25% → $70M × 25% = $17.5M
Series B owns 20% → $70M × 20% = $14M
Series A owns 30% → $70M × 30% = $21M
Common owns 25% → $70M × 25% = $17.5M

Total Distribution:
- Series C: $30M + $17.5M = $47.5M
- Series B: $14M
- Series A: $21M
- Common: $17.5M
```

---

### 5. Capital Allocation Frameworks

#### 5.1 Net Present Value (NPV) Analysis

**NPV Formula:**

```
NPV = Σ[Cash Flow_t / (1 + Discount Rate)^t] - Initial Investment

Where:
- Cash Flow_t = Expected cash inflow in year t
- Discount Rate = Appropriate cost of capital (WACC or hurdle rate)
- t = Time period (0, 1, 2, ... n years)
- Initial Investment = Upfront cost at t=0 (negative cash flow)
```

**NPV Decision Rule:**
- NPV > 0: Accept the investment (creates value)
- NPV < 0: Reject the investment (destroys value)
- NPV = 0: Indifferent (returns equal to required rate)

**Example: Investment Decision**

```
Investment in new product line:
- Initial cost: $5,000,000
- Annual cash flows: Year 1: $1.2M, Year 2: $1.5M, Year 3: $2.0M, Year 4: $2.0M, Year 5: $1.8M
- Terminal value: $2M (residual equipment value)
- Discount rate: 10% (company WACC)

NPV Calculation:
Year 0: -$5,000,000
Year 1: $1,200,000 / 1.10^1 = $1,090,909
Year 2: $1,500,000 / 1.10^2 = $1,239,669
Year 3: $2,000,000 / 1.10^3 = $1,502,630
Year 4: $2,000,000 / 1.10^4 = $1,366,027
Year 5: $1,800,000 / 1.10^5 = $1,118,454
Year 5 (terminal): $2,000,000 / 1.10^5 = $1,242,726

NPV = -$5,000,000 + $1,090,909 + $1,239,669 + $1,502,630 + $1,366,027 + $1,118,454 + $1,242,726
    = $2,560,415

Decision: Accept (NPV > 0; creates $2.56M in value)
```

#### 5.2 Internal Rate of Return (IRR)

**IRR Definition:**
Discount rate at which NPV equals zero. Also called the "money-weighted return" or "time-weighted return" of investment.

**IRR Formula:**

```
0 = Σ[Cash Flow_t / (1 + IRR)^t] - Initial Investment

Solve for IRR (typically using Excel IRR() function or iterative solver)
```

**IRR Decision Rule:**
- IRR > Hurdle Rate: Accept the investment
- IRR < Hurdle Rate: Reject the investment
- IRR = Hurdle Rate: Indifferent

**Example: Private Equity Investment**

```
Investment: $10M in private company
Year 1 distributions: $0
Year 2 distributions: $0
Year 3 distributions: $2M
Year 4 distributions: $3M
Year 5 distributions (exit): $15M
Hurdle rate: 25%

Cash flows:
Year 0: -$10M
Year 1: $0
Year 2: $0
Year 3: $2M
Year 4: $3M
Year 5: $15M

IRR = 29.1% (calculated via Excel or calculator)

Decision: Accept (29.1% > 25% hurdle; exceeds required return)
```

#### 5.3 Multiple on Invested Capital (MOIC)

**MOIC Formula:**

```
MOIC = Total Value Returned / Total Capital Invested

Where:
- Total Value Returned = Sum of all cash distributions + Current value (if still invested)
- Total Capital Invested = Sum of all cash invested (including follow-on rounds)
```

**Example:**

```
Investment 1: $5M invested in Year 0
Distributions: Year 3: $2M, Year 4: $3M, Year 5 (exit): $12M
Total returned: $2M + $3M + $12M = $17M
MOIC = $17M / $5M = 3.4x

Interpretation: $5M invested returned $17M; capital multiplied 3.4 times
```

**MOIC vs. IRR Relationship:**
```
MOIC and IRR measure same investment performance from different angles:
- MOIC ignores time value of money (absolute multiple)
- IRR accounts for timing (higher MOIC with later cash distributions = lower IRR)

Example:
Investment A: -$10M (Year 0), +$30M (Year 5) → MOIC = 3.0x, IRR = 24.6%
Investment B: -$10M (Year 0), +$30M (Year 2) → MOIC = 3.0x, IRR = 73.3%

Both have 3.0x MOIC, but Investment B has higher IRR due to faster capital return
```

#### 5.4 Payback Period

**Payback Period Definition:**
Time required for cumulative cash flows from investment to return initial capital.

**Payback Formula:**

```
Payback Period = Year before full recovery + (Unrecovered amount / Year cash flow)
```

**Example:**

```
Investment: $10M
Year 1: $2M
Year 2: $3M
Year 3: $3M
Year 4: $4M

Cumulative:
Year 1: $2M (unrecovered: $8M)
Year 2: $5M (unrecovered: $5M)
Year 3: $8M (unrecovered: $2M)
Year 4: $12M (recovered)

Payback = 3 years + ($2M / $4M) = 3.5 years

Interpretation: Takes 3.5 years to recover $10M investment from cash flows
```

**Payback Period Analysis:**

| Metric | Implication | Use Case |
|--------|-------------|----------|
| **Short Payback (1-3 years)** | Rapid capital recovery; lower risk profile | High-risk startups; distressed assets; cash-constrained investors |
| **Medium Payback (3-5 years)** | Balanced recovery; moderate risk | Growth companies; established businesses |
| **Long Payback (5+ years)** | Extended hold; capital locked up; higher risk | Infrastructure; long-dated real estate; strategic investments |

**Payback Period Limitations:**
- Ignores time value of money (use discounted payback period)
- Ignores cash flows after payback period
- Doesn't directly measure return (high MOIC possible with long payback)

---

### 6. Risk Assessment Frameworks

#### 6.1 Risk Scoring Matrix

**Investment Risk Assessment:**

| Risk Category | Score 1 (Low) | Score 2 (Medium) | Score 3 (High) | Score 4 (Critical) |
|---|---|---|---|---|
| **Business Risk** | Established market, diversified revenue | Growing market, some revenue concentration | Emerging market, concentrated revenue | Startup market, single customer |
| **Financial Risk** | Positive FCF, low leverage (1-2x), cash reserves | Positive EBITDA, moderate leverage (2-4x), thin cash | High leverage (4-6x), tight cash position | Negative cash flow, covenant violations |
| **Competitive Risk** | Defensible moat, clear differentiation | Competitive advantages, some substituability | Commoditized, limited differentiation | Intense competition, unclear differentiation |
| **Management Risk** | Proven track record, stable team, depth | Experienced CEO, some management depth | New CEO, limited depth, retention risk | Inexperienced team, high turnover |
| **Liquidity Risk** | Public market / frequent distributions (annual) | Private but secondary market, 2-3 year lockup | Illiquid investment, 5+ year hold | Highly illiquid, uncertain exit |
| **Regulatory Risk** | Stable regulatory environment, compliance history | Some regulatory oversight, no major issues | Significant regulation, recent compliance violations | Heavy regulation, existential risk |
| **Market Risk** | Recession-resilient, counter-cyclical demand | Cyclical demand, manageable downside | Sensitive to macro, significant downside | Existential to downturn |
| **Technology Risk** | Proven, scalable tech, low obsolescence | Mature technology, ongoing development | Emerging technology, still evolving | Unproven technology, high obsolescence risk |

**Risk Score Calculation:**
```
Total Risk Score = Σ(Component Score × Weight)

Example weights (customize per investment type):
- Business Risk: 20%
- Financial Risk: 20%
- Competitive Risk: 15%
- Management Risk: 15%
- Liquidity Risk: 10%
- Regulatory Risk: 10%
- Market Risk: 5%
- Technology Risk: 5%

Score Interpretation:
1.0 - 1.5: Conservative risk profile (suitable for risk-averse investors)
1.5 - 2.5: Moderate risk profile (core portfolio holdings)
2.5 - 3.5: Aggressive risk profile (growth allocations)
3.5 - 4.0: Venture/speculative risk (limited allocation, high return expectation)
```

#### 6.2 Concentration Risk Assessment

**Position Concentration Limits:**

| Portfolio Size | Max Single Position | Sector Limit | Geographic Limit |
|---|---|---|---|
| < $100M | 5% | 20% | 25% |
| $100M - $500M | 3% | 15% | 20% |
| $500M - $2B | 2% | 10% | 15% |
| > $2B | 1% | 8% | 10% |

**Concentration Monitoring Dashboard:**

```
Position Analysis:
- Sort positions by size (largest first)
- Calculate cumulative % (top 10 positions should be <50% in diversified portfolio)
- Flag any position >5% that underperforms risk profile

Sector Exposure:
- Group by GICS sector (or custom scheme)
- Calculate total sector exposure
- Identify overweight sectors relative to benchmark or target

Geographic Exposure:
- Group by country/region
- Identify country concentration risk (especially emerging markets)
- Assess currency exposure (if applicable)

Customer/Supplier Concentration (Portfolio Companies):
- Top 10 customers should be <50% of revenue (for operating companies)
- No single supplier should be >20% of COGS
- Assess switching costs and relationships
```

#### 6.3 Liquidity Risk Assessment

**Liquidity Classification:**

| Liquidity Tier | Characteristics | Holding Period | Mark-to-Market | Redemption |
|---|---|---|---|---|
| **Tier 1 - Highly Liquid** | Large-cap stocks, liquid bonds, most ETFs | Sell within days | Daily/real-time | Daily/weekly |
| **Tier 2 - Liquid** | Mid-cap stocks, high-yield bonds, liquid alternatives | Sell within weeks | Daily | Monthly/quarterly |
| **Tier 3 - Semi-Liquid** | Small-cap stocks, private company secondaries, most PE | Sell within months | Quarterly | Quarterly/semi-annual |
| **Tier 4 - Illiquid** | Direct private equity, venture, real estate | 4-7 year hold | Annual | Annual/exit |
| **Tier 5 - Highly Illiquid** | Pre-revenue ventures, infrastructure, certain distressed | 7+ year hold | Infrequent | Exit-dependent |

**Portfolio Liquidity Planning:**

```
Annual Liquidity Need: $X
Tier 1 Allocation: 1-2 × Annual Need (buffer)
Tier 1-2 Combined: 50-70% of portfolio
Tier 3+: 30-50% of portfolio (long-term capital)

Example: $10M portfolio, $500K annual need
- Tier 1: $1.0M (10%)
- Tier 1-2: $6.5M (65%)
- Tier 3-5: $3.5M (35%)
```

#### 6.4 Downside Scenario Analysis

**Scenario Framework:**

```
Base Case: Management guidance, historical trends, analyst consensus
- Probability: 50%
- Revenue CAGR: 10%
- EBITDA Margin: 20%
- Valuation multiple: 8x EBITDA

Upside Case: Market share gains, margin expansion, M&A synergies
- Probability: 25%
- Revenue CAGR: 15%
- EBITDA Margin: 25%
- Valuation multiple: 10x EBITDA
- Potential return: 20% + 50% multiple expansion = 85% total return

Downside Case: Revenue headwinds, margin compression, competitive pressure
- Probability: 20%
- Revenue CAGR: 3%
- EBITDA Margin: 15%
- Valuation multiple: 6x EBITDA
- Potential return: 25% revenue growth + 25% multiple contraction = -10% total return

Bear Case: Recession, industry disruption, management failure
- Probability: 5%
- Revenue decline: -20%
- EBITDA Margin: 5%
- Valuation multiple: 4x EBITDA (or distressed sale)
- Potential loss: -50% or greater
```

**Expected Value Calculation:**
```
Expected Return = (85% × 0.25) + (20% × 0.50) + (-10% × 0.20) + (-50% × 0.05)
               = 21.25% + 10% - 2% - 2.5%
               = 26.75% expected return

Risk Assessment:
- Downside volatility (downside only): 0.20 × 10% + 0.05 × 50% = 4.5% risk
- Upside potential: 85% with 25% probability
- Asymmetric payoff (positive skew preferable)
```

---

## How to Invoke This Agent

### Trigger Phrases

**Valuation Analysis:**
- "Run a DCF valuation on [Company]"
- "What's the fair value using comparable multiples?"
- "Build a valuation range for this acquisition candidate"
- "Compare [Company A] to precedent transactions in [Industry]"
- "Model the equity returns in an LBO scenario"

**Due Diligence:**
- "Conduct financial due diligence on [Company]"
- "What red flags do you see in this financials?"
- "Assess the management team for [Company]"
- "Run a quality of earnings analysis"
- "Check this cap table for dilution concerns"

**Portfolio Management:**
- "Rebalance my portfolio"
- "Should I adjust my asset allocation?"
- "What's my portfolio Sharpe ratio?"
- "Identify concentration risks in my portfolio"
- "Run a performance attribution analysis"

**Deal Evaluation:**
- "Model this SAFE conversion"
- "Calculate the waterfall distribution at exit"
- "What's the dilution from this financing round?"
- "Analyze this convertible note economics"
- "Build a full cap table projection"

**Capital Allocation:**
- "Evaluate NPV of this investment opportunity"
- "Calculate the IRR on this deal"
- "Run a sensitivity analysis on [Investment]"
- "Compare investment candidates on risk-adjusted returns"
- "What's the payback period on this investment?"

**Risk Assessment:**
- "Score the risk profile of [Investment]"
- "Identify concentration risks in my portfolio"
- "Run a downside scenario analysis"
- "Assess liquidity risk in my positions"
- "Stress test my portfolio against [Market Scenario]"

---

## Investment Memo Template Structure

### Executive Summary
- Investment thesis (2-3 sentences)
- Key investment highlights
- Valuation summary (DCF, comparables, precedent range)
- Expected return (IRR, MOIC)
- Key risks and mitigants
- Recommended investment size and terms

### Investment Thesis
- Market opportunity and size
- Company differentiation and competitive moat
- Management team assessment
- Path to profitability / exit scenario
- Key value creation milestones

### Financial Analysis
- Historical financials (3-5 years) with normalized EBITDA
- Valuation analysis (DCF, comps, precedent transactions, SOTP)
- Sensitivity and scenario analysis
- Quality of earnings assessment
- Working capital normalization

### Valuation Conclusion
- DCF valuation range (base, upside, downside)
- Comparable company valuation (median, range)
- Precedent transaction valuation (median, range)
- Recommended valuation and entry price
- Rationale for selected valuation

### Risk Assessment
- Key risks and impact on valuation
- Mitigation strategies
- Red flags from due diligence
- Contingency planning

### Deal Terms
- Security type and pricing
- Liquidation preferences (if preferred stock)
- Board and governance rights
- Anti-dilution provisions
- Use of proceeds

### Investment Committee Recommendation
- Go / No-Go decision
- Conviction level and rationale
- Conditions to investment
- Required approvals

---

## Example Workflows

### 1. Investment Opportunity Evaluation Workflow

```
Step 1: Initial Thesis Development
- Define market opportunity and competitive landscape
- Assess company differentiation and defensibility
- Identify key value drivers and growth assumptions
- Establish go/no-go criteria (return target, risk tolerance, strategic fit)

Step 2: Financial Data Collection
- Obtain 3-5 years historical financials (audited if available)
- Gather management projections (3-5 year forecast)
- Collect market data and comparable companies
- Research precedent transactions

Step 3: Quality of Earnings Analysis
- Normalize historical EBITDA (add back non-recurring items)
- Assess revenue quality (customer concentration, growth sustainability)
- Evaluate cost structure (fixed vs. variable, margin trends)
- Calculate normalized working capital requirements

Step 4: Valuation Analysis
- Build DCF model (explicit forecast + terminal value)
- Run comparable company analysis (identify 5-15 peers)
- Research precedent transactions (5-10 recent deals)
- Develop valuation range (DCF base, upside, downside)
- Sanity check: Is valuation reasonable vs. trading/precedent multiples?

Step 5: Management Assessment
- Review management track record (prior exits, company growth)
- Conduct management interviews (strategy, execution capability)
- Request reference checks (board members, prior investors, customers)
- Assess organizational depth and bench strength

Step 6: Risk Assessment
- Score investment on risk matrix (business, financial, competitive, market, tech)
- Identify key downside scenarios and probability
- Develop mitigation strategies
- Stress test financial model to critical assumptions

Step 7: Investment Decision
- Present summary memo to investment committee
- Review expected returns (IRR, MOIC, payback period)
- Confirm investment aligns with return hurdles and portfolio risk tolerance
- Recommend investment size, terms, and governance structure
- Approve or reject investment

Step 8: Post-Investment Management
- Establish KPI monitoring dashboard
- Schedule quarterly board meetings and operational reviews
- Track actual vs. plan performance
- Prepare annual/exit planning as applicable
```

### 2. Quarterly Portfolio Review Workflow

```
Step 1: Performance Reporting
- Calculate period returns (all positions + aggregate portfolio)
- Perform attribution analysis (allocation effect vs. selection effect)
- Compare performance to benchmark and investment objectives
- Note significant position moves and market drivers

Step 2: Risk Monitoring
- Calculate concentration metrics (top 10 positions, sector exposure, geography)
- Assess liquidity profile (% in Tier 1-2 vs. Tier 3-5 positions)
- Review covenant compliance (for portfolio companies with leverage)
- Monitor key operational metrics for portfolio companies

Step 3: Valuation Updates
- Update valuations for public positions (use market prices)
- Update private company valuations (recent comparable multiples, DCF updates)
- Identify material valuation adjustments and drivers

Step 4: Portfolio Rebalancing
- Calculate current vs. target allocation for each asset class
- Identify rebalancing triggers (drift >1-2% from target)
- Execute rebalancing trades (sell overweights, buy underweights)
- Document rebalancing rationale and timing

Step 5: Risk Assessment
- Revisit concentration risks and rebalance if needed
- Stress test portfolio to recession, rate hike, liquidity event scenarios
- Identify positions with deteriorating risk profiles
- Escalate red flags to investment committee

Step 6: Opportunity Assessment
- Review watchlist for investment triggers (valuation, strategy, competitive)
- Assess capital allocation across portfolio (sufficient dry powder?)
- Identify follow-on investment opportunities in existing positions
- Plan for near-term liquidity events and redemptions

Step 7: Documentation & Reporting
- Prepare quarterly portfolio review memo
- Present to investment committee with performance, risks, actions taken
- Document all decisions and rationale for future review
- Update portfolio tracking model with latest positions, valuations
```

### 3. Due Diligence Process Workflow

```
Step 1: Assign Due Diligence Work Streams
- Financial DD (lead analyst): Historical financials, normalization, QOE
- Commercial DD (business development): Market, customers, competitive position
- Legal DD (legal team): Contracts, litigation, IP, regulatory compliance
- Technology DD (CTO or tech advisor): Architecture, security, scalability, IP
- Management DD (all leads): Reference calls, background checks, cultural fit

Step 2: Financial DD Deep Dive
- [ ] Extract and audit historical financials (5 years)
- [ ] Analyze revenue by customer, geography, product (identify concentration)
- [ ] Calculate gross margin by segment; identify trends and drivers
- [ ] Review working capital movements; normalize for seasonality
- [ ] Model normalized EBITDA and calculate key metrics (FCF, debt/EBITDA)
- [ ] Perform variance analysis on prior guidance vs. actuals
- [ ] Assess accounting policies and potential restatement risk
- [ ] Build 3-year management projections and stress test to conservative scenario

Step 3: Commercial DD Deep Dive
- [ ] Map industry dynamics and competitive landscape
- [ ] Analyze top 10 customers (concentration, contracts, churn risk)
- [ ] Assess product differentiation and market positioning
- [ ] Identify regulatory or industry headwinds
- [ ] Evaluate pricing power and margin sustainability
- [ ] Review go-to-market strategy and sales effectiveness

Step 4: Legal DD Deep Dive
- [ ] Review material contracts (customer, vendor, debt, employment)
- [ ] Search for litigation history and pending matters
- [ ] Verify IP ownership (patents, trademarks, trade secrets)
- [ ] Confirm regulatory compliance (licenses, permits, audits)
- [ ] Review corporate governance and cap table
- [ ] Assess material related-party transactions

Step 5: Technology DD Deep Dive (if applicable)
- [ ] Review technology architecture and scalability
- [ ] Assess technical team capability and retention risk
- [ ] Evaluate IP defensibility and patent portfolio
- [ ] Perform security audit or penetration testing
- [ ] Review development velocity and technical debt

Step 6: Management DD Deep Dive
- [ ] Conduct in-depth management interviews
- [ ] Request reference calls (5-10 references per key executive)
- [ ] Assess track record on prior company(ies)
- [ ] Evaluate organizational depth and succession plans
- [ ] Confirm incentive alignment (equity, options, bonus structure)

Step 7: Red Flag Consolidation & Risk Scoring
- [ ] Compile red flags from all work streams
- [ ] Classify by severity and probability of impact
- [ ] Develop mitigation strategies for material risks
- [ ] Prepare risk matrix and impact scenarios

Step 8: Final Investment Committee Presentation
- [ ] Summarize DD findings by work stream
- [ ] Present valuation analysis and recommended entry price
- [ ] Articulate key risks and mitigants
- [ ] Recommend investment decision (Go/No-Go) and any required conditions
- [ ] Obtain IC approval and document decision
```

### 4. Cap Table Modeling & Dilution Analysis Workflow

```
Step 1: Build Historical Cap Table
- [ ] Identify all share classes (Common, Series A, Series B, etc.)
- [ ] Record founder shares and vesting schedule
- [ ] Document all financing rounds (amount raised, price per share, investors)
- [ ] Model option pool (size, vesting schedule, exercise prices)
- [ ] Verify cap table totals match share registry

Step 2: Model Pro-Forma Cap Table (New Round)
- [ ] Define new round terms (amount, price per share, investor name)
- [ ] Calculate post-money valuation
- [ ] Calculate new shares issued = Investment / Price per share
- [ ] Calculate resulting ownership % for all shareholders
- [ ] Calculate dilution % for each existing shareholder

Step 3: Assess Founder Dilution
- [ ] Calculate cumulative dilution from all prior rounds
- [ ] Project future dilution from planned rounds (use industry benchmark)
- [ ] Assess if founder incentive alignment is at risk (ownership <10-15% is concerning)
- [ ] Model future financing scenarios (Series C, D) and cumulative dilution

Step 4: Model SAFE/Convertible Note Impact
- [ ] Document all SAFEs outstanding (valuation cap, discount, pro-rata rights)
- [ ] Estimate probability each SAFE converts in next round (cap vs. discount)
- [ ] Calculate pro-forma dilution including SAFE conversion
- [ ] Compare to debt-free cap table for contrast

Step 5: Waterfall Analysis
- [ ] Define exit scenarios (acquisition at $X, IPO at $Y, down round at $Z)
- [ ] For each scenario, model waterfall distribution
  - Step 1: Pay debt and transaction fees
  - Step 2: Return capital to preferred shareholders (per liquidation preferences)
  - Step 3: Distribute remaining pro-rata to common
- [ ] Calculate payoff to each shareholder class in each scenario
- [ ] Assess risk to common shareholders (downside protection)

Step 6: Present Model to Founders & Board
- [ ] Explain cap table structure and shareholder rights
- [ ] Present dilution scenarios from planned future rounds
- [ ] Discuss founder incentive alignment
- [ ] Discuss de-risking (exit scenarios, preferred terms impact)
- [ ] Confirm alignment on equity expectations
```

---

## Tables & Reference Materials

### Valuation Summary Table

| Valuation Method | Range Low | Range High | Recommended Value | Rationale |
|---|---|---|---|---|
| **DCF (Base Case)** | $85M | $110M | $95M | WACC 8%, growth 10%, terminal 2.5% |
| **DCF (Upside)** | $120M | $150M | $130M | WACC 7.5%, growth 15%, margin expansion |
| **DCF (Downside)** | $60M | $80M | $70M | WACC 9%, growth 3%, margin compression |
| **Trading Multiples** | $88M | $112M | $100M | 10-11x EBITDA median; normalized EBITDA $9.5M |
| **Precedent Transactions** | $90M | $115M | $105M | 9.5-12x EBITDA; adjusted for company profile |
| **SOTP (if multi-division)** | $92M | $108M | $100M | Segment-specific valuations aggregated |
| **Consensus Valuation Range** | **$85M** | **$115M** | **$100M** | Mid-point of all methodologies; $95-105M target range |

### Risk Scoring Matrix (Populated Example)

| Risk Category | Score | Notes | Mitigation |
|---|---|---|---|
| Business Risk | 2 | Established market, some revenue concentration in top 3 customers (35% of revenue) | Diversify customer base over 2 years; expand into adjacent markets |
| Financial Risk | 2 | Positive FCF, moderate leverage at 2.5x EBITDA, 12 months cash on hand | Maintain 1-1.5x coverage; refinance debt before maturity |
| Competitive Risk | 2 | Clear differentiation via proprietary tech; some substitutes exist | Continue innovation; build switching costs via ecosystem |
| Management Risk | 1 | CEO is successful founder with 2 prior exits; COO brings industry expertise | Ensure deep org chart; build bench strength |
| Liquidity Risk | 3 | Private company; exit timeline 4-5 years via acquisition or IPO | Establish relationships with potential acquirers; plan IPO readiness |
| Regulatory Risk | 2 | Subject to industry regulation; clean compliance history | Maintain compliance; budget for regulatory monitoring |
| Market Risk | 2 | Cyclical demand tied to enterprise IT spending; resilient in past recession | Diversify end markets; build counter-cyclical offerings |
| Technology Risk | 1 | Mature, scalable architecture; continuous development; low obsolescence risk | Maintain R&D spend at 8-10% of revenue; monitor emerging tech |
| **Weighted Risk Score** | **1.8** | **Moderate Risk Profile** | **Suitable for core portfolio allocation** |

---

## Key Investment Metrics & Formulas Summary

### Valuation Multiples (Quick Reference)

```
EV/EBITDA = Enterprise Value / EBITDA
EV/Revenue = Enterprise Value / Revenue
P/E Ratio = Market Cap / Net Income
EV/EBIT = Enterprise Value / Operating Income
PEG Ratio = P/E Ratio / Expected Growth Rate (%)
```

### Return Metrics (Quick Reference)

```
IRR = Internal rate of return (discount rate where NPV = 0)
MOIC = Multiple on Invested Capital = Total Value Returned / Capital Invested
Payback Period = Years to recover initial investment from cash flows
Sharpe Ratio = (Return - Risk-Free Rate) / Volatility
Alpha = Actual Return - Expected Return per CAPM
Beta = Covariance(Asset, Market) / Variance(Market)
```

### Portfolio Risk Metrics (Quick Reference)

```
Portfolio Return = Σ(Weight × Expected Return)
Portfolio Volatility = √[Σ(Weight² × Volatility²) + 2×Σ(Weight × Weight × Correlation)]
Concentration = Top 10 Positions / Total Portfolio %
Liquidity Score = % in Tier 1-2 (Highly Liquid) / Total Portfolio %
```

---

## Version History

| Version | Date | Updates |
|---------|------|---------|
| 1.0 | 2026-03-28 | Initial creation; core capabilities and operating framework defined |
| 2.0 | 2026-03-28 | Comprehensive expansion: valuation formulas (DCF, comps, precedent, SOTP, LBO), detailed due diligence checklists (financial DD, red flags, QOE, management), portfolio frameworks (MPT, Sharpe ratio, alpha/beta, rebalancing), deal evaluation tools (cap table, SAFE/note modeling, waterfalls), capital allocation (NPV, IRR, MOIC, payback), risk assessment (scoring matrix, concentration, liquidity, scenario analysis), example workflows (4 detailed processes), investment memo template, populated example tables and formulas, How to Invoke section with trigger phrases |

---

**Last Updated:** 2026-03-28
**Next Review:** Quarterly or as investment strategy evolves

---

**Owner:** [Your Name]
**Classification:** Partial-Coverage Agent | Finance Plugin Foundation
