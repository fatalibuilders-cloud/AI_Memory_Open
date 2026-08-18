# Structural drawings, geotech, design production, allowances (2026-08-18)

Owner's multi-part request (structural drawings with all elements + bending/
cutting list; foundation per soil; verified build 3–5% of cost; progress daily
logs; trial = 1 project; web rate comparison; design production PDF with all
views incl. interior/exterior; subscriber project allowance 3/mo +1 per month;
geotechnical report referencing ISSMGE). Built & pushed (app @ main; 309 tests).

## Done
1. **Foundation per soil** — `foundationForSoil()` in `engines/structural`: rock/
   gravel/sand/silt/clay/black-cotton/unknown each get a distinct scheme +
   `SOIL_BEARING` (indicative kN/m²). Feeds the scheme, drawings and geotech report.
2. **Structural 2D drawings** (`engines/drawings/structural.ts`, served via the
   drawings route + shown in the Structural tab):
   - Foundation & column layout — grid bubbles, dimension strings, columns + pad
     bases (or load-bearing walls for masonry), beams.
   - Slab reinforcement — main/distribution bars + section.
   - **Bar bending schedule** — all elements (footings, columns+links, beams+links,
     ground beams+links, lintels, slab main+dist, staircase), a bending-shape
     diagram per row (BS 8666 straight/link/L), + a **cutting/ordering list** by
     bar size (total length, mass kg, 12 m stock lengths incl. ~5% waste) & tonnage.
3. **Verified Build = 3–5% of construction cost** — `verifiedBuildPriceForCost()`
   (`VERIFIED_BUILD_PCT` clamped 3–5%, default 4%; KES floor; FX for USD). Checkout
   + project panel use it.
4. **Trial/free = 1 project; subscribers 3 + 1 per month; lifetime unlimited** —
   `projectAllowance()` (LEFT JOIN LATERAL on latest subscription); enforced in
   POST /api/projects.
5. **2025 market rate cross-check** — `engines/cost/market-rates.ts` (cement, rebar,
   concrete, blocks, ballast, sand, build cost/m²) from published Kenyan sources
   (via WebSearch — integrum.co.ke egress is blocked); shown on /rates with source
   links. Handbook stays the pricing basis; these are external cross-checks.
6. **Preliminary Geotechnical Report** (`lib/geotech-pdf.ts`, `/api/projects/[id]/
   geotech`) — soil bearing, suited foundation, a site-investigation + lab-testing
   plan (trial pits/boreholes, SPT, Atterberg, swell, shear/oedometer, CBR,
   chemical), risks, standards (BS 5930, EN 1997) + ISSMGE library link, and a
   certification block. Honest: a desk study, not a site investigation.
7. **Design Production PDF** (`lib/design-production-pdf.ts`, `/api/projects/[id]/
   design-production`) — one PDF per project with all views: exterior (AI render
   when configured & under the render cap, else massing) + spec/budget; plans +
   structural layout; interior concept (room-by-room layout per floor + finishes).
   Button in DrawingsView.

## Honesty line held
All structural/geotech/architectural outputs labelled PRELIMINARY / INDICATIVE /
CONCEPT with "engineer / geotechnical engineer / architect to design & seal".
Didn't fabricate site test data or claim "the world's best geotech report" — built
a credible desk-study template that scopes the real investigation.

## Still open / to confirm with owner
- "Progress tab daily logs" — a build diary + tasks already exist; confirm whether
  a distinct daily-program log view is wanted (not built this round).
- Design Production vs the other session's per-sheet render model — production
  uses the daily render cap for its AI exterior; align if the sheet model should
  meter it instead.
- integrum.co.ke is egress-blocked from the build env — market figures came from
  other reputable Kenyan sources via search; swap in integrum's if the owner wants.
