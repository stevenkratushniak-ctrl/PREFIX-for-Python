import org.jetbrains.intellij.platform.gradle.IntelliJPlatformType
import org.jetbrains.intellij.platform.gradle.TestFrameworkType
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.3.21"
    id("org.jetbrains.intellij.platform") version "2.19.0"
}

group = "com.fastindustries.prefix"
version = "0.1.0-proof"

repositories {
    mavenCentral()
    intellijPlatform { defaultRepositories() }
}

dependencies {
    implementation("com.google.code.gson:gson:2.11.0")
    intellijPlatform {
        pycharm("2026.2")
        bundledPlugin("PythonCore")
        testFramework(TestFrameworkType.Platform)
        pluginVerifier()
    }
    testImplementation(kotlin("test"))\n    testImplementation("org.junit.jupiter:junit-jupiter:5.11.4")
}

kotlin {
    jvmToolchain(25)
    compilerOptions { jvmTarget.set(JvmTarget.JVM_25) }
}

intellijPlatform {
    buildSearchableOptions = false
    pluginConfiguration {
        id = "com.fastindustries.prefix.python.jetbrains"
        name = "PREFIX for Python — JetBrains Proof"
        version = project.version.toString()
        ideaVersion {
            sinceBuild = "262.8665.309"
            untilBuild = "262.*"
        }
        description = "Isolated proof adapter for the unchanged PREFIX for Python 0.1.0 local engine."
        vendor {
            name = "Fast Industries"
        }
    }
    pluginVerification {
        ides {
            create(IntelliJPlatformType.PyCharm, "2026.2")
        }
    }
}

tasks.test {
    useJUnitPlatform()
    systemProperty("prefix.test.repoRoot", rootProject.projectDir.parentFile.parentFile.absolutePath)
}
