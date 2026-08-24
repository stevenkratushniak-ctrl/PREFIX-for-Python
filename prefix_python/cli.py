from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

from .ast_bridge import validate_source_text
from .engine import (
    ACCEPT_FIXED,
    ACCEPT_OUTCOMES,
    ACCEPT_VALID,
    LANE_ANALYZE,
    LANE_APPLY,
    STATE_APPLIED,
    STATE_REFUSED,
    correct_source,
)

VERSION = "0.1.0"
RECEIPT_VERSION = "1.0.0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="prefix-python",
        description="Deterministic Python prefix layer for bounded correctness.",
    )
    parser.add_argument("path", nargs="?", help="Path to a Python file to analyze.")
    parser.add_argument("--stdin", action="store_true", help="Read Python source from stdin.")
    parser.add_argument("--json", action="store_true", help="Print canonical JSON output.")
    parser.add_argument("--version", action="store_true", help="Print the installed PREFIX for Python version.")
    parser.add_argument("--apply", action="store_true", help="Apply an accepted deterministic fix to the target file.")
    parser.add_argument("--write", action="store_true", help="Legacy alias for --apply.")
    parser.add_argument("--rollback", metavar="RECEIPT", help="Rollback a prior applied fix using a receipt JSON file.")
    parser.add_argument("--inspect-receipt", metavar="RECEIPT", help="Inspect a receipt without mutating any files.")
    parser.add_argument("--replay-receipt", metavar="RECEIPT", help="Replay an apply receipt deterministically and verify the stored correction.")
    parser.add_argument(
        "--receipt-dir",
        help="Directory for apply or rollback receipts. Defaults to .prefix-python-receipts next to the target file.",
    )
    args = parser.parse_args(argv)

    if args.version:
        sys.stdout.write(f"prefix-python {VERSION}\n")
        return 0

    administrative_modes = [bool(args.rollback), bool(args.inspect_receipt), bool(args.replay_receipt)]
    if sum(1 for enabled in administrative_modes if enabled) > 1:
        parser.error("Specify at most one of --rollback, --inspect-receipt, or --replay-receipt.")

    if args.rollback:
        return _run_rollback(args)
    if args.inspect_receipt:
        return _run_inspect_receipt(args)
    if args.replay_receipt:
        return _run_replay_receipt(args)

    if args.stdin == bool(args.path):
        parser.error("Specify exactly one source: either a file path or --stdin.")

    try:
        if args.stdin:
            source = sys.stdin.read()
            source_path: Path | None = None
            source_path_was_symlink = False
        else:
            source_argument = Path(args.path)
            source_path_was_symlink = source_argument.is_symlink()
            source_path = source_argument.resolve()
            if not source_path.exists():
                return _emit_cli_refusal(
                    args.json,
                    refusal_reason=f"PREFIX could not open `{source_path}` because the file does not exist.",
                    refusal_code="path_missing",
                )
            if not source_path.is_file():
                return _emit_cli_refusal(
                    args.json,
                    refusal_reason=f"PREFIX expects a regular file, not `{source_path}`.",
                    refusal_code="path_not_file",
                    path=str(source_path),
                )
            source = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return _emit_cli_refusal(
            args.json,
            refusal_reason="PREFIX could not decode the file as UTF-8 text.",
            refusal_code="input_decode_error",
            path=str(source_path) if "source_path" in locals() and source_path is not None else None,
        )
    except OSError as exc:
        return _emit_cli_refusal(
            args.json,
            refusal_reason=f"PREFIX could not open the input: {exc}",
            refusal_code="input_open_error",
            path=str(source_path) if "source_path" in locals() and source_path is not None else None,
        )

    result = correct_source(source)
    apply_requested = bool(args.apply or args.write)

    if apply_requested and source_path is None:
        parser.error("--apply requires a file path.")

    if apply_requested and source_path is not None and source_path_was_symlink:
        return _emit_cli_refusal(
            args.json,
            refusal_reason=f"PREFIX refuses `--apply` on symbolic links: `{source_path}`.",
            refusal_code="write_symlink_refused",
            path=str(source_path),
        )

    wrote = False
    receipt_path: str | None = None
    if apply_requested and source_path is not None:
        if result.status == ACCEPT_FIXED:
            try:
                _atomic_write_text(source_path, result.source)
                receipt_path = str(
                    _write_apply_receipt(
                        source_path,
                        source,
                        result.source,
                        result,
                        _resolve_receipt_dir(source_path, args.receipt_dir),
                    )
                )
                wrote = True
            except OSError as exc:
                return _emit_cli_refusal(
                    args.json,
                    refusal_reason=f"PREFIX could not commit the deterministic governed transition: {exc}",
                    refusal_code="apply_commit_failed",
                    path=str(source_path),
                )
        elif result.status not in ACCEPT_OUTCOMES:
            payload = result.to_dict()
            payload["path"] = str(source_path)
            payload["receipt_path"] = None
            payload["version"] = VERSION
            payload["wrote"] = False
            if args.json:
                sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            else:
                _print_human(payload)
            return 2

    payload = result.to_dict()
    if source_path is not None:
        payload["path"] = str(source_path)
    payload["receipt_path"] = receipt_path
    payload["version"] = VERSION
    payload["wrote"] = wrote

    if args.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        _print_human(payload)

    return 0 if result.status in ACCEPT_OUTCOMES else 2


