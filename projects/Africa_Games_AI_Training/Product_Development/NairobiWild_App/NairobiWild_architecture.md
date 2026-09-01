# Nairobi Wild — Architecture (v0.4)

## What it is
A match-3 puzzle game made in **Nairobi** and played across the whole of Africa. Swap adjacent animals, match three or more, chase a target inside a move limit. The mechanic is the genre standard (Candy Crush shape); the identity is the content — the countries, their animals, the music, the ornament.

## Design philosophy
1. **Familiar mechanic, local world.** The match-3 loop needs no teaching. What makes it *ours* is a tour of all 54 African countries, each fielding its own animals, which call out when you match them, over a Benga groove, with Maasai beadwork as the app's one ornament.
2. **Data-light or die.** ~153 KB total, no external requests, **no image or audio assets at all** — tiles are emoji on CSS gradients, the skyline is inline SVG, and every note of music and every animal call is synthesised at runtime. That is what keeps the install trivial on a prepaid data bundle.
3. **Offline is the default, online is the bonus.** Solo, Relax, pass-and-play and challenge links work with no network whatsoever. Live online duelling lights up when it can and never degrades the rest.
4. **Engine/UI separation.** All rules are pure functions on plain state; the UI plays back engine-produced phases and never re-derives rules.
5. **One seam per external concern.** `monetization.js` for money, `multiplayer.js` for opponents, `sounds.js`/`music.js` for audio, `atlas.js` for content. None of it is scattered through game code.

## Files
| File | Role |
|---|---|
| `atlas.js` | The content: the animal pool, all 54 countries with their cities and their own six animals, and the generated campaign |
| `match3.js` | Engine: board generation, match detection, specials, cascades, gravity/refill, deadlock reshuffle, boosters, duel config |
| `music.js` | Generative Benga soundtrack + pure, testable pattern builders |
| `sounds.js` | Animal voices — a registry of call archetypes |
| `multiplayer.js` | Challenge-link codec, the `room`-backed online adapter, the production realtime seam |
| `monetization.js` | Product catalogue, provider selection, AdMob / Play Billing / mobile-money checkout, revenue events |
| `index.html` | All screens, animation, input, economy, persistence, lobby, duel flow |
| `match3.test.mjs` | 31 tests — engine rules and the campaign |
| `extras.test.mjs` | 47 tests — music, animal voices, multiplayer, monetization |

## The campaign: a tour of Africa, country by country
**54 countries, 246 stages.** Pick a country, play its major cities in order, finish it and the next country unlocks. The tour opens in Nairobi — where the game is made — then works outward through East Africa, the Horn, Southern, Central, West, North Africa and the islands.

**Every country fields its own six animals**, the creatures it is actually known for. Kenya plays the Big Five plus a giraffe; Uganda swaps in gorillas and hippos; Namibia brings the oryx and a Cape fur seal; Madagascar plays lemurs and chameleons; **Mauritius fields the dodo**. That is what stops 246 stages of one mechanic feeling like a single long level — a test asserts at least 20 distinct line-ups.

The board keeps **six colour slots with fixed hues**, and a country maps its animals onto them. Colour identity therefore never depends on which animals are in play, so the board stays readable for colour-blind players anywhere on the map. A test rejects any country whose six animals share a glyph, since two identical-looking tiles would be unplayable.

### Difficulty: points per move, not raw target
Difficulty is **points required per move**, rising from 190 (against the ~550 a decent player scores) to 620, which needs real cascades. Because it is a function of the global stage number, **every city is harder than the one before it — inside a country and across the whole tour.**

The first cut of this curve escalated the raw target instead, and ended up demanding **132,000 points in 13 moves** — arithmetically impossible, because late stages have *fewer* moves. Targets now span 4,750–9,190, and a test rejects anything above 700 points per move.

