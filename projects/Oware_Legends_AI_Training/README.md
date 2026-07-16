# Oware Legends — Project Memory

**One-liner:** A beautiful, data-light mobile game of **Oware** — the mancala strategy game already played across the whole of Africa (Ayo in Nigeria, Awalé in Côte d'Ivoire/Senegal, Warri in Ghana/Caribbean, Adji in Togo/Benin, Bao's cousin in East Africa) — with fair, optional monetization built for African payment realities.

## Why this game wins across the continent

1. **Zero learning curve, continent-wide.** Hundreds of millions of people already know the rules from childhood. We are not teaching a new game — we are digitizing the most widely shared game on the continent.
2. **Deep enough to retain.** Oware is a solved-nothing, chess-class strategy game. Mastery curves drive long-term retention far better than disposable hyper-casual loops.
3. **Built for real African devices and data plans.** The entire game is < 40 KB, fully offline, runs on any Android WebView/low-end phone, and never requires an account to play.
4. **Ethical engagement, not exploitation.** Daily streaks, win rewards, and unlockable themes create habit; there are no loot boxes, no pay-to-win, no forced ads, and no gameplay behind a paywall.

## What exists today (v0.1 prototype)

| Piece | Location | Status |
|---|---|---|
| Rules engine (Abapa rules, 13 passing tests) | `Product_Development/OwareLegends_App/engine.js` + `engine.test.mjs` | ✅ Done |
| Playable game (vs AI ×3 difficulties, pass-and-play, themes, coins, streaks, sound, haptics) | `Product_Development/OwareLegends_App/index.html` | ✅ Done |
| Monetization hooks (rewarded ads, IAP/coins) | `Monetization` object in `index.html` | ✅ Stubbed, ready for SDKs |
| Monetization strategy | `Finance/monetization-model.md` | ✅ Done |
| Go-to-market plan | `Marketing/go-to-market.md` | ✅ Done |
| Architecture notes | `Product_Development/OwareLegends_App/OwareLegends_architecture.md` | ✅ Done |

**Play it now:** open `Product_Development/OwareLegends_App/index.html` in any browser (works from the file system, no server needed).

**Run the tests:** `node Product_Development/OwareLegends_App/engine.test.mjs`

## Key project files

- `NextSteps.md` — prioritized roadmap
- `Key-Decisions.md` — decision log
- `Sessions.md` — session index
- `Risk-Registry.md` — top risks (regulatory, platform, market)
