from __future__ import annotations

import ast
import builtins
import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace

from .ast_bridge import PYTHON_VERSION_PIN, build_ast_construction_signature, validate_source_text

MAX_SOURCE_BYTES = 1_048_576
MAX_CORRECTION_ROUNDS = 8

ACCEPT_VALID = "ACCEPT_VALID"
ACCEPT_FIXED = "ACCEPT_FIXED"
REFUSE_UNMAPPED = "REFUSE_UNMAPPED"
REFUSE_AMBIGUOUS = "REFUSE_AMBIGUOUS"
REFUSE_INVALID = "REFUSE_INVALID"

STATE_APPLIED = "APPLIED"
STATE_ADVISED = "ADVISED"
STATE_REFUSED = "REFUSED"

LANE_APPLY = "APPLY"
LANE_ADVISE = "ADVISE"
LANE_ANALYZE = "ANALYZE"
LANE_ROADMAP = "ROADMAP"

ACCEPT_OUTCOMES = {ACCEPT_VALID, ACCEPT_FIXED}
REFUSAL_OUTCOMES = {REFUSE_UNMAPPED, REFUSE_AMBIGUOUS, REFUSE_INVALID}
RUNTIME_STATE_VALUES = {STATE_APPLIED, STATE_ADVISED, STATE_REFUSED}
RUNTIME_LANE_VALUES = {LANE_APPLY, LANE_ADVISE, LANE_ANALYZE, LANE_ROADMAP}

HEADER_PREFIXES = (
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
)
ASYNC_HEADER_PREFIXES = (
    "async def",
    "async for",
    "async with",
)
ASSIGNMENT_PATTERN = re.compile(r"^(?P<indent>\s*)(?P<target>[A-Za-z_][\w,\s]*)=\s*$")
TRAILING_OPERATOR_PATTERN = re.compile(
    r"^(?P<body>.*?)(?P<operator>\+|-|\*|/|//|%|\*\*|==|!=|<=|>=|<|>|and|or)\s*$"
)
BUILTIN_NAMES = set(dir(builtins))

CANDIDATE_RULE_PRIORITY = {
    "REMOVE_EXTRA_DELIMITER_CANDIDATE": 100,
    "ELIF_TO_IF_CANDIDATE": 80,
}
ANALYZE_REFUSAL_CODES = {
    "apply_commit_failed",
    "assignment_rhs_unmapped",
    "ast_authority_failure",
    "break_outside_loop",
    "continue_outside_loop",
    "correction_budget_exhausted",
    "correction_loop_detected",
    "elif_requires_explicit_authority",
    "input_contains_nul",
    "input_too_large",
    "no_op_correction",
    "orphaned_else",
    "return_outside_function",
    "trailing_operator_unmapped",
    "undefined_name_unmapped",
}


@dataclass(frozen=True)
class CorrectionEvent:
    rule_id: str
    line: int
    before: str
    after: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CorrectionCandidate:
    rule_id: str
    line: int
    before: str
    after: str
    reason: str
    column: int = 0
    rank: int = 0
    score: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RecommendationPacket:
    auto_apply_allowed: bool
    candidate_count: int
    packet_sha256: str
    ranking_model: str
    recommended_after: str
    recommended_column: int
    recommended_line: int
    recommended_rule_id: str
    recommended_score: int
    summary: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CorrectionResult:
    status: str
    state: str
    lane: str
    original_source: str
    source: str
    events: tuple[CorrectionEvent, ...]
    candidates: tuple[CorrectionCandidate, ...] = ()
    recommendation_packet: RecommendationPacket | None = None
    refusal_reason: str | None = None
    refusal_code: str | None = None
    syntax_error: str | None = None
    rounds: int = 0
    input_sha256: str = ""
    output_sha256: str = ""
    ast_sha256: str = ""
    python_version_pin: str = PYTHON_VERSION_PIN
    mutation_performed: bool = False
    parse_reparse_validated: bool = False
    token_sha256: str = ""
    legality_report: dict[str, object] | None = None
    legality_score: dict[str, object] | None = None
    proof_trace: dict[str, object] | None = None
    structural_context: dict[str, object] | None = None
    continuation_graph: dict[str, object] | None = None
    transition_governance: dict[str, object] | None = None

    @property
    def accepted(self) -> bool:
        return self.state == STATE_APPLIED

    @property
    def changed(self) -> bool:
        return self.source != self.original_source

    def to_dict(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "ast_sha256": self.ast_sha256,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "changed": self.changed,
            "events": [event.to_dict() for event in self.events],
            "input_sha256": self.input_sha256,
            "lane": self.lane,
            "legality_report": self.legality_report,
            "legality_score": self.legality_score,
            "mutation_performed": self.mutation_performed,
            "output_sha256": self.output_sha256,
            "parse_reparse_validated": self.parse_reparse_validated,
            "proof_trace": self.proof_trace,
            "python_version_pin": self.python_version_pin,
            "recommendation_packet": self.recommendation_packet.to_dict() if self.recommendation_packet else None,
            "refusal_code": self.refusal_code,
            "refusal_reason": self.refusal_reason,
            "rounds": self.rounds,
            "source": self.source,
            "state": self.state,
            "status": self.status,
            "structural_context": self.structural_context,
            "syntax_error": self.syntax_error,
            "token_sha256": self.token_sha256,
            "continuation_graph": self.continuation_graph,
            "transition_governance": self.transition_governance,
        }


