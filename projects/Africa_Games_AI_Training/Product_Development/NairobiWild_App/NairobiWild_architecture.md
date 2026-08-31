# Nairobi Wild — Architecture (v0.3)

## What it is
A match-3 puzzle game made in and set in **Nairobi**. Swap adjacent animals, match three or more, chase a target inside a move limit. The mechanics are the genre standard (Candy Crush shape); the identity is Kenyan — the animals, the places, the music, the ornament.

## Design philosophy
1. **Familiar mechanic, local world.** The match-3 loop needs no teaching. What makes it *ours* is the content: the Big Five and friends as tiles that call out when you match them, a journey across 51 African cities from Nairobi to Cape Town, Swahili in the copy, Maasai beadwork as the app's one ornament, and Benga in the speakers.
2. **Data-light or die.** ~123 KB total, no external requests, **no image or audio assets at all** — every tile is emoji on a CSS gradient, the skyline is inline SVG, and all music and sound is synthesised at runtime. That is what keeps the install trivial on a Kenyan prepaid data bundle.
3. **Offline is the default, online is the bonus.** Solo, Relax, pass-and-play and challenge links all work with no network whatsoever. Live online duelling lights up when it can, and its absence never degrades the rest.
4. **Engine/UI separation.** All rules are pure functions on plain state; the UI plays back engine-produced phases and never re-derives rules.
5. **One seam per external concern.** `monetization.js` for money, `multiplayer.js` for opponents, `sounds.js`/`music.js` for audio. None of it is scattered through game code.

## Files
| File | Role |
|---|---|
| `match3.js` | Engine: board generation, match detection, specials, cascades, gravity/refill, deadlock reshuffle, boosters, the city table and generated campaign, duel config |
| `music.js` | Generative Benga soundtrack + pure, testable pattern builders |
| `sounds.js` | Animal voices — one synthesised call per species |
| `multiplayer.js` | Challenge-link codec, the `room`-backed online adapter, and the production realtime seam |
| `monetization.js` | Product catalogue, provider selection, AdMob / Play Billing / mobile-money checkout, revenue events |
| `index.html` | All screens, animation, input, economy, persistence, lobby, duel flow |
| `match3.test.mjs` | 28 tests — engine rules and the campaign |
| `extras.test.mjs` | 39 tests — music, animal voices, multiplayer, monetization |

## The animals
Colour index → animal, with the Swahili name the UI shows:

| # | Animal | Swahili | Tile hue |
|---|---|---|---|
| 0 | Lion | Simba | amber |
| 1 | Elephant | Tembo | blue |
| 2 | Zebra | Punda Milia | cream |
| 3 | Giraffe | Twiga | orange |
| 4 | Rhino | Kifaru | violet |
| 5 | Leopard | Chui | green |

Six distinct hues **and** six distinct silhouettes, so the board stays readable for colour-blind players — colour alone is never the only signal.

### Animal voices
Matching a herd sounds **that animal**, not a beep. `sounds.js` splits into a pure data spec per species and a renderer that turns it into WebAudio nodes, so the calls are unit-testable.

Two things make a synthesised call sound like an animal rather than a buzz, and both are in every voice:

1. **A harmonic stack.** Real calls are rich, so each voice sums several partials (multiples of the fundamental) rather than using one oscillator.
2. **Formants.** An animal's throat resonates at fixed frequencies regardless of pitch. A parallel bank of narrow band-passes reproduces that, and it is what gives a roar its body.

| Animal | Call | How it is built |
|---|---|---|
| Simba | roar | 4 partials sweeping 200→75 Hz, formants at 420/900/1850 Hz, and a 28 Hz amplitude growl |
| Tembo | trumpet | brass-like stack climbing 380→800 Hz, formants at 1150/2100 Hz |
| Punda Milia | double bark | two short sharp pulses — a zebra barks, it does not whinny |
| Twiga | hum | the real 92 Hz night hum, voiced with 7 partials so a phone can carry it |
| Kifaru | snort | a double puff, 85% breath |
| Chui | sawing call | five rasping strokes with a 45 Hz rasp |

**Phone speakers set the design.** A phone reproduces almost nothing below ~300 Hz, so a "correct" 55 Hz lion roar is *silent* on the device most players use. Every voice therefore carries its character in partials and formants inside roughly 300–3000 Hz while keeping the fundamental honest. Measured by rendering each call offline and high-passing at 300 Hz, the share of energy a phone can actually reproduce is:

| | Simba | Tembo | Punda Milia | Twiga | Kifaru | Chui |
|---|---|---|---|---|---|---|
| before | 55% | 79% | 82% | 28% | 37% | 59% |
| **after** | **76%** | **94%** | **92%** | **59%** | **78%** | **81%** |

Calls are short (≤1.1 s), rate-limited to one per 70 ms, and rise in pitch as a cascade builds. **The music ducks to 30% under each call** — without that the Benga groove sits on top of the calls and buries them. A tappable legend in *How to play* lets any player hear all six on demand.

### The campaign — one journey across Africa
The 51 stages are **generated from a city table** (`CITIES`), so adding a city is one line and the difficulty curve stays consistent by construction. The route runs Nairobi → East Africa → the Horn → North Africa → West Africa → Central Africa → Southern Africa, ending in Cape Town, covering 40+ countries. Each stage carries its city, country and flag, and asks for the animal assigned to that place.

## Music: why it is synthesised
There is not one audio file in the build — not for the music, and not for the animals. A licensed music bed would add megabytes to a game whose entire pitch is a tiny install, and would need clearing in every launch market. Instead `music.js` sequences a **Benga**-flavoured groove — the fast, guitar-led Nairobi dance style — from oscillators and filtered noise:

