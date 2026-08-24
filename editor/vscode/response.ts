export type EngineEvent = {
    rule_id: string;
    line: number;
    before: string;
    after: string;
    reason: string;
};

export type EngineCandidate = {
    rule_id: string;
    line: number;
    before: string;
    after: string;
    reason: string;
    column?: number;
    rank?: number;
    score?: number;
};

export type RecommendationPacket = {
    auto_apply_allowed: boolean;
    candidate_count: number;
    packet_sha256: string;
    ranking_model: string;
    recommended_after: string;
    recommended_column: number;
    recommended_line: number;
    recommended_rule_id: string;
    recommended_score: number;
    summary: string;
};

export type WhySurface = {
    summary: string;
    lines: string[];
};

export type EngineResponse = {
    status: "ACCEPT_VALID" | "ACCEPT_FIXED" | "REFUSE_UNMAPPED" | "REFUSE_AMBIGUOUS" | "REFUSE_INVALID";
    state: "APPLIED" | "ADVISED" | "REFUSED";
    lane: "APPLY" | "ADVISE" | "ANALYZE" | "ROADMAP";
    source: string;
    ast_sha256?: string;
    mutation_performed?: boolean;
    token_sha256?: string;
    refusal_code?: string;
    refusal_reason?: string;
    syntax_error?: string;
    parse_reparse_validated?: boolean;
    legality_report?: {
        node_count: number;
        edge_count: number;
        token_count: number;
        violation_count: number;
    } | null;
    legality_score?: {
        candidate_count: number;
        event_count: number;
        governing_law: string;
        parse_reparse_validated: boolean;
        score: number;
        score_sha256: string;
        surface_class: string;
    } | null;
    proof_trace?: Record<string, unknown> | null;
    structural_context?: {
        event_count: number;
        governing_law: string;
        lane: string;
        locality: string;
        refusal_code?: string | null;
        source_line_count: number;
        status: string;
        surface_class: string;
        syntax_error?: string | null;
        witness_sha256: string;
    } | null;
    continuation_graph?: {
        continuation_kind: string;
        graph_sha256: string;
        refusal_code?: string | null;
        successor_count: number;
        successors: Array<Record<string, unknown>>;
    } | null;
    transition_governance?: {
        continuation_graph_sha256: string;
        governing_law: string;
        lane: string;
        local_mutation_boundary: string;
        status: string;
        structural_witness_sha256: string;
        transition_witness_root_sha256: string;
    } | null;
    recommendation_packet?: RecommendationPacket | null;
    events: EngineEvent[];
    candidates?: EngineCandidate[];
};

export function shouldApplyMutation(response: EngineResponse): boolean {
    return response.state === "APPLIED" && response.status === "ACCEPT_FIXED";
}

export function isAdvisedOutcome(response: EngineResponse): boolean {
    return response.state === "ADVISED" && response.lane === "ADVISE";
}

export function isAnalyzeOutcome(response: EngineResponse): boolean {
    return response.state === "REFUSED" && response.lane === "ANALYZE";
}

export function buildOutcomeMessage(response: EngineResponse): string {
    if (isAdvisedOutcome(response)) {
        const packet = response.recommendation_packet;
        if (packet) {
            return `PREFIX advised ranked Python continuations without mutating the buffer. Top recommendation: ${packet.recommended_rule_id} on line ${packet.recommended_line}.`;
        }
        return "PREFIX advised ranked Python continuations without mutating the buffer.";
    }

    if (isAnalyzeOutcome(response)) {
        return response.refusal_reason
            ? `PREFIX analyzed the Python state, refused automatic mutation, and surfaced the bounded reason. ${response.refusal_reason}`
            : "PREFIX analyzed the Python state and refused automatic mutation.";
    }

    switch (response.status) {
        case "ACCEPT_VALID":
            return "PREFIX confirmed the current Python state is already lawful. No mutation was required.";
        case "ACCEPT_FIXED": {
            const summary = response.events.map((event) => `${event.rule_id} line ${event.line}`).join(", ");
            return summary
                ? `PREFIX applied an ALWAYS_SAFE Python governed transition. ${summary}`
                : "PREFIX applied an ALWAYS_SAFE Python governed transition.";
        }
        case "REFUSE_AMBIGUOUS": {
            const candidateSummary = (response.candidates ?? [])
                .map((candidate) => `${candidate.rule_id} line ${candidate.line}`)
                .join(", ");
            return candidateSummary
                ? `PREFIX refused the transition because more than one lawful continuation exists (${response.refusal_code ?? "ambiguous"}). Candidates: ${candidateSummary}`
                : `PREFIX refused the transition because more than one lawful continuation exists (${response.refusal_code ?? "ambiguous"}).`;
        }
        case "REFUSE_UNMAPPED":
            return response.refusal_reason ?? `PREFIX refused the transition because the state is outside the mapped Python prefix surface (${response.refusal_code ?? "unmapped"}).`;
        case "REFUSE_INVALID":
            return response.refusal_reason ?? `PREFIX refused the transition because the state violates the admissible Python input contract (${response.refusal_code ?? "invalid"}).`;
        default:
            return "PREFIX returned an unknown outcome.";
    }
}