def correct_source(source: str, *, max_rounds: int = 8) -> CorrectionResult:
    input_sha256 = _sha256_text(source)
    output_newline = _detect_newline(source)
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    expanded = normalized.expandtabs(4)
    preprocessing_events = tuple(_build_tab_normalization_events(normalized, expanded))
    normalized = expanded
    repair_events: list[CorrectionEvent] = []
    seen_states: set[str] = {normalized}
    size_bytes = len(source.encode("utf-8", errors="replace"))

    if "\x00" in normalized:
        return _refusal(
            status=REFUSE_INVALID,
            original_source=source,
            source=source,
            refusal_reason="PREFIX refused the transition because source containing NUL bytes is outside the admissible input surface.",
            refusal_code="input_contains_nul",
            input_sha256=input_sha256,
        )

    if size_bytes > MAX_SOURCE_BYTES:
        return _refusal(
            status=REFUSE_INVALID,
            original_source=source,
            source=source,
            refusal_reason=f"PREFIX refused the transition because the input exceeds the {MAX_SOURCE_BYTES}-byte release boundary.",
            refusal_code="input_too_large",
            input_sha256=input_sha256,
        )

    for round_index in range(min(max_rounds, MAX_CORRECTION_ROUNDS)):
        validation = validate_source_text(normalized)
        if validation.is_valid and validation.authority is not None:
            semantic_refusal = _semantic_gate(
                normalized,
                validation.authority.tree,
                input_sha256=input_sha256,
                original_source=source,
                rounds=round_index,
            )
            if semantic_refusal is not None:
                return semantic_refusal

            final_source = _restore_newlines(normalized, output_newline)
            accepted_events = tuple(preprocessing_events) + tuple(repair_events)
            status = ACCEPT_VALID if final_source == source else ACCEPT_FIXED
            structural_context = _build_structural_context(
                source=source,
                lane=LANE_APPLY,
                status=status,
                events=accepted_events,
                candidates=(),
                refusal_code=None,
                syntax_error=None,
            )
            continuation_graph = _build_continuation_graph(
                lane=LANE_APPLY,
                status=status,
                events=accepted_events,
                candidates=(),
                refusal_code=None,
            )
            transition_governance = _build_transition_governance(
                lane=LANE_APPLY,
                status=status,
                structural_context=structural_context,
                continuation_graph=continuation_graph,
            )
            legality_score = _build_legality_score(
                lane=LANE_APPLY,
                status=status,
                event_count=len(accepted_events),
                candidate_count=0,
                parse_reparse_validated=True,
                structural_context=structural_context,
            )
            return CorrectionResult(
                status=status,
                state=STATE_APPLIED,
                lane=LANE_APPLY,
                original_source=source,
                source=final_source,
                events=accepted_events,
                rounds=round_index,
                input_sha256=input_sha256,
                output_sha256=_sha256_text(final_source),
                ast_sha256=validation.authority.ast_sha256,
                mutation_performed=status == ACCEPT_FIXED,
                parse_reparse_validated=True,
                token_sha256=validation.authority.token_sha256,
                legality_report=validation.authority.legality_report.to_dict(),
                legality_score=legality_score,
                proof_trace={
                    "ast_sha256": validation.authority.ast_sha256,
                    "ast_construction_signature": validation.authority.construction_signature,
                    "event_count": len(accepted_events),
                    "event_sha256": _sha256_text(
                        "|".join(
                            f"{event.rule_id}:{event.line}:{event.before}:{event.after}:{event.reason}"
                            for event in accepted_events
                        )
                    ),
                    "legality_violation_count": validation.authority.legality_report.violation_count,
                    "node_count": validation.authority.legality_report.node_count,
                    "roundtrip_sha256": validation.authority.roundtrip_sha256,
                    "token_count": validation.authority.legality_report.token_count,
                    "token_sha256": validation.authority.token_sha256,
                },
                structural_context=structural_context,
                continuation_graph=continuation_graph,
                transition_governance=transition_governance,
            )

        error = validation.syntax_error
        if error is None:
            return _refusal(
                status=REFUSE_INVALID,
                original_source=source,
                source=source,
                refusal_reason="PREFIX refused the transition because AST authority validation failed without a parseable syntax error.",
                refusal_code="ast_authority_failure",
                rounds=round_index,
                input_sha256=input_sha256,
            )

        direct_refusal = _direct_refusal_for_invalid_state(
            error,
            original_source=source,
            input_sha256=input_sha256,
            rounds=round_index,
        )
        if direct_refusal is not None:
            return direct_refusal

        correction = _deterministic_correction(normalized, error)
        if correction is not None:
            updated_source, event = correction
            if updated_source == normalized:
                return _refusal(
                    status=REFUSE_INVALID,
                    original_source=source,
                    source=source,
                    refusal_reason="PREFIX refused the transition because the deterministic repair path produced no state change.",
                    refusal_code="no_op_correction",
                    syntax_error=_format_syntax_error(error),
                    rounds=round_index,
                    input_sha256=input_sha256,
                )

            normalized = updated_source
            repair_events.append(event)
            if normalized in seen_states:
                return _refusal(
                    status=REFUSE_INVALID,
                    original_source=source,
                    source=source,
                    refusal_reason="PREFIX refused the transition because the correction path re-entered a prior state.",
                    refusal_code="correction_loop_detected",
                    syntax_error=_format_syntax_error(error),
                    rounds=round_index + 1,
                    input_sha256=input_sha256,
                )
            seen_states.add(normalized)
            continue

        candidates, candidate_code, candidate_reason = _candidate_repairs(normalized, error)
        if candidates:
            refusal_status = REFUSE_AMBIGUOUS if len(candidates) > 1 else REFUSE_UNMAPPED
            return _refusal(
                status=refusal_status,
                original_source=source,
                source=source,
                refusal_reason=candidate_reason,
                refusal_code=candidate_code,
                syntax_error=_format_syntax_error(error),
                rounds=round_index,
                input_sha256=input_sha256,
                candidates=tuple(candidates),
            )

        if candidate_code != "unsupported_syntax_state":
            refusal_status = REFUSE_INVALID if candidate_code in {"input_contains_nul", "input_too_large"} else REFUSE_UNMAPPED
            return _refusal(
                status=refusal_status,
                original_source=source,
                source=source,
                refusal_reason=candidate_reason,
                refusal_code=candidate_code,
                syntax_error=_format_syntax_error(error),
                rounds=round_index,
                input_sha256=input_sha256,
            )

        return _refusal(
            status=REFUSE_UNMAPPED,
            original_source=source,
            source=source,
            refusal_reason=_build_refusal_reason(error),
            refusal_code="unsupported_syntax_state",
            syntax_error=_format_syntax_error(error),
            rounds=round_index,
            input_sha256=input_sha256,
        )

    return _refusal(
        status=REFUSE_INVALID,
        original_source=source,
        source=source,
        refusal_reason="PREFIX exhausted the bounded correction budget.",
        refusal_code="correction_budget_exhausted",
        rounds=min(max_rounds, MAX_CORRECTION_ROUNDS),
        input_sha256=input_sha256,
    )


