"use strict";

const assert = require("node:assert/strict");
const vscode = require("vscode");
const { execFileSync } = require("node:child_process");
const path = require("node:path");
const fs = require("node:fs");

const EXTENSION_ID = "fastindustries.prefix-python";

async function run() {
    const cases = [];
    async function check(name, operation) {
        await operation();
        cases.push({ name, passed: true });
    }
    const extension = vscode.extensions.getExtension(EXTENSION_ID);
    assert.ok(extension, `${EXTENSION_ID} is not installed`);
    const api = await extension.activate();
    assert.ok(api, "PREFIX extension did not expose its qualification API");
    const commands = new Set(await vscode.commands.getCommands(true));
    await check("commands_and_purchase_route", async () => { for (const command of [
        "prefixPython.correctDocument",
        "prefixPython.correctSelection",
        "prefixPython.showGovernanceSurface",
        "prefixPython.licenseStatus",
        "prefixPython.activateLicense",
        "prefixPython.deactivateLicense",
        "prefixPython.buyPrefix",
    ]) {
        assert.ok(commands.has(command), `missing command: ${command}`);
    }
    assert.equal(extension.packageJSON.contributes.configuration.properties["prefixPython.purchaseUrl"].default,
        "https://fastlaunch.lemonsqueezy.com/checkout/buy/37f6bf48-4f0d-4151-a076-8b60f030e985");
    });

    const configuration = vscode.workspace.getConfiguration("prefixPython");
    await configuration.update("pythonCommand", "", vscode.ConfigurationTarget.Global);
    await configuration.update("enableOnEnter", true, vscode.ConfigurationTarget.Global);
    const invocation = api.getResolvedInvocation();
    await check("installed_runtime_discovery", async () => assert.equal(invocation.source, "installed"));

    for (const [fixture,expected] of [["unactivated","UNACTIVATED"],["invalid","CACHE_INVALID"],["expired","CACHE_EXPIRED"]]) {
        await check(`entitlement_denial_${fixture}`, async () => {
            configureFixture(invocation, fixture);
            const status=await vscode.commands.executeCommand("prefixPython.licenseStatus");
            assert.equal(status.state,expected);
            assert.equal(status.entitled,false);
            const source="if ready\nprint('launch')\n";
            const editor=await showPython(source);
            await vscode.commands.executeCommand("prefixPython.correctDocument");
            assert.equal(editor.document.getText(),source);
            const outcome=api.getLastOutcome();
            assert.ok(outcome, api.getLastEngineError());
            assert.equal(outcome.refusal_code,"entitlement_required");
            assert.equal(outcome.mutation_performed,false);
            assert.equal(outcome.source,source);
        });
    }
    await check("synthetic_activation_cached_status", async () => {
        configureFixture(invocation,"active");
        const status=await vscode.commands.executeCommand("prefixPython.licenseStatus");
        assert.equal(status.state,"ACTIVE_CACHED");
        assert.equal(status.entitled,true);
    });
    await check("document_correction",()=>testDocumentCorrection(api));
    await check("selection_correction",()=>testSelectionCorrection(api));
    await check("advice_without_mutation",()=>testAdviceWithoutMutation(api));
    await check("structural_refusal_without_mutation",()=>testRefusalWithoutMutation(api));
    await check("enter_correction",()=>testEnterCorrection(api));
    await check("literal_preservation",()=>testPreservesLiteralData(api));
    await check("concurrent_typing_preserved",()=>testConcurrentTyping(api, configuration));
    await check("missing_interpreter",()=>testInvalidInterpreter(api, configuration));
    await check("wrong_interpreter",()=>testWrongInterpreter(api, configuration));
    await check("engine_timeout",()=>testTimeout(api, configuration));
    await configuration.update("pythonCommand", "", vscode.ConfigurationTarget.Global);

    const proof={
        extension: EXTENSION_ID,
        invocation,
        vscode: vscode.version,
        cases,
        synthetic_entitlement_only:true,
        live_activation_verified:false,
        interactive_password_input_verified:false,
        passed:cases.length===16 && cases.every(test=>test.passed)
    };
    if (process.env.PREFIX_HOST_CASE_REPORT) fs.writeFileSync(process.env.PREFIX_HOST_CASE_REPORT,JSON.stringify(proof,null,2)+"\n");
    process.stdout.write(`PREFIX_VSCODE_HOST_PROOF_OK ${JSON.stringify(proof)}\n`);
}

function configureFixture(invocation, scenario) {
    assert.ok(process.env.PREFIX_ENTITLEMENT_ROOT,"isolated entitlement root is required");
    const raw=execFileSync(invocation.command,[...invocation.prefixArgs,path.join(__dirname,"..","entitlement_fixture.py"),scenario],{encoding:"utf8"});
    const fixture=JSON.parse(raw);
    assert.equal(fixture.synthetic,true);
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

async function testPreservesLiteralData(api) {
    const source = 'value = "a\tb"\n';
    const editor = await showPython(source);
    await vscode.commands.executeCommand("prefixPython.correctDocument");
    assert.equal(editor.document.getText(), source);
    assert.equal(api.getLastOutcome().status, "ACCEPT_VALID");
}

async function testConcurrentTyping(api, configuration) {
    await configuration.update("enableOnEnter", false, vscode.ConfigurationTarget.Global);
    const source = "if True\n    print('x')\n" + "value = 1\n".repeat(4000);
    const editor = await showPython(source);
    const pending = vscode.commands.executeCommand("prefixPython.correctDocument");
    // The real command has spawned the real packaged engine; change the document
    // before its asynchronous result returns. No replacement engine is used.
    await new Promise(resolve => setTimeout(resolve, 20));
    const marker = "# newer customer typing\n";
    assert.equal(await editor.edit(builder => builder.insert(new vscode.Position(0, 0), marker)), true);
    await pending;
    assert.equal(editor.document.getText(), marker + source);
    assert.match(api.getLastEngineError(), /document_changed/);
    assert.equal(api.getLastOutcome(), null);
    await configuration.update("enableOnEnter", true, vscode.ConfigurationTarget.Global);
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