def _run_rollback(args: argparse.Namespace) -> int:
    payload, receipt_path, error_exit = _load_receipt(args.rollback, args.json, "rollback")
    if error_exit is not None:
        return error_exit

    target_path = Path(payload.get("path", "")).resolve()
    if args.path is not None and Path(args.path).resolve() != target_path:
        return _emit_cli_refusal(
            args.json,
            refusal_reason="PREFIX refused rollback because the supplied path does not match the receipt target.",
            refusal_code="rollback_path_mismatch",
            path=str(target_path),
        )

    if not target_path.exists() or not target_path.is_file():
        return _emit_cli_refusal(
            args.json,
            refusal_reason=f"PREFIX could not find rollback target `{target_path}`.",
            refusal_code="rollback_target_missing",
            path=str(target_path),
        )

    before_source = payload.get("before_source", "")
    after_source = payload.get("after_source", "")
    before_sha256 = payload.get("before_sha256", "")
    after_sha256 = payload.get("after_sha256", "")
    current_source = target_path.read_text(encoding="utf-8")

    if _sha256_text(current_source) != after_sha256:
        return _emit_cli_refusal(
            args.json,
            refusal_reason="PREFIX refused rollback because the current file content does not match the receipt post-image.",
            refusal_code="rollback_postimage_mismatch",
            path=str(target_path),
        )

    if _sha256_text(before_source) != before_sha256:
        return _emit_cli_refusal(
            args.json,
            refusal_reason="PREFIX refused rollback because the receipt pre-image hash is invalid.",
            refusal_code="rollback_receipt_tampered",
            path=str(target_path),
        )

    before_validation = validate_source_text(before_source)
    if not before_validation.is_valid:
        return _emit_cli_refusal(
            args.json,
            refusal_reason="PREFIX refused rollback because the receipt pre-image is not parse-valid under the Python 3.12 authority surface.",
            refusal_code="rollback_preimage_invalid",
            path=str(target_path),
        )

    try:
        _atomic_write_text(target_path, before_source)
        rollback_receipt = _write_rollback_receipt(
            target_path,
            before_source,
            after_source,
            receipt_path,
            _resolve_receipt_dir(target_path, args.receipt_dir),
        )
    except OSError as exc:
        return _emit_cli_refusal(
            args.json,
            refusal_reason=f"PREFIX could not commit rollback evidence: {exc}",
            refusal_code="rollback_commit_failed",
            path=str(target_path),
        )

    result_payload: dict[str, object] = {
        "accepted": True,
        "ast_sha256": "",
        "candidates": [],
        "changed": current_source != before_source,
        "events": [],
        "input_sha256": after_sha256,
        "lane": LANE_APPLY,
        "mutation_performed": current_source != before_source,
        "output_sha256": before_sha256,
        "parse_reparse_validated": True,
        "path": str(target_path),
        "python_version_pin": payload.get("python_version_pin", "3.12"),
        "receipt_path": str(rollback_receipt),
        "recommendation_packet": None,
        "refusal_code": None,
        "refusal_reason": None,
        "rounds": 0,
        "source": before_source,
        "state": STATE_APPLIED,
        "status": ACCEPT_FIXED,
        "syntax_error": None,
        "version": VERSION,
        "wrote": True,
    }
    if args.json:
        sys.stdout.write(json.dumps(result_payload, indent=2, sort_keys=True) + "\n")
    else:
        _print_human(result_payload)
    return 0


