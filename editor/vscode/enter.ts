import { EngineResponse } from "./response";

export type EnterChange = {
    text: string;
    rangeLength: number;
};

export type EnterCorrectionPlan = {
    cursorLine: number;
    reason: "missing_colon_header";
    targetLine: number;
};

export type EnterCorrectionInput = {
    activeDocumentId: string;
    changeCount: number;
    changes: EnterChange[];
    cursorLine: number;
    documentId: string;
    documentInFlight: boolean;
    documentText: string;
    enableOnEnter: boolean;
    hasSelection: boolean;
    languageId: string;
    selectionCount: number;
};

const DIRECT_HEADER_PREFIXES = [
    "if",
    "elif",
    "else",
    "for",
    "while",
    "def",
    "class",
    "try",
    "except",
    "except*",
    "finally",
    "with",
    "match",
    "case",
] as const;

const ASYNC_HEADER_PREFIXES = [
    "async def",
    "async for",
    "async with",
] as const;

const ENTER_ALLOWED_RULES = new Set([
    "AUTO_INDENT",
    "INSERT_PASS",
    "MISSING_COLON",
    "NORMALIZE_TABS",
]);

export function buildEnterCorrectionPlan(input: EnterCorrectionInput): EnterCorrectionPlan | null {
    if (input.languageId !== "python") {
        return null;
    }

    if (input.activeDocumentId !== input.documentId) {
        return null;
    }

    if (!input.enableOnEnter || input.documentInFlight) {
        return null;
    }

    if (input.selectionCount !== 1 || input.hasSelection) {
        return null;
    }

    if (input.changeCount !== 1 || input.changes.length !== 1) {
        return null;
    }

    const change = input.changes[0];
    if (change.rangeLength !== 0 || !isSingleEnterInsertion(change.text)) {
        return null;
    }

    if (input.cursorLine <= 0) {
        return null;
    }

    const normalized = normalizeNewlines(input.documentText);
    if (isInsideTripleQuotedString(normalized, input.cursorLine)) {
        return null;
    }

    const lines = normalized.split("\n");
    const previousLine = lines[input.cursorLine - 1] ?? "";
    const currentLine = lines[input.cursorLine] ?? "";
    if (!isMissingColonHeader(previousLine)) {
        return null;
    }

    if (!hasBalancedInlineDelimiters(previousLine)) {
        return null;
    }

    if (previousLine.trimEnd().endsWith("\\")) {
        return null;
    }

    if (currentLine.trim().length > 0) {
        return null;
    }

    return {
        cursorLine: input.cursorLine,
        reason: "missing_colon_header",
        targetLine: input.cursorLine - 1,
    };
}

export function shouldApplyEnterMutation(response: EngineResponse, plan: EnterCorrectionPlan): boolean {
    if (response.status !== "ACCEPT_FIXED") {
        return false;
    }

    if (response.events.length === 0) {
        return false;
    }

    let sawMissingColon = false;
    for (const event of response.events) {
        if (!ENTER_ALLOWED_RULES.has(event.rule_id)) {
            return false;
        }
        if (event.line < plan.targetLine + 1 || event.line > plan.cursorLine + 1) {
            return false;
        }
        if (event.rule_id === "MISSING_COLON") {
            sawMissingColon = true;
        }
    }
    return sawMissingColon;
}

function isSingleEnterInsertion(text: string): boolean {
    if (!text.includes("\n")) {
        return false;
    }
    const normalized = text.replace("\r\n", "\n").replace("\r", "\n");
    if (normalized.split("\n").length !== 2) {
        return false;
    }
    const [, trailing] = normalized.split("\n");
    return /^[ \t]*$/.test(trailing);
}

function isMissingColonHeader(line: string): boolean {
    const stripped = line.trim();
    if (!stripped || stripped.endsWith(":") || stripped.startsWith("#")) {
        return false;
    }
    return matchHeaderPrefix(stripped) !== null;
}

function matchHeaderPrefix(stripped: string): string | null {
    for (const prefix of ASYNC_HEADER_PREFIXES) {
        if (stripped === prefix || stripped.startsWith(`${prefix} `)) {
            return prefix;
        }
    }
    for (const prefix of DIRECT_HEADER_PREFIXES) {
        if (stripped === prefix || stripped.startsWith(`${prefix} `)) {
            return prefix;
        }
    }
    return null;
}

function hasBalancedInlineDelimiters(line: string): boolean {
    const stack: string[] = [];
    const openToClose: Record<string, string> = { "(": ")", "[": "]", "{": "}" };
    let escape = false;
    let inSingle = false;
    let inDouble = false;

    for (const character of line) {
        if (escape) {
            escape = false;
            continue;
        }
        if (character === "\\") {
            escape = true;
            continue;
        }
        if (character === "'" && !inDouble) {
            inSingle = !inSingle;
            continue;
        }
        if (character === "\"" && !inSingle) {
            inDouble = !inDouble;
            continue;
        }
        if (inSingle || inDouble) {
            continue;
        }
        if (character in openToClose) {
            stack.push(character);
            continue;
        }
        if (character === ")" || character === "]" || character === "}") {
            const previous = stack.at(-1);
            if (!previous || openToClose[previous] !== character) {
                return false;
            }
            stack.pop();
        }
    }

    return stack.length === 0 && !inSingle && !inDouble;
}

function isInsideTripleQuotedString(documentText: string, cursorLine: number): boolean {
    const lines = documentText.split("\n");
    const prefix = lines.slice(0, cursorLine).join("\n");
    const single = countTripleQuotes(prefix, "'''");
    const double = countTripleQuotes(prefix, "\"\"\"");
    return single % 2 === 1 || double % 2 === 1;
}

function countTripleQuotes(source: string, triple: string): number {
    let count = 0;
    let index = 0;
    while (true) {
        const matchIndex = source.indexOf(triple, index);
        if (matchIndex === -1) {
            return count;
        }
        count += 1;
        index = matchIndex + triple.length;
    }
}

function normalizeNewlines(source: string): string {
    return source.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}