export function buildWhySurface(response: EngineResponse): WhySurface {
    const structural = response.structural_context ?? null;
    const governance = response.transition_governance ?? null;
    const graph = response.continuation_graph ?? null;
    const score = response.legality_score ?? null;
    const proof = response.proof_trace ?? null;
    const report = response.legality_report ?? null;
    const packet = response.recommendation_packet ?? null;
    const events = response.events ?? [];
    const candidates = response.candidates ?? [];

    const governingLaw = structural?.governing_law ?? governance?.governing_law ?? "unavailable";
    const surfaceClass = structural?.surface_class ?? "unclassified";
    const locality = structural?.locality ?? "unreported";
    const cardinality = graph?.successor_count ?? 0;
    const mutationBoundary = governance?.local_mutation_boundary ?? (response.state === "APPLIED" ? "bounded_local" : "no_mutation");
    const witness = governance?.transition_witness_root_sha256 ?? structural?.witness_sha256 ?? "unavailable";
    const legalityScore = score?.score ?? "unscored";

    const summary = `PREFIX ${response.state} / ${response.lane}: law=${governingLaw}, surface=${surfaceClass}, continuations=${cardinality}, witness=${witness}`;
    const lines = [
        "PREFIX Structural Governance Surface",
        "====================================",
        `Outcome: ${response.state} / ${response.lane} / ${response.status}`,
        `Governing law: ${governingLaw}`,
        `Admissibility class: ${deriveAdmissibilityClass(response)}`,
        `Surface class: ${surfaceClass}`,
        `Structural locality: ${locality}`,
        `Mutation scope: ${response.mutation_performed ? mutationBoundary : "no_mutation"}`,
        `Continuation cardinality: ${cardinality}`,
        `Legality score: ${legalityScore}`,
        `Boundedness proof: ${deriveBoundednessProof(response)}`,
        `Ambiguity proof: ${deriveAmbiguityProof(response)}`,
        `Idempotency proof: ${deriveIdempotencyProof(response)}`,
        `AST-distance explanation: ${deriveAstDistanceExplanation(response)}`,
        `Deterministic replay path: ${deriveReplayPath(response)}`,
        `Witness lineage: ${witness}`,
    ];

    if (response.refusal_code) {
        lines.push(`Refusal boundary: ${response.refusal_code}`);
    }
    if (response.refusal_reason) {
        lines.push(`Refusal reason: ${response.refusal_reason}`);
    }
    if (response.syntax_error) {
        lines.push(`Syntax authority signal: ${response.syntax_error}`);
    }
    if (response.ast_sha256) {
        lines.push(`AST sha256: ${response.ast_sha256}`);
    }
    if (response.token_sha256) {
        lines.push(`Token sha256: ${response.token_sha256}`);
    }
    if (report) {
        lines.push(
            `AST locality report: nodes=${report.node_count}, edges=${report.edge_count}, tokens=${report.token_count}, violations=${report.violation_count}`,
        );
    }
    if (proof) {
        const roundtrip = typeof proof.roundtrip_sha256 === "string" ? proof.roundtrip_sha256 : "unavailable";
        const construction = proof.ast_construction_signature;
        lines.push(`Roundtrip witness: ${roundtrip}`);
        if (isRecord(construction)) {
            lines.push(`AST construction signature: ${String(construction.signature_sha256 ?? "unavailable")}`);
        }
    }
    if (governance) {
        lines.push(`Continuation graph sha256: ${governance.continuation_graph_sha256}`);
        lines.push(`Structural witness sha256: ${governance.structural_witness_sha256}`);
    }
    if (graph) {
        lines.push(`Continuation graph sha256: ${graph.graph_sha256}`);
        for (const successor of graph.successors) {
            lines.push(`Continuation successor: ${formatRecord(successor)}`);
        }
    }
    if (packet) {
        lines.push(`Recommendation packet sha256: ${packet.packet_sha256}`);
        lines.push(`Ranking model: ${packet.ranking_model}`);
        lines.push(`Top admissible continuation: ${packet.recommended_rule_id} line ${packet.recommended_line} score ${packet.recommended_score}`);
        lines.push("Automatic mutation from ADVISE: forbidden");
    }
    for (const event of events) {
        lines.push(`Governed mutation: ${event.rule_id} line ${event.line} :: ${event.reason}`);
        lines.push(`Structural delta: ${event.before} => ${event.after}`);
    }
    for (const candidate of candidates) {
        lines.push(
            `Admissible continuation candidate #${candidate.rank ?? 0}: ${candidate.rule_id} line ${candidate.line} score ${candidate.score ?? 0}`,
        );
        lines.push(`Candidate structural delta: ${candidate.before} => ${candidate.after}`);
    }

    return { summary, lines };
}

