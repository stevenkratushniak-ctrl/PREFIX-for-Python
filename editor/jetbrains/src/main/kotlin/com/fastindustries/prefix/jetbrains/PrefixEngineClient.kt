package com.fastindustries.prefix.jetbrains
import java.io.File
import java.nio.charset.StandardCharsets
import java.util.concurrent.TimeUnit

class PrefixEngineClient(private val timeoutMillis: Long = 5_000, private val environment: Map<String,String> = System.getenv()) {
    fun evaluate(source: String): EngineDecision {
        val invocation = resolveInvocation()
        val entitlement = PrefixLicenseClient(this, timeoutMillis).run("status")
        if (!entitlement.entitled) {
            if (entitlement.state == "ENGINE_UNAVAILABLE")
                return EngineDecision.Failure("engine_unavailable", entitlement.message)
            return EngineDecision.Failure("entitlement_required", "Activate your PREFIX license from Tools > PREFIX for Python > Activate License. Install the matching commercial PREFIX runtime first.")
        }
        return try {
            val process = ProcessBuilder(invocation + listOf("-m","prefix_python","--stdin","--json")).redirectErrorStream(false).start()
            process.outputStream.bufferedWriter(StandardCharsets.UTF_8).use { it.write(source) }
            if (!process.waitFor(timeoutMillis, TimeUnit.MILLISECONDS)) {
                process.destroyForcibly()
                return EngineDecision.Failure("engine_timeout","PREFIX engine timed out")
            }
            val stdout = process.inputStream.bufferedReader(StandardCharsets.UTF_8).readText()
            val stderr = process.errorStream.bufferedReader(StandardCharsets.UTF_8).readText()
            if (stdout.isBlank()) EngineDecision.Failure("engine_failure", stderr.ifBlank { "PREFIX engine returned no JSON" })
            else EngineContract.parse(stdout)
        } catch (e: Exception) {
            EngineDecision.Failure("engine_unavailable", e.message ?: e.javaClass.simpleName)
        }
    }
    internal fun resolveInvocation(): List<String> {
        val configured = System.getProperty("prefixPython.pythonCommand")?.trim().orEmpty()
        if (configured.isNotEmpty()) return listOf(configured)
        val env = environment["PREFIX_PYTHON_ENGINE"]?.trim().orEmpty()
        if (env.isNotEmpty()) return listOf(env)
        val os = System.getProperty("os.name").lowercase()
        if (os.contains("win")) {
            val local = environment["LOCALAPPDATA"]?.let { File(it,"FastIndustries/PREFIX for Python/runtime/python.exe") }
            if (local?.isFile == true) return listOf(local.absolutePath)
            return listOf("py","-3.12")
        }
        val root = environment["XDG_DATA_HOME"]?.takeIf { it.isNotBlank() } ?: environment["HOME"]?.let { File(it,".local/share").path }
        val installed = root?.let { File(it,"fastindustries/prefix-python/runtime/prefix-python-python") }
        if (installed?.isFile == true) return listOf(installed.absolutePath)
        return listOf("python3.12")
    }
}
