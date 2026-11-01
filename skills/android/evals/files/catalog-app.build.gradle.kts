// app/build.gradle.kts — Catalog app. AGP 9.5.0, Gradle 9.6.0, Kotlin 2.4.21 (see gradle/libs.versions.toml).
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.example.catalog"
    compileSdk = 37

    defaultConfig {
        applicationId = "com.example.catalog"
        minSdk = 26
        targetSdk = 37
        versionCode = 41
        versionName = "3.2.0"
    }

    buildFeatures {
        compose = true
    }

    buildTypes {
        release {
            optimization {
                enable = true
            }
        }
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.activity.compose)
    debugImplementation(libs.androidx.compose.ui.tooling)

    testImplementation(libs.junit)
}

// The catalog's components live in src/main/kotlin/com/example/catalog/ui/components/
// and every component already has @Preview functions (light, dark, font scale 1.5).
