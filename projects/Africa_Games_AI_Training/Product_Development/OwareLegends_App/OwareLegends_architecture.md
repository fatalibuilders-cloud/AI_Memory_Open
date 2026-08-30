# Oware Legends — Architecture (v0.1)

## Design philosophy
1. **Data-light or die.** Total payload < 40 KB, zero external requests, zero assets (all visuals are CSS, all sound is WebAudio synthesis). This is a product feature for African data budgets, not an implementation detail.
2. **Engine/UI separation.** All rules live in `engine.js` as pure functions on immutable-ish state; the UI never mutates game state directly. The same file runs in the browser and under Node for tests.
3. **Monetization behind one seam.** Game code only ever calls `Monetization.showRewardedAd(cb)` and `Monetization.purchase(id, cb)`. Swapping the dev simulation for AdMob/Play Billing/Flutterwave touches exactly one object.

## Files
| File | Role |
|---|---|
| `engine.js` | Rules engine (Abapa variant): sowing, capture chains, grand-slam forfeit, feeding obligation, starvation/stall endings, minimax AI (alpha-beta, 3 difficulties) |
| `index.html` | Full UI: home / game / shop / how-to screens, sowing + capture animations, themes (CSS custom properties), coins, daily streak, localStorage persistence, WebAudio sfx, haptics |
| `engine.test.mjs` | 13 Node tests: rules edge cases + AI sanity ("hard" must beat random ≥8/10) |

## Engine state shape
```js
{ board: number[12],   // pits 0-5 South (human), 6-11 North; sowing 0→11→0
  captured: [s, n],    // seeds banked per player
  turn: 0|1, moves: n,
  ended: bool, endReason: 'win25'|'starved'|'stalled'|null }
```
`applyMove(state, pit)` returns `{ state, path, capturedPits, capturedCount, grandSlam }` — the metadata drives the UI animation without re-deriving rules.

## Rules implemented (tournament Abapa)
- Origin pit always skipped when sowing (matters at 12+ seeds).
- Capture: last seed → opponent pit at 2–3 → capture + backwards chain of 2s/3s.
- Grand slam forfeits captures (move stands).
- Feeding: must reach a starved opponent when possible; if impossible, mover banks own seeds and game ends.
- 25 seeds wins; 250-move stall guard splits remaining seeds by side.

## Persistence (localStorage `owareLegends.v1`)
`coins, wins/losses/draws, streak + lastDay, themes owned, active theme, sound, difficulty`. No accounts, no server, no PII — deliberate for launch compliance simplicity.

## Path to production
1. **Wrap:** Trusted Web Activity (Android) → Play Store; the raw HTML stays the web/offline build.
2. **SDKs:** implement the `Monetization` seam (AdMob rewarded; Play Billing; Flutterwave/Paystack for web).
3. **Online play (v0.3+):** the engine is deterministic & serializable — a move-relay server (or even WhatsApp-shared board states) needs no rules logic server-side, only sequencing + anti-tamper re-validation using this same engine in Node.
4. **Localization:** extract the ~50 UI strings to a dictionary; add language picker.

## Verification status (2026-07-16)
- `node engine.test.mjs` → 13/13 passing.
- Playwright smoke on bundled Chromium: home → vs-AI match (6 human moves, AI replies, captures fired) → shop; zero console errors; seed conservation on-screen = 48. Screenshots archived in session summary.
