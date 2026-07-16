# Key Decisions — Oware Legends

| # | Date | Decision | Rationale | Keywords |
|---|---|---|---|---|
| 1 | 2026-07-16 | Game = **Oware (mancala)**, not an original casual concept | Pre-existing continent-wide familiarity (Ayo/Awalé/Warri/Adji) removes the hardest problem (teaching a new game); chess-class depth drives long-term retention | game-choice, oware, mancala, retention |
| 2 | 2026-07-16 | **Abapa (tournament) rules**: grand-slam forfeit, feeding obligation, 25-to-win | The variant used in competitive play; unambiguous, well-documented, fair | rules, abapa, grand-slam, feeding |
| 3 | 2026-07-16 | **HTML5-first, < 40 KB, zero assets, offline** | African data costs and low-end Android are the market; tiny size is both engineering and marketing | html5, data-light, offline, low-end |
| 4 | 2026-07-16 | **Ethical monetization only**: rewarded ads (opt-in), cosmetic IAP, tournament passes; NO pay-to-win, loot boxes, energy gates, forced ads | Long-term brand trust; gambling-adjacent mechanics are also a legal risk in several jurisdictions | monetization, rewarded-ads, iap, ethics |
| 5 | 2026-07-16 | **Mobile money is first-class**: Flutterwave/Paystack (M-Pesa, MoMo, Airtel, airtime) alongside Play Billing | Card penetration is low; mobile money is how the continent pays | payments, mobile-money, mpesa, flutterwave |
| 6 | 2026-07-16 | Monetization isolated behind one `Monetization` object seam | SDK integration/testing/AB-swaps never touch game code | architecture, seam, sdk |
| 7 | 2026-07-16 | Engine as pure functions, shared browser/Node, tested | Same engine will re-validate moves server-side for future online play; rules bugs are caught in CI not production | engine, testing, determinism |
