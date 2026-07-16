# Next Steps — Oware Legends

**Last Updated:** 2026-07-16

## High Priority
1. **Playtest the prototype on real phones** (open `Product_Development/OwareLegends_App/index.html`, or serve it and share the link). Log feel/bugs in `Product_Development/Releases/Bugs.md` (create on first bug).
2. **Decide launch identity** — confirm name "Oware Legends" and soft-launch markets (proposed: Ghana + Kenya, see `Marketing/go-to-market.md`).
3. **Android wrap** — package as Trusted Web Activity, target APK < 5 MB.

## Medium Priority
4. Integrate real SDKs behind the `Monetization` seam: AdMob rewarded → Play Billing → Flutterwave/Paystack (order per `Finance/monetization-model.md`).
5. Localize UI strings (EN/FR/SW first) — extract ~50 strings to a dictionary.
6. Challenge links via WhatsApp (serialize board state into a URL) — the #1 planned growth loop.
7. National-pride theme pack pipeline (cosmetics roadmap).

## Low Priority
8. Online multiplayer (move-relay server re-validating moves with the same engine).
9. KaiOS/feature-phone build.
10. Leaderboards + weekly tournaments (requires accounts → revisit data-protection notes in Risk-Registry).

## Recently Completed
| Item | Date | Notes |
|---|---|---|
| Playable v0.1 prototype (engine + UI + AI + themes + coins + streaks) | 2026-07-16 | 13/13 engine tests; Playwright smoke passed |
| Monetization model & go-to-market docs | 2026-07-16 | `Finance/`, `Marketing/` |
