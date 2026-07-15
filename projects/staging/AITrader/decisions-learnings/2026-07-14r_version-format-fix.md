# Fix: MQL5 Market Version Format

**Date:** 2026-07-14
**Owner:** Founder (fatalibuilders@gmail.com)

---

## What Happened

Founder ran the file through MetaEditor and got a real validation error (not a code-logic bug): `version '0.30' is incompatible with MQL5 Market, must be xxx.yyy` at line 12. This is a **milestone** — it's the first evidence the file has actually been opened in real MetaEditor, and the error is specific to MQL5 Market's own submission rules, not a syntax/logic error in the EA itself.

## Fix

Changed `#property version "0.30"` to `#property version "1.00"`. MQL5 Market requires a strict `X.XX` two-decimal-digit format, and versions starting with `0.` aren't accepted as a valid release version — Market listings are expected to start at `1.00`.

## Note

The informal "v0.30" draft-stage language used throughout this project's documentation and code comments (referring to the EA's development stage: risk management → entry filters → real signal design) is separate from this `#property version` tag, which is a strict Market-compliance field. Left the informal draft numbering as-is in comments/docs since it accurately reflects development history; only the compiler-facing tag needed the format fix.

## Open Items

- Continue compiling — there may be further errors/warnings once this one clears. Send them back for fixes as they come up, same process as before.
