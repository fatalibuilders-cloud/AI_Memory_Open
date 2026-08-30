# Market Day — Architecture (v0.1)

## What it is
A match-3 puzzle game in the Candy Crush mould — swap adjacent goods, match 3+, chase a score target inside a move limit — themed as an African market stall. The mechanics are the genre standard because that is what makes the genre work; the *theme* is the differentiator.

## Design philosophy
1. **Familiar mechanic, familiar goods.** The match-3 loop is understood by anyone who has touched a phone. The goods on the board — cowries, maize, mangoes, greens, fish, kola — are recognised by every generation. That pairing is the whole product thesis: the grandchild already knows the game, the grandmother already knows the goods.
2. **Data-light or die.** ~58 KB total, no external requests, no image or audio assets (tiles are emoji on CSS gradients; sound is synthesised WebAudio). Works offline on low-end Android.
3. **Engine/UI separation.** All rules are pure functions in `match3.js` operating on plain state; the UI never derives rules. The same file runs in the browser and under Node for tests.
4. **Monetization behind one seam.** Game code only ever calls `Monetization.showRewardedAd(cb)` and `Monetization.purchase(id, cb)`.
5. **Nobody is ever locked out.** Relax Mode is unlimited, life-free and free forever — the lives system applies to the level campaign only.

## Files
| File | Role |
|---|---|
| `match3.js` | Engine: board generation, match detection, special pieces, cascades, gravity/refill, deadlock reshuffle, boosters, 15 levels |
| `index.html` | Full game: home, level map, board with animation playback, boosters, shop, overlays, persistence, sound, haptics |
| `match3.test.mjs` | 22 Node tests covering rules, specials, scoring, goals, boosters and level integrity |

## Engine model
```js
// Board: flat array, row-major, 8x8.
// Cell = null (hole, mid-cascade) | { c: colourIndex 0-5, s: special|null }
// special: 'row' | 'col' | 'bomb' | 'rainbow'
```

`resolveMove(state, a, b)` returns `{ valid, phases, state }`. A **phase** is one snapshot of the cascade — `{ cleared, created, gained, combo, board, shuffled }` — and the UI simply plays the phases back as animation. The UI never re-runs rules logic, which is why the animation can never disagree with the score.

### Rules implemented
- Match 3+ in a line clears and scores (`60 × tiles × cascade depth`).
- Match **4** → striped tile that clears its row or column.
- Match **5+** → rainbow; swap it onto any good to clear every tile of that colour. Rainbow + rainbow clears the board.
- **L/T shape** → bomb that clears its 3×3 neighbourhood.
- Specials chain: clearing a striped tile detonates any special it takes with it.
- New boards never start with a match and always contain a legal move.
- After every move the board is re-checked; a deadlocked board reshuffles rather than stranding the player.

### Boosters
`useBooster(state, kind, target)` — `hammer` (remove one tile) and `shuffle`. Neither costs a move; both settle any matches they create.

### Progression
15 levels, each with a score target, a move limit, and optionally "collect N of a good" goals. Difficulty ramps by raising targets while tightening moves (asserted by a test). Stars at 1.0× / 1.4× / 1.9× of target.

## Economy & persistence (`localStorage` key `marketDay.v1`)
`coins, lives, lifeAt, stars{}, unlocked, sound, streak, lastDay, hammers, shuffles`.

- **Lives:** 5 max, one consumed per campaign attempt, refunded on a win, one regenerating per 10 minutes on a wall-clock timer (so closing the app never wastes them). Refill via rewarded ad or 100 coins.
- **Coins:** earned from stars (25/45/70) and a daily streak bonus; spent on boosters and life refills.
- No accounts, no server, no PII.

## Path to production
1. **Wrap** as a Trusted Web Activity → Play Store (target APK < 5 MB).
2. **Wire the `Monetization` seam:** AdMob rewarded video → Play Billing → Flutterwave/Paystack for mobile money (M-Pesa, MTN MoMo, Airtel) and carrier airtime billing.
3. **Content:** the level table is data, not code — levels are cheap to add. Next content beat is blockers (jute sacks, crates) and ingredient-drop goals.
4. **Localize:** ~70 UI strings to extract into a dictionary.

## Verification status (2026-08-30)
- `node match3.test.mjs` → **22/22 passing**.
- Playwright smoke on bundled Chromium (412×880 viewport): home → level map (15 levels, 1 unlocked) → level intro → 3 real matches scored via tap-tap input (score 0 → 1,440, moves 25 → 22) → board stayed 64/64 filled → shop (5 items) → Relax Mode shows ∞ moves. Zero console errors.
