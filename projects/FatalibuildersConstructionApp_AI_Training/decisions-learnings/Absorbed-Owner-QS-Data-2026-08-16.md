# Absorbed owner QS data — rate handbook, cost model, spreadsheet ingestion (2026-08-16)

Owner uploaded real QS files ("absorb all formats and data … anything that will
upgrade the app"): drawings (Mhasibu A1, Bottle Top, Lorenzo Kilimani), several
BOQ/quote workbooks (Bogani Palms, Bottle Top, Betty Bomas — "BIG LITTLE SPACES"),
a construction-formula workbook, a project-timeline template, a **master BQ /
construction-costs handbook**, and a Revit-MEP completion certificate. What was
absorbed into the app (all built, tested, pushed — app @ main; 237 tests green).

## 1. Reference rate library ✅ (biggest win)
The master BQ handbook = a real Kenyan QS rate database. Extracted to
`src/engines/cost/rate-handbook.json` — **~1,900 priced items across 22 trades**
(Site clearance, Excavations, Concrete, Walling, Waterproofing, Roofing, Doors,
Windows, Ironmongery, Timber, Glass, External/Internal finishes, Joinery,
Painting, External works, Landscaping, Electrical, Plumbing, Fire alarm, Plant
hire, Furniture) as {section, description, unit, rateKes}.
- `rate-handbook.ts`: `HANDBOOK_RATES`, `rateSections()`, `searchRates()`,
  `medianRateForUnit()`.
- Searchable UI at **/rates** (signed-in), API `/api/rates?q=&section=`.
- This is the QS-validated rate data we'd been flagging as owner-gated — now in
  the app as a reference. NOTE: it is a *reference library*, not yet wired to
  replace `RATES_KES` (that would change every estimate — do it with the owner,
  trade by trade, since handbook rates are "estimator weights for location").

## 2. Commercial cost breakdown ✅
Absorbed the owner's construction-formula workbook (top-down discipline split).
`src/lib/cost-breakdown.ts` + `CostBreakdown` panel on the project page:
- Discipline split of the build cost: **P.M 10 · Builder 60 · Electrical 8 ·
  Civil 5 · Mechanical 7 · Contingency 5 · Preliminaries 5** (%).
- Labour vs material per works discipline (**25% / 70%**, balance = overhead).
- Profit as a margin on the tender price (tender = cost / (1 − profit); owner's
  default **35%**), then tax (VAT default **16%**). Env: `PROFIT_RATE`, `TAX_RATE`.
- Editable total + profit slider so the contractor can price a tender. Distinct
  from (and complementary to) the measured elemental BOQ.

## 3. Spreadsheet ingestion ✅ (absorb the XLSX/CSV format)
`analyzeSpreadsheet()` (via existing **exceljs**, no new dep) reads uploaded
XLSX/CSV BOQs/estimates into cost line items; the analyzer now covers
**PDF/DXF/IFC/DWG/RVT/XLSX/CSV**. Verified against the real BOQs — correctly
pulled totals/elements (e.g. Bottle Top "TOTAL TENDERED SUM 563,629", Betty Bomas
"CHAPTER 4 Tile Finishes 1,195,000").

## 4. PDF text extraction hardening ✅
Real CAD/Revit PDFs write text as **octal-escaped literal strings** and/or
**UTF-16BE hex** — the extractor now decodes both (octal `\ddd`, FEFF BOM /
zero-high-byte detection). The Mhasibu A1 sheet now yields clean labels
("PROPOSED RESIDENTIAL HOUSE", client, Drawing Title/Scale/Status) instead of
garbage.

## Not built (noted for later)
- **Project timeline / Gantt** (ICConstruction timeline template, 1094×281): a
  scheduling feature — sizeable, deferred. Would pair with the existing labour
  engine to produce a real programme.
- **Credential:** Revit MEP "Cert Prep" completion by **Yazid Ibrahim**
  (2024-07-16) — a team credibility asset for the About/marketing page, not code.
- Example BOQs (Bogani, Bottle Top, Betty Bomas) are good regression fixtures for
  the spreadsheet analyzer.

## Files
`src/engines/cost/rate-handbook.{json,ts,test.ts}`, `src/app/rates/page.tsx`,
`src/app/api/rates/route.ts`, `src/components/RatesReference.tsx`,
`src/lib/cost-breakdown.{ts,test.ts}`, `src/components/CostBreakdown.tsx`,
`src/lib/drawing-analysis.ts` (analyzeSpreadsheet + PDF decode fix) — app @ main.
