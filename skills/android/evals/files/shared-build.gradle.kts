// shared/build.gradle.kts — Kotlin 2.2.20, Compose Multiplatform 1.9
plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.androidKotlinMultiplatformLibrary)
    alias(libs.plugins.composeMultiplatform)
    alias(libs.plugins.composeCompiler)
}

kotlin {
    androidLibrary {
        namespace = "com.example.pantry.shared"
        compileSdk = 36
        minSdk = 26
    }
    iosArm64()
    iosSimulatorArm64()
    macosArm64()
    js { browser() }
    @OptIn(org.jetbrains.kotlin.gradle.ExperimentalWasmDsl::class)
    wasmJs { browser() }

    sourceSets {
        commonMain.dependencies {
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(libs.kotlinx.coroutines.core)
        }

        // Added in this PR: one place for code shared by the browser targets.
        val browserMain by creating {
            dependsOn(commonMain.get())
        }
        jsMain.get().dependsOn(browserMain)
        wasmJsMain.get().dependsOn(browserMain)

        // iosMain and macosMain both need the Keychain wrapper; today it is
        // copy-pasted into each of them.
    }
}
