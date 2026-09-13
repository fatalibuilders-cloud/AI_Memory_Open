# Play Store listing — Nairobi Wild

Everything Google asks for at submission, written out so the console is a
copy-paste job rather than an evening of invention.

## What is in here

| File | What Play calls it | Spec |
|---|---|---|
| `play-icon-512.png` | App icon | 512×512, 32-bit PNG, no transparency |
| `play-feature-1024x500.png` | Feature graphic | 1024×500, no transparency |
| `screenshots/*.png` | Phone screenshots | 1080×1920, need at least 2 |
| `art.html`, `make-art.mjs` | — | regenerate the icons and banner |
| `make-screenshots.mjs` | — | regenerate the screenshots by playing the game |

Regenerating (needs Node and Playwright):

```sh
node make-art.mjs                       # icon + banner + every launcher density
node ../build.mjs && node make-screenshots.mjs ../nairobi-wild.html
```

`make-art.mjs` writes the launcher icons straight into the Android project,
so the app icon and the store icon can never drift apart.

---

## Listing copy

**App name** (30 char max)

```
Nairobi Wild
```

**Short description** (80 char max)

```
Match Africa's wildlife across 246 levels and 54 countries. Plays offline.
```

**Full description** (4000 char max)

```
Swap and match the animals of Africa — from Nairobi National Park to the
Mara, and on across the whole continent.

Nairobi Wild is a match-3 game built in Nairobi. Line up three lions,
elephants, zebras, giraffes, rhinos or leopards to clear them, and hear each
animal answer as it goes. Chain a cascade and the calls rise with it.

• 246 levels across 54 African countries
• Every country fields its own animals — camels and fennec foxes in Egypt,
  not borrowed savanna game
• Real cities as levels: Nairobi, Mombasa, Kisumu, Lagos, Accra, Cairo,
  Dakar, and hundreds more
• Duel a friend on the same phone, or send a challenge link — you both play
  the exact same board
• Relax mode: no timer, no lives, no pressure
• Benga-flavoured music, generated as you play

Built to work where the network does not. The whole game is under 200 KB, it
never downloads anything, and it plays with the data switched off and the
plane mode on. No account. No sign-up. Nothing to lose when you change phone
— your stars come back with your Google backup.

Swahili names on every animal. Nairobi's skyline on the horizon, where it
belongs.
```

**Category:** Games → Puzzle
**Tags:** match 3, puzzle, casual
**Contact email:** *(yours — Play publishes it on the listing)*

---

## The submission checklist

Things that stop a submission dead, roughly in the order you hit them.

- [ ] **Play Developer account** — one-time **$25**, and Google verifies
      your identity (a national ID and an address that matches). Allow days,
      not minutes, for verification.
- [ ] **Closed testing before production.** A personal developer account
      opened after Nov 2023 must run a closed test with **at least 12
      testers who stay opted in for 14 continuous days** before it can apply
      for production access. Start this early — it is the longest pole in
      the whole process, and nothing else you do shortens it.
- [ ] **A signed `.aab`.** See `../android/README.md`. An unsigned bundle is
      rejected at upload.
- [ ] **Privacy policy URL.** Required for every app, including one that
      collects nothing. A GitHub Pages page saying "this app collects no
      data, has no accounts and sends nothing anywhere" is enough, and in
      this build it is also true.
- [ ] **Data safety form.** This build has no `INTERNET` permission and no
      analytics, so every answer is "no data collected, no data shared".
      That changes the day AdMob goes in — the ad SDK collects a device
      identifier, and the form must be updated in the same release.
- [ ] **Content rating questionnaire.** No violence, no gambling, no user
      content. Expect PEGI 3 / ESRB Everyone.
- [ ] **Ads declaration.** "No" today. "Yes" the moment rewarded video is
      switched on.
- [ ] **Target audience.** If you say the app targets children, Families
      Policy applies and your ad options narrow sharply (Risk #2). Deciding
      this before you build the ad integration saves rebuilding it.
- [ ] **Name clearance.** Check "Nairobi Wild" is not someone's trademark in
      Kenya and in your other launch markets before the listing goes live
      (Risk #8). Never use "Crush" or "Saga" in the title.
- [ ] **Play it on a real phone first.** The APK from the same CI run
      installs directly. Nobody has yet played this on an actual Android
      device, and that is the one test no amount of CI replaces.

---

## Two things that will cost you money if you get them wrong

**Never tap your own ads once they are live.** AdMob bans accounts
permanently for invalid traffic, and a developer testing their own live ad
unit is the classic way it happens. `testMode: true` ships by default and a
test asserts it (Risk #19). `../../../Finance/revenue-activation.md` warns
again at the step where it is switched off.

**Only ever put public keys in the app.** A Flutterwave or Paystack *public*
key belongs in client config; the secret key belongs on a server you
control. Anything shipped in an APK is readable by anyone who downloads it.