- **kick** four-on-the-floor with a syncopated push
- **shaker** kayamba-style 16ths, off-beat accents
- **clap** backbeat on 2 and 4
- **bass** pentatonic root movement, short and round
- **riff** the Benga guitar/nyatiti line — plucked 8ths that shift a scale degree each bar, so four bars read as a phrase rather than a loop
- **marimba** sparse answering phrases, layered in only at high energy

Everything sits in F minor pentatonic, so layers never clash. Scheduling uses the standard WebAudio lookahead pattern (a 25 ms timer queues notes 120 ms ahead against the audio clock), so timing does not drift with the main thread. Cascades of 3+ call `flourish()`, which lifts the arrangement for three seconds.

Music and SFX are separate toggles. Audio starts only on a user gesture, because browsers block it otherwise.

## Multiplayer

### Offline (works anywhere, no server)
- **Pass and play** — two players, one phone, the same board in turn.
- **Challenge links** — you play a board, then share a link carrying the seed and your score (`#d=<seed>.<score>.<base64 nick>`). Your friend plays **the identical board** and the app compares. Zero infrastructure, and the share is the growth loop.

Both rely on the engine being deterministic: `newGame(level, seed)` reproduces a board exactly, which is asserted by a test.

### Online, live
The published page declares the **`room`** capability, which gives every open copy of the page a shared presence channel. No server of ours is involved.

The whole lobby-and-duel handshake runs on **presence only** — never events — because presence is settable by any viewer while event topics are admin-only by default:

1. Host sets `{st:'host', seed}`.
2. Guest sees the host and sets `{st:'join', seed:<host seed>, vs:<host peer>}`.
3. Host sees a guest pointing at it, locks on to the **first** one, sets `{st:'duel', vs:<guest peer>}`.
4. Guest sees the host point back → both start on the same seed.
5. Through the round each player publishes `{score, moves, done}`; each renders the other's live.

Handled: a guest who is not chosen falls back to the lobby; a 12-second join timeout; an opponent who leaves mid-duel forfeits; stale peers and non-viewer (agent) peers are filtered out.

**Untrusted input.** Everything in a peer's presence is written by another person's page. Peer values are coerced and clamped on read (`Number(...) || 0`, nickname sliced to 16 chars) and peer-supplied text goes to the DOM via `textContent`, never `innerHTML`.

**Fairness caveat.** Scores are client-reported. That is fine for playing with friends, and is **not** cheat-proof. A ranked or leaderboard mode needs an authoritative server — which the deterministic engine makes straightforward: the server replays a submitted move list and recomputes the score.

### Production path
For the standalone Android build there is no `room`, so implement `RealtimeAdapter` in `multiplayer.js` against a WebSocket service with the same method surface as `RoomAdapter` (`set`, `peers`, `openHosts`, `opponent`, `onChange`). Nothing in the UI changes. Offline modes need no server ever.

## Money (`monetization.js`)
The entire money layer is one module with four entry points — `rewardedAd`, `purchase`, `products`, `onEvent`. Game code never touches an SDK, a price or a network.

**Provider selection is automatic and capability-checked** (a pure, tested function): Play Billing via the Digital Goods API when running as a TWA, a mobile-money checkout when a public key is configured, an AdMob bridge when one is present, and otherwise **simulated** — where every flow completes without charging anyone, so play-testing is never blocked by missing accounts.

- **Ads:** four named rewarded placements (`continue`, `double`, `lives`, `shop`). The placement name is reported on every revenue event, because "which moment earned this" is the number worth having.
- **IAP:** a single catalogue drives the shop, including local-currency display (KES by default) and a tip jar.
- **Shipped config is inert on purpose:** empty IDs, `testMode: true`, no key in the repo. A test asserts `isLive().any === false` so no one can accidentally commit live credentials.

`Finance/revenue-activation.md` is the checklist for switching it on: which accounts to open, in what order, the fees, and where the money lands.

## Economy & persistence (`localStorage` key `nairobiWild.v1`)
`coins, lives, lifeAt, stars{}, unlocked, sound, music, streak, lastDay, hammers, shuffles, nick`.

- **Lives:** 5 max, one per campaign attempt, refunded on a win, one regenerating per 10 minutes on a wall clock. Refill via rewarded ad or 100 coins. **Duels never cost a life** — multiplayer should be encouraged, not taxed.
- **Coins:** from stars (25/45/70), duel results (60/30/10) and a daily streak bonus.
- No accounts, no server, no PII. The only identity is a nickname the player types, kept on their own device.

## Verification status (2026-08-30)
- `node match3.test.mjs` → **28/28**; `node extras.test.mjs` → **39/39**.
- Browser: shop renders 8 catalogue items with KES pricing and the honest "Demo mode" notice; a simulated purchase grants coins; and on a match the page creates both oscillator **and noise-buffer** nodes — the signature of a synthesised animal call rather than a beep.
- Playwright, 412×880, both the source tree and the bundled single file:
  - **Offline solo:** level map (15 Kenyan locations) → 3 real matches → board stayed 64/64 filled.
  - **No-room degradation:** lobby correctly reports online unavailable, disables hosting, and still offers both offline duels.
  - **Pass and play:** VS panel shown, 20 moves, opponent labelled Player 2.
  - **Live online duel, two browser pages:** A hosts → B sees "Wanjiru" in the lobby → B joins → **both land in the duel on an identical board with correct opponent names** → A plays and **B's screen shows A's score rise 0 → 720 live**.
  - Zero console errors throughout.
