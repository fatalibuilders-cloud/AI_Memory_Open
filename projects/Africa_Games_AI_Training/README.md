# Africa Games — Project Memory

**Goal (from the owner):** *"A game which will be attractive and addictive all over the continent, with some monetary contributions to the app game."* Clarified: **like Candy Crush — addictive for both the old and the new generation.**

## The two games

| App | What it is | Status |
|---|---|---|
| **Market Day** ⭐ *flagship* | Match-3 puzzle in the Candy Crush mould, themed as an African market stall. 15 levels, specials, boosters, lives, coins, and a free unlimited Relax Mode. | ✅ Playable v0.1, 22/22 tests |
| **Oware Legends** | The pan-African mancala strategy game (Ayo/Awalé/Warri/Adji) vs an AI or pass-and-play. | ✅ Playable v0.1, 13/13 tests |

**Why both:** Market Day is the mass-market growth engine — the genre with the largest proven audience and the clearest monetization. Oware Legends is the credibility and retention play: a deep, culturally-owned strategy game that keeps players who tire of match-3. Together they give a studio a funnel (Market Day acquires) and a moat (Oware retains).

## Why Market Day works across generations

This was the owner's core requirement, and it drives the design:

- **The mechanic is universal to the young.** Swap-and-match needs no instructions; anyone who has held a phone already knows it.
- **The goods are universal to the old.** The tiles are cowries, maize, mangoes, greens, fish and kola — a market stall anyone's grandmother can read at a glance. Nothing on the board is an abstract jewel or an imported candy.
- **Relax Mode removes the barrier.** No timer, no lives, no failure. Older or casual players can simply play; the level campaign with its lives and stars is there for those who want the chase.
- **It runs on the phones people actually have.** ~58 KB, fully offline, no assets to download.

## Playing it

Both games are single-page HTML — open `index.html` in any browser, no server needed.

- Market Day: `Product_Development/MarketDay_App/index.html` · tests: `node match3.test.mjs`
- Oware Legends: `Product_Development/OwareLegends_App/index.html` · tests: `node engine.test.mjs`

## Key files

| File | Purpose |
|---|---|
| `NextSteps.md` | Prioritized roadmap |
| `Key-Decisions.md` | Decision log with rationale |
| `Sessions.md` | Session index |
| `Risk-Registry.md` | Regulatory, platform and market risks |
| `Finance/monetization-model.md` | Revenue model, payments, unit economics |
| `Marketing/go-to-market.md` | Markets, localization, growth loops, launch beats |
| `Product_Development/{App}/…_architecture.md` | Per-app architecture |
