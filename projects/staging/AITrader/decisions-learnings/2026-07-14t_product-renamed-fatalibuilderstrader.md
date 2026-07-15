# Decision: Product Renamed to FatalibuildersTrader

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## Decision

The EA/product is renamed from **AITrader** to **FatalibuildersTrader**. This is the name that appears in the code, the compiled file, log output, and all MQL5 Market-facing materials.

**Scope note:** the internal staging project folder (`projects/staging/AITrader/`) is left unchanged and continues to be used as the internal project codename/directory name in this AI Memory system. This is a common, low-risk distinction (internal project codename vs. public product name) — flagged explicitly here in case the founder actually wants the whole staging folder renamed too, which is a bigger, more disruptive change (would touch every file path and cross-reference in the project) not yet requested.

## What Was Renamed

- `Product_Development/MQL5_EA/AITrader.mq5` → `FatalibuildersTrader.mq5` (git-tracked rename)
- Inside the code: `#property copyright`, all `Print`/`PrintFormat` log-message prefixes, the trade-comment string passed to `trade.Buy()`/`trade.Sell()`, and header/inline comments
- `Product_Development/MQL5_EA/README.md`, `compile_guide.md`, `mql5_listing_description.md`, `mql5_submission_checklist.md` — all product-name and filename references updated

## What Was NOT Renamed

- The staging project folder itself (`projects/staging/AITrader/`)
- Historical `decisions-learnings/` files from prior sessions — these are point-in-time records of what was decided and discussed at the time (including the real screenshot/research context that used "AITrader"), and rewriting them would misrepresent the actual history. They are not updated to say "FatalibuildersTrader" retroactively.
- `Master-Context.md`, root `NextSteps.md`, `Key-Decisions.md`, `Sessions.md` prose that refers to the project/vision generally — the *product* name in these should be treated as FatalibuildersTrader going forward in spirit, but a full find-and-replace across every historical mention was judged lower value than keeping the decision logs and MQL5-facing deliverables (the actual thing being submitted/compiled) correctly renamed.

## Open Items / Follow-ups

- If the founder wants the entire staging folder renamed to `projects/staging/FatalibuildersTrader/` for full consistency, that's a separate, larger request — not done here.
- Re-send the founder the renamed `.mq5` file to replace the one already in their MetaEditor Experts folder (old filename should be deleted there to avoid confusion/duplicates).
