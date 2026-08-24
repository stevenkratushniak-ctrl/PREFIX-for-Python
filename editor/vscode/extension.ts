import * as vscode from "vscode";
import { spawn } from "node:child_process";
import { buildEnterCorrectionPlan, EnterCorrectionPlan, shouldApplyEnterMutation } from "./enter";
import {
    buildWhySurface,
    buildOutcomeMessage,
    EngineResponse,
    isAdvisedOutcome,
    shouldApplyMutation,
} from "./response";

export function activate(context: vscode.ExtensionContext) {
    const output = vscode.window.createOutputChannel("PREFIX for Python");
    const inFlightDocuments = new Set<string>();
    let lastGovernanceSurface: string[] | null = null;
    const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    setStatus(statusItem, "ready");
    statusItem.show();

    const correctDocument = vscode.commands.registerCommand("prefixPython.correctDocument", async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== "python") {
            void vscode.window.showWarningMessage("PREFIX expects an active Python document.");
            return;
        }

        lastGovernanceSurface = await applyCorrection(editor, output, false, inFlightDocuments, statusItem, "manual");
    });

    const correctSelection = vscode.commands.registerCommand("prefixPython.correctSelection", async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== "python") {
            void vscode.window.showWarningMessage("PREFIX expects an active Python document.");
            return;
        }

        if (editor.selections.length !== 1 || editor.selection.isEmpty) {
            void vscode.window.showWarningMessage("PREFIX selection correction requires one explicit Python selection.");
            return;
        }

        lastGovernanceSurface = await applyCorrection(editor, output, true, inFlightDocuments, statusItem, "manual");
    });

    const showGovernanceSurface = vscode.commands.registerCommand("prefixPython.showGovernanceSurface", () => {
        if (!lastGovernanceSurface) {
            void vscode.window.showInformationMessage("PREFIX has no transition governance surface yet. Run PREFIX on Python text first.");
            return;
        }
        output.appendLine("");
        output.appendLine("Last PREFIX governance surface");
        output.appendLine("--------------------------------");
        for (const line of lastGovernanceSurface) {
            output.appendLine(line);
        }
        output.show(true);
    });

    const onDidChange = vscode.workspace.onDidChangeTextDocument(async (event) => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return;
        }

        const enterPlan = buildEnterCorrectionPlan({
            activeDocumentId: editor.document.uri.toString(),
            changeCount: event.contentChanges.length,
            changes: event.contentChanges.map((change) => ({
                rangeLength: change.rangeLength,
                text: change.text,
            })),
            cursorLine: editor.selection.active.line,
            documentId: event.document.uri.toString(),
            documentInFlight: inFlightDocuments.has(event.document.uri.toString()),
            documentText: event.document.getText(),
            enableOnEnter: vscode.workspace.getConfiguration("prefixPython").get<boolean>("enableOnEnter", true),
            hasSelection: !editor.selection.isEmpty,
            languageId: event.document.languageId,
            selectionCount: editor.selections.length,
        });
        if (!enterPlan) {
            return;
        }

        const governanceSurface = await applyCorrection(editor, output, false, inFlightDocuments, statusItem, "enter", enterPlan);
        if (governanceSurface) {
            lastGovernanceSurface = governanceSurface;
        }
    });

    context.subscriptions.push(output, statusItem, correctDocument, correctSelection, showGovernanceSurface, onDidChange);
}

