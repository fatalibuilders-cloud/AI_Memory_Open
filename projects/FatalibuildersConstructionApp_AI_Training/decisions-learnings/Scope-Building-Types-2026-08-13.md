# Scope decision — building types & structural systems (2026-08-13)

Owner asked whether the app supports: two soil types, boundary walls (stone/
precast), full timber structures, full steel structures, bridges, stadiums, and
road design. Decision on scope + what was built.

## Built now (in residential scope) ✅
- **Second soil type** (`soilType2`) — for a mixed site. Informational (feeds the
  future geotech report; flags "engineer to assess"). Does not yet change
  quantities (consistent with `soilType` today).
- **Boundary wall** — optional perimeter wall: natural stone / precast panels /
  concrete block, with length + height → a costed "Boundary wall (external
  works)" BOQ section (trench, strip footing, walling by type). Default off.

## Scope expanded by owner (2026-08-13): residential + commercial, 4 systems ✅ BUILT
Owner directed: "let the app focus in residential and commercial projects —
masonry, steel, concrete, timber." Built:
- **projectCategory**: residential (default) | commercial. Commercial applies a
  denser services multiplier (lighting/sockets ×1.6, toilets ×1.4).
- **structureType**: masonry (load-bearing, no RC columns) | concrete_frame (RC,
  the baseline; unset = this so existing estimates unchanged) | steel_frame
  (structural steel ~55 kg/m² + metal-deck floors) | timber_frame (timber frame +
  timber floors). Rates added: structuralSteelKg, metalDeckFloorM2, timberFrameM2,
  timberFloorM2. Wizard selects + 5-language labels + review.
- **Steel & timber remain INDICATIVE first-pass** (labelled in the UI/sections):
  the ~55 kg/m² steel metric and timber per-m² rates are planning figures that
  **must be validated by a licensed engineer** with real rate data before relied
  on — same accuracy bar as the residential rate card.

## Out of scope — separate engineering products 🔴 (deliberately NOT faked)
- **Bridges, stadiums, and roads** are different engineering disciplines (bridge
  design, crowd/dynamic loads, highway geometric + pavement design, earthworks,
  drainage) with their own codes and take-offs. They are **not** a residential
  house-app option. Bolting on fake calculators would produce dangerous, wrong
  numbers and destroy the app's core differentiator — accuracy/design-code rigour.
  **Decision: do not add to the residential app.** If the owner wants to pursue
  infrastructure, it is a **separate product** ("Fatalibuilders Infrastructure")
  built with proper engineering models, code validation, and QS/engineer input —
  scoped and resourced on its own, not shipped as a toggle here.

## Principle
The moat is *credible, design-code-accurate* estimates. Every added building type
must clear the same accuracy bar (owner-engineer sign-off) before it ships as
"real," exactly like the residential rate card and services/fittings assumptions.
