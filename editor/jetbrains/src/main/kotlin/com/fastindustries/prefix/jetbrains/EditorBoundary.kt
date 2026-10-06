package com.fastindustries.prefix.jetbrains
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.fileEditor.FileDocumentManager
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.project.Project

data class EditorSnapshot(val text:String,val modificationStamp:Long,val caretOffset:Int,val documentIdentity:Int)

object EditorBoundary {
    fun isSupported(project: Project, editor: Editor): Boolean {
        val file=FileDocumentManager.getInstance().getFile(editor.document) ?: return false
        return file.fileSystem.protocol=="file" && file.name.endsWith(".py",true) &&
            file.isWritable && editor.document.isWritable && editor.caretModel.caretCount==1
    }
    fun isSupportedEnter(project: Project, editor: Editor)=isSupported(project,editor) && !editor.selectionModel.hasSelection()
    fun snapshot(editor: Editor)=EditorSnapshot(editor.document.text,editor.document.modificationStamp,editor.caretModel.offset,System.identityHashCode(editor.document))
    fun isCurrent(project: Project, editor: Editor, snapshot: EditorSnapshot): Boolean =
        isSupported(project,editor) && FileEditorManager.getInstance(project).selectedTextEditor===editor &&
        System.identityHashCode(editor.document)==snapshot.documentIdentity &&
        editor.document.modificationStamp==snapshot.modificationStamp &&
        editor.caretModel.offset==snapshot.caretOffset && editor.document.text==snapshot.text
}
