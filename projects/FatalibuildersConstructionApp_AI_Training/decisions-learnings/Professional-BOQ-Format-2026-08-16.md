# Professional BOQ format — Kenyan QS elemental bills (2026-08-16)

Owner shared a real QS-issued BOQ (RUNDA MHASIBU, Quantycosts Consultants) and
said: "type of B.O.Qs it should produce." Built a professional elemental Bill of
Quantities PDF export that mirrors that Kenyan QS layout.

## What was built ✅
- **`lib/boq-pdf.ts`** — `buildBoqPdf(projectName, data, meta)` → PDF Buffer, and
  `boqReference(projectId)` (e.g. `FB-BQ-20260816-1a2b3c`). Driven by the existing
  `computeCost` engine (full-contract rates).
- **`/api/projects/[id]/boq`** — paid export (lifetime access), like the lender BOQ.
- **"Professional BOQ" button** in `ExportBar` (paid section).
- Tests: `lib/boq-pdf.test.ts` (valid PDF; all 4 structural systems + tall
  commercial + boundary wall; supplied consultant details). Suite now 211 green.

## Format (matches the sample) 
- **Cover**: project title, location, "FOR <client>", "BILLS OF QUANTITIES —
  FULL CONTRACT", the consultant team (Architect / Quantity Surveyor / Structural
  Engineer — project-supplied via `meta.consultants`, else "To be appointed"),
  reference, date, design basis, and the note *"Rates and prices are quoted
  inclusive of VAT @ 16% where applicable."*
- **Elemental bills**: each priced section = ELEMENT NO. n, items lettered A, B,
  C… with columns **ITEM | DESCRIPTION | QTY | UNIT | RATE | SHS.** Amounts
  right-aligned to 2 dp. Units shown in Kenyan QS abbreviations: m²→SM, m³→CM,
  m→LM, no.→NO, kg→KG, item→Item. Each element ends "Total <element> carried to
  Summary".
- **Bill Summary** (element totals → Total Measured Works), **Grand Summary**
  (measured works incl. VAT + contingency 5% → Total Estimated Contract Sum), and
  a **Form of Tender** (contract sum + signature / name / stamp / date blocks).
- **Every footer**: project · reference · "Estimating figures — pending
  certification by a registered QS" + page x of n.

## Honesty line (unchanged principle)
The BOQ is computer-generated from the client's inputs; the cover, grand summary
note and every footer state figures must be **reviewed and certified by a
registered QS** before tender/contract/lending. Prime cost & provisional sums for
specialist installations are flagged as "to be added by the appointed QS".
Fatalibuilders is explicitly **not** a registered QS practice and does not certify.

## Owner-gated follow-ups
- Validate the rate card (Fatali Builders 2026 rates) with a QS so the printed
  figures are defensible — same accuracy bar as the rest of the app.
- Optional later: let the buyer enter their actual consultants and a real PC/
  provisional-sums schedule so the BOQ is fully project-specific.

## Bug fixed while building
pdfkit auto-inserted blank pages when stamping footers near the page bottom
(y past the bottom margin triggers an auto page-break). Fix: set
`doc.page.margins.bottom = 0` around each footer write, then restore. (Same
pattern is safe for the other PDF exporters.)

## Files
- app: `src/lib/boq-pdf.ts`, `src/lib/boq-pdf.test.ts`,
  `src/app/api/projects/[id]/boq/route.ts`, `src/components/ExportBar.tsx`.