function deriveAdmissibilityClass(response: EngineResponse): string {
    if (response.state === "APPLIED" && response.status === "ACCEPT_VALID") {
        return "already_lawful";
    }
    if (response.state === "APPLIED") {
        return "singular_lawful_mutation";
    }
    if (response.state === "ADVISED") {
        return "bounded_multi_continuation_no_mutation";
    }
    if (response.lane === "ANALYZE") {
        return "unsafe_or_semantic_boundary_no_mutation";
    }
    return "unsupported_or_unmapped_topology_no_mutation";
}

function deriveBoundednessProof(response: EngineResponse): string {
    if (response.state === "APPLIED") {
        return response.parse_reparse_validated
            ? "bounded mutation admitted only after parse/reparse validation"
            : "already lawful or no parse-changing mutation reported";
    }
    if (response.state === "ADVISED") {
        return "bounded candidate set emitted with auto_apply_allowed=false";
    }
    return "mutation withheld because bounded admissibility was not proven";
}

function deriveAmbiguityProof(response: EngineResponse): string {
    const graph = response.continuation_graph;
    if (response.state === "APPLIED") {
        return "exactly one lawful continuation reached APPLY";
    }
    if (response.state === "ADVISED") {
        return `${graph?.successor_count ?? response.candidates?.length ?? 0} lawful continuation(s) ranked deterministically; no mutation`;
    }
    return "no singular lawful continuation admitted";
}

function deriveIdempotencyProof(response: EngineResponse): string {
    if (response.state === "APPLIED" && response.status === "ACCEPT_FIXED") {
        return "engine output is parse/reparse validated and replayable through receipt or identical engine input";
    }
    if (response.state === "APPLIED") {
        return "already lawful input is stable under analysis";
    }
    return "zero-mutation outcome is idempotent by construction";
}

function deriveAstDistanceExplanation(response: EngineResponse): string {
    if (response.state === "APPLIED") {
        const eventCount = response.events?.length ?? 0;
        return eventCount === 0
            ? "zero structural delta"
            : `${eventCount} bounded structural delta(s), projected from text into parse-valid AST authority`;
    }
    if (response.state === "ADVISED") {
        return "candidate distance ranked by rule precedence, edit locality, and canonical tie-breakers";
    }
    return "AST distance not admitted because no safe transition target was proven";
}

function deriveReplayPath(response: EngineResponse): string {
    if (response.transition_governance?.transition_witness_root_sha256) {
        return `replay with identical input and pinned engine should reproduce witness ${response.transition_governance.transition_witness_root_sha256}`;
    }
    if (response.recommendation_packet?.packet_sha256) {
        return `replay recommendation packet ${response.recommendation_packet.packet_sha256}`;
    }
    return "replay unavailable for unreadable or engine-unavailable response";
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatRecord(value: Record<string, unknown>): string {
    return Object.keys(value)
        .sort()
        .map((key) => `${key}=${String(value[key])}`)
        .join(", ");
}
