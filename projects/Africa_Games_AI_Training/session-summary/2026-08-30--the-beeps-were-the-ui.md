# Session Summary — 2026-08-30 — "I hear beeps not animal sounds"

## Owner input
> "I hear beeps not animal sounds."

This was the clarification that cracked it. The two previous reports said *no* sound; this one said the **wrong** sound. Audio was working — the game was simply beeping over its own animals.

## The method that finally worked
Three earlier audio investigations asked the wrong question — *did something play?* — and answered it with measurements that could not distinguish one sound from another. This time the page was instrumented to **log every oscillator and noise source a match creates**, with waveform, frequencies and duration, with the music off so nothing else could contaminate the log.

The answer arrived in a single run:

```
osc sine      freqs [560]      ← every tile tap
osc sawtooth  freqs [190]      ← every rejected swap
osc sine      freqs [560]
osc sawtooth  freqs [190]
...  (repeating, dozens of times)
osc sawtooth  freqs [168,94]   dur 0.18   ← the animal, at last
osc sawtooth  freqs [336,188]  dur 0.18
osc triangle  freqs [504,282]  dur 0.18
noise                          dur 0.18
```

**The beeps were the UI.** A 560 Hz sine fired on *every tile tap* and a 190 Hz sawtooth on *every rejected swap*. At dozens per minute they were the loudest and most frequent thing in the game. The animal call did play — but it was a rhino snort of **0.18 s per puff**, lost among them.

## The fix
1. **UI sounds are no longer tonal.** Taps are a 20 ms high-passed noise *click*; rejected swaps are a 140 ms low-passed *thud*; a special piece gets a rising noise *whoosh* layered **under** the call rather than instead of it. Only rare reward moments (level win, coin) stay musical. The animals are now the only voice in the game.
2. **No call shorter than 0.4 s**, asserted by a new test. The short archetypes — bark, snort, yelp, honk, squawk, bleat, splash — were lengthened to 0.45–0.55 s. A 0.18 s puff reads as a blip, not an animal.

**Verified by the same log.** A match now produces only: two 40 ms noise clicks, one 160 ms thud, and the animal — a zebra bark, sawtooth 532→205 Hz with a square harmonic at 1064→409 Hz plus breath, across two 0.22 s pulses. **Not one tonal beep.** A later run caught a lion roar: five partials from 194→73 Hz over 1.02 s.

## Verification
- `node match3.test.mjs` → **31/31**; `node extras.test.mjs` → **48/48** (new: no call under 0.4 s).
- Sound log clean on both the source tree and the bundled build; full tour check still passes (54 countries, one running AudioContext, Sound check reporting "Sound is on").

## Lesson recorded
Decision #41: **diagnose audio by logging what actually played**, not by asking whether anything played. Three failed investigations preceded this one — node counting was confounded by the music, and the autoplay-disabled browser flag meant the tests never reproduced a real one.

## Published
https://claude.ai/code/artifact/678a3eae-7baa-43a4-a65b-fce33f3c17a6 (same URL, updated in place)

## Still open
Recognisability — whether a listener hears "lion" rather than "growly noise" — remains unmeasurable by machine (`Risk-Registry.md` #23). If playtesters cannot name the animal blind, the fallback is short recorded samples at a real cost to install size.
