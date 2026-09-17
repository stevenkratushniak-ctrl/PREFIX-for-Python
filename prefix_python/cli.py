from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from contextlib import contextmanager
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
    MAX_SOURCE_BYTES,
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
            source = sys.stdin.buffer.read(MAX_SOURCE_BYTES + 1).decode("utf-8")
            source_path: Path | None = None
            source_path_was_symlink = False
        else:
            source_argument = Path(args.path)
            source_path_was_symlink = _has_link(source_argument)
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
            with source_path.open("rb") as source_handle:
                source = source_handle.read(MAX_SOURCE_BYTES + 1).decode("utf-8")
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
                with _mutation_lock(source_path):
                    _require_preimage(source_path, source)
                    receipt_path = str(
                        _write_apply_receipt(
                            source_path, source, result.source, result,
                            _resolve_receipt_dir(source_path, args.receipt_dir),
                        )
                    )
                    _require_preimage(source_path, source)
                    _atomic_write_text(source_path, result.source)
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

    target_argument = Path(payload["path"])
    if _has_link(target_argument):
        return _emit_cli_refusal(args.json, refusal_reason="Rollback refuses a symbolic-link or junction target.",
                                 refusal_code="rollback_symlink_refused")
    target_path = target_argument.resolve()
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
    try:
        current_source = target_path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return _emit_cli_refusal(args.json, refusal_reason=f"Cannot read rollback target: {exc}",
                                 refusal_code="rollback_target_unreadable", path=str(target_path))

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
        with _mutation_lock(target_path):
            _require_preimage(target_path, current_source)
            rollback_receipt = _write_rollback_receipt(
                target_path, before_source, after_source, receipt_path,
                _resolve_receipt_dir(target_path, args.receipt_dir),
            )
            _require_preimage(target_path, current_source)
            _atomic_write_text(target_path, before_source)
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
    try:
        target = Path(payload["path"])
        target_matches = not _has_link(target) and hashlib.sha256(target.read_bytes()).hexdigest() == payload["after_sha256"]
    except OSError:
        target_matches = False
    inspection_payload = {
        "accepted": target_matches,
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
            "receipt_content_verified": True,
            "target_matches_postimage": target_matches,
            "custody_scope": "local content hash, not an authenticated signature or execution attestation",
        },
        "receipt_kind": payload.get("receipt_kind"),
        "receipt_path": str(receipt_path),
        "replay_verified": False,
        "source": "",
        "state": STATE_APPLIED if target_matches else STATE_REFUSED,
        "status": ACCEPT_VALID if target_matches else "REFUSE_INVALID",
        "refusal_code": None if target_matches else "receipt_target_postimage_mismatch",
        "version": VERSION,
        "wrote": False,
    }
    if args.json:
        sys.stdout.write(json.dumps(inspection_payload, indent=2, sort_keys=True) + "\n")
    else:
        _print_human(inspection_payload)
    return 0 if target_matches else 2


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
        with NamedTemporaryFile("wb", dir=str(path.parent), delete=False) as handle:
            temp_name = handle.name
            handle.write(content.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, path.stat().st_mode)
        Path(temp_name).replace(path)
    finally:
        if temp_name:
            temp_path = Path(temp_name)
            if temp_path.exists():
                temp_path.unlink()


