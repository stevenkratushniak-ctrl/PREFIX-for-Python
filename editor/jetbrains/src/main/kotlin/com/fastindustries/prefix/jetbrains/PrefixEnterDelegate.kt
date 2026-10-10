package com.fastindustries.prefix.jetbrains
import com.intellij.codeInsight.editorActions.enter.EnterHandlerDelegate
import com.intellij.openapi.actionSystem.DataContext
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.editor.actionSystem.EditorActionHandler
import com.intellij.openapi.project.Project
import com.intellij.openapi.util.Ref
import com.intellij.psi.PsiFile

class PrefixEnterDelegate : EnterHandlerDelegate {
    override fun preprocessEnter(file: PsiFile, editor: Editor, caretOffsetRef: Ref<Int>, caretAdvance: Ref<Int>, dataContext: DataContext, originalHandler: EditorActionHandler?): EnterHandlerDelegate.Result =
        EnterHandlerDelegate.Result.Continue

    override fun postProcessEnter(file: PsiFile, editor: Editor, dataContext: DataContext): EnterHandlerDelegate.Result {
        val project: Project=file.project
        if (EditorBoundary.isSupportedEnter(project,editor)) {
            PrefixCoordinator.govern(project,editor,editor.document.text,enter=true)
        }
        return EnterHandlerDelegate.Result.Continue
    }
}
