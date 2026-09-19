# Session Summary — 2026-09-19 — Getting it onto friends' phones

## Owner input
"I want my friends and family to try it on their phones … how can they
download and play without putting it in the Google Play store"

## The answer, and why it is a link rather than a file
Three routes exist — a link, the single HTML file, the debug APK — and the
link wins on every axis that matters for this audience:

- **iPhone.** The APK is Android-only; a meaningful share of any Kenyan
  family group is not.
- **No warnings.** Sideloading makes Android ask twice whether the user
  really trusts a file from outside the Play Store. That conversation has to
  be had with every single relative.
- **It still becomes an app.** Chrome's *Install app*, iOS's *Add to Home
  Screen*: lion icon, full screen, no address bar.
- **It works offline**, which is the point in this market. ~200 KB on the
  first visit, nothing ever again.
- **Fixes propagate.** A push reaches everyone on next launch instead of
  eleven people being asked to re-download.

The Play Store is months away regardless — identity verification, then
twelve testers opted in for fourteen days — so waiting for it before
collecting any feedback would be a self-inflicted delay.

## What was built

### An installable, offline web build
`web/manifest.webmanifest` (standalone, portrait, maskable icons at 192 and
512), `web/sw.js`, and a registration in the page guarded to run only in a
secure context that is not the APK's own origin.

The service worker takes the four-file shell on first visit and serves
cache-first with a background refresh, so a player never waits for the
network and is at most one launch behind. `VERSION` is stamped with the
commit at deploy time: the browser byte-compares `sw.js` on every
navigation, so a publish is what tells an installed copy to drop its cache.

### A deploy workflow
`.github/workflows/nairobi-wild-web.yml` — engine tests, then build, then
the offline test, then GitHub Pages. Gated so a broken game cannot publish.

### A real bug, found by adding the manifest
The web-only head tags point at files that exist only on the host. The
standalone single file — the one handed out over WhatsApp — was therefore
sitting there failing to fetch three things it did not need, and logging an
error for it. `build.mjs` now strips that block by default, keeps it under
`--web`, and **throws if a standalone build still references a web-only
file**.

### `web.test.mjs` — the matatu test
Serves the built site over localhost (a secure context, so workers are live)
and checks what a friend actually experiences: manifest parses and is
standalone, worker takes control, shell cached, a move scores, then
**the network is cut** and the page still opens with the save file intact.
Plus a no-404 check, which is what caught the missing favicon.
**10/10**, and it gates the deploy.

### `SHARING.md`
All three routes with their honest costs, the message to paste into the
family group, and the two questions worth asking a relative who has just
played: *did the animals make their own sounds?* (wrong three times, and no
machine can settle it) and *where did you stop, and why?*

## What could not be done here
**Switching Pages on.** The owner approved it, but this container's proxy
blocks the GitHub Pages settings API — a third host on the blocked list,
after `dl.google.com` and the artifact storage. So the first deploy failed
exactly as predicted, with GitHub's own unhelpful 404. A `failure()` step now
prints the fix into the run summary, so the red X explains itself.

The fix is one setting: **Settings → Pages → Source → GitHub Actions**, then
re-run.

## Verification
- `match3` 31/31, `extras` 57/57, `web` 10/10 — **98 tests**.
- Standalone file re-checked from `file://`: 54 countries, 64 tiles, **no
  service worker, no console errors** — the strip works.
- CI: the web build job passed including the offline test; the deploy job
  failed only on Pages not being enabled.

## Next
The owner flips one switch and sends the link. That is now NextSteps #2,
deliberately ahead of the Play Console: it is the fastest feedback loop
available and it costs nothing.