def _resolve_receipt_dir(path: Path, configured: str | None) -> Path:
    candidate = Path(configured) if configured else path.parent / ".prefix-python-receipts"
    if _has_link(candidate):
        raise OSError("receipt_symlink_refused: receipt directory must not traverse links or junctions")
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
    if receipt_path.exists() or receipt_path.is_symlink():
        if _safe_read_receipt(receipt_path) != wrapped:
            raise OSError("receipt_existing_content_mismatch")
    else:
        # Durable preimage and transition must exist before the source can change.
        # A crash here leaves a prepared receipt; inspect checks the actual target.
        with receipt_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(wrapped, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        if _safe_read_receipt(receipt_path) != wrapped:
            raise OSError("receipt_readback_mismatch")
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
        if _has_link(path):
            raise ValueError("linked receipt")
        with path.open("rb") as handle:
            raw = handle.read(16 * 1024 * 1024 + 1)
        if len(raw) > 16 * 1024 * 1024:
            raise ValueError("receipt exceeds 16 MiB")
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        _validate_receipt(payload)
        return payload
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        raise OSError(f"receipt_invalid: {exc}") from exc


def _receipt_chain_depth(receipt_dir: Path, payload: dict[str, object]) -> int:
    depth = 0
    parent_receipt_id = payload.get("parent_receipt_id")
    seen: set[str] = set()
    while parent_receipt_id:
        if parent_receipt_id in seen or depth >= 256:
            raise OSError("receipt_chain_invalid: cyclic or excessive chain")
        seen.add(parent_receipt_id)
        depth += 1
        parent_path = receipt_dir / f"{parent_receipt_id.removeprefix('sha256:')}.json"
        parent_payload = _safe_read_receipt(parent_path)
        if parent_payload["path"] != payload["path"] or parent_payload["after_sha256"] != payload["before_sha256"]:
            raise OSError("receipt_chain_invalid: disconnected transition")
        payload = parent_payload
        parent_receipt_id = parent_payload["parent_receipt_id"]
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
        payload = _safe_read_receipt(Path(receipt_argument))
        _receipt_chain_depth(receipt_path.parent, payload)
    except OSError as exc:
        return {}, receipt_path, _emit_cli_refusal(
            json_mode,
            refusal_reason=f"PREFIX could not parse {operation_name} receipt `{receipt_path}`: {exc}",
            refusal_code=f"{operation_name}_receipt_invalid",
        )
    return payload, receipt_path, None


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate receipt field: {key}")
        result[key] = value
    return result


def _validate_receipt(payload) -> None:
    common = {"after_sha256", "after_source", "after_authority", "before_sha256", "before_source",
              "before_authority", "chain_sha256", "lineage_id", "parent_receipt_id", "path",
              "python_version_pin", "receipt_kind", "receipt_version", "rollback_ready", "tool_version",
              "transition_sha256", "receipt_id", "receipt_sha256"}
    if not isinstance(payload, dict) or payload.get("receipt_kind") not in {"apply", "rollback"}:
        raise ValueError("unknown receipt shape or kind")
    extra = "engine_result" if payload["receipt_kind"] == "apply" else "parent_receipt_path"
    if set(payload) != common | {extra}:
        raise ValueError("missing or unrecognized receipt fields")
    for field in ("path", "before_source", "after_source", "lineage_id", "receipt_id", "receipt_sha256"):
        if not isinstance(payload[field], str):
            raise ValueError(f"invalid {field}")
    if not Path(payload["path"]).is_absolute() or payload["receipt_version"] != RECEIPT_VERSION or payload["tool_version"] != VERSION or payload["python_version_pin"] != "3.12":
        raise ValueError("receipt authority/version mismatch")
    parent = payload["parent_receipt_id"]
    if parent is not None and (not isinstance(parent, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", parent)):
        raise ValueError("invalid parent receipt identity")
    unwrapped = {key: value for key, value in payload.items() if key not in {"receipt_id", "receipt_sha256"}}
    digest = _sha256_text(_canonical_json(unwrapped))
    if payload["receipt_sha256"] != digest or payload["receipt_id"] != f"sha256:{digest}":
        raise ValueError("receipt content hash mismatch")
    for prefix in ("before", "after"):
        if len(payload[f"{prefix}_source"].encode("utf-8")) > MAX_SOURCE_BYTES:
            raise ValueError(f"{prefix} source exceeds the input boundary")
        if payload[f"{prefix}_sha256"] != _sha256_text(payload[f"{prefix}_source"]):
            raise ValueError(f"{prefix} source hash mismatch")
        if payload[f"{prefix}_authority"] != _authority_snapshot(payload[f"{prefix}_source"]):
            raise ValueError(f"{prefix} authority mismatch")
    if payload["lineage_id"] != f"sha256:{_sha256_text(payload['path'])}":
        raise ValueError("lineage mismatch")
    transition = {key: payload[key] for key in ("after_sha256", "before_sha256", "path")}
    chain_transition = transition.copy()
    transition[extra] = payload[extra]
    if extra == "engine_result":
        if not isinstance(payload[extra], dict) or payload[extra].get("source") != payload["after_source"] or payload[extra].get("status") != ACCEPT_FIXED:
            raise ValueError("invalid engine result")
        chain_transition = transition
    elif not isinstance(payload[extra], str) or not Path(payload[extra]).is_absolute():
        raise ValueError("invalid rollback parent path")
    if payload["transition_sha256"] != _sha256_text(_canonical_json(transition)):
        raise ValueError("transition hash mismatch")
    if payload["chain_sha256"] != _sha256_text(f"{parent or 'ROOT'}|{_sha256_text(_canonical_json(chain_transition))}"):
        raise ValueError("chain hash mismatch")
    expected_rollback_ready = payload["before_authority"]["is_valid"] if extra == "engine_result" else payload["after_authority"]["is_valid"]
    if type(payload["rollback_ready"]) is not bool or payload["rollback_ready"] != expected_rollback_ready:
        raise ValueError("rollback boundary mismatch")


def _has_link(path: Path) -> bool:
    return any(part.is_symlink() or part.is_junction() for part in (path.absolute(), *path.absolute().parents))


def _require_preimage(path: Path, expected: str) -> None:
    if _has_link(path) or path.read_bytes() != expected.encode("utf-8"):
        raise OSError("source_changed: source no longer matches the reviewed preimage")


@contextmanager
def _mutation_lock(path: Path):
    """Serialize PREFIX writers; OS releases the lock even if this process exits."""
    lock = path.with_name(f".{path.name}.prefix-python.lock")
    if _has_link(lock):
        raise OSError("write_lock_link_refused")
    with lock.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
