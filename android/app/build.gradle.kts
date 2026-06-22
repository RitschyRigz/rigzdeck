plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Optionaler fester Signier-Key: liegt eine keystore-Datei vor (z.B. in CI aus einem
// GitHub-Secret dekodiert), wird damit signiert -> App-Updates ohne Deinstallieren.
// Fehlt sie (lokal / CI ohne Secret), nutzt AGP den Standard-Debug-Key -> die APK ist
// trotzdem installierbar. So bleibt das oeffentliche Repo ohne committeten Schluessel.
val signKeystore = file("rigzdeck.keystore")

android {
    namespace = "com.rigzdeck"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.rigzdeck"
        minSdk = 26
        targetSdk = 34
        versionCode = 19
        versionName = "0.10.2"
    }

    signingConfigs {
        if (signKeystore.exists()) {
            create("rigz") {
                storeFile = signKeystore
                storePassword = System.getenv("RIGZDECK_KS_PASS") ?: "rigzdeck"
                keyAlias = System.getenv("RIGZDECK_KS_ALIAS") ?: "rigzdeck"
                keyPassword = System.getenv("RIGZDECK_KS_PASS") ?: "rigzdeck"
            }
        }
    }

    buildTypes {
        debug {
            if (signKeystore.exists()) signingConfig = signingConfigs.getByName("rigz")
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            if (signKeystore.exists()) signingConfig = signingConfigs.getByName("rigz")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity-ktx:1.9.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
}