def _semantic_gate(
    source: str,
    tree: ast.AST,
    *,
    input_sha256: str,
    original_source: str,
    rounds: int,
) -> CorrectionResult | None:
    unresolved = _find_module_level_unresolved_names(tree)
    if not unresolved:
        return None

    names = ", ".join(sorted(unresolved))
    return _refusal(
        status=REFUSE_UNMAPPED,
        original_source=original_source,
        source=original_source,
        refusal_reason=f"PREFIX refused the transition because unresolved module-level names remain outside the deterministic correction surface: {names}.",
        refusal_code="undefined_name_unmapped",
        rounds=rounds,
        input_sha256=input_sha256,
    )


def _find_module_level_unresolved_names(tree: ast.AST) -> set[str]:
    if not isinstance(tree, ast.Module):
        return set()

    defined: set[str] = set()
    unresolved: set[str] = set()

    for statement in tree.body:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            for alias in statement.names:
                defined.add(alias.asname or alias.name.split(".")[0])
            continue
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(statement.name)
            continue
        if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith)):
            for name in _extract_store_names(statement):
                defined.add(name)
            continue

        if isinstance(statement, ast.Expr):
            for node in ast.walk(statement.value):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id not in defined and node.id not in BUILTIN_NAMES:
                        unresolved.add(node.id)

    return unresolved


