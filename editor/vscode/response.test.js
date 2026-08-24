const assert = require("node:assert/strict");
const { buildEnterCorrectionPlan, shouldApplyEnterMutation } = require("./out/enter.js");
const {
    buildOutcomeMessage,
    buildWhySurface,
    isAdvisedOutcome,
    isAnalyzeOutcome,
    shouldApplyMutation,
} = require("./out/response.js");

const acceptedFixed = {
    lane: "APPLY",
    state: "APPLIED",
    status: "ACCEPT_FIXED",
    source: "if ready:\n    print('x')\n",
    events: [{ rule_id: "MISSING_COLON", line: 1, before: "if ready", after: "if ready:", reason: "..." }],
    mutation_performed: true,
    parse_reparse_validated: true,
    structural_context: {
        event_count: 1,
        governing_law: "single_lawful_continuation",
        lane: "APPLY",
        locality: "bounded_local",
        source_line_count: 2,
        status: "ACCEPT_FIXED",
        surface_class: "block_header_continuation",
        witness_sha256: "structural",
    },
    continuation_graph: {
        continuation_kind: "apply",
        graph_sha256: "graph",
        successor_count: 1,
        successors: [{ kind: "applied_continuation", rank: 1, rule_ids: ["MISSING_COLON"], status: "ACCEPT_FIXED" }],
    },
    transition_governance: {
        continuation_graph_sha256: "graph",
        governing_law: "single_lawful_continuation",
        lane: "APPLY",
        local_mutation_boundary: "line_local_or_bounded_local",
        status: "ACCEPT_FIXED",
        structural_witness_sha256: "structural",
        transition_witness_root_sha256: "witness",
    },
    legality_score: {
        candidate_count: 0,
        event_count: 1,
        governing_law: "single_lawful_continuation",
        parse_reparse_validated: true,
        score: 98,
        score_sha256: "score",
        surface_class: "block_header_continuation",
    },
};

const acceptedValid = {
    lane: "APPLY",
    state: "APPLIED",
    status: "ACCEPT_VALID",
    source: "print('x')\n",
    events: [],
};

const advised = {
    lane: "ADVISE",
    state: "ADVISED",
    status: "REFUSE_UNMAPPED",
    source: "elif ready:\n    print('x')\n",
    events: [],
    candidates: [{ rule_id: "ELIF_TO_IF_CANDIDATE", line: 1, before: "elif ready:", after: "if ready:", reason: "...", rank: 1, score: 79989, column: 1 }],
    mutation_performed: false,
    structural_context: {
        event_count: 0,
        governing_law: "multiple_lawful_continuations",
        lane: "ADVISE",
        locality: "bounded_local",
        source_line_count: 2,
        status: "REFUSE_UNMAPPED",
        surface_class: "block_header_continuation",
        witness_sha256: "advice-structural",
    },
    continuation_graph: {
        continuation_kind: "advise",
        graph_sha256: "advice-graph",
        successor_count: 1,
        successors: [{ kind: "advised_continuation", rank: 1, rule_id: "ELIF_TO_IF_CANDIDATE", line: 1, column: 1, score: 79989 }],
    },
    recommendation_packet: {
        auto_apply_allowed: false,
        candidate_count: 1,
        packet_sha256: "abc123",
        ranking_model: "prefix-python-deterministic-lane-v1",
        recommended_after: "if ready:",
        recommended_column: 1,
        recommended_line: 1,
        recommended_rule_id: "ELIF_TO_IF_CANDIDATE",
        recommended_score: 79989,
        summary: "Candidates are ranked deterministically by Python rule precedence, edit locality, and canonical tie-breakers. ADVISED never mutates code automatically.",
    },
};

const analyzed = {
    lane: "ANALYZE",
    state: "REFUSED",
    status: "REFUSE_UNMAPPED",
    source: "value =\n",
    refusal_reason: "PREFIX analyzed the transition and refused automatic mutation because completing an assignment without a right-hand side would require a semantic default-value guess.",
    events: [],
};

const refusedRoadmap = {
    lane: "ROADMAP",
    state: "REFUSED",
    status: "REFUSE_INVALID",
    source: "return 1\n",
    refusal_reason: "PREFIX refused the transition because `return` outside a function has no lawful deterministic repair.",
    events: [],
};

const enterPlan = buildEnterCorrectionPlan({
    activeDocumentId: "doc.py",
    changeCount: 1,
    changes: [{ rangeLength: 0, text: "\n" }],
    cursorLine: 1,
    documentId: "doc.py",
    documentInFlight: false,
    documentText: "if ready\n",
    enableOnEnter: true,
    hasSelection: false,
    languageId: "python",
    selectionCount: 1,
});

assert.equal(shouldApplyMutation(acceptedFixed), true);
assert.equal(shouldApplyMutation(acceptedValid), false);
assert.equal(shouldApplyMutation(advised), false);
assert.equal(shouldApplyMutation(analyzed), false);

assert.equal(isAdvisedOutcome(advised), true);
assert.equal(isAnalyzeOutcome(analyzed), true);
assert.equal(isAnalyzeOutcome(refusedRoadmap), false);

