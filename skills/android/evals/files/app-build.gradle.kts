// :app module build script, currently on AGP 8.13 / Gradle 8.14.
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    kotlin("kapt")
    alias(libs.plugins.hilt)
}

android {
    namespace = "com.example.shop"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.shop"
        minSdk = 26
        versionCode = 41
        versionName = "4.1.0"
        testInstrumentationRunner = "android.test.InstrumentationTestRunner"

        buildConfigField("String", "API_BASE_URL", "https://api.example.com/")
        buildConfigField("boolean", "TELEMETRY", "true")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android.txt"),
                "proguard-rules.pro",
            )
        }
    }

    buildFeatures {
        compose = true
    }
}

// Rename the release APK to include the version name.
android.applicationVariants.all {
    if (buildType.name == "release") {
        outputs.forEach { output ->
            println("packaging ${output.name} for $versionName")
        }
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.room.runtime)
    implementation(libs.hilt.android)
    kapt(libs.hilt.compiler)
    kapt(libs.androidx.room.compiler)
    testImplementation(libs.junit)
}
