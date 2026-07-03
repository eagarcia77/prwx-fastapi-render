plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "edu.prwx.quakebridge"
    compileSdk = 35

    defaultConfig {
        applicationId = "edu.prwx.quakebridge"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "2.0.0"
        buildConfigField("String", "DEFAULT_SERVER_URL", "https://prwx-fastapi-render.onrender.com/")
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
