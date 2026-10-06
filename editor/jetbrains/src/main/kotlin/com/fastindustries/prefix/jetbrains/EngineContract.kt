package com.fastindustries.prefix.jetbrains

import com.google.gson.Gson
import com.google.gson.JsonParseException

enum class PrefixStatus { ACCEPT_VALID, ACCEPT_FIXED, REFUSE_UNMAPPED, REFUSE_AMBIGUOUS, REFUSE_INVALID }
enum class PrefixState { APPLIED, ADVISED, REFUSED }
enum class PrefixLane { APPLY, ADVISE, ANALYZE, ROADMAP }

data class PrefixEvent(val rule_id: String = "", val line: Int = 0, val before: String = "", val after: String = "", val reason: String = "")
data class PrefixResponse(
    val status: String = "", val state: String = "", val lane: String = "", val source: String = "",
    val events: List<PrefixEvent> = emptyList(), val refusal_code: String? = null, val refusal_reason: String? = null,
    val python_version_pin: String = "", val version: String = ""
)
sealed interface EngineDecision {
    data class Response(val value: PrefixResponse) : EngineDecision
    data class Failure(val code: String, val detail: String) : EngineDecision
}
object EngineContract {
    const val ENGINE_VERSION = "0.1.0"
    const val PYTHON_AUTHORITY = "3.12"
    private val gson = Gson()
    fun parse(stdout: String): EngineDecision {
        val response = try { gson.fromJson(stdout, PrefixResponse::class.java) }
        catch (e: JsonParseException) { return EngineDecision.Failure("malformed_response", e.message ?: "Malformed JSON") }
        catch (e: RuntimeException) { return EngineDecision.Failure("malformed_response", e.message ?: "Unreadable response") }
            ?: return EngineDecision.Failure("malformed_response", "Empty JSON response")
        if (runCatching { PrefixStatus.valueOf(response.status) }.isFailure ||
            runCatching { PrefixState.valueOf(response.state) }.isFailure ||
            runCatching { PrefixLane.valueOf(response.lane) }.isFailure)
            return EngineDecision.Failure("unknown_response", "Unknown PREFIX outcome")
        if (response.version != ENGINE_VERSION)
            return EngineDecision.Failure("engine_version_mismatch", "Expected PREFIX " + ENGINE_VERSION + ", got " + response.version)
        if (response.python_version_pin != PYTHON_AUTHORITY)
            return EngineDecision.Failure("unsupported_python_authority", "Expected Python authority " + PYTHON_AUTHORITY + ", got " + response.python_version_pin)
        return EngineDecision.Response(response)
    }
    fun mayMutate(response: PrefixResponse): Boolean =
        response.state == PrefixState.APPLIED.name && response.lane == PrefixLane.APPLY.name && response.status == PrefixStatus.ACCEPT_FIXED.name
}