## Animal voices
Matching a herd sounds **that animal**, not a beep. Voices are keyed by **archetype** — `roar`, `trumpet`, `grunt`, `hoot`, `hiss` and 14 more — rather than by species, because the six animals change with the country and many species share a manner of calling (a warthog snorts much like a rhino). `atlas.js` maps each animal to an archetype, and a test rejects any animal pointing at a voice that does not exist.

Two things make a synthesised call sound like an animal rather than a buzz, and both are in every voice:

1. **A harmonic stack** — several partials, so the ear hears a voice rather than a test tone.
2. **Formants** — a parallel bank of narrow band-passes standing in for the throat, which resonates at fixed frequencies whatever the pitch. This is what gives a roar its body.

| Archetype | Who uses it | How it is built |
|---|---|---|
| roar | lion | 4 partials sweeping 200→75 Hz, formants at 420/900/1850 Hz, a 28 Hz growl |
| trumpet | elephant | brass-like stack climbing 380→800 Hz |
| grunt | hippo | three deep honking pulses |
| hoot | gorilla, chimp | a rising pant-hoot |
| bark | zebra, wild dog | two short sharp pulses — a zebra barks, it does not whinny |
| hum | giraffe | the real 92 Hz night hum, voiced with 7 partials so a phone can carry it |
| rasp | leopard | five sawing strokes |
| *plus* snort, bellow, whoop, hiss, chatter, bleat, honk, screech, squawk, bray, yelp, splash | rhino, buffalo, hyena, crocodile, monkey, antelope, flamingo, eagle, parrot, penguin, fennec fox, turtle | 19 archetypes in all |

**Phone speakers set the design.** A phone reproduces almost nothing below ~300 Hz, so a zoologically "correct" 55 Hz lion roar is *silent* on the device most players use. Every voice keeps an honest fundamental but carries its character inside roughly 300–3000 Hz. Measured by rendering each call in an `OfflineAudioContext` and high-passing at 300 Hz, the share of energy a phone can reproduce rose from **28–59%** to **59–94%**.

### One AudioContext for everything
Music, sound effects and animal calls share a **single** AudioContext. iOS makes only one context audible, so the earlier arrangement — music on one, effects on another — left part of the game silent on a phone. Audio is re-armed on **every** tap rather than once, because a context can be suspended again later (backgrounding a tab, iOS).

Calls are ≤1.1 s, rate-limited to one per 70 ms, mixed above the music, and rise in pitch as a cascade builds; **the music ducks to 30% under each call**. A **Sound check** panel on the home screen states plainly whether audio is running and plays any call on demand — because a player who cannot hear a feature reasonably concludes it is missing.

### How to verify audio honestly
Counting audio nodes created during a match proves nothing: the soundtrack creates oscillators and noise buffers continuously, so the count rises either way. That mistake once had a broken feature reported as working. The methods that do work:

1. Run with **music off**, so any node created during a match must be a voice.
2. **Render each call in an `OfflineAudioContext`** and measure its energy, including after a 300 Hz high-pass.
3. Launch the browser **without** `--autoplay-policy=no-user-gesture-required`, or the test is not reproducing a real browser.

## Music: why it is synthesised
There is not one audio file in the build. A licensed bed would add megabytes to a game whose pitch is a tiny install, and would need clearing in every launch market. `music.js` sequences a **Benga**-flavoured groove — the fast, guitar-led Nairobi dance style — from oscillators and filtered noise: four-on-the-floor kick, kayamba 16ths, backbeat clap, pentatonic bass, the plucked nyatiti/guitar riff that shifts a scale degree each bar, and a sparse marimba that appears only at high energy.

Everything sits in F minor pentatonic, so layers never clash. Scheduling uses the standard WebAudio lookahead pattern (a 25 ms timer queues notes 120 ms ahead against the audio clock), so timing never drifts. Cascades of 3+ call `flourish()`.

## Multiplayer

