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

## Follow-up (same day): consultants + PC sums, and drawing analysis ✅
Owner: "yes [add consultants + PC sums to the wizard]" and "put an option of
uploading pdf architectural and structural drawings including DWG or revit …
it analyze and give out the data"; then clarified: "come up with realistic
renders and numbers" and "can the app analyze the documents **without storing
them**". Built both.

### Project team + provisional sums on the BOQ
- schema: optional `consultants[]` (role/name/address) and `provisionalSums[]`
  (label/amountKes) on `ProjectData`.
- wizard: optional "Professional details" section on the review step.
- boq-pdf: cover prints the supplied team; grand summary lists each PC/
  provisional sum and rolls it into the contract sum (and the form of tender).

### In-memory drawing analysis (NO storage)
`lib/drawing-analysis.ts` + `/api/projects/[id]/analyze-drawing` (POST multipart)
+ `DrawingAnalyzer` + `/projects/[id]/analyze`. **The file is parsed in memory
and discarded — never written to disk/blob** (owner's explicit choice; also the
right privacy default, and sidesteps Vercel's lack of file storage).
- **DXF** (AutoCAD export) → bounding-box footprint in metres (via `$INSUNITS`),
  entity/label counts. Real geometry.
- **IFC** (Revit export) → storeys, walls/slabs/columns/beams/doors/windows
  counts, space names, and areas/volumes from `IfcElementQuantity`. Real BIM data.
- **PDF** → best-effort embedded text (handles hex `<...>` string tokens) +
  detected `L × W` dimension pairs. **Advisory only** — a picture is not a
  measured take-off.
- **DWG / RVT** → closed binaries; detected only, with a one-click "export DXF/
  IFC" instruction. (Cannot be read in a serverless app without a paid CAD cloud
  — same honesty line as bridges/renders: don't fake it.)
- Extracted inputs merge into the project → indicative estimate + render, and an
  "Apply to project" (PUT) so the BOQ/drawings pick them up. Everything labelled
  "indicative — verify with a licensed QS/engineer".

Honesty reminder given to owner: real auto-quantities come from **IFC/DXF**;
PDF is text/suggestion; DWG/RVT need export. Numbers still gated on validating
the rate card with a QS. Suite: 217 green; tsc/lint/build clean.

### Follow-up: IFC→rooms + AI vision read ("all of them") ✅ 224 green
- **IFC spaces → room list** (`extractIfcRooms`): walks the STEP graph — IfcSpace
  → IfcRelDefinesByProperties → IfcElementQuantity → IfcQuantityArea (area, room
  size = √area), and IfcRelAggregates(storey→spaces) for the floor number. Applying
  it populates `data.rooms` so the room-layout plan draws itself from the model.
  Gotcha fixed: the RelatingObject is the **last #ref before the related ()-list**
  (GlobalId/OwnerHistory/etc. come first), not `refs[0]`.
- **AI vision read** (`lib/drawing-vision.ts`, mock-until-keys on VISION_API_URL/
  KEY/MODEL): rasterize first PDF page via **mupdf (WASM, dynamic import, server
  only)** or an uploaded image via sharp → OpenAI-compatible vision chat → strict
  JSON {footprintLengthM,footprintWidthM,floors,rooms[]}. Parsed + bounded
  (`parseVisionSuggestion`), shown as a **separate "AI suggestion — verify"** block
  with its own apply (`aiMergedData`). Deterministic extraction unchanged when no
  vision key. New dep: `mupdf`.
- Env: added VISION_API_URL / VISION_API_KEY / VISION_API_MODEL to `.env.example`.
