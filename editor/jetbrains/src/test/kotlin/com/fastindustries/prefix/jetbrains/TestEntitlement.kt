package com.fastindustries.prefix.jetbrains

internal object TestEntitlement {
    fun seed() {
        // Synthetic local fixture only. This never calls a provider or establishes a live entitlement.
        val script = """
            from prefix_python.entitlement import root,write,fp
            import time
            key='synthetic-jetbrains-test-key'
            write(root(),{'schema':1,'policy_version':1,'instance_id':'fixture','install_id':'fixture','license_fingerprint':fp(key),'store_id':476739,'product_id':1416057,'variant_id':2212018,'last_validated_at':int(time.time())},key)
        """.trimIndent()
        val process = ProcessBuilder(PrefixEngineClient().resolveInvocation() + listOf("-c", script)).redirectErrorStream(true).start()
        val out = process.inputStream.bufferedReader().readText()
        check(process.waitFor() == 0) { "Synthetic entitlement fixture setup failed: $out" }
    }
    fun clear() {
        val script = """
            from prefix_python.entitlement import root,paths
            for p in paths(root()):
                if p.exists(): p.unlink()
        """.trimIndent()
        val process = ProcessBuilder(PrefixEngineClient().resolveInvocation() + listOf("-c", script)).redirectErrorStream(true).start()
        val out = process.inputStream.bufferedReader().readText()
        check(process.waitFor() == 0) { "Synthetic entitlement fixture cleanup failed: $out" }
    }
}
