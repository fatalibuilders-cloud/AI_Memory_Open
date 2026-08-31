# Session Summary — 2026-08-30 — Fixing the animal calls (and correcting a bad verification)

## Owner input
> "With the html share, the animal voices still are not integrated — like roar for the lions."

The owner was right, and my previous session's verification of this feature was wrong.

## The correction that mattered most
Last session I reported the calls working because "a match creates oscillator and noise-buffer nodes." **That proved nothing.** The Benga soundtrack creates oscillators and noise buffers continuously, so that count would have risen whether or not any animal made a sound. I presented a confounded measurement as evidence.

**Method that actually works** (now documented and repeatable):
1. Run with **music off**, so any audio node created during a match must be a voice.
2. Render each call in an **OfflineAudioContext** and measure its energy, including after a 300 Hz high-pass — a proxy for what a phone speaker can reproduce.

## What the honest measurement found
The calls *were* firing (music off: 1 → 19 oscillators on a match). The wiring was fine. **The sound was the problem**, in two ways:

1. **Too crude.** A single oscillator swept through a low-pass is a buzz, not a voice.
2. **Below what a phone can play.** A phone reproduces almost nothing under ~300 Hz. A zoologically "correct" 55 Hz lion roar is effectively *silent* on the device most players will use.

Share of each call's energy above 300 Hz, before the fix: Twiga **28%**, Kifaru **37%**, Simba **55%**, Chui 59%.

## The fix
Rebuilt every voice in `sounds.js` around two things real animal calls have:
- **A harmonic stack** — several partials per voice instead of one oscillator.
- **Formants** — a parallel bank of narrow band-passes standing in for the throat resonances that give a roar its body regardless of pitch.

Fundamentals stay honest (the giraffe still hums at 92 Hz) but the character now lives in 300–3000 Hz where phones work.

| | Simba | Tembo | Punda Milia | Twiga | Kifaru | Chui |
|---|---|---|---|---|---|---|
| energy above 300 Hz, before | 55% | 79% | 82% | 28% | 37% | 59% |
| **after** | **76%** | **94%** | **92%** | **59%** | **78%** | **81%** |

Two supporting changes, because audibility is not only synthesis:
- **The music now ducks to 30% under every call.** The continuous groove was sitting right on top of them.
- **A tappable voice legend in *How to play*** — six buttons, one per animal, so any call can be heard on demand. A player who cannot hear a feature concludes it is missing, which is exactly what happened here.

## A second real bug, found by accident
The browser suite began failing with a duel ending unprompted. The cause was genuine, not a test artifact: presence was only refreshed when a player **moved**, so anyone who paused to think for 45 seconds was judged stale and their opponent was told they had quit. Added a 15-second heartbeat (`unref`'d so it never keeps the Node test process alive).

## Verification
- `node match3.test.mjs` → **28/28**; `node extras.test.mjs` → **45/45**, including new assertions that every voice has a harmonic stack, has formants inside the vocal range, reaches at least 900 Hz (so a phone can carry it), that the first call is never swallowed by the rate limiter, and that a muted voice reports it did not play.
- Browser, source tree **and** bundled build: all six legend buttons synthesise their stack (7–27 oscillators each); music ducking present; full smoke suite green — 51-stage map, solo play, offline degradation, pass-and-play, and the two-page live duel with live opponent scoring.

## Published
https://claude.ai/code/artifact/678a3eae-7baa-43a4-a65b-fce33f3c17a6 (same URL, updated in place)

## Open item
Audibility is now measured; **recognisability is not, and cannot be by machine**. If playtesters cannot name the animal blind, the fallback is short recorded samples at a real size cost (`Risk-Registry.md` #23).
