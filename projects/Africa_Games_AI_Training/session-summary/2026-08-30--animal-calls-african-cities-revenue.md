# Session Summary — 2026-08-30 — Animal calls, 51 African cities, real revenue plumbing

## Owner input
> "Once you match the animals then make their animal sounds instead of beep. Can use all the city in Africa as stage levels. Also make it generate funds for the developers."

## What was done

### 1. Animals now call when you match them
`sounds.js` — six synthesised voices, one per species, replacing the match beep:

| Animal | Call | How |
|---|---|---|
| Simba | roar | sawtooth falling 150→55 Hz with a 24 Hz tremolo — the rumble is what makes it read as a roar |
| Tembo | trumpet | bright rising sweep, band-passed so it blares |
| Punda Milia | double bark | two short square pulses — a zebra barks, it does not whinny |
| Twiga | hum | 92 Hz, because giraffes really do hum at about that pitch at night |
| Kifaru | snort | noise-dominant, almost no pitch |
| Chui | sawing call | five rasping pulses in a row |

Still **no audio files**. Each voice is a pure data spec plus a renderer, so the calls are unit-tested (audible, ≤1s, distinct from one another, lion below zebra, trumpet rising). They are quiet, rate-limited to one per 70 ms, and pitch up as a cascade builds. The engine now reports the colours cleared in each phase so the UI knows which animal to sound.

### 2. The campaign is 51 African cities
Replaced the 15 Kenyan locations with one journey across the continent: **Nairobi → East Africa → the Horn → North Africa → West Africa → Central Africa → Southern Africa → Cape Town**, spanning 40+ countries, each stage carrying its city, country and flag.

Levels are **generated from a city table**, not hand-written, so adding a city is one line and the difficulty curve stays monotonic by construction (asserted by tests). This also clears the content-burn risk — 15 stages was a demo, not a game.

### 3. Money: production-shaped, honestly incomplete
`monetization.js` — the whole money layer behind four functions:
- **Provider selection is automatic and capability-checked:** Play Billing via the Digital Goods API in a TWA, mobile-money checkout when a key is configured, an AdMob bridge when present, otherwise **simulated** (every flow completes, nothing is charged).
- **Four named ad placements** (`continue`, `double`, `lives`, `shop`) — placement is reported on every revenue event, because "which moment earned this" is the number worth having.
- **One catalogue** drives the shop, with local-currency display (KES) and a **tip jar** that grants only free-earnable coins.
- **Shipped config is inert on purpose** — no IDs, `testMode: true`, no keys committed — and a test asserts `isLive().any === false`.

`Finance/revenue-activation.md` is the new checklist: which accounts to open in what order, the fees, payout thresholds, and where the money lands.

**Stated plainly to the owner:** revenue cannot be switched on from here. AdMob, Play Console and Flutterwave/Paystack all require the owner's identity, bank details and tax status. The code is finished; the accounts are the blocker.

## Verification
- `node match3.test.mjs` → **28/28** (added: campaign integrity, Nairobi start, no duplicate cities, goals reachable inside the move budget, data-driven level building, phases carrying cleared colours).
- `node extras.test.mjs` → **39/39** (added: voice physics, per-animal character, catalogue sanity, "nothing sold buys progress", local pricing, provider selection, inert shipped config, purchase and ad event flows).
- `node engine.test.mjs` (Oware) → 13/13.
- Browser, source tree **and** bundled single file: 51-stage map (🇰🇪 Nairobi → 🇿🇦 Cape Town), solo play, offline degradation, pass-and-play, and a **two-page live online duel** with the opponent's score updating live. Shop renders 8 catalogue items in KES with the honest "Demo mode" notice; a purchase grants coins; and a match creates **both oscillator and noise-buffer nodes** — the signature of a synthesised animal call rather than a beep.

**Incident during the work:** a scripted edit matched a comment inside the `<style>` block and destroyed the CSS and markup of `index.html`. Caught immediately, restored from the last commit, and redone with precise anchors. No damaged file was published or committed.

## Published
Nairobi Wild — https://claude.ai/code/artifact/678a3eae-7baa-43a4-a65b-fce33f3c17a6 (same URL, updated in place)

## Open items → `NextSteps.md`
Switch on revenue (AdMob first); playtest in Nairobi, specifically whether the animal calls grate over a long session; name clearance; Android TWA wrap; and play the generated difficulty curve, which is monotonic but entirely unplayed.
