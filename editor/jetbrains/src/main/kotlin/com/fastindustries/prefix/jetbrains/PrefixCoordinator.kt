package com.fastindustries.prefix.jetbrains
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.command.WriteCommandAction
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.project.Project
import com.intellij.openapi.diagnostic.Logger
import java.util.concurrent.ConcurrentHashMap

object PrefixCoordinator {
    private val log=Logger.getInstance(PrefixCoordinator::class.java)
    private val inFlight=ConcurrentHashMap<Int,Long>()
    private val client=PrefixEngineClient()

    fun govern(project: Project, editor: Editor, source: String, replaceStart: Int=0, replaceEnd: Int=editor.document.textLength, enter: Boolean=false) {
        if (enter && !EditorBoundary.isSupportedEnter(project,editor)) return
        if (!enter && !EditorBoundary.isSupported(project,editor)) return
        val snapshot=EditorBoundary.snapshot(editor)
        val key=snapshot.documentIdentity
        if (inFlight.putIfAbsent(key,snapshot.modificationStamp)!=null) return
        ApplicationManager.getApplication().executeOnPooledThread {
            val decision=try { client.evaluate(source) } catch(t:Throwable) { EngineDecision.Failure("adapter_exception",t.message?:"adapter exception") }
            ApplicationManager.getApplication().invokeLater {
                try {
                    if (!EditorBoundary.isCurrent(project,editor,snapshot)) return@invokeLater
                    val response=(decision as? EngineDecision.Response)?.value ?: return@invokeLater
                    if (!EngineContract.mayMutate(response)) return@invokeLater
                    if (enter && !enterMutationIsBounded(response,snapshot)) return@invokeLater
                    if (replaceStart<0 || replaceEnd<replaceStart || replaceEnd>editor.document.textLength) return@invokeLater
                    if (!editor.document.isWritable) return@invokeLater
                    WriteCommandAction.runWriteCommandAction(project,"PREFIX governed transition",null,Runnable {
                        if (!EditorBoundary.isCurrent(project,editor,snapshot)) return@Runnable
                        editor.document.replaceString(replaceStart,replaceEnd,response.source)
                    })
                } catch(t:Throwable) { log.warn("PREFIX adapter failed closed",t) }
                finally { inFlight.remove(key) }
            }
        }
    }

    private fun enterMutationIsBounded(response: PrefixResponse, snapshot: EditorSnapshot): Boolean {
        if (response.events.isEmpty()) return false
        val caretLine=snapshot.text.take(snapshot.caretOffset.coerceAtMost(snapshot.text.length)).count { it=='\n' } + 1
        val allowed=setOf("AUTO_INDENT","INSERT_PASS","MISSING_COLON","NORMALIZE_TABS")
        return response.events.all { it.rule_id in allowed && it.line in (caretLine-1)..(caretLine+1) } &&
            response.events.any { it.rule_id=="MISSING_COLON" }
    }
}