def _extract_store_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
    return names


def _direct_refusal_for_invalid_state(
    error: SyntaxError,
    *,
    original_source: str,
    input_sha256: str,
    rounds: int,
) -> CorrectionResult | None:
    line_text = (error.text or "").strip()
    message = error.msg or ""

    if line_text.startswith("return") or "'return' outside function" in message:
        return _refusal(
            status=REFUSE_INVALID,
            original_source=original_source,
            source=original_source,
            refusal_reason="PREFIX refused the transition because `return` outside a function has no lawful deterministic repair.",
            refusal_code="return_outside_function",
            syntax_error=_format_syntax_error(error),
            rounds=rounds,
            input_sha256=input_sha256,
        )

    if line_text.startswith("continue") or "'continue' not properly in loop" in message:
        return _refusal(
            status=REFUSE_INVALID,
            original_source=original_source,
            source=original_source,
            refusal_reason="PREFIX refused the transition because `continue` outside a loop has no lawful deterministic repair.",
            refusal_code="continue_outside_loop",
            syntax_error=_format_syntax_error(error),
            rounds=rounds,
            input_sha256=input_sha256,
        )

    if line_text.startswith("break") or "'break' outside loop" in message:
        return _refusal(
            status=REFUSE_INVALID,
            original_source=original_source,
            source=original_source,
            refusal_reason="PREFIX refused the transition because `break` outside a loop has no lawful deterministic repair.",
            refusal_code="break_outside_loop",
            syntax_error=_format_syntax_error(error),
            rounds=rounds,
            input_sha256=input_sha256,
        )

    if line_text.startswith("else"):
        return _refusal(
            status=REFUSE_INVALID,
            original_source=original_source,
            source=original_source,
            refusal_reason="PREFIX refused the transition because orphaned `else` does not admit a singular deterministic correction.",
            refusal_code="orphaned_else",
            syntax_error=_format_syntax_error(error),
            rounds=rounds,
            input_sha256=input_sha256,
        )

    return None


def _build_refusal_reason(error: SyntaxError) -> str:
    message = error.msg or "Unknown syntax error"
    return f"PREFIX refused the transition because `{message}` is outside the mapped deterministic correction surface."


def _format_syntax_error(error: SyntaxError | None) -> str | None:
    if error is None:
        return None
    line = error.lineno or 0
    offset = error.offset or 0
    message = error.msg or "Syntax error"
    return f"line {line}, column {offset}: {message}"


def _deterministic_correction(source: str, error: SyntaxError) -> tuple[str, CorrectionEvent] | None:
    lines = source.split("\n")
    line_index = max((error.lineno or 1) - 1, 0)
    current_line = lines[line_index] if line_index < len(lines) else ""

    if _is_missing_colon(current_line, error):
        updated_line = current_line.rstrip() + ":"
        lines[line_index] = updated_line
        return "\n".join(lines), CorrectionEvent(
            rule_id="MISSING_COLON",
            line=line_index + 1,
            before=current_line,
            after=updated_line,
            reason="Block-introducing line was missing a colon.",
        )

    if _needs_indented_block(error):
        return _indent_or_fill(lines, line_index)

    delimiter_fix = _fix_unmatched_delimiter(lines, line_index)
    if delimiter_fix is not None:
        return delimiter_fix

    extra_delimiter_fix = _fix_single_extra_closing_delimiter(source, lines, line_index)
    if extra_delimiter_fix is not None:
        return extra_delimiter_fix

    return None


