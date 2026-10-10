package com.fastindustries.prefix.jetbrains

import com.google.gson.Gson
import java.nio.charset.StandardCharsets
import java.util.concurrent.TimeUnit

data class LicenseResult(val state: String = "UNKNOWN", val entitled: Boolean = false, val message: String = "PREFIX license status is unavailable.")

/** Uses the installed engine's entitlement. The adapter owns no key store or licensing policy. */
class PrefixLicenseClient(private val engine: PrefixEngineClient = PrefixEngineClient(), private val timeoutMillis: Long = 10_000) {
    internal fun arguments(operation: String): List<String> {
        require(operation in setOf("status", "activate", "validate", "deactivate"))
        return engine.resolveInvocation() + listOf("-m", "prefix_python", "license", operation, "--json") +
            if (operation == "activate") listOf("--stdin") else emptyList()
    }

    fun run(operation: String, key: CharArray? = null): LicenseResult {
        var process: Process? = null
        return try {
            process = ProcessBuilder(arguments(operation)).redirectErrorStream(false).start()
            process.outputStream.bufferedWriter(StandardCharsets.UTF_8).use { writer ->
                if (operation == "activate") {
                    if (key == null || key.isEmpty()) return LicenseResult("INVALID_KEY", false, "Enter the key supplied with your PREFIX purchase.")
                    writer.write(key)
                    writer.newLine()
                }
            }
            if (!process.waitFor(timeoutMillis, TimeUnit.MILLISECONDS)) {
                process.destroyForcibly()
                return LicenseResult("NETWORK_UNAVAILABLE", false, "The license command timed out. Check your connection and try again.")
            }
            val stdout = process.inputStream.bufferedReader(StandardCharsets.UTF_8).readText()
            val value = Gson().fromJson(stdout, LicenseResult::class.java)
            if (value == null || value.state.isBlank()) LicenseResult()
            else if (value.entitled && value.state !in setOf("ACTIVE_VALIDATED", "ACTIVE_CACHED", "OFFLINE_GRACE")) LicenseResult("UNKNOWN", false, "The installed runtime returned an unsupported entitlement state.")
            else value.copy(message = safeMessage(value.state))
        } catch (_: Exception) {
            LicenseResult("ENGINE_UNAVAILABLE", false, "Install the matching PREFIX runtime and CPython 3.12, then try again.")
        } finally {
            key?.fill('\u0000')
            process?.destroy()
        }
    }

    private fun safeMessage(state: String): String = when (state) {
        "ACTIVE_VALIDATED", "ACTIVE_CACHED", "OFFLINE_GRACE" -> "PREFIX is activated on this installation."
        "UNACTIVATED" -> "Activate the license key supplied with your PREFIX purchase."
        "DEACTIVATED" -> "PREFIX has been deactivated on this installation."
        "INVALID_KEY", "WRONG_PRODUCT", "WRONG_VARIANT" -> "That key is not valid for this PREFIX product."
        "ACTIVATION_LIMIT_REACHED" -> "The license has reached its activation limit. Deactivate an existing installation or contact order support."
        "CACHE_INVALID", "CACHE_EXPIRED" -> "The local entitlement is invalid or expired. Validate or reactivate your license."
        "NETWORK_UNAVAILABLE" -> "The licensing service is unavailable. Check your connection and try again."
        "CONFIGURATION_REQUIRED" -> "This candidate runtime has not been configured for commercial activation."
        else -> "PREFIX license status could not be confirmed."
    }
}