### Offline (works anywhere, no server)
- **Pass and play** — two players, one phone, the same board in turn.
- **Challenge links** — you play a board, then share a link carrying the seed and your score (`#d=<seed>.<score>.<base64 nick>`). Your friend plays **the identical board** and the app compares. Zero infrastructure, and the share is the growth loop.

Both rely on the engine being deterministic: `newGame(level, seed)` reproduces a board exactly, asserted by a test.

### Online, live
The published page declares the **`room`** capability, giving every open copy a shared presence channel. No server of ours is involved. The whole lobby-and-duel handshake runs on **presence only** — never events — because presence is settable by any viewer while event topics are admin-only by default:

1. Host sets `{st:'host', seed}`.
2. Guest sees the host and sets `{st:'join', seed, vs:<host peer>}`.
3. Host locks on to the **first** guest pointing at it, sets `{st:'duel', vs:<guest peer>}`.
4. Guest sees the host point back → both start on the same seed.
5. Each publishes `{score, moves, done}` through the round; each renders the other's live.

Handled: unchosen joiners fall back; a 12-second join timeout; an opponent who leaves forfeits; stale and non-viewer peers filtered out. A **15-second heartbeat** keeps a player who pauses to think from being judged stale — without it, sitting still for 45 seconds told your opponent you had quit.

**Untrusted input.** Everything in a peer's presence is written by another person's page: values are coerced and clamped on read, nicknames sliced to 16 characters, and peer text reaches the DOM via `textContent`, never `innerHTML`.

**Fairness caveat.** Scores are client-reported — fine between friends, **not** cheat-proof. Ranked play needs an authoritative server, which the deterministic engine makes straightforward: replay the move list and recompute.

### Production path
The standalone Android build has no `room`, so implement `RealtimeAdapter` in `multiplayer.js` against a WebSocket service with the same method surface as `RoomAdapter`. Nothing in the UI changes. Offline modes need no server ever.

## Money (`monetization.js`)
One module, four entry points — `rewardedAd`, `purchase`, `products`, `onEvent`. Game code never touches an SDK, a price or a network.

**Provider selection is automatic and capability-checked**: Play Billing via the Digital Goods API in a TWA, mobile-money checkout when a public key is configured, an AdMob bridge when present, otherwise **simulated** — every flow completes without charging anyone, so play-testing is never blocked by missing accounts.

- **Ads:** four named rewarded placements (`continue`, `double`, `lives`, `shop`), reported on every revenue event, because "which moment earned this" is the number worth having.
- **IAP:** a single catalogue drives the shop, with local-currency display (KES) and a tip jar.
- **Shipped config is inert on purpose:** empty IDs, `testMode: true`, no key in the repo. A test asserts `isLive().any === false`.

`Finance/revenue-activation.md` is the checklist for switching it on.

## Economy & persistence (`localStorage` key `nairobiWild.v1`)
`coins, lives, lifeAt, stars{}, unlocked, sound, music, streak, lastDay, hammers, shuffles, nick`.

- **Lives:** 5 max, one per campaign attempt, refunded on a win, one regenerating per 10 minutes on a wall clock. Refill via rewarded ad or 100 coins. **Duels never cost a life** — multiplayer should be encouraged, not taxed.
- No accounts, no server, no PII. The only identity is a nickname kept on the player's own device.

## Verification status (2026-08-30)
- `node match3.test.mjs` → **31/31**; `node extras.test.mjs` → **47/47**.
- Playwright at 412×880, source tree **and** bundled single file, under **real browser autoplay rules**:
  - 54 countries listed, Kenya first with its six animals; 6 Kenyan cities; stage intro reads "Nairobi · Kenya · city 1 of 6".
  - A match creates **exactly one** AudioContext, in state `running`, and `voices.play()` returns true for a real archetype.
  - Sound check reports "Sound is on" and lists Lion:roar … Leopard:sawing call.
  - Offline degradation, pass-and-play, and a two-page live online duel with live opponent scoring all still pass.