assert.match(buildOutcomeMessage(acceptedFixed), /ALWAYS_SAFE Python governed transition/i);
assert.match(buildOutcomeMessage(acceptedValid), /already lawful/i);
assert.match(buildOutcomeMessage(advised), /advised ranked Python continuations/i);
assert.match(buildOutcomeMessage(analyzed), /analyzed the Python state/i);
assert.match(buildOutcomeMessage(refusedRoadmap), /outside a function/i);

const appliedWhy = buildWhySurface(acceptedFixed);
assert.match(appliedWhy.summary, /PREFIX APPLIED \/ APPLY/i);
assert.ok(appliedWhy.lines.some((line) => line.includes("Governing law: single_lawful_continuation")));
assert.ok(appliedWhy.lines.some((line) => line.includes("Continuation cardinality: 1")));
assert.ok(appliedWhy.lines.some((line) => line.includes("Witness lineage: witness")));
assert.ok(appliedWhy.lines.some((line) => line.includes("Structural delta: if ready => if ready:")));

const advisedWhy = buildWhySurface(advised);
assert.match(advisedWhy.summary, /PREFIX ADVISED \/ ADVISE/i);
assert.ok(advisedWhy.lines.some((line) => line.includes("Automatic mutation from ADVISE: forbidden")));
assert.ok(advisedWhy.lines.some((line) => line.includes("Candidate structural delta: elif ready: => if ready:")));

assert.deepEqual(enterPlan, {
    cursorLine: 1,
    reason: "missing_colon_header",
    targetLine: 0,
});

assert.equal(
    buildEnterCorrectionPlan({
        activeDocumentId: "doc.py",
        changeCount: 1,
        changes: [{ rangeLength: 0, text: "\n" }],
        cursorLine: 1,
        documentId: "doc.py",
        documentInFlight: false,
        documentText: "if ready:\n",
        enableOnEnter: true,
        hasSelection: false,
        languageId: "python",
        selectionCount: 1,
    }),
    null,
);

assert.deepEqual(
    buildEnterCorrectionPlan({
        activeDocumentId: "doc.py",
        changeCount: 1,
        changes: [{ rangeLength: 0, text: "\n" }],
        cursorLine: 1,
        documentId: "doc.py",
        documentInFlight: false,
        documentText: "async def build()\n",
        enableOnEnter: true,
        hasSelection: false,
        languageId: "python",
        selectionCount: 1,
    }),
    {
        cursorLine: 1,
        reason: "missing_colon_header",
        targetLine: 0,
    },
);

assert.equal(
    buildEnterCorrectionPlan({
        activeDocumentId: "doc.py",
        changeCount: 1,
        changes: [{ rangeLength: 0, text: "\n" }],
        cursorLine: 1,
        documentId: "doc.py",
        documentInFlight: false,
        documentText: "def build(\n",
        enableOnEnter: true,
        hasSelection: false,
        languageId: "python",
        selectionCount: 1,
    }),
    null,
);

assert.equal(
    buildEnterCorrectionPlan({
        activeDocumentId: "doc.py",
        changeCount: 1,
        changes: [{ rangeLength: 0, text: "\n" }],
        cursorLine: 2,
        documentId: "doc.py",
        documentInFlight: false,
        documentText: "\"\"\"\nif ready\n",
        enableOnEnter: true,
        hasSelection: false,
        languageId: "python",
        selectionCount: 1,
    }),
    null,
);

assert.equal(
    buildEnterCorrectionPlan({
        activeDocumentId: "doc.py",
        changeCount: 1,
        changes: [{ rangeLength: 0, text: "\n" }],
        cursorLine: 1,
        documentId: "doc.py",
        documentInFlight: false,
        documentText: "if ready\\\n",
        enableOnEnter: true,
        hasSelection: false,
        languageId: "python",
        selectionCount: 1,
    }),
    null,
);

assert.equal(
    buildEnterCorrectionPlan({
        activeDocumentId: "doc.py",
        changeCount: 1,
        changes: [{ rangeLength: 0, text: "\n" }],
        cursorLine: 1,
        documentId: "doc.py",
        documentInFlight: false,
        documentText: "if ready\n",
        enableOnEnter: true,
        hasSelection: false,
        languageId: "python",
        selectionCount: 2,
    }),
    null,
);

assert.equal(
    shouldApplyEnterMutation(
        {
            lane: "APPLY",
            state: "APPLIED",
            status: "ACCEPT_FIXED",
            source: "if ready:\n    pass\n",
            events: [
                { rule_id: "MISSING_COLON", line: 1, before: "if ready", after: "if ready:", reason: "..." },
                { rule_id: "INSERT_PASS", line: 2, before: "", after: "    pass", reason: "..." },
            ],
        },
        enterPlan,
    ),
    true,
);

assert.equal(
    shouldApplyEnterMutation(
        {
            lane: "APPLY",
            state: "APPLIED",
            status: "ACCEPT_FIXED",
            source: "print('x')\n",
            events: [{ rule_id: "CLOSE_DELIMITER", line: 1, before: "print('x'", after: "print('x')", reason: "..." }],
        },
        enterPlan,
    ),
    false,
);

console.log("VS Code response behavior tests passed.");
