import org.jetbrains.intellij.platform.gradle.IntelliJPlatformType
import org.jetbrains.intellij.platform.gradle.TestFrameworkType
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.3.21"
    id("org.jetbrains.intellij.platform") version "2.19.0"
}

group = "com.fastindustries.prefix"
version = "0.1.0"

repositories {
    mavenCentral()
    intellijPlatform { defaultRepositories() }
}

dependencies {
    implementation("com.google.code.gson:gson:2.11.0")
    intellijPlatform {
        pycharm("2026.2")
        bundledPlugin("PythonCore")
        pluginVerifier()
        testFramework(TestFrameworkType.Platform)
    }
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.4")
    testRuntimeOnly("org.junit.vintage:junit-vintage-engine:5.11.4")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.opentest4j:opentest4j:1.3.0")
}

kotlin {
    jvmToolchain(25)
    compilerOptions { jvmTarget.set(JvmTarget.JVM_25) }
}

intellijPlatform {
    buildSearchableOptions = false
    pluginConfiguration {
        id = "com.fastindustries.prefix.python.jetbrains"
        name = "PREFIX for Python"
        version = project.version.toString()
        ideaVersion {
            sinceBuild = "262.8665.309"
            untilBuild = "262.*"
        }
        description = """
            <p>PREFIX for Python applies a bounded set of deterministic Python structural corrections using the local PREFIX 0.1.0 engine.</p>
            <p>Govern the active Python document or selected structure. Mapped block corrections can be evaluated after Enter. Unsupported and ambiguous input is refused.</p>
            <p>Requires the separately installed PREFIX runtime with CPython 3.12 on Windows x64 or Linux x64 and the same activated PREFIX license used by the CLI and VS Code adapter.</p>
            <p>The plugin download is part of the existing PREFIX product. Commercial activation costs 29 USD once through Lemon Squeezy. Correction runs locally; license activation and validation contact Lemon Squeezy.</p>
        """.trimIndent()
        changeNotes = """
            <p>Reuses the PREFIX 0.1.0 correction engine and existing JetBrains adapter. Adds shared commercial license status, activation through password input and standard input, deactivation, and the existing purchase link.</p>
        """.trimIndent()
        vendor {
            name = "Fast Industries"
            url = "https://github.com/stevenkratushniak-ctrl/PREFIX-for-Python"
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
    maxHeapSize = "2g"
    systemProperty("java.awt.headless", "true")
    systemProperty("prefix.test.repoRoot", rootProject.projectDir.parentFile.parentFile.absolutePath)
    systemProperty("prefix.test.workRoot", layout.buildDirectory.dir("interaction-tests").get().asFile.absolutePath)
    environment("PREFIX_ENTITLEMENT_ROOT", layout.buildDirectory.dir("test-entitlement").get().asFile.absolutePath)
}
