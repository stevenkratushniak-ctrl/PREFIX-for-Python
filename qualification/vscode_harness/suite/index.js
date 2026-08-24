"use strict";

const assert = require("node:assert/strict");
const vscode = require("vscode");

const EXTENSION_ID = "fastindustries.prefix-python";

async function run() {
    const extension = vscode.extensions.getExtension(EXTENSION_ID);
    assert.ok(extension, `${EXTENSION_ID} is not installed`);
    const api = await extension.activate();
    assert.ok(api, "PREFIX extension did not expose its qualification API");
    const commands = new Set(await vscode.commands.getCommands(true));
    for (const command of [
        "prefixPython.correctDocument",
        "prefixPython.correctSelection",
        "prefixPython.showGovernanceSurface",
    ]) {
        assert.ok(commands.has(command), `missing command: ${command}`);
    }

    const configuration = vscode.workspace.getConfiguration("prefixPython");
    await configuration.update("pythonCommand", "", vscode.ConfigurationTarget.Global);
    await configuration.update("enableOnEnter", true, vscode.ConfigurationTarget.Global);
    const invocation = api.getResolvedInvocation();
    assert.equal(invocation.source, "installed");

    await testDocumentCorrection(api);
    await testSelectionCorrection(api);
    await testAdviceWithoutMutation(api);
    await testRefusalWithoutMutation(api);
    await testEnterCorrection(api);
    await testInvalidInterpreter(api, configuration);
    await testWrongInterpreter(api, configuration);
    await testTimeout(api, configuration);
    await configuration.update("pythonCommand", "", vscode.ConfigurationTarget.Global);

    process.stdout.write(`PREFIX_VSCODE_HOST_PROOF_OK ${JSON.stringify({
        extension: EXTENSION_ID,
        invocation,
        vscode: vscode.version,
    })}\n`);
}

async function testDocumentCorrection(api) {
    const editor = await showPython("if ready\nprint('launch')\n");
    await vscode.commands.executeCommand("prefixPython.correctDocument");
    assert.match(editor.document.getText(), /^if ready:\n    print\('launch'\)/m);
    assert.equal(api.getLastOutcome().status, "ACCEPT_FIXED");
    assert.ok(api.getLastGovernanceSurface().some((line) => line.includes("Governing law:")));
}

async function testSelectionCorrection(api) {
    const editor = await showPython("if selected\nprint('yes')\n\nprint('outside')\n");
    editor.selection = new vscode.Selection(new vscode.Position(0, 0), new vscode.Position(2, 0));
    await vscode.commands.executeCommand("prefixPython.correctSelection");
    assert.match(editor.document.getText(), /^if selected:\n    print\('yes'\)/m);
    assert.match(editor.document.getText(), /print\('outside'\)/);
    assert.equal(api.getLastOutcome().status, "ACCEPT_FIXED");
}

async function testAdviceWithoutMutation(api) {
    const source = "elif ready:\n    print('x')\n";
    const editor = await showPython(source);
    await vscode.commands.executeCommand("prefixPython.correctDocument");
    assert.equal(editor.document.getText(), source);
    assert.equal(api.getLastOutcome().state, "ADVISED");
    assert.equal(api.getLastOutcome().lane, "ADVISE");
}

async function testRefusalWithoutMutation(api) {
    const source = "return 1\n";
    const editor = await showPython(source);
    await vscode.commands.executeCommand("prefixPython.correctDocument");
    assert.equal(editor.document.getText(), source);
    assert.equal(api.getLastOutcome().state, "REFUSED");
    assert.equal(api.getLastOutcome().refusal_code, "return_outside_function");
}

async function testEnterCorrection(api) {
    const editor = await showPython("if ready");
    editor.selection = new vscode.Selection(new vscode.Position(0, 8), new vscode.Position(0, 8));
    await vscode.commands.executeCommand("type", { text: "\n" });
    assert.ok(editor.document.lineCount >= 2, `Enter command did not insert a line: ${JSON.stringify(editor.document.getText())}`);
    await waitFor(
        () => api.getLastOutcome() && api.getLastOutcome().status === "ACCEPT_FIXED",
        60000,
        () => ({ text: editor.document.getText(), selection: editor.selection.active, outcome: api.getLastOutcome(), error: api.getLastEngineError() }),
    );
    assert.match(editor.document.getText(), /^if ready:\r?\n\s+pass/m);
}

async function testInvalidInterpreter(api, configuration) {
    const missing = process.platform === "win32" ? "C:\\PREFIX-MISSING\\python.exe" : "/prefix-missing/python3.12";
    await configuration.update("pythonCommand", missing, vscode.ConfigurationTarget.Global);
    await showPython("print('x')\n");
    await vscode.commands.executeCommand("prefixPython.correctDocument");
    assert.match(api.getLastEngineError(), /could not start its CPython 3\.12 engine/i);
    assert.equal(api.getLastOutcome(), null);
}

async function testWrongInterpreter(api, configuration) {
    const command = process.env.PREFIX_WRONG_ENGINE;
    assert.ok(command, "PREFIX_WRONG_ENGINE is required");
    await configuration.update("pythonCommand", command, vscode.ConfigurationTarget.Global);
    await showPython("print('x')\n");
    await vscode.commands.executeCommand("prefixPython.correctDocument");
    assert.match(api.getLastEngineError(), /unreadable response/i);
    assert.equal(api.getLastOutcome(), null);
}

async function testTimeout(api, configuration) {
    const command = process.env.PREFIX_TIMEOUT_ENGINE;
    assert.ok(command, "PREFIX_TIMEOUT_ENGINE is required");
    await configuration.update("pythonCommand", command, vscode.ConfigurationTarget.Global);
    await showPython("print('x')\n");
    const started = Date.now();
    await vscode.commands.executeCommand("prefixPython.correctDocument");
    assert.ok(Date.now() - started >= 4500, "timeout returned before its bounded deadline");
    assert.match(api.getLastEngineError(), /timed out/i);
    assert.equal(api.getLastOutcome(), null);
}

async function showPython(content) {
    const document = await vscode.workspace.openTextDocument({ language: "python", content });
    return vscode.window.showTextDocument(document);
}

async function waitFor(predicate, timeoutMs, diagnostic = () => null) {
    const started = Date.now();
    while (!predicate()) {
        if (Date.now() - started > timeoutMs) {
            throw new Error(`condition not reached within ${timeoutMs} ms: ${JSON.stringify(diagnostic())}`);
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
    }
}

module.exports = { run };
