# African_Wildlife_SFX — the recorded sound pack

Drop real recordings in here and the game uses them automatically. **Nothing is required** — every animal already has a synthesised call, and any animal without a file simply keeps it. A half-finished pack works fine.

## Where the files go

```
African_Wildlife_SFX/
├── 01_LION/roar_01.ogg  roar_02.ogg  growl.ogg  snarl.ogg  distant_roar.ogg
├── 02_ELEPHANT/trumpet_01.ogg  trumpet_02.ogg  rumble.ogg  angry.ogg  herd.ogg
├── 03_HYENA/whoop_01  whoop_02  laugh  giggle
├── 04_HIPPO/grunt_01  grunt_02  honk  splash
├── 05_CROCODILE/hiss  growl  snap  bellow
├── 06_LEOPARD/saw_01  saw_02  growl  snarl
├── 07_CHEETAH/chirp_01  chirp_02  purr  growl
├── 08_GORILLA/hoot_01  hoot_02  chest_beat  grunt
├── 09_BUFFALO/bellow_01  bellow_02  snort  herd
├── 10_ZEBRA/bark_01  bark_02  whinny  snort
├── 11_GIRAFFE/hum  snort  bleat
├── 12_MONKEY_BABOON/chatter_01  chatter_02  screech  bark
├── 13_WARTHOG/snort_01  snort_02  squeal  grunt
├── 14_SNAKE/hiss_01  hiss_02  rattle
├── 15_EAGLE_BIRDS/eagle_01  eagle_02  screech  call  parrot_01  parrot_02  squawk
├── 16_INSECTS/insects_loop
├── 17_JUNGLE_AMBIENCE/jungle_loop
├── 18_SAVANNA_AMBIENCE/savanna_loop
├── 19_WATER/water_loop
├── 20_RAIN_THUNDER/rain_loop
├── Android/optimized_OGG/     ← checked FIRST; put the small mobile files here
└── LICENSE/credits.txt        ← must be filled in before shipping
```

The exact filenames matter — they are listed in `MANIFEST` in `sfxpack.js`. Change them there if your pack names things differently.

## File format

Tried in this order per variant: **`.ogg` → `.m4a` → `.mp3`**. Ogg is smallest; m4a covers older iOS, which historically would not decode ogg. Shipping ogg **and** m4a for each call is the safe combination.

## Keep it small — this is the whole point of the game

The game is ~150 KB today and installs on a prepaid data bundle. A careless pack destroys that.

| Sound | Target length | Target size (ogg ~64 kbps mono) |
|---|---|---|
| One animal call | 0.4–1.2 s | **8–20 KB** |
| Ambience loop | 8–15 s, seamless | 60–120 KB |
| **Whole pack** | | **aim under 3 MB** |

Practical rules: **mono**, 44.1 kHz, trim silence at both ends, normalise to about −3 dBFS, and no reverb tail (the game overlaps calls during cascades). Put the compressed versions in `Android/optimized_OGG/` — that folder is checked first.

## Licensing — read before shipping

`LICENSE/credits.txt` must list, for every file: **source, author, licence, and link**. This is not optional:

- **CC0 / public domain** — safest. No attribution required, but record it anyway.
- **CC-BY** — usable, but you *must* credit the author in the app's credits screen. Track which files need this.
- **Commercial pack licence** — check whether it permits use in a *paid or ad-supported* app; many "free for personal use" packs do not.
- **Never** take audio from YouTube, documentaries, or another game. A takedown after launch is far more expensive than buying a licence.

Reasonable sources: Freesound (filter by CC0), BBC Sound Effects Archive (check the terms), Zapsplat, and commercial libraries. Best of all for a Nairobi studio: **record your own** at a local conservancy — it is cheap, unambiguous to license, and a genuine marketing story.

## How the game uses it

1. On entering a stage, the six animals of that country are fetched **in the background**. Never on the menus.
2. A match plays a random variant, never the same one twice running, pitched up slightly as a cascade builds.
3. Until a file is decoded — or if it is missing, 404s, or fails to decode — that animal uses its **synthesised** voice. Play is never blocked or delayed.
4. **Sound check** on the home screen marks recorded calls with a ● so you can see at a glance what the pack covers.

## Two things to know

- **Animals with no folder keep synthesis, permanently.** The pack covers 15 of the 32 animals in the atlas. Rhino, camel, antelope, flamingo, penguin, seal, fennec fox, goat, chameleon, turtle, bat, fish, dolphin, shark, crab, dodo and owl have no folder in this layout and will always synthesise unless you add folders and register them in `MANIFEST`.
- **The claude.ai artifact preview cannot load these files.** That sandbox blocks media fetches, so the preview always uses synthesised voices. The pack works in the packaged Android app and on any normal web host. This is expected, not a bug.
