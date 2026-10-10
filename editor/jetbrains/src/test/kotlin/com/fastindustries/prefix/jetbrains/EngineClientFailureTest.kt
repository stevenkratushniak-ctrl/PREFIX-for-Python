package com.fastindustries.prefix.jetbrains
import kotlin.test.*

class EngineClientFailureTest {
    @Test fun missingEngineFailsClosed(){
        val old=System.getProperty("prefixPython.pythonCommand")
        try {
            System.setProperty("prefixPython.pythonCommand","definitely-not-prefix-python")
            val d=PrefixEngineClient(100).evaluate("x=1\n")
            assertIs<EngineDecision.Failure>(d)
            assertEquals("engine_unavailable",d.code)
        } finally { if(old==null) System.clearProperty("prefixPython.pythonCommand") else System.setProperty("prefixPython.pythonCommand",old) }
    }
}
