# Next Steps — Africa Games

**Last Updated:** 2026-08-30

## High Priority

1. **Playtest Nairobi Wild on real phones in Nairobi** — with both generations, and specifically test a **live duel between two phones on mobile data**, which is the one mode the automated tests can only simulate.
2. **Name clearance** — "Nairobi Wild" needs a trademark and Play Store search before any listing. Never use "Crush" or "Saga" (decision #12).
3. **Android wrap** — Trusted Web Activity, target APK < 5 MB.
4. **More levels** — 15 ship today; the genre needs ~100 for launch. Levels are pure data in `match3.js`, so this is content work. Extend the journey past the Rift Valley (Turkana, Kilifi, Kakamega, Marsabit).

## Medium Priority

5. **Wire the real SDKs behind the `Monetization` seam** — AdMob rewarded → Play Billing → Flutterwave/Paystack for **M-Pesa** first (this is Kenya; M-Pesa is the default way to pay, not an alternative one).
6. **`RealtimeAdapter` for the standalone app** — the Android build has no artifact `room`, so online duels need a WebSocket service implementing the same interface as `RoomAdapter` (see `NairobiWild_architecture.md`). Offline duels need nothing.
7. **Blockers and new goal types** — snares to cut, waterholes to fill, an animal to escort down the board. This is what keeps a match-3 alive past level 30.
8. **Localize** — Swahili first (the UI already uses Swahili animal names and interjections), then English, French, Amharic.
9. **Soft-launch instrumentation** — per-level fail rates and D1/D7 retention before any paid UA. The difficulty curve is currently hand-set and unvalidated.

## Low Priority

10. **Ranked duels / leaderboards** — blocked on an authoritative server, because scores are client-reported today (decision #19). The deterministic engine makes verification straightforward: replay the move list server-side.
11. Music variety — a second groove (Gengetone-flavoured) and a calmer Relax-mode arrangement.
12. Online play for Oware Legends.
13. KaiOS/feature-phone build.

## Recently Completed

| Item | Date | Notes |
|---|---|---|
| Nairobi Wild v0.2 — Kenyan wildlife theme, Benga soundtrack, 5 play modes incl. live online duels | 2026-08-30 | 43/43 tests; two-browser live duel verified |
| Market Day v0.1 — playable match-3 (renamed and re-themed to Nairobi Wild) | 2026-08-30 | 22/22 engine tests |
| Project restructured as a two-game studio | 2026-08-30 | `Africa_Games_AI_Training` |
| Oware Legends v0.1 — playable mancala vs AI | 2026-07-16 | 13/13 engine tests |
