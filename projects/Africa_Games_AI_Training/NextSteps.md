# Next Steps — Africa Games

**Last Updated:** 2026-08-30

## High Priority

1. **Playtest Market Day on real phones** — especially with players from both target generations (a teenager and a parent/grandparent). The whole thesis is that both find it readable. Log findings in `Product_Development/Releases/Bugs.md` (create on first bug).
2. **Confirm the flagship and the name** — "Market Day" is the working title. Avoid "Crush"/"Saga" in any final name (King defends those marks aggressively).
3. **Android wrap** — package Market Day as a Trusted Web Activity, target APK < 5 MB, and get it into internal testing on Play.
4. **More levels** — 15 ship today; the genre needs ~100 for a real launch. Levels are pure data in `match3.js`, so this is content work, not engineering.

## Medium Priority

5. **Wire the real SDKs behind the `Monetization` seam** — AdMob rewarded → Play Billing → Flutterwave/Paystack for mobile money. Order and rationale in `Finance/monetization-model.md`.
6. **Blockers and new goal types** — jute sacks, crates, ingredient-drop levels. This is what keeps a match-3 fresh past level 30.
7. **Localize** — ~70 strings in Market Day, ~50 in Oware. English, French, Swahili first.
8. **Soft-launch instrumentation** — funnel and level-failure analytics before any paid UA. Without per-level fail rates the level curve cannot be tuned.

## Low Priority

9. Leaderboards, weekly tournaments (needs accounts → triggers the data-protection work in `Risk-Registry.md`).
10. WhatsApp challenge links (share a board state) — the planned viral loop.
11. Online multiplayer for Oware Legends.
12. KaiOS/feature-phone build.

## Recently Completed

| Item | Date | Notes |
|---|---|---|
| Market Day v0.1 — playable match-3 with 15 levels, specials, boosters, economy, Relax Mode | 2026-08-30 | 22/22 engine tests; Playwright smoke passed |
| Project restructured as a two-game studio | 2026-08-30 | `Oware_Legends_AI_Training` → `Africa_Games_AI_Training` |
| Oware Legends v0.1 — playable mancala vs AI | 2026-07-16 | 13/13 engine tests |
| Monetization model & go-to-market docs | 2026-07-16 | Updated 2026-08-30 for match-3 economics |