async function applyCorrection(
    editor: vscode.TextEditor,
    output: vscode.OutputChannel,
    selectionOnly: boolean,
    inFlightDocuments: Set<string>,
    statusItem: vscode.StatusBarItem,
    invocationSurface: "manual" | "enter",
    enterPlan?: EnterCorrectionPlan,
): Promise<string[] | null> {
    const documentKey = editor.document.uri.toString();
    if (inFlightDocuments.has(documentKey)) {
        if (invocationSurface === "manual") {
            void vscode.window.showInformationMessage("PREFIX is already processing this document.");
        }
        return null;
    }

    inFlightDocuments.add(documentKey);
    setStatus(statusItem, "working");
    const selection = editor.selection;
    if (selectionOnly && selection.isEmpty) {
        setStatus(statusItem, "refused", "Selection correction requires explicit text");
        if (invocationSurface === "manual") {
            void vscode.window.showWarningMessage("PREFIX selection correction requires explicit Python text.");
        }
        return null;
    }
    const source = selectionOnly && !selection.isEmpty
        ? editor.document.getText(selection)
        : editor.document.getText();

    try {
        const response = await runEngine(source, editor.document.uri.fsPath, output);
        if (!response) {
            setStatus(statusItem, "refused", "Engine unavailable");
            return null;
        }

        if (response.status === "ACCEPT_VALID") {
            emitProofSurface(output, response);
            setStatus(statusItem, "ready", "Lawful Python state");
            if (invocationSurface === "manual") {
                void vscode.window.showInformationMessage(buildOutcomeMessage(response));
            }
            return buildWhySurface(response).lines;
        }

        if (isAdvisedOutcome(response)) {
            const message = buildOutcomeMessage(response);
            output.appendLine(message);
            emitRecommendationSurface(output, response);
            emitProofSurface(output, response);
            const recommendation = response.recommendation_packet;
            setStatus(
                statusItem,
                "advised",
                recommendation
                    ? `${recommendation.recommended_rule_id} line ${recommendation.recommended_line}`
                    : "Ranked Python continuations available",
            );
            if (invocationSurface === "manual") {
                output.show(true);
                void vscode.window.showInformationMessage(message);
            }
            return buildWhySurface(response).lines;
        }

        if (!shouldApplyMutation(response)) {
            const message = buildOutcomeMessage(response);
            output.appendLine(message);
            emitProofSurface(output, response);
            if (response.syntax_error) {
                output.appendLine(response.syntax_error);
            }
            for (const candidate of response.candidates ?? []) {
                output.appendLine(`Candidate ${candidate.rule_id} line ${candidate.line}: ${candidate.reason}`);
            }
            setStatus(statusItem, "refused", response.refusal_code ?? response.status);
            if (invocationSurface === "manual") {
                output.show(true);
                void vscode.window.showWarningMessage(message);
            }
            return buildWhySurface(response).lines;
        }

        if (invocationSurface === "enter" && enterPlan && !shouldApplyEnterMutation(response, enterPlan)) {
            output.appendLine("PREFIX refused the Enter-trigger mutation because the transition exceeded the bounded line-local Python surface.");
            emitProofSurface(output, response);
            setStatus(statusItem, "refused", "Enter correction exceeded bounded surface");
            return buildWhySurface(response).lines;
        }

        await editor.edit((editBuilder) => {
            if (selectionOnly && !selection.isEmpty) {
                editBuilder.replace(selection, response.source);
                return;
            }

            const fullRange = new vscode.Range(
                editor.document.positionAt(0),
                editor.document.positionAt(editor.document.getText().length),
            );
            editBuilder.replace(fullRange, response.source);
        });

        if (invocationSurface === "enter" && enterPlan) {
            placeEnterSelection(editor, response, enterPlan);
        }

        emitProofSurface(output, response);
        const eventSummary = response.events.map((event) => event.rule_id).join(", ");
        setStatus(statusItem, "fixed", eventSummary || "Deterministic prefix correction");
        if (invocationSurface === "manual") {
            void vscode.window.showInformationMessage(buildOutcomeMessage(response));
        }
        return buildWhySurface(response).lines;
    } finally {
        inFlightDocuments.delete(documentKey);
    }
}

async function runEngine(
    source: string,
    documentPath: string,
    output: vscode.OutputChannel,
): Promise<EngineResponse | null> {
    const config = vscode.workspace.getConfiguration("prefixPython");
    const pythonCommand = config.get<string>("pythonCommand", "python");
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

    return new Promise((resolve) => {
        const child = spawn(
            pythonCommand,
            ["-m", "prefix_python", "--stdin", "--json"],
            {
                cwd,
                shell: false,
            },
        );
        const timeoutHandle = setTimeout(() => {
            child.kill();
            const message = `PREFIX timed out while processing ${documentPath}.`;
            output.appendLine(message);
            output.show(true);
            void vscode.window.showErrorMessage(message);
            resolve(null);
        }, 5000);

        let stdout = "";
        let stderr = "";

        child.stdout.on("data", (chunk) => {
            stdout += chunk.toString();
        });

        child.stderr.on("data", (chunk) => {
            stderr += chunk.toString();
        });

        child.on("error", (error) => {
            clearTimeout(timeoutHandle);
            const message = `PREFIX could not start the local engine for ${documentPath}: ${error.message}`;
            output.appendLine(message);
            output.show(true);
            void vscode.window.showErrorMessage(message);
            resolve(null);
        });

        child.on("close", () => {
            clearTimeout(timeoutHandle);
            if (stderr.trim()) {
                output.appendLine(stderr.trim());
            }

            try {
                const parsed = JSON.parse(stdout) as EngineResponse;
                resolve(parsed);
            } catch {
                const message = "PREFIX returned an unreadable response. Confirm that `prefix-python` is installed in the configured interpreter.";
                output.appendLine(stdout.trim());
                output.appendLine(message);
                output.show(true);
                void vscode.window.showErrorMessage(message);
                resolve(null);
            }
        });

        child.stdin.write(source);
        child.stdin.end();
    });
}

export function deactivate() {}

