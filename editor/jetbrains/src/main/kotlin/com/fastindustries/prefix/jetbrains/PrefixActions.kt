package com.fastindustries.prefix.jetbrains
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys

class GovernDocumentAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project=e.project ?: return
        val editor=e.getData(CommonDataKeys.EDITOR) ?: return
        PrefixCoordinator.govern(project,editor,editor.document.text)
    }
}
class GovernSelectionAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project=e.project ?: return
        val editor=e.getData(CommonDataKeys.EDITOR) ?: return
        if (!EditorBoundary.isSupported(project,editor) || !editor.selectionModel.hasSelection()) return
        val start=editor.selectionModel.selectionStart
        val end=editor.selectionModel.selectionEnd
        PrefixCoordinator.govern(project,editor,editor.document.getText(com.intellij.openapi.util.TextRange(start,end)),start,end)
    }
}
