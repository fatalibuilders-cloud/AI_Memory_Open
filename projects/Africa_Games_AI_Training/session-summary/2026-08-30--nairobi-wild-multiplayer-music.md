# Session Summary — 2026-08-30 — Nairobi Wild: wildlife, multiplayer, Benga

## Owner input
> "The game is from Nairobi hence put matching animals instead of market items. Let's have online multiplayer and offline solo player. Use Afro music and culture for background music and interfaces."

Three changes: a re-theme, a major feature, and an identity direction. All three shipped.

## What was done

### 1. Re-themed to Nairobi — **Market Day → Nairobi Wild**
- Tiles are now Kenyan wildlife, named in Swahili in the UI: 🦁 Simba, 🐘 Tembo, 🦓 Punda Milia, 🦒 Twiga, 🦏 Kifaru, 🐆 Chui.
- The 15 levels became a journey out of the city: Nairobi National Park → Karura → Athi Plains → Ngong Hills → Amboseli → Nakuru → Hell's Gate → Tsavo → Samburu → Aberdares → Mount Kenya → Maasai Mara → Meru → the Rift Valley. Each level's collect goal matches the animal that place is actually known for.
- App folder renamed `MarketDay_App` → `NairobiWild_App`.

### 2. Multiplayer — five modes, only one needs a network
| Mode | Network |
|---|---|
| Safari (15-level solo) | No |
| Relax (unlimited) | No |
| Duel: pass and play on one phone | No |
| Duel: challenge link — same board, share your score | Only to send the link |
| Duel: **live online**, opponent's score in real time | Yes |

- **Duels are same-seed races:** both players get a byte-identical board and 20 moves; higher score wins. The engine is deterministic, so a shared seed is all the synchronisation a fair match needs — which makes the offline and online duels literally the same game.
- **Live online runs on the artifact `room` capability** — no server of ours. The entire lobby-and-duel handshake uses **presence only**, never events, because presence is settable by any viewer while event topics are admin-only by default (an events-based lobby would have worked for the owner and silently failed for everyone else).
- Handled: unchosen joiners fall back, 12s join timeout, opponent-leaves forfeit, stale/agent peers filtered, and all peer-supplied values coerced and rendered with `textContent` (never `innerHTML`).
- `RealtimeAdapter` is left as the documented seam for the standalone Android build, which has no `room`.

### 3. Afro music and culture
- **`music.js`** — a generative **Benga** groove (the fast, guitar-led Nairobi dance style), sequenced live from oscillators and filtered noise: kick, kayamba shaker, backbeat clap, pentatonic bass, and the signature plucked nyatiti/guitar riff that shifts a scale degree each bar, with a sparse marimba layer that only appears at high energy. Cascades of 3+ trigger a three-second flourish. Standard WebAudio lookahead scheduling, so timing never drifts.
- **No audio files at all.** A licensed bed would cost megabytes on a prepaid data bundle and need clearing per market.
- **Interface culture:** Maasai beadwork band as the app's one ornament; a savanna-dusk palette with shuka red and Kenyan flag green; an inline-SVG horizon of the **Nairobi skyline with the KICC tower and an acacia** — the park's signature view of wildlife with a city behind it; Swahili combo words (Poa!, Safi!, Moto sana!) and "Asante sana" on purchase.

## Verification
- `node match3.test.mjs` → **22/22**. `node extras.test.mjs` → **21/21** (music pattern builders, challenge-link codec, room-adapter handshake, hostile-peer input).
- Playwright at 412×880, run against **both** the source tree and the bundled single file:
  - Offline solo: 15-level map, 3 real matches, board stayed 64/64 filled.
  - No-room degradation: lobby reports online unavailable, disables hosting, still offers both offline duels.
  - Pass and play: VS panel, 20 moves.
  - **Live online duel across two browser pages:** A hosts → B sees "Wanjiru" listed → B joins → both land on an identical board with correct opponent names → **B's screen shows A's score rise 0 → 720 live**.
  - Zero console errors.

**Bugs found and fixed during verification:** the online handshake never fired (it was gated behind "already in a duel", so a duel could never start); a fragile monkey-patched function replaced with a direct branch; a CSS specificity collision that left the horizon artwork floating mid-screen; and a redundant progress bar duplicating the duel scoreboard.

## Published
- Nairobi Wild — https://claude.ai/code/artifact/678a3eae-7baa-43a4-a65b-fce33f3c17a6 (supersedes the Market Day link)
- Oware Legends — https://claude.ai/code/artifact/4d5e21bb-eab1-4396-9daf-e66367af4472

**For online duels the owner must share the artifact** — both players need the page open.

## Open items → `NextSteps.md`
Playtest a live duel on two real phones on mobile data; trademark-clear the name; Android TWA wrap; grow 15 levels toward ~100; M-Pesa first for payments.
