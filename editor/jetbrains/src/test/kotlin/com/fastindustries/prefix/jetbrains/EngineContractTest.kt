package com.fastindustries.prefix.jetbrains
import kotlin.test.*

class EngineContractTest {
    private fun json(status:String="ACCEPT_FIXED",state:String="APPLIED",lane:String="APPLY",version:String="0.1.0",pin:String="3.12") =
        """{"status":"$status","state":"$state","lane":"$lane","source":"x=1\n","events":[],"version":"$version","python_version_pin":"$pin"}"""

    @Test fun applyMayMutate(){ val r=(EngineContract.parse(json()) as EngineDecision.Response).value; assertTrue(EngineContract.mayMutate(r)) }
    @Test fun validDoesNotMutate(){ val r=(EngineContract.parse(json("ACCEPT_VALID")) as EngineDecision.Response).value; assertFalse(EngineContract.mayMutate(r)) }
    @Test fun adviseDoesNotMutate(){ val r=(EngineContract.parse(json("REFUSE_UNMAPPED","ADVISED","ADVISE")) as EngineDecision.Response).value; assertFalse(EngineContract.mayMutate(r)) }
    @Test fun analyzeDoesNotMutate(){ val r=(EngineContract.parse(json("REFUSE_INVALID","REFUSED","ANALYZE")) as EngineDecision.Response).value; assertFalse(EngineContract.mayMutate(r)) }
    @Test fun roadmapDoesNotMutate(){ val r=(EngineContract.parse(json("REFUSE_UNMAPPED","REFUSED","ROADMAP")) as EngineDecision.Response).value; assertFalse(EngineContract.mayMutate(r)) }
    @Test fun malformedFailsClosed(){ assertIs<EngineDecision.Failure>(EngineContract.parse("{")) }
    @Test fun unknownFailsClosed(){ assertIs<EngineDecision.Failure>(EngineContract.parse(json(status="BOGUS"))) }
    @Test fun engineMismatchFailsClosed(){ assertEquals("engine_version_mismatch",(EngineContract.parse(json(version="9")) as EngineDecision.Failure).code) }
    @Test fun pythonMismatchFailsClosed(){ assertEquals("unsupported_python_authority",(EngineContract.parse(json(pin="3.13")) as EngineDecision.Failure).code) }
    @Test fun entitlementRefusalIsActionableAndCannotMutate() {
        val decision = EngineContract.parse("""{"status":"REFUSE_INVALID","state":"REFUSED","lane":"ANALYZE","refusal_code":"entitlement_required","source":"","events":[]}""")
        assertEquals("entitlement_required", assertIs<EngineDecision.Failure>(decision).code)
    }
}