def _candidate_repairs(source: str, error: SyntaxError) -> tuple[list[CorrectionCandidate], str, str]:
    lines = source.split("\n")
    line_index = max((error.lineno or 1) - 1, 0)
    current_line = lines[line_index] if line_index < len(lines) else ""
    stripped = current_line.strip()

    if stripped.startswith("elif "):
        updated_line = current_line.replace("elif", "if", 1)
        return (
            [
                CorrectionCandidate(
                    rule_id="ELIF_TO_IF_CANDIDATE",
                    line=line_index + 1,
                    before=current_line,
                    after=updated_line,
                    reason="Promotion from orphaned `elif` to `if` is available as a ranked recommendation, but is never auto-applied.",
                )
            ],
            "elif_requires_explicit_authority",
            "PREFIX advised a ranked Python continuation for orphaned `elif`, but no ALWAYS_SAFE automatic mutation exists.",
        )

    if _is_assignment_without_rhs(current_line):
        return (
            [],
            "assignment_rhs_unmapped",
            "PREFIX analyzed the transition and refused automatic mutation because completing an assignment without a right-hand side would require a semantic default-value guess.",
        )

    if _is_trailing_operator(current_line):
        return (
            [],
            "trailing_operator_unmapped",
            "PREFIX analyzed the transition and refused automatic mutation because completing a trailing operator would require a semantic default-value guess.",
        )

    ambiguous_delimiters = _ambiguous_extra_closing_delimiter_candidates(source, line_index)
    if ambiguous_delimiters:
        return (
            ambiguous_delimiters,
            "extra_closing_delimiter_ambiguous",
            "PREFIX advised ranked delimiter-removal candidates because more than one lawful continuation exists and no singular authoritative correction is available.",
        )

    return ([], "unsupported_syntax_state", _build_refusal_reason(error))


def _is_missing_colon(line: str, error: SyntaxError) -> bool:
    if error.msg not in {"expected ':'", "invalid syntax"}:
        return False
    stripped = line.strip()
    if not stripped or stripped.endswith(":"):
        return False
    return _match_header_prefix(stripped) is not None


def _needs_indented_block(error: SyntaxError) -> bool:
    return "expected an indented block" in (error.msg or "")


def _indent_or_fill(lines: list[str], line_index: int) -> tuple[str, CorrectionEvent]:
    body_index = min(line_index, len(lines) - 1)
    header_index = max(body_index - 1, 0)
    current_line = lines[body_index]

    if _is_header_line(current_line):
        header_line = current_line
        header_index = body_index
        current_line = ""
    else:
        header_line = lines[header_index]

    header_indent = _leading_spaces(header_line)
    current_line = lines[body_index]
    stripped = current_line.strip()
    desired_indent = " " * (header_indent + 4)

    if stripped and not _is_header_line(current_line):
        updated_line = desired_indent + stripped
        lines[body_index] = updated_line
        return "\n".join(lines), CorrectionEvent(
            rule_id="AUTO_INDENT",
            line=body_index + 1,
            before=current_line,
            after=updated_line,
            reason="Block body was indented to the required depth.",
        )

    insert_at = header_index + 1
    lines.insert(insert_at, desired_indent + "pass")
    return "\n".join(lines), CorrectionEvent(
        rule_id="INSERT_PASS",
        line=insert_at + 1,
        before="",
        after=desired_indent + "pass",
        reason="Empty block body was completed with `pass`.",
    )


def _is_assignment_without_rhs(line: str) -> bool:
    return ASSIGNMENT_PATTERN.match(line) is not None


