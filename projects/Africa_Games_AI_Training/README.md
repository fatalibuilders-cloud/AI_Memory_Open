# Africa Games — Project Memory

**Goal (from the owner):** *"A game which will be attractive and addictive all over the continent, with some monetary contributions to the app game."* Clarified: **like Candy Crush — addictive for both the old and the new generation.**

## The two games

| App | What it is | Status |
|---|---|---|
| **Nairobi Wild** ⭐ *flagship* | Match-3 puzzle in the Candy Crush mould, set in Nairobi with Kenyan wildlife, a synthesised Benga soundtrack, offline solo play and **live online duels**. | ✅ Playable v0.2, 43/43 tests |
| **Oware Legends** | The pan-African mancala strategy game (Ayo/Awalé/Warri/Adji) vs an AI or pass-and-play. | ✅ Playable v0.1, 13/13 tests |

**Why both:** Nairobi Wild is the mass-market growth engine — the genre with the largest proven audience and the clearest monetization. Oware Legends is the credibility and retention play: a deep, culturally-owned strategy game that keeps players who tire of match-3. Together they give a studio a funnel (Nairobi Wild acquires) and a moat (Oware retains).

## Why Nairobi Wild works across generations

This was the owner's core requirement, and it drives the design:

- **The mechanic is universal to the young.** Swap-and-match needs no instructions; anyone who has held a phone already knows it.
- **The animals are universal to everyone.** Lion, elephant, zebra, giraffe, rhino, leopard — named in Swahili in the UI — read instantly to any age, and the level journey runs through places Kenyans know by name, starting at Nairobi National Park.
- **Relax Mode removes the barrier.** No timer, no lives, no failure. Older or casual players can simply play; the level campaign with its lives and stars is there for those who want the chase.
- **Playing together needs no network.** Pass-and-play and challenge links work offline, so a duel never depends on both people having data.
- **It runs on the phones people actually have.** ~97 KB, fully offline, no image or audio assets at all.

## Ways to play

| Mode | Needs a network? |
|---|---|
| Safari — 15-level solo journey | No |
| Relax — unlimited, no lives | No |
| Duel: same phone, pass and play | No |
| Duel: challenge link (same board, share your score) | No — only to send the link |
| Duel: live online, opponent's score updating in real time | Yes |

## Playing it

Both games are single-page HTML — open `index.html` in any browser, no server needed.

- Nairobi Wild: `Product_Development/NairobiWild_App/index.html` · tests: `node match3.test.mjs` and `node extras.test.mjs`
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
