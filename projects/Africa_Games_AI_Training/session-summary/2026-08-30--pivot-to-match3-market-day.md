# Session Summary — 2026-08-30 — Pivot to Match-3, Market Day v0.1

## Owner input this session
1. *"How can I open index.html on my phone?"*
2. *"The game I was thinking is like Candy Crush — addictive to both old and new generation."*

The second is a **redirect of the product direction**, not a tweak: the owner wants the mass-market casual genre, not a board game.

## What was done

### 1. Answered the phone question by publishing both games as links
Local `index.html` files can't be opened on a phone directly, so both games were published as private hosted pages the owner can tap on any device:
- Market Day — https://claude.ai/code/artifact/162005e5-2920-45c8-afcc-3197044ddc15
- Oware Legends — https://claude.ai/code/artifact/4d5e21bb-eab1-4396-9daf-e66367af4472

### 2. Built **Market Day** — the match-3 flagship
`Product_Development/MarketDay_App/` — full Candy-Crush-style game:
- **Engine** (`match3.js`): match detection, cascades with score multipliers, gravity/refill, special pieces (match-4 → striped, match-5 → rainbow, L/T → bomb), special chaining, deadlock reshuffle, hammer/shuffle boosters, 15 levels as data.
- **Game** (`index.html`): home, level map with stars and locks, animated board (pop → fall → cascade with combo banners), goal chips, boosters, lives, coins, daily streak, shop, sound, haptics, tap-tap **and** swipe input, hint system after 6s idle.
- **Relax Mode**: unlimited moves, no lives, no failure — free forever.

### 3. Solved the actual brief: "addictive for old AND new generation"
The bridge is the **theme, not the mechanic** (decision #9). The match-3 loop is what every young player already knows; the tiles — cowries, maize, mangoes, greens, fish, kola — are a market stall every older player already knows. Relax Mode removes the timer/lives barrier for casual and older players entirely.

### 4. Restructured the project as a two-game studio
`projects/Oware_Legends_AI_Training/` → `projects/Africa_Games_AI_Training/`, with Market Day as flagship and Oware Legends as the second title (acquisition engine + retention moat).

### 5. Updated the business docs for match-3 economics
`Finance/monetization-model.md`: four rewarded-ad placements (the "+5 moves" continue is the genre's highest-intent moment), coin/booster IAP, and the lives economy. Revenue per 1,000 DAU revised to **$20–45 for Market Day vs $8–20 for Oware** — the quantitative reason the match-3 is the flagship.

**Honest reversal recorded:** the original model said "no energy systems that lock people out." Market Day's campaign *does* use lives, because match-3 pacing and economics depend on them. The commitment was narrowed rather than quietly dropped (decisions #10, #11): every gate has a free path (rewarded ad or wait), winners keep their heart, and Relax Mode is always unlimited.

## Verification
- `node match3.test.mjs` → **22/22 passing** (rules, specials, chaining, scoring, goals, boosters, level integrity, and a 8-seed × 40-move soak asserting the board is never left deadlocked or unfilled).
- `node engine.test.mjs` (Oware) → 13/13 still passing.
- Playwright smoke on bundled Chromium at 412×880: home → level map (15 levels, 1 unlocked) → level intro → **3 real matches played through the UI** (score 0 → 1,440, moves 25 → 22) → board stayed 64/64 filled → shop (5 items) → Relax Mode shows ∞. **Zero console errors.**
- Two UI bugs found and fixed during verification: dead vertical space on the game screen, and Relax Mode displaying a meaningless "/ 999,999,999" target.

## Open items → `NextSteps.md`
Top four: playtest with both generations, confirm the name (avoid "Crush"/"Saga" — trademark), Android TWA wrap, and expand 15 levels toward ~100.
