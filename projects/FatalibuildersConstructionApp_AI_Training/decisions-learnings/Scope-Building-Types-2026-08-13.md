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

## Real new modules — buildable, but NOT a checkbox 🟡
- **Timber-frame structure** and **steel-frame structure** are distinct structural
  SYSTEMS. The current materials/cost engine is masonry + reinforced concrete.
  Supporting them properly needs new quantity take-offs (timber: studs/plates/
  joists/sheathing/fasteners; steel: sections/connections/base plates/cladding),
  new rate data, and **licensed-engineer validation**. A first-pass estimator is
  feasible as a follow-up module; it must not be presented as accurate without
  validation. **Deferred pending owner go-ahead + rate data.**

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
