// One Java activity around one HTML file — deliberately no Kotlin plugin and
// no third-party build tooling, because every extra version axis is another
// way for the release build to break on a day you need it to work.
plugins {
    id("com.android.application") version "8.9.1" apply false
}