def _run_inspect_receipt(args: argparse.Namespace) -> int:
    payload, receipt_path, error_exit = _load_receipt(args.inspect_receipt, args.json, "inspect")
    if error_exit is not None:
        return error_exit

    receipt_dir = receipt_path.parent
    inspection_payload = {
        "accepted": True,
        "chain_depth": _receipt_chain_depth(receipt_dir, payload),
        "lane": LANE_ANALYZE,
        "lineage_id": payload.get("lineage_id"),
        "mutation_performed": False,
        "path": payload.get("path"),
        "proof_trace": {
            "after_authority_valid": bool(payload.get("after_authority", {}).get("is_valid", False)),
            "before_authority_valid": bool(payload.get("before_authority", {}).get("is_valid", False)),
            "chain_sha256": payload.get("chain_sha256"),
            "parent_receipt_id": payload.get("parent_receipt_id"),
            "receipt_id": payload.get("receipt_id"),
            "rollback_ready": bool(payload.get("rollback_ready", False)),
            "transition_sha256": payload.get("transition_sha256"),
        },
        "receipt_kind": payload.get("receipt_kind"),
        "receipt_path": str(receipt_path),
        "replay_verified": False,
        "source": "",
        "state": STATE_APPLIED,
        "status": ACCEPT_VALID,
        "version": VERSION,
        "wrote": False,
    }
    if args.json:
        sys.stdout.write(json.dumps(inspection_payload, indent=2, sort_keys=True) + "\n")
    else:
        _print_human(inspection_payload)
    return 0


def _run_replay_receipt(args: argparse.Namespace) -> int:
    payload, receipt_path, error_exit = _load_receipt(args.replay_receipt, args.json, "replay")
    if error_exit is not None:
        return error_exit

    if payload.get("receipt_kind") != "apply":
        return _emit_cli_refusal(
            args.json,
            refusal_reason="PREFIX can replay only apply receipts deterministically.",
            refusal_code="replay_requires_apply_receipt",
            path=str(receipt_path),
        )

    before_source = str(payload.get("before_source", ""))
    replay_result = correct_source(before_source)
    replay_payload = replay_result.to_dict()
    expected_payload = payload.get("engine_result")
    if replay_payload != expected_payload:
        return _emit_cli_refusal(
            args.json,
            refusal_reason="PREFIX refused replay because deterministic correction output diverged from the stored receipt evidence.",
            refusal_code="replay_diverged",
            path=str(receipt_path),
        )

    if _sha256_text(replay_result.source) != payload.get("after_sha256"):
        return _emit_cli_refusal(
            args.json,
            refusal_reason="PREFIX refused replay because the stored receipt post-image hash does not match the replayed output.",
            refusal_code="replay_postimage_mismatch",
            path=str(receipt_path),
        )

    result_payload: dict[str, object] = {
        "accepted": True,
        "ast_sha256": replay_result.ast_sha256,
        "candidates": [],
        "changed": False,
        "events": [event.to_dict() for event in replay_result.events],
        "input_sha256": replay_result.input_sha256,
        "lane": LANE_ANALYZE,
        "legality_report": replay_result.legality_report,
        "mutation_performed": False,
        "output_sha256": replay_result.output_sha256,
        "parse_reparse_validated": replay_result.parse_reparse_validated,
        "path": payload.get("path"),
        "proof_trace": {
            **(replay_result.proof_trace or {}),
            "receipt_id": payload.get("receipt_id"),
            "replay_verified": True,
            "stored_transition_sha256": payload.get("transition_sha256"),
        },
        "python_version_pin": replay_result.python_version_pin,
        "receipt_path": str(receipt_path),
        "recommendation_packet": None,
        "refusal_code": None,
        "refusal_reason": None,
        "rounds": replay_result.rounds,
        "source": replay_result.source,
        "state": STATE_APPLIED,
        "status": ACCEPT_VALID,
        "syntax_error": None,
        "token_sha256": replay_result.token_sha256,
        "version": VERSION,
        "wrote": False,
    }
    if args.json:
        sys.stdout.write(json.dumps(result_payload, indent=2, sort_keys=True) + "\n")
    else:
        _print_human(result_payload)
    return 0


