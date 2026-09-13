# Nairobi Wild — the Android wrapper

One Java activity around one HTML file. The game is `../index.html`; this
folder only gives it a window, an icon and a Play Store identity.

`bundleRelease` produces the `.aab` Google Play wants. `assembleRelease`
produces the `.apk` a phone can actually install — Play will not accept an
APK from a new app, and a phone will not install an AAB, so you generally
want both.

---

## The fastest way to get an .aab

**Push the branch and let GitHub build it.** You do not need Android Studio,
a 10 GB SDK download, or a laptop at all.

1. Push to any branch. `.github/workflows/nairobi-wild-android.yml` runs.
2. Open the repository on GitHub → **Actions** → the newest
   *Nairobi Wild — Android* run.
3. At the bottom of the run page, **Artifacts**:

| Artifact | What it is for |
|---|---|
| `nairobi-wild-aab` | the upload to Play |
| `nairobi-wild-apk-debug` | **the one a phone will install today** |
| `nairobi-wild-apk` | the release APK, installable only once you sign it |

Without the signing secrets below, the bundle and the release APK are
**unsigned** — fine for looking at, rejected by Play, and not installable on
a phone either, because Android refuses unsigned packages.

That is why the debug APK is there. Android signs debug builds with its own
throwaway keystore, so it installs without any key of yours. It is the same
game with the same assets and is the right way to test on a real phone before
going anywhere near the Play Console. It cannot be uploaded to Play.

## Building on your own machine

Needs a JDK 17 and the Android SDK (Android Studio installs both).

```sh
cd android
./gradlew bundleRelease      # app/build/outputs/bundle/release/app-release.aab
./gradlew assembleRelease    # app/build/outputs/apk/release/app-release.apk
```

Gradle runs `node ../build.mjs` first and writes the bundled page into
`app/src/main/assets/index.html`, so the APK can never contain a stale copy
of the game. **Node must be on your PATH.**

---

## The upload key

Play signs every release with a key that identifies you. Lose it and you
cannot ship an update — only Google can reset it, and only sometimes. It is
the single most important file in this project and **it is not in this
repository**, by design.

Make it once, on a machine you control:

```sh
keytool -genkeypair -v \
  -keystore upload.jks \
  -storetype PKCS12 \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias nairobiwild
```

It asks for a password twice and for your name and location. Then:

- **Back it up somewhere that is not this laptop.** A password manager
  attachment, an encrypted drive, a printed base64 copy in a safe — any two
  of those. A phone in Nairobi is stolen more often than a key is lost to
  disk failure.
- Never commit it. `.gitignore` already blocks `*.jks` and
  `keystore.properties`, but the habit matters more than the rule.

### Building signed, locally

Create `android/keystore.properties` (git-ignored):

```properties
storeFile=upload.jks
storePassword=…
keyAlias=nairobiwild
keyPassword=…
```

### Building signed, in CI

Turn the key into text and store it as a repository secret:

```sh
base64 -w0 upload.jks    # macOS: base64 -i upload.jks
```

GitHub → Settings → Secrets and variables → Actions → **New repository
secret**, four of them:

| Secret | Value |
|---|---|
| `NW_KEYSTORE_BASE64` | the base64 blob above |
| `NW_KEYSTORE_PASSWORD` | the store password |
| `NW_KEY_ALIAS` | `nairobiwild` |
| `NW_KEY_PASSWORD` | the key password |

The build reads them only if all four are present; otherwise it produces an
unsigned bundle rather than failing, so a red build always means real
breakage.

---

## Decisions worth knowing before you change them

**`applicationId` is `com.fatalibuilders.nairobiwild` and is permanent.**
Play binds it to the listing on first upload and it can never be changed —
a different id is a different app, with no ratings, no installs and no
updates for anyone who already has it. Change it now if you want something
else. It does not have to match a domain you own.

**No `INTERNET` permission.** Everything ships in `assets`, so the app asks
for nothing and the Data-safety form is an honest row of "no". The cost:
online duels and the recorded sound pack are off in this build. Both already
degrade cleanly — the game shows the two offline duel modes and synthesises
every animal call. Adding AdMob later means adding the permission *and*
updating the Data-safety declaration in the same release.

**A WebView, not a Trusted Web Activity.** A TWA would need the game hosted
on HTTPS with Digital Asset Links — a server to pay for, and no offline play
worth the name. A WebView over local assets keeps the whole point of the
game: it works with the data off. It also keeps AdMob possible, which a TWA
does not.

**The page is served from `https://appassets.androidplatform.net/`, not
`file://`.** `WebViewAssetLoader` gives the page a real web origin. Under
`file://` there is no `localStorage`, and every player's stars, coins and
streak would vanish on exit.

**`minSdk` 21 (Android 5.0).** In this market a four-year-old phone is a new
phone. The game asks nothing of the hardware, so there is no reason to
exclude anyone.

**`targetSdk` 36.** Play requires new apps to target a recent API level and
raises the floor every August — check the current requirement before your
first upload and raise this number if it has moved.
