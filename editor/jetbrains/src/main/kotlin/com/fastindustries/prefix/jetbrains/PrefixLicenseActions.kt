package com.fastindustries.prefix.jetbrains

import com.intellij.ide.BrowserUtil
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.openapi.ui.Messages
import java.awt.BorderLayout
import javax.swing.JComponent
import javax.swing.JLabel
import javax.swing.JPanel
import javax.swing.JPasswordField

private class PrefixActivationDialog(project: Project?) : DialogWrapper(project) {
    private val keyInput = JPasswordField(36)
    init {
        title = "Activate PREFIX for Python"
        setOKButtonText("Activate")
        init()
    }
    override fun createCenterPanel(): JComponent = JPanel(BorderLayout(0, 8)).apply {
        add(JLabel("License key from your PREFIX purchase:"), BorderLayout.NORTH)
        add(keyInput, BorderLayout.CENTER)
        add(JLabel("Activation sends the key to Lemon Squeezy."), BorderLayout.SOUTH)
    }
    override fun getPreferredFocusedComponent(): JComponent = keyInput
    fun takeKey(): CharArray = keyInput.password.also { keyInput.text = "" }
}

private fun runLicense(project: Project?, operation: String, key: CharArray? = null) {
    ApplicationManager.getApplication().executeOnPooledThread {
        val result = PrefixLicenseClient().run(operation, key)
        ApplicationManager.getApplication().invokeLater {
            if (project?.isDisposed == true) return@invokeLater
            Messages.showInfoMessage(project, "${result.state}\n${result.message}", "PREFIX for Python")
        }
    }
}

class ActivateLicenseAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val dialog = PrefixActivationDialog(e.project)
        if (dialog.showAndGet()) runLicense(e.project, "activate", dialog.takeKey())
        else dialog.takeKey().fill('\u0000')
    }
}
class LicenseStatusAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) = runLicense(e.project, "status")
}
class ValidateLicenseAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) = runLicense(e.project, "validate")
}
class DeactivateLicenseAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) = runLicense(e.project, "deactivate")
}
class BuyPrefixAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        BrowserUtil.browse("https://fastlaunch.lemonsqueezy.com/checkout/buy/37f6bf48-4f0d-4151-a076-8b60f030e985")
    }
}