def _print_human(payload: dict[str, object]) -> None:
    state = payload.get("state")
    lane = payload.get("lane")
    if state and lane:
        sys.stdout.write(f"{state} / {lane}\n")
    sys.stdout.write(f"{str(payload['status']).upper()}\n")
    if payload.get("refusal_reason"):
        sys.stdout.write(f"{payload['refusal_reason']}\n")
    if payload.get("syntax_error"):
        sys.stdout.write(f"{payload['syntax_error']}\n")
    structural_context = payload.get("structural_context")
    if isinstance(structural_context, dict):
        sys.stdout.write(
            f"Surface: {structural_context.get('surface_class')} / law={structural_context.get('governing_law')} / locality={structural_context.get('locality')}\n"
        )
    legality_score = payload.get("legality_score")
    if isinstance(legality_score, dict):
        sys.stdout.write(f"Legality score: {legality_score.get('score')}\n")
    recommendation_packet = payload.get("recommendation_packet")
    if isinstance(recommendation_packet, dict):
        sys.stdout.write(
            f"Recommendation: {recommendation_packet['recommended_rule_id']} line {recommendation_packet['recommended_line']} score {recommendation_packet['recommended_score']}\n"
        )
        sys.stdout.write(f"{recommendation_packet['summary']}\n")
    for event in payload.get("events", []):
        sys.stdout.write(f"- {event['rule_id']} on line {event['line']}: {event['reason']}\n")
    if payload.get("candidates"):
        sys.stdout.write("Candidates:\n")
        for candidate in payload["candidates"]:
            rank = candidate.get("rank", 0)
            score = candidate.get("score", 0)
            sys.stdout.write(
                f"- #{rank} {candidate['rule_id']} on line {candidate['line']} score {score}: {candidate['reason']}\n"
            )
    if payload.get("receipt_path"):
        sys.stdout.write(f"Receipt: {payload['receipt_path']}\n")
    if payload.get("proof_trace"):
        proof_trace = payload["proof_trace"]
        if isinstance(proof_trace, dict):
            for key in sorted(proof_trace):
                sys.stdout.write(f"{key}: {proof_trace[key]}\n")
    if payload["status"] == ACCEPT_FIXED:
        sys.stdout.write("\n")
        sys.stdout.write(str(payload["source"]))
        if not str(payload["source"]).endswith("\n"):
            sys.stdout.write("\n")