def _is_trailing_operator(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return TRAILING_OPERATOR_PATTERN.match(stripped) is not None


def _fix_unmatched_delimiter(lines: list[str], line_index: int) -> tuple[str, CorrectionEvent] | None:
    line = lines[line_index]
    open_to_close = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    in_single = False
    in_double = False
    escape = False

    for char in line:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if char in open_to_close:
            stack.append(char)
        elif char in open_to_close.values():
            if stack and open_to_close[stack[-1]] == char:
                stack.pop()

    if not stack:
        return None

    closers = "".join(open_to_close[char] for char in reversed(stack))
    updated_line = line + closers
    lines[line_index] = updated_line
    return "\n".join(lines), CorrectionEvent(
        rule_id="CLOSE_DELIMITER",
        line=line_index + 1,
        before=line,
        after=updated_line,
        reason="Unmatched delimiters were closed deterministically at the end of the line.",
    )


def _fix_single_extra_closing_delimiter(
    source: str,
    lines: list[str],
    line_index: int,
) -> tuple[str, CorrectionEvent] | None:
    candidates = _delimiter_removal_candidates(source, line_index)
    if len(candidates) != 1:
        return None

    index_to_remove, updated_source = candidates[0]
    before_line = lines[line_index]
    after_line = updated_source.split("\n")[line_index]
    return updated_source, CorrectionEvent(
        rule_id="REMOVE_EXTRA_DELIMITER",
        line=line_index + 1,
        before=before_line,
        after=after_line,
        reason=f"Removed the singular extra closing delimiter at column {index_to_remove + 1}.",
    )


def _ambiguous_extra_closing_delimiter_candidates(source: str, line_index: int) -> list[CorrectionCandidate]:
    candidates = _delimiter_removal_candidates(source, line_index)
    if len(candidates) <= 1:
        return []

    lines = source.split("\n")
    before_line = lines[line_index]
    result: list[CorrectionCandidate] = []
    for index_to_remove, updated_source in candidates:
        after_line = updated_source.split("\n")[line_index]
        result.append(
            CorrectionCandidate(
                rule_id="REMOVE_EXTRA_DELIMITER_CANDIDATE",
                line=line_index + 1,
                before=before_line,
                after=after_line,
                reason=f"Removing the closing delimiter at column {index_to_remove + 1} yields a parse-valid candidate.",
            )
        )
    return result


def _delimiter_removal_candidates(source: str, line_index: int) -> list[tuple[int, str]]:
    lines = source.split("\n")
    if line_index >= len(lines):
        return []
    line = lines[line_index]
    candidates: list[tuple[int, str]] = []
    seen_sources: set[str] = set()
    for index, char in enumerate(line):
        if char not in ")]}":
            continue
        updated_line = line[:index] + line[index + 1 :]
        updated_lines = list(lines)
        updated_lines[line_index] = updated_line
        updated_source = "\n".join(updated_lines)
        validation = validate_source_text(updated_source)
        if validation.is_valid and updated_source not in seen_sources:
            candidates.append((index, updated_source))
            seen_sources.add(updated_source)
    return candidates


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _match_header_prefix(stripped: str) -> str | None:
    for prefix in ASYNC_HEADER_PREFIXES:
        if stripped == prefix or stripped.startswith(prefix + " "):
            return prefix

    for prefix in HEADER_PREFIXES:
        if stripped == prefix or stripped.startswith(prefix + " "):
            return prefix
    return None


def _is_header_line(line: str) -> bool:
    return _match_header_prefix(line.strip()) is not None


def _rank_candidates(candidates: tuple[CorrectionCandidate, ...]) -> tuple[CorrectionCandidate, ...]:
    scored_candidates = []
    for candidate in candidates:
        column = _first_difference_column(candidate.before, candidate.after)
        priority = CANDIDATE_RULE_PRIORITY.get(candidate.rule_id, 50)
        delta = abs(len(candidate.after) - len(candidate.before))
        score = priority * 1000 - column * 10 - delta
        scored_candidates.append(replace(candidate, column=column, score=score))

    ordered = sorted(
        scored_candidates,
        key=lambda candidate: (
            -candidate.score,
            candidate.line,
            candidate.column,
            candidate.rule_id,
            candidate.after,
            candidate.before,
        ),
    )
    return tuple(replace(candidate, rank=index + 1) for index, candidate in enumerate(ordered))


def _first_difference_column(before: str, after: str) -> int:
    for index, (left, right) in enumerate(zip(before, after), start=1):
        if left != right:
            return index
    return min(len(before), len(after)) + 1


def _build_recommendation_packet(candidates: tuple[CorrectionCandidate, ...]) -> RecommendationPacket | None:
    if not candidates:
        return None

    top_candidate = candidates[0]
    payload = {
        "auto_apply_allowed": False,
        "candidate_count": len(candidates),
        "ranking_model": "prefix-python-deterministic-lane-v1",
        "recommended_after": top_candidate.after,
        "recommended_column": top_candidate.column,
        "recommended_line": top_candidate.line,
        "recommended_rule_id": top_candidate.rule_id,
        "recommended_score": top_candidate.score,
        "summary": "Candidates are ranked deterministically by Python rule precedence, edit locality, and canonical tie-breakers. ADVISED never mutates code automatically.",
    }
    packet_sha256 = _sha256_text(_canonical_json(payload))
    return RecommendationPacket(
        auto_apply_allowed=False,
        candidate_count=len(candidates),
        packet_sha256=packet_sha256,
        ranking_model="prefix-python-deterministic-lane-v1",
        recommended_after=top_candidate.after,
        recommended_column=top_candidate.column,
        recommended_line=top_candidate.line,
        recommended_rule_id=top_candidate.rule_id,
        recommended_score=top_candidate.score,
        summary="Candidates are ranked deterministically by Python rule precedence, edit locality, and canonical tie-breakers. ADVISED never mutates code automatically.",
    )


def _derive_lane(status: str, refusal_code: str | None, candidates: tuple[CorrectionCandidate, ...]) -> str:
    if status in ACCEPT_OUTCOMES:
        return LANE_APPLY
    if candidates:
        return LANE_ADVISE
    if refusal_code in ANALYZE_REFUSAL_CODES:
        return LANE_ANALYZE
    return LANE_ROADMAP


def _derive_state(lane: str) -> str:
    if lane == LANE_APPLY:
        return STATE_APPLIED
    if lane == LANE_ADVISE:
        return STATE_ADVISED
    return STATE_REFUSED


def _build_structural_context(
    *,
    source: str,
    lane: str,
    status: str,
    events: tuple[CorrectionEvent, ...],
    candidates: tuple[CorrectionCandidate, ...],
    refusal_code: str | None,
    syntax_error: str | None,
) -> dict[str, object]:
    surface_class = "unsupported_surface"
    locality = "bounded_local"

    rule_ids = {event.rule_id for event in events}
    candidate_rule_ids = {candidate.rule_id for candidate in candidates}

    if "MISSING_COLON" in rule_ids or any(rule_id == "ELIF_TO_IF_CANDIDATE" for rule_id in candidate_rule_ids):
        surface_class = "block_header_continuation"
    elif "AUTO_INDENT" in rule_ids or "INSERT_PASS" in rule_ids:
        surface_class = "block_body_stabilization"
    elif "CLOSE_DELIMITER" in rule_ids or "REMOVE_EXTRA_DELIMITER" in rule_ids or any(
        rule_id == "REMOVE_EXTRA_DELIMITER_CANDIDATE" for rule_id in candidate_rule_ids
    ):
        surface_class = "delimiter_balance"
    elif refusal_code in {"assignment_rhs_unmapped", "trailing_operator_unmapped"}:
        surface_class = "incomplete_expression"
    elif refusal_code in {"return_outside_function", "break_outside_loop", "continue_outside_loop", "orphaned_else"}:
        surface_class = "scope_keyword_misplacement"
    elif refusal_code == "undefined_name_unmapped":
        surface_class = "name_resolution_boundary"
        locality = "module_level"
    elif refusal_code in {"input_contains_nul", "input_too_large"}:
        surface_class = "input_contract_boundary"
        locality = "input_contract"

    if lane == LANE_APPLY and status == ACCEPT_VALID:
        governing_law = "already_lawful"
    elif lane == LANE_APPLY:
        governing_law = "single_lawful_continuation"
    elif lane == LANE_ADVISE:
        governing_law = "multiple_lawful_continuations"
    elif lane == LANE_ANALYZE:
        governing_law = "unsafe_or_unproven_continuation"
    else:
        governing_law = "unmapped_surface"

    payload = {
        "event_count": len(events),
        "governing_law": governing_law,
        "lane": lane,
        "locality": locality,
        "refusal_code": refusal_code,
        "source_line_count": source.count("\n") + (0 if not source else 1),
        "status": status,
        "surface_class": surface_class,
        "syntax_error": syntax_error,
    }
    payload["witness_sha256"] = _sha256_text(_canonical_json(payload))
    return payload


def _build_continuation_graph(
    *,
    lane: str,
    status: str,
    events: tuple[CorrectionEvent, ...],
    candidates: tuple[CorrectionCandidate, ...],
    refusal_code: str | None,
) -> dict[str, object]:
    successors: list[dict[str, object]] = []
    if lane == LANE_APPLY:
        successors.append(
            {
                "kind": "applied_continuation",
                "rank": 1,
                "rule_ids": [event.rule_id for event in events],
                "status": status,
            }
        )
    elif lane == LANE_ADVISE:
        for candidate in candidates:
            successors.append(
                {
                    "after": candidate.after,
                    "column": candidate.column,
                    "kind": "advised_continuation",
                    "line": candidate.line,
                    "rank": candidate.rank,
                    "rule_id": candidate.rule_id,
                    "score": candidate.score,
                }
            )

    payload = {
        "continuation_kind": lane.lower(),
        "refusal_code": refusal_code,
        "successor_count": len(successors),
        "successors": successors,
    }
    payload["graph_sha256"] = _sha256_text(_canonical_json(payload))
    return payload


def _build_transition_governance(
    *,
    lane: str,
    status: str,
    structural_context: dict[str, object],
    continuation_graph: dict[str, object],
) -> dict[str, object]:
    payload = {
        "continuation_graph_sha256": continuation_graph["graph_sha256"],
        "governing_law": structural_context["governing_law"],
        "lane": lane,
        "local_mutation_boundary": "line_local_or_bounded_local" if lane == LANE_APPLY else "no_mutation",
        "status": status,
        "structural_witness_sha256": structural_context["witness_sha256"],
    }
    payload["transition_witness_root_sha256"] = _sha256_text(_canonical_json(payload))
    return payload


def _build_legality_score(
    *,
    lane: str,
    status: str,
    event_count: int,
    candidate_count: int,
    parse_reparse_validated: bool,
    structural_context: dict[str, object],
) -> dict[str, object]:
    if lane == LANE_APPLY and status == ACCEPT_VALID:
        score = 100
    elif lane == LANE_APPLY:
        score = 98
    elif lane == LANE_ADVISE:
        score = 72
    elif lane == LANE_ANALYZE:
        score = 48
    else:
        score = 24

    payload = {
        "candidate_count": candidate_count,
        "event_count": event_count,
        "governing_law": structural_context["governing_law"],
        "parse_reparse_validated": parse_reparse_validated,
        "score": score,
        "surface_class": structural_context["surface_class"],
    }
    payload["score_sha256"] = _sha256_text(_canonical_json(payload))
    return payload


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _detect_newline(source: str) -> str:
    if "\r\n" in source:
        return "\r\n"
    if "\r" in source:
        return "\r"
    return "\n"


def _restore_newlines(source: str, newline: str) -> str:
    if newline == "\n":
        return source
    return source.replace("\n", newline)


def _build_tab_normalization_events(before: str, after: str) -> list[CorrectionEvent]:
    if before == after:
        return []
    events: list[CorrectionEvent] = []
    before_lines = before.split("\n")
    after_lines = after.split("\n")
    for index, (before_line, after_line) in enumerate(zip(before_lines, after_lines), start=1):
        if before_line != after_line:
            events.append(
                CorrectionEvent(
                    rule_id="NORMALIZE_TABS",
                    line=index,
                    before=before_line,
                    after=after_line,
                    reason="Tabs were expanded deterministically to four spaces.",
                )
            )
    return events


def _refusal(
    *,
    status: str,
    original_source: str,
    source: str,
    refusal_reason: str,
    refusal_code: str,
    syntax_error: str | None = None,
    rounds: int = 0,
    input_sha256: str = "",
    candidates: tuple[CorrectionCandidate, ...] = (),
) -> CorrectionResult:
    ranked_candidates = _rank_candidates(candidates)
    lane = _derive_lane(status, refusal_code, ranked_candidates)
    structural_context = _build_structural_context(
        source=source,
        lane=lane,
        status=status,
        events=(),
        candidates=ranked_candidates,
        refusal_code=refusal_code,
        syntax_error=syntax_error,
    )
    continuation_graph = _build_continuation_graph(
        lane=lane,
        status=status,
        events=(),
        candidates=ranked_candidates,
        refusal_code=refusal_code,
    )
    transition_governance = _build_transition_governance(
        lane=lane,
        status=status,
        structural_context=structural_context,
        continuation_graph=continuation_graph,
    )
    legality_score = _build_legality_score(
        lane=lane,
        status=status,
        event_count=0,
        candidate_count=len(ranked_candidates),
        parse_reparse_validated=False,
        structural_context=structural_context,
    )
    return CorrectionResult(
        status=status,
        state=_derive_state(lane),
        lane=lane,
        original_source=original_source,
        source=source,
        events=(),
        candidates=ranked_candidates,
        recommendation_packet=_build_recommendation_packet(ranked_candidates) if lane == LANE_ADVISE else None,
        refusal_reason=refusal_reason,
        refusal_code=refusal_code,
        syntax_error=syntax_error,
        rounds=rounds,
        input_sha256=input_sha256,
        output_sha256=_sha256_text(source),
        mutation_performed=False,
        parse_reparse_validated=False,
        legality_score=legality_score,
        structural_context=structural_context,
        continuation_graph=continuation_graph,
        transition_governance=transition_governance,
    )
