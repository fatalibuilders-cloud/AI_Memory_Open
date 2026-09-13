# Session Summary — 2026-09-13 — The Android app and the Play bundle

## Owner input
"Create abb file in order to upload on Google store" — an `.aab`, the Android
App Bundle Google Play accepts.

## What was stated plainly, up front
**This container cannot build an `.aab`.** The network policy blocks
`dl.google.com`, and `maven.google.com` only redirects there, so there is no
Android SDK, no AGP and no `aapt2` to be had — verified rather than assumed.
So the deliverable is not a file produced here: it is the project that
produces one, plus a build machine the owner actually has.

That build machine is **GitHub Actions**. Push the branch, and the `.aab`
and a sideloadable `.apk` arrive as artifacts on the run. No Android Studio,
no 10 GB SDK download, no laptop.

## What was built

### The Android project (`android/`)
One Java activity around one HTML file. `build.mjs` runs as a Gradle
pre-build step and writes the bundled page into `assets/`, so an APK can
never ship a stale copy of the game.

Four decisions that are hard to reverse later:

- **A WebView over local assets, not a Trusted Web Activity.** A TWA needs
  the game hosted on HTTPS with asset links — a server to pay for, and no
  offline play worth the name, which is the whole proposition in this
  market. It also cannot show AdMob. The cost: Play Billing now needs a
  native bridge instead of the Digital Goods API.
- **Served from `https://appassets.androidplatform.net/`, never `file://`.**
  `file://` has no `localStorage`; every player's stars, coins and streak
  would be erased on exit. The most expensive mistake available in a wrapper
  this small, avoided by one dependency.
- **No `INTERNET` permission.** Everything is in `assets`, so Play's
  Data-safety form is an honest row of "no data collected". Online duels and
  the recorded pack are off in this build; both already degrade cleanly.
- **`applicationId` is permanent.** `com.fatalibuilders.nairobiwild`, flagged
  loudly in the README because Play binds it on first upload and it can
  never be changed.

The activity also earns its place on back handling, system-bar insets, font
scaling, long-press suppression and timer pausing — the ways a WebView game
feels wrong on Android if nobody does the work.

### `window.NW_back` in the page
Android back asks the page first. Rather than duplicating navigation, it
**clicks the back control the screen already shows**, so "back" has exactly
one definition. Decision points (`ovDuelEnd`, `ovHandover`) swallow the press
so a duel cannot be dropped by a stray swipe. Verified in a browser: closes
an overlay, steps cities → map → home, then returns false so Android exits.

### Store art and listing (`store/`)
Icon, feature graphic, six 1080×1920 screenshots taken by actually playing
the game, plus the scripts that regenerate all of it. `make-art.mjs` writes
the launcher icons straight into the Android project, so the app icon and
the store icon cannot drift apart.

The listing copy and the full submission checklist are written out, including
the two items that cost real time and money: **identity verification plus a
12-tester, 14-day closed test before production access**, and never tapping
your own live ads.

### An icon that took four tries
The first three attempts were a hand-drawn acacia. Every one read as a
mushroom at 48 px — the proportions of a flat-topped thorn tree do not
survive that reduction. Abandoned for **a lion on one of the game's own
amber tiles**, which says "match-3" and "wildlife" in the same glance. Worth
recording because the failure was not in the drawing but in the choice of
subject.

## Two real bugs, both caught by CI
1. **`Cannot convert '' to File`.** An unset GitHub Actions step output
   arrives as `""`, not as nothing, so the unsigned path called `file("")`
   and died instead of skipping the signing config. Blank now means absent.
2. The first run also proved the useful half: the engine tests, the SDK
   setup and AGP resolution all worked, so the failure was one line deep.

## What could not be verified here
**Nobody has run this on an Android device.** The Java compiles and the
bundle builds, but insets, the back gesture, WebView audio and the save file
have only been reasoned about, not seen. Installing the CI `.apk` on a real
Nairobi phone is the first thing to do, and it is in NextSteps #4.

## Verification
- `node match3.test.mjs` → **31/31**; `node extras.test.mjs` → **57/57**,
  both also run in CI as a gate before the Android build.
- Browser: back hook correct on every screen and overlay; bundle still makes
  **zero network requests** and logs no console errors.
- GitHub Actions: `.aab` and `.apk` built from a clean checkout.

## Next
The remaining steps are all the owner's and none are code: make and back up
the upload key, open the Play account, start the 12-tester closed test, and
play it on a real phone.