def _emit_cli_refusal(
    json_mode: bool,
    *,
    refusal_reason: str,
    refusal_code: str,
    path: str | None = None,
) -> int:
    payload: dict[str, object] = {
        "accepted": False,
        "ast_sha256": "",
        "candidates": [],
        "changed": False,
        "events": [],
        "input_sha256": "",
        "lane": LANE_ANALYZE,
        "legality_report": None,
        "mutation_performed": False,
        "output_sha256": "",
        "parse_reparse_validated": False,
        "python_version_pin": "3.12",
        "proof_trace": None,
        "receipt_path": None,
        "recommendation_packet": None,
        "refusal_code": refusal_code,
        "refusal_reason": refusal_reason,
        "rounds": 0,
        "source": "",
        "state": STATE_REFUSED,
        "status": "REFUSE_INVALID",
        "syntax_error": None,
        "token_sha256": "",
        "version": VERSION,
        "wrote": False,
    }
    if path:
        payload["path"] = path
    if json_mode:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        _print_human(payload)
    return 2


def _atomic_write_text(path: Path, content: str) -> None:
    temp_name: str | None = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as handle:
            handle.write(content)
            temp_name = handle.name
        Path(temp_name).replace(path)
    finally:
        if temp_name:
            temp_path = Path(temp_name)
            if temp_path.exists():
                temp_path.unlink()


def _resolve_receipt_dir(path: Path, configured: str | None) -> Path:
    if configured:
        receipt_dir = Path(configured).resolve()
    else:
        receipt_dir = (path.parent / ".prefix-python-receipts").resolve()
    receipt_dir.mkdir(parents=True, exist_ok=True)
    return receipt_dir


def _write_apply_receipt(
    path: Path,
    before_source: str,
    after_source: str,
    result,
    receipt_dir: Path,
) -> Path:
    before_authority = _authority_snapshot(before_source)
    after_authority = _authority_snapshot(after_source)
    parent_receipt_id = _find_parent_receipt_id(receipt_dir, path, _sha256_text(before_source))
    transition_sha256 = _sha256_text(
        _canonical_json(
            {
                "after_sha256": _sha256_text(after_source),
                "before_sha256": _sha256_text(before_source),
                "engine_result": result.to_dict(),
                "path": str(path),
            }
        )
    )
    payload: dict[str, object] = {
        "after_sha256": _sha256_text(after_source),
        "after_source": after_source,
        "after_authority": after_authority,
        "before_sha256": _sha256_text(before_source),
        "before_source": before_source,
        "before_authority": before_authority,
        "chain_sha256": _sha256_text(f"{parent_receipt_id or 'ROOT'}|{transition_sha256}"),
        "engine_result": result.to_dict(),
        "lineage_id": f"sha256:{_sha256_text(str(path))}",
        "parent_receipt_id": parent_receipt_id,
        "path": str(path),
        "python_version_pin": result.python_version_pin,
        "receipt_kind": "apply",
        "receipt_version": RECEIPT_VERSION,
        "rollback_ready": bool(before_authority.get("is_valid", False)),
        "tool_version": VERSION,
        "transition_sha256": transition_sha256,
    }
    return _write_receipt(receipt_dir, payload)


def _write_rollback_receipt(
    path: Path,
    restored_source: str,
    previous_source: str,
    parent_receipt_path: Path,
    receipt_dir: Path,
) -> Path:
    before_authority = _authority_snapshot(previous_source)
    after_authority = _authority_snapshot(restored_source)
    parent_receipt = _safe_read_receipt(parent_receipt_path)
    payload: dict[str, object] = {
        "after_sha256": _sha256_text(restored_source),
        "after_source": restored_source,
        "after_authority": after_authority,
        "before_sha256": _sha256_text(previous_source),
        "before_source": previous_source,
        "before_authority": before_authority,
        "chain_sha256": _sha256_text(
            f"{parent_receipt.get('receipt_id', '') or 'ROOT'}|{_sha256_text(_canonical_json({'path': str(path), 'after_sha256': _sha256_text(restored_source), 'before_sha256': _sha256_text(previous_source)}))}"
        ),
        "lineage_id": f"sha256:{_sha256_text(str(path))}",
        "parent_receipt_id": parent_receipt.get("receipt_id"),
        "parent_receipt_path": str(parent_receipt_path),
        "path": str(path),
        "python_version_pin": "3.12",
        "receipt_kind": "rollback",
        "receipt_version": RECEIPT_VERSION,
        "rollback_ready": bool(after_authority.get("is_valid", False)),
        "tool_version": VERSION,
        "transition_sha256": _sha256_text(
            _canonical_json(
                {
                    "after_sha256": _sha256_text(restored_source),
                    "before_sha256": _sha256_text(previous_source),
                    "parent_receipt_path": str(parent_receipt_path),
                    "path": str(path),
                }
            )
        ),
    }
    return _write_receipt(receipt_dir, payload)


