import java.util.Properties

plugins {
    id("com.android.application")
}

/*
 * Signing.
 *
 * Play needs every upload signed with YOUR upload key — the same one, every
 * release, forever. Lose it and you cannot update the app without asking
 * Google to reset it.
 *
 * The key is never in this repository. It is read from keystore.properties
 * (git-ignored, for building on your own machine) or from environment
 * variables (for CI, where the .jks arrives as a base64 secret). If neither
 * is present the build still runs and produces an UNSIGNED bundle, which is
 * fine for testing and rejected by Play.
 */
val keystoreProps = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}
// An unset GitHub Actions step output arrives as "" rather than as nothing,
// so blank has to mean absent — otherwise an unsigned build dies on
// file("") instead of quietly skipping the signing config.
fun secret(prop: String, env: String): String? =
    (keystoreProps.getProperty(prop) ?: System.getenv(env))?.takeIf { it.isNotBlank() }

val storeFilePath = secret("storeFile", "NW_KEYSTORE_FILE")
val hasSigning = storeFilePath != null && rootProject.file(storeFilePath).exists()

android {
    namespace = "com.fatalibuilders.nairobiwild"
    compileSdk = 36

    defaultConfig {
        // PERMANENT. Play binds this to the listing on first upload and it can
        // never be changed. Decide now, not after the first release.
        applicationId = "com.fatalibuilders.nairobiwild"

        // Android 5.0. Deliberately low: in this market a four-year-old phone
        // is a new phone, and the game asks nothing of the hardware.
        minSdk = 21
        targetSdk = 36

        versionCode = 1
        versionName = "0.6"
    }

    signingConfigs {
        if (hasSigning) {
            create("release") {
                storeFile = rootProject.file(storeFilePath!!)
                storePassword = secret("storePassword", "NW_KEYSTORE_PASSWORD")
                keyAlias = secret("keyAlias", "NW_KEY_ALIAS")
                keyPassword = secret("keyPassword", "NW_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            // No code to shrink worth the risk: the app is a WebView and a
            // manifest. R8 here buys kilobytes and costs debuggability.
            isMinifyEnabled = false
            isShrinkResources = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            if (hasSigning) signingConfig = signingConfigs.getByName("release")
        }
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    // index.html is already one self-contained file; compressing it again in
    // the APK saves little and costs start-up time on slow storage.
    androidResources {
        noCompress += listOf("html")
    }

    bundle {
        // The game has no per-device variation at all — same HTML, same
        // behaviour everywhere — so splitting the bundle would only create
        // more artifacts to reason about for zero download saving.
        language.enableSplit = false
        density.enableSplit = false
        abi.enableSplit = false
    }
}

dependencies {
    // There is no Kotlin in this app, but AndroidX drags the Kotlin standard
    // library in transitively at two different versions, and since Kotlin 1.8
    // the old kotlin-stdlib-jdk7/jdk8 artifacts were folded into the main one.
    // Mixed versions therefore ship the same classes twice and the build fails
    // on duplicate classes. The BOM pins them all to one version, where jdk7
    // and jdk8 are empty forwarding shims.
    implementation(platform("org.jetbrains.kotlin:kotlin-bom:1.9.24"))

    implementation("androidx.appcompat:appcompat:1.7.0")
    // Serves src/main/assets over https://appassets.androidplatform.net/ so the
    // page gets a real web origin. Without it the page is a file:// URL, and
    // file:// has no localStorage — every player's progress would vanish.
    implementation("androidx.webkit:webkit:1.12.1")
}

/*
 * The HTML is generated, not stored twice. build.mjs folds the seven script
 * files into one page and writes it straight into assets, so an APK can never
 * ship a stale copy of the game.
 */
val bundleGame by tasks.registering(Exec::class) {
    val game = rootProject.file("../index.html")
    val out = rootProject.file("app/src/main/assets/index.html")
    inputs.files(
        game,
        rootProject.file("../atlas.js"), rootProject.file("../match3.js"),
        rootProject.file("../music.js"), rootProject.file("../multiplayer.js"),
        rootProject.file("../sounds.js"), rootProject.file("../sfxpack.js"),
        rootProject.file("../monetization.js"),
    )
    outputs.file(out)
    commandLine("node", rootProject.file("../build.mjs").absolutePath, out.absolutePath)
}

tasks.named("preBuild") { dependsOn(bundleGame) }
