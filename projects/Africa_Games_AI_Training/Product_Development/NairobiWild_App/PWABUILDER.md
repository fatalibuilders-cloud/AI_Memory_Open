# Packaging with PWABuilder

PWABuilder (pwabuilder.com) turns a live PWA into a signed Android App
Bundle. Paste the URL, answer a short form, download a `.aab`, upload it to
Play. It is the least painful route to the store and it is a reasonable
choice here — the manifest, the service worker and the icons it wants are
all already in place.

**But read the next section before you start.** There is one thing about our
current URL that will quietly spoil the result, and it is much cheaper to
fix before packaging than after.

---

## The thing that will bite: Digital Asset Links

PWABuilder builds a **Trusted Web Activity** — an Android app that is really
Chrome, told to trust one website and hide all its browser chrome. The
"trust" is not a setting. Chrome checks it, every launch, by fetching a file
from the **root of the site's origin**:

```
https://fatalibuilders-cloud.github.io/.well-known/assetlinks.json
```

Note what is *not* in that path: `/AI_Memory_Open/`. Asset links are
verified per **origin**, never per folder. Our game lives at
`https://fatalibuilders-cloud.github.io/AI_Memory_Open/`, and that root path
belongs to a different repository — a GitHub user site, named
`fatalibuilders-cloud.github.io`. Nothing we publish from *this* repo can
ever appear there.

**If the file is missing, the app still builds, installs and runs — with a
browser address bar across the top, permanently.** It looks like a web page
in a frame, not like an app. It also makes Play's "minimum functionality"
reviewers more likely to look twice (Risk #32).

So fix the address first. Three ways.

### Option A — publish at the root of a user site (free)

Create a repository named exactly **`fatalibuilders-cloud.github.io`** and
publish the game from it. The address becomes
`https://fatalibuilders-cloud.github.io/` — shorter, better on a store
listing, and `.well-known/assetlinks.json` now sits where Chrome looks.

Two details that waste an evening if you miss them:

- GitHub Pages runs Jekyll, which **ignores folders starting with a dot**.
  An empty `.nojekyll` file at the root fixes it. Our build already creates
  one.
- The manifest's `id` is deliberately `"nairobi-wild"` rather than a path,
  so moving the game from `/AI_Memory_Open/` to `/` on the same host does
  **not** orphan the copies people have already installed.

### Option B — a custom domain (a few dollars a year)

Point a domain you own at GitHub Pages. `nairobiwild.co.ke` on a store
listing reads like a studio; `fatalibuilders-cloud.github.io/AI_Memory_Open`
reads like a hobby. You then own the root, so asset links just work, and the
build already ships `web/.well-known/` if you put the file there.

### Option C — skip the TWA entirely

`android/` in this repo already builds a `.aab` that needs **no** asset
links, because it does not trust a website — it carries the whole game
inside the APK. It also works offline from the very first launch, where a
TWA needs one online visit before its cache exists.

---

## Which route, honestly

| | PWABuilder (TWA) | The `android/` build (WebView) |
|---|---|---|
| Effort | paste a URL | push, download from Actions |
| Needs asset links | **yes** | no |
| Offline on first launch | no — needs one online visit | yes |
| Updates | push the website, no new upload | new `.aab` for every change |
| **AdMob rewarded video** | **no** | **yes** |
| Play Billing | yes, built in | needs a native bridge |

That AdMob row is the one to think about. NextSteps #1 calls AdMob the
biggest revenue stream, and `monetization.js` is written against the AdMob
**Android SDK** — which a TWA cannot load, because a TWA has no Android code
of its own. Choosing the TWA means rewarded video has to be re-planned
around a web ad network instead.

The update row is the one in PWABuilder's favour, and it is a big one: fix a
bug, push, and every installed copy has it on next launch, with no upload and
no review. For a game you are about to put in front of relatives for the
first time, that matters more than ad revenue you have not switched on yet.

**A reasonable plan:** fix the address (Option A), ship the TWA with
PWABuilder, and keep `android/` for the day ads actually go in.

---

## Doing it

Once the game is at the root of an origin you control:

1. **pwabuilder.com** → paste the address → **Start**.
2. It scores the manifest and service worker. Ours should come back clean;
   anything it flags as "optional" (`shortcuts`, `iarc_rating_id`,
   `related_applications`) is genuinely optional and none of it blocks
   packaging.
3. **Package for stores → Android → Generate**. Settings worth getting
   right:

   | Field | Use | Why |
   |---|---|---|
   | Package ID | `ke.nairobiwild.game` | **Permanent.** Play binds it on first upload and it can never change. The same id is already in `android/app/build.gradle.kts`, so the two routes stay interchangeable. |
   | App name | Nairobi Wild | |
   | Launcher name | Nairobi Wild | what shows under the icon |
   | App version | `0.7` | |
   | Version code | `1` | must go **up** on every upload, forever |
   | Display mode | Standalone | Fullscreen hides the clock and battery; a puzzle game played in short sessions should not |
   | Signing key | **New** | PWABuilder makes one and gives it to you |
   | Google Play Billing | leave off for now | only needed when IAP actually ships |

4. **Download the zip. Then, before anything else, deal with the key.**

---

## The key, and the file

The zip contains:

| File | What to do with it |
|---|---|
| `app-release-signed.aab` | upload this to Play |
| `signing.keystore` | **back it up in two places, forever** |
| `signing-key-info.txt` | the password and alias for that key — same |
| `assetlinks.json` | host it (next section) |

**`signing.keystore` and `signing-key-info.txt` are the only copies that will
ever exist.** PWABuilder does not keep them. Lose them and you cannot ship an
update to your own app — a new key is a new app, with none of your installs
or ratings. Put them in a password manager and on one other device. Today,
not later.

Everything `android/README.md` says about the upload key applies here too.

### Hosting assetlinks.json

Put it at `.well-known/assetlinks.json` **at the root of the origin**, so it
answers at `https://<your-host>/.well-known/assetlinks.json`.

If the game is served from this repo's build, drop it at
`Product_Development/NairobiWild_App/web/.well-known/assetlinks.json` and the
workflow will publish it — but remember that only lands at the right address
if this repo is serving the origin root (Option B), not a project path.

Check it afterwards by opening that URL in a browser. You should see JSON
with your package name and a `sha256_cert_fingerprints` entry. If you get a
404, the TWA will show the address bar.

---

## Then: the parts PWABuilder does not change

The Play Console side is identical whichever `.aab` you upload, and it is
still the long pole:

- **$25 developer account**, plus identity verification that takes days.
- **12 testers opted in for 14 continuous days** before a personal account
  can reach production.
- Privacy policy URL, Data safety form, content rating, ads declaration.

All of it is written out in `store/README.md`, including the listing copy,
the icon and the screenshots.

One difference worth noting: a TWA **does** reach the network, so its Data
safety answers are not the clean row of "no" that the offline WebView build
gives. Chrome is doing the fetching, and the game itself still collects
nothing and has no accounts — but answer the form for what the app actually
does, not for what the old build did.