def _write_receipt(receipt_dir: Path, payload: dict[str, object]) -> Path:
    canonical = _canonical_json(payload)
    receipt_id = _sha256_text(canonical)
    wrapped = dict(payload)
    wrapped["receipt_id"] = f"sha256:{receipt_id}"
    wrapped["receipt_sha256"] = receipt_id
    receipt_path = receipt_dir / f"{receipt_id}.json"
    if not receipt_path.exists():
        receipt_path.write_text(json.dumps(wrapped, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_path


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _authority_snapshot(source: str) -> dict[str, object]:
    validation = validate_source_text(source)
    if validation.is_valid and validation.authority is not None:
        return {
            "ast_sha256": validation.authority.ast_sha256,
            "is_valid": True,
            "legality_report": validation.authority.legality_report.to_dict(),
            "roundtrip_sha256": validation.authority.roundtrip_sha256,
            "token_sha256": validation.authority.token_sha256,
        }
    return {
        "failure_reason": validation.failure_reason,
        "is_valid": False,
        "syntax_error": validation.syntax_error.msg if validation.syntax_error else None,
    }


def _find_parent_receipt_id(receipt_dir: Path, path: Path, before_sha256: str) -> str | None:
    matches: list[str] = []
    for candidate in sorted(receipt_dir.glob("*.json")):
        payload = _safe_read_receipt(candidate)
        if payload.get("path") != str(path):
            continue
        if payload.get("after_sha256") != before_sha256:
            continue
        receipt_id = payload.get("receipt_id")
        if isinstance(receipt_id, str):
            matches.append(receipt_id)
    return min(matches) if matches else None


def _safe_read_receipt(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _receipt_chain_depth(receipt_dir: Path, payload: dict[str, object]) -> int:
    depth = 0
    parent_receipt_id = payload.get("parent_receipt_id")
    seen: set[str] = set()
    while isinstance(parent_receipt_id, str) and parent_receipt_id and parent_receipt_id not in seen:
        seen.add(parent_receipt_id)
        depth += 1
        parent_path = receipt_dir / f"{parent_receipt_id.removeprefix('sha256:')}.json"
        parent_payload = _safe_read_receipt(parent_path)
        parent_receipt_id = parent_payload.get("parent_receipt_id")
    return depth


def _load_receipt(receipt_argument: str, json_mode: bool, operation_name: str) -> tuple[dict[str, object], Path, int | None]:
    receipt_path = Path(receipt_argument).resolve()
    if not receipt_path.exists() or not receipt_path.is_file():
        return {}, receipt_path, _emit_cli_refusal(
            json_mode,
            refusal_reason=f"PREFIX could not open {operation_name} receipt `{receipt_path}`.",
            refusal_code=f"{operation_name}_receipt_missing",
        )

    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, receipt_path, _emit_cli_refusal(
            json_mode,
            refusal_reason=f"PREFIX could not parse {operation_name} receipt `{receipt_path}`: {exc}",
            refusal_code=f"{operation_name}_receipt_invalid",
        )
    return payload, receipt_path, None
