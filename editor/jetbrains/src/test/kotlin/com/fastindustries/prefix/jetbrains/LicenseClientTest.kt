package com.fastindustries.prefix.jetbrains

import kotlin.test.*

class LicenseClientTest {
    @Test fun activationHasNoKeyInArguments() {
        val client = PrefixLicenseClient()
        val args = client.arguments("activate")
        assertEquals(listOf("-m", "prefix_python", "license", "activate", "--json", "--stdin"), args.takeLast(6))
        assertFalse(args.any { it.contains("license-key") })
    }
    @Test fun statusDoesNotAcceptSecretInput() {
        assertFalse(PrefixLicenseClient().arguments("status").contains("--stdin"))
    }
    @Test fun keyBufferIsClearedWhenEngineIsUnavailable() {
        val key = "synthetic-not-a-live-key".toCharArray()
        val unavailable = PrefixEngineClient(environment = mapOf("PREFIX_PYTHON_ENGINE" to "prefix-distribution-test-missing-engine"))
        val result = PrefixLicenseClient(unavailable).run("activate", key)
        assertEquals("ENGINE_UNAVAILABLE", result.state)
        assertTrue(key.all { it == '\u0000' })
        assertFalse(result.message.contains("synthetic"))
    }
    @Test fun unsupportedOperationFailsClosed() {
        assertFailsWith<IllegalArgumentException> { PrefixLicenseClient().arguments("export-key") }
    }
}
