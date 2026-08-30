# Risk Registry — Africa Games

*(Covers both titles. Nairobi-Wild-specific risks are marked **NW**.)*

| # | Risk | Likelihood | Impact | Mitigation | Keywords |
|---|---|---|---|---|---|
| 1 | Ad eCPM/fill too low in target markets to sustain rewarded-only model | Medium | High | Mediation (AdMob + AppLovin/Unity); validate $/1k-DAU in GH/KE soft launch before scaling UA | ads, ecpm, fill |
| 2 | Play Store Families Policy issues (large minor audience + ads) | Medium | High | Age screen, families-compliant ad configs, rewarded-only placement | policy, families, compliance |
| 3 | Rules disputes — regional Oware variants differ (capture/grand-slam handling) | Medium | Medium | Ship tournament Abapa as default; add regional variant toggles later; rules screen cites the variant | rules, variants |
| 4 | Payment aggregator fees/coverage gaps eat IAP margin | Medium | Medium | Start with Play Billing; add Flutterwave/Paystack only where volume justifies; renegotiate at scale | payments, fees |
| 5 | Clone risk — the concept is unprotectable | High | Medium | Win on brand, polish, community/tournaments and speed; the moat is execution + network effects, not IP | competition, clones |
| 6 | Data-protection obligations once accounts/leaderboards land (NDPR, POPIA, Kenya DPA) | Low (now) | Medium | v0.1 stores nothing server-side; do a compliance pass before any account feature ships | privacy, ndpr, popia |
| 7 | Gambling-adjacent perception if tournaments have entry fees + prizes | Low | High | Coin entry earnable free; cosmetic/coin prizes only; no cash-out, ever | tournaments, gambling, legal |
| 8 | **NW** — Trademark exposure on naming ("Crush", "Saga" are aggressively enforced by King) | Medium | High | Working title "Nairobi Wild"; legal name-clearance search before any store listing; decision #12 bans those words | legal, trademark, naming |
| 9 | **NW** — Match-3 is the most crowded genre on the Play Store; discovery is brutal | High | High | Theme is the wedge, not the mechanic — the cultural angle is what earns organic press, creator coverage and store featuring in African markets; do not compete on generic match-3 keywords | competition, discovery, aso |
| 10 | **NW** — Level difficulty curve untuned; a bad spike kills D7 retention | High | High | 15 levels are hand-set and **unvalidated**. Instrument per-level fail rates in soft launch before adding paid UA (NextSteps #8); levels are data, so retuning is cheap | difficulty, retention, tuning |
| 11 | **NW** — Content burn: engaged players exhaust 15 levels in a sitting | High | Medium | Need ~100 levels for launch; Relax Mode absorbs overflow meanwhile; level table is data, not code | content, levels, retention |
| 12 | **NW** — Lives system draws "predatory" criticism, especially with minors | Low | Medium | Free path at every gate (rewarded ad or wait), heart refunded on win, Relax Mode always unlimited; documented in decisions #10/#11 | lives, ethics, perception |
| 13 | **NW** — Client-reported duel scores are trivially forgeable | High | Low (now) | Friendly duels only; no ranking, no prizes, no leaderboard until an authoritative server verifies by replaying moves (decision #19). The risk becomes High-impact the moment anything is staked on a score | anti-cheat, duel, ranked |
| 14 | **NW** — Online duels need both players to have the page *and* a connection; empty lobbies feel broken | Medium | Medium | Lobby states this plainly and always shows the two offline duel modes beside it; challenge links carry the social loop where data is thin | online, lobby, ux |
| 15 | **NW** — Wildlife framing invites "tourist gaze" criticism if it reads as a safari brochure rather than a Nairobi game | Low | Medium | Swahili names on every animal, real place names on every level, Nairobi skyline in the artwork, Benga rather than generic drums; validate with Kenyan playtesters (NextSteps #1) | culture, authenticity, brand |
| 16 | **NW** — Emoji tiles render differently across Android versions and could collide visually | Medium | Medium | Six distinct hues carry the colour identity independently of the glyph, so matching never depends on emoji fidelity; swap to inline SVG animals if playtests show confusion | accessibility, emoji, rendering |
| 17 | **NW** — Synthesised music may read as cheap next to licensed Afrobeats competitors | Medium | Low | Deliberate trade for install size and clean rights (decision #20); revisit with a commissioned Benga loop once revenue supports licensing and the size budget allows | music, quality, licensing |

