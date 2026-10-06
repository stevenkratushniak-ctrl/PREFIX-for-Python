package com.fastindustries.prefix.jetbrains
import kotlin.test.*

class EngineIntegrationTest {
    private val client=PrefixEngineClient(timeoutMillis=10_000)
    private fun response(source:String)=assertIs<EngineDecision.Response>(client.evaluate(source)).value

    @Test fun mappedApplyUsesRealEngine(){ val r=response("if ready\n    pass\n"); assertEquals("APPLY",r.lane); assertEquals("ACCEPT_FIXED",r.status); assertTrue(EngineContract.mayMutate(r)) }
    @Test fun alreadyValidUsesRealEngine(){ val r=response("x = 1\n"); assertEquals("ACCEPT_VALID",r.status); assertFalse(EngineContract.mayMutate(r)) }
    @Test fun adviseUsesRealEngine(){ val r=response("elif ready:\n    pass\n"); assertEquals("ADVISE",r.lane); assertFalse(EngineContract.mayMutate(r)) }
    @Test fun analyzeUsesRealEngine(){ val r=response("return 1\n"); assertEquals("ANALYZE",r.lane); assertFalse(EngineContract.mayMutate(r)) }
    @Test fun refusalUsesRealEngine(){ val r=response("if (\n"); assertFalse(EngineContract.mayMutate(r)) }
    @Test fun repeatedCorrectionIsIdempotent(){ val first=response("if ready\n    pass\n"); val second=response(first.source); assertEquals("ACCEPT_VALID",second.status); assertFalse(EngineContract.mayMutate(second)) }
}
