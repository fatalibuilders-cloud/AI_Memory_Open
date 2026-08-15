# Fatalibuilders Civil / Infrastructure — product plan

**For:** Eng Ali Ahmed · **Date:** 2026-08-13 · **Status:** plan only (no code)

**Why separate:** bridges, stadiums, and roads are different engineering
disciplines from buildings — different codes, loads, geometry, and take-offs.
They must NOT be faked inside the residential/commercial house app (that would
wreck its accuracy moat). This is a **distinct product**, built with proper
engineering and its own validation, sharing only the platform (accounts,
payments, exports, i18n, PWA) where it makes sense.

---

## 1. Scope (three modules, phased)

### A. Roads (start here — most demand, most standardisable)
- **Inputs:** road class, length, carriageway width, number of lanes, shoulders,
  terrain, design traffic (ESALs/CBR), pavement type (flexible/rigid).
- **Outputs:** earthworks (cut/fill), sub-base/base/wearing-course quantities +
  cost, drainage (culverts, side drains), signage/markings, a costed BOQ.
- **Codes:** Kenya Road Design Manual (KeNHA/KURA), TRL/Overseas Road Note 31,
  AASHTO as an alternate profile — mirrors the building app's design-code profiles.
- **Types:** earth/gravel, bitumen (surface dressing / AC), concrete, urban vs rural.

### B. Bridges (higher engineering bar)
- **Inputs:** span(s), width, bridge type (slab, beam-and-slab, box girder, truss),
  loading class, foundation type.
- **Outputs:** deck/superstructure + substructure (piers/abutments) + foundation
  quantities, indicative cost. Structural design is preliminary → **registered
  engineer sign-off mandatory** before any use.
- **Codes:** Eurocode (EN 1991-2 traffic loads, EN 1992/1993/1994), AASHTO LRFD.

### C. Stadiums / large-span structures
- **Inputs:** capacity, plan geometry, roof type (long-span steel/cable/membrane),
  tiers.
- **Outputs:** structural frame (steel tonnage), terracing/precast, roof, MEP for
  crowds, a costed BOQ. Crowd/dynamic loads → **engineer-led**.
- **Codes:** Eurocode + sports-ground safety guidance (e.g. Green Guide).

## 2. Shared platform (reuse)
Accounts, payments (M-Pesa/Pesapal/Paddle), the cost-section/BOQ engine pattern,
Excel/PDF/lender exports, the "indicative — engineer to verify" discipline,
multi-language, offline. The engine architecture (Measures → rate card → BOQ
sections) transfers directly; only the take-off logic and rate cards are new.

## 3. Pricing & positioning
Higher-value than the $30 house tier — infrastructure buyers are contractors,
counties, consultants. Likely per-project or subscription. Verified/QS sign-off
tiers apply strongly here.

## 4. Hard prerequisites (owner-gated)
- **Engineering input + validated rate cards** per module (like the residential
  card) — non-negotiable; accuracy is the whole product.
- Design-code licences/standards references.
- Likely a **registered engineer partner** for sign-off (liability).

## 5. Recommended sequence
1. **Roads MVP first** (most standardisable, clear demand) — pavement + earthworks
   + drainage BOQ on the Kenya Road Design Manual profile.
2. Bridges (engineer-led).
3. Stadiums/large-span.

Each module ships only when its rate card + method is validated by a licensed
engineer — same bar as the residential app.

## 6. Decision needed from owner
- Pursue this as a separate product now, or after the building app is
  revenue-generating? (Recommendation: **after** — get the house app to paying
  users first; infrastructure is a bigger, engineer-heavy build.)