function emitProofSurface(output: vscode.OutputChannel, response: EngineResponse): void {
    const whySurface = buildWhySurface(response);
    output.appendLine("");
    output.appendLine(whySurface.summary);
    for (const line of whySurface.lines) {
        output.appendLine(line);
    }
    output.appendLine("");
    output.appendLine(`State: ${response.state}`);
    output.appendLine(`Lane: ${response.lane}`);
    if (response.structural_context) {
        output.appendLine(`Surface class: ${response.structural_context.surface_class}`);
        output.appendLine(`Governing law: ${response.structural_context.governing_law}`);
        output.appendLine(`Locality: ${response.structural_context.locality}`);
    }
    if (response.refusal_code) {
        output.appendLine(`Refusal code: ${response.refusal_code}`);
    }
    if (response.ast_sha256) {
        output.appendLine(`AST sha256: ${response.ast_sha256}`);
    }
    if (response.token_sha256) {
        output.appendLine(`Token sha256: ${response.token_sha256}`);
    }
    if (response.parse_reparse_validated !== undefined) {
        output.appendLine(`Parse/reparse validated: ${response.parse_reparse_validated}`);
    }
    if (response.legality_report) {
        output.appendLine(
            `Legality report: nodes=${response.legality_report.node_count}, edges=${response.legality_report.edge_count}, tokens=${response.legality_report.token_count}, violations=${response.legality_report.violation_count}`,
        );
    }
    if (response.legality_score) {
        output.appendLine(`Legality score: ${response.legality_score.score}`);
    }
    if (response.continuation_graph) {
        output.appendLine(`Continuation count: ${response.continuation_graph.successor_count}`);
    }
    if (response.transition_governance) {
        output.appendLine(`Transition witness: ${response.transition_governance.transition_witness_root_sha256}`);
    }
}

function emitRecommendationSurface(output: vscode.OutputChannel, response: EngineResponse): void {
    const packet = response.recommendation_packet;
    if (!packet) {
        return;
    }
    output.appendLine(`Recommendation packet sha256: ${packet.packet_sha256}`);
    output.appendLine(`Ranking model: ${packet.ranking_model}`);
    output.appendLine(
        `Top recommendation: ${packet.recommended_rule_id} line ${packet.recommended_line} column ${packet.recommended_column} score ${packet.recommended_score}`,
    );
    output.appendLine(packet.summary);
    for (const candidate of response.candidates ?? []) {
        output.appendLine(
            `Candidate #${candidate.rank ?? 0}: ${candidate.rule_id} line ${candidate.line} column ${candidate.column ?? 0} score ${candidate.score ?? 0}`,
        );
    }
}

function placeEnterSelection(
    editor: vscode.TextEditor,
    response: EngineResponse,
    plan: EnterCorrectionPlan,
): void {
    const insertPassEvent = response.events.find((event) => event.rule_id === "INSERT_PASS");
    if (insertPassEvent) {
        const lineIndex = insertPassEvent.line - 1;
        if (lineIndex < editor.document.lineCount) {
            const text = editor.document.lineAt(lineIndex).text;
            const firstNonWhitespace = text.search(/\S|$/);
            const passStart = text.slice(firstNonWhitespace).startsWith("pass") ? firstNonWhitespace : text.length;
            const passEnd = text.slice(passStart).startsWith("pass") ? passStart + 4 : text.length;
            const anchor = new vscode.Position(lineIndex, passStart);
            const active = new vscode.Position(lineIndex, passEnd);
            editor.selection = new vscode.Selection(anchor, active);
            editor.revealRange(new vscode.Range(anchor, active));
            return;
        }
    }

    const targetLineIndex = Math.min(plan.cursorLine, editor.document.lineCount - 1);
    if (targetLineIndex < 0) {
        return;
    }
    const text = editor.document.lineAt(targetLineIndex).text;
    const firstNonWhitespace = text.search(/\S|$/);
    const position = new vscode.Position(targetLineIndex, firstNonWhitespace);
    editor.selection = new vscode.Selection(position, position);
    editor.revealRange(new vscode.Range(position, position));
}

function setStatus(
    statusItem: vscode.StatusBarItem,
    state: "ready" | "working" | "fixed" | "advised" | "refused",
    detail?: string,
): void {
    switch (state) {
        case "ready":
            statusItem.text = "$(shield) PREFIX ready";
            statusItem.tooltip = detail
                ? `PREFIX for Python\n${detail}`
                : "PREFIX for Python\nLawful Python structure is ready to continue.";
            return;
        case "working":
            statusItem.text = "$(sync~spin) PREFIX working";
            statusItem.tooltip = "PREFIX for Python\nEvaluating the current Python structure locally.";
            return;
        case "fixed":
            statusItem.text = "$(check) PREFIX governed";
            statusItem.tooltip = detail
                ? `PREFIX for Python\n${detail}`
                : "PREFIX for Python\nA deterministic governed transition was applied.";
            return;
        case "advised":
            statusItem.text = "$(lightbulb) PREFIX advised";
            statusItem.tooltip = detail
                ? `PREFIX for Python\n${detail}`
                : "PREFIX for Python\nRanked Python continuations are available and no mutation was applied.";
            return;
        case "refused":
            statusItem.text = "$(warning) PREFIX refused";
            statusItem.tooltip = detail
                ? `PREFIX for Python\n${detail}`
                : "PREFIX for Python\nNo lawful deterministic continuation was available.";
            return;
    }
}
