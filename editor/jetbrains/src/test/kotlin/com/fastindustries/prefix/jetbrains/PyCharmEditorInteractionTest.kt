package com.fastindustries.prefix.jetbrains

import com.intellij.openapi.actionSystem.ActionManager
import com.intellij.openapi.actionSystem.IdeActions
import com.intellij.ide.DataManager
import com.intellij.openapi.command.WriteCommandAction
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.editor.actionSystem.EditorActionManager
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.fileEditor.OpenFileDescriptor
import com.intellij.openapi.vfs.LocalFileSystem
import com.intellij.testFramework.fixtures.BasePlatformTestCase
import com.intellij.util.ui.UIUtil
import java.nio.file.Files
import java.nio.file.Path

/** Actual PyCharm application/editor model fixtures; these do not qualify rendered Swing UI. */
class PyCharmEditorInteractionTest : BasePlatformTestCase() {
    private lateinit var testEditor: Editor
    private lateinit var testPath: Path

    override fun setUp() {
        super.setUp()
        TestEntitlement.seed()
        val root = Path.of(System.getProperty("prefix.test.workRoot"))
        Files.createDirectories(root)
        testPath = Files.createTempFile(root, "prefix-interaction-", ".py")
    }

    override fun tearDown() {
        try {
            FileEditorManager.getInstance(project).closeAllFiles()
            Files.deleteIfExists(testPath)
        } finally { super.tearDown() }
    }

    private fun open(text: String): Editor {
        Files.writeString(testPath, text)
        val file = LocalFileSystem.getInstance().refreshAndFindFileByNioFile(testPath) ?: error("Physical fixture file missing")
        testEditor = FileEditorManager.getInstance(project).openTextEditor(OpenFileDescriptor(project, file), true) ?: error("PyCharm editor did not open")
        assertTrue("Fixture editor is outside the supported local file scope", EditorBoundary.isSupported(project, testEditor))
        return testEditor
    }

    private fun pumpUntil(predicate: () -> Boolean) {
        val deadline = System.nanoTime() + 15_000_000_000L
        do {
            UIUtil.dispatchAllInvocationEvents()
            if (predicate()) return
            Thread.sleep(20)
        } while (System.nanoTime() < deadline)
        assertTrue("Timed out waiting for PyCharm editor result", predicate())
    }

    private fun awaitEvaluation(editor: Editor) {
        // Synchronization only: assert document behavior after the real asynchronous evaluation finishes.
        val field = PrefixCoordinator::class.java.getDeclaredField("inFlight").apply { isAccessible = true }
        val pending = field.get(null) as java.util.concurrent.ConcurrentHashMap<*, *>
        pumpUntil { !pending.containsKey(System.identityHashCode(editor.document)) }
    }

    fun testMappedCorrectionUsesRealDocumentAndEngine() {
        val editor = open("if ready\n    pass\n")
        PrefixCoordinator.govern(project, editor, editor.document.text)
        pumpUntil { editor.document.text == "if ready:\n    pass\n" }
    }

    fun testEnterInvokesRegisteredDelegateAndLocalEngine() {
        val editor = open("if ready")
        editor.caretModel.moveToOffset(editor.document.textLength)
        WriteCommandAction.runWriteCommandAction(project, Runnable {
            EditorActionManager.getInstance().getActionHandler(IdeActions.ACTION_EDITOR_ENTER)
                .execute(editor, editor.caretModel.currentCaret, DataManager.getInstance().getDataContext(editor.contentComponent))
        })
        pumpUntil { editor.document.text.startsWith("if ready:") }
        assertTrue(editor.document.text.contains("pass"))
    }

    fun testUnactivatedDocumentRemainsUnchanged() {
        val editor = open("if ready\n    pass\n")
        TestEntitlement.clear()
        PrefixCoordinator.govern(project, editor, editor.document.text)
        awaitEvaluation(editor)
        assertEquals("if ready\n    pass\n", editor.document.text)
        val result = PrefixEngineClient().evaluate(editor.document.text)
        assertEquals("entitlement_required", (result as EngineDecision.Failure).code)
    }

    fun testUnsupportedSourceRemainsUnchanged() {
        val editor = open("x = @\n")
        PrefixCoordinator.govern(project, editor, editor.document.text)
        awaitEvaluation(editor)
        assertEquals("x = @\n", editor.document.text)
    }

    fun testEditWhileEngineRunsDiscardsStaleCorrection() {
        val editor = open("if ready\n    pass\n")
        PrefixCoordinator.govern(project, editor, editor.document.text)
        WriteCommandAction.runWriteCommandAction(project, Runnable { editor.document.setText("x = 2\n") })
        awaitEvaluation(editor)
        assertEquals("x = 2\n", editor.document.text)
    }

    fun testLicenseAndCorrectionActionsAreInstalled() {
        val actions = ActionManager.getInstance()
        for (id in listOf("PrefixPython.GovernDocument", "PrefixPython.GovernSelection", "PrefixPython.ActivateLicense", "PrefixPython.LicenseStatus", "PrefixPython.ValidateLicense", "PrefixPython.DeactivateLicense", "PrefixPython.BuyPrefix")) {
            assertNotNull("Action missing: $id", actions.getAction(id))
        }
    }
}
