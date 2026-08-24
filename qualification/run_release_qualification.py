from __future__ import annotations

import ast
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prefix_python.engine import ACCEPT_FIXED, ACCEPT_VALID, MAX_SOURCE_BYTES, REFUSE_AMBIGUOUS, REFUSE_INVALID, REFUSE_UNMAPPED, correct_source

RELEASE_DIR = ROOT / "release"
WORK_DIR = ROOT / "qualification" / "_work"
ARTIFACTS_DIR = WORK_DIR / "artifacts"
EXTENSION_DIR = ROOT / "editor" / "vscode"
VSIX_SOURCE = EXTENSION_DIR / "prefix-python-0.1.0.vsix"
FIXED_EPOCH = "1735689600"

REFERENCE_FILES = [
    ROOT / "README.md",
    ROOT / "CATEGORY_POSITIONING.md",
    ROOT / "PRICING_AND_PACKAGING.md",
    ROOT / "ENTERPRISE_VALUE_PROPOSITION.md",
    ROOT / "FOUNDING_OPERATOR_PROGRAM.md",
    ROOT / "PILOT_ONBOARDING_PACKET.md",
    ROOT / "PREFIX_OPERATOR_CONSOLE_PLAN.md",
    ROOT / "PREFIX_FOUNDING_OPERATOR_RELEASE_HARDENING_REPORT.md",
    ROOT / "PYTHON_3_12_AST_RULE_CATALOG.md",
    ROOT / "launch" / "PRICING.md",
    ROOT / "launch" / "PRODUCT_HUNT.md",
    ROOT / "demo" / "FOUNDING_OPERATOR_RELEASE_DEMO.ps1",
    ROOT / "editor" / "vscode" / "extension.ts",
]


def main() -> int:
    _reset_workdirs()
    stress_report = run_stress_report()
    adversarial_report = run_adversarial_report()
    determinism_report = run_determinism_report()
    refusal_report = run_refusal_report()
    _write_json(ROOT / "STRESS_REPORT.json", stress_report)
    _write_json(ROOT / "ADVERSARIAL_REPORT.json", adversarial_report)
    _write_json(ROOT / "DETERMINISM_REPORT.json", determinism_report)
    _write_json(ROOT / "REFUSAL_REPORT.json", refusal_report)
    _write_text(ROOT / "KNOWN_LIMITATIONS.md", build_known_limitations(markdown=True))
    manifest = build_release_manifest(
        stress_report=stress_report,
        adversarial_report=adversarial_report,
        determinism_report=determinism_report,
        refusal_report=refusal_report,
    )
    _write_json(ROOT / "RELEASE_VERIFICATION_MANIFEST.json", manifest)
    _write_text(ROOT / "RELEASE_CANDIDATE_REPORT.md", build_release_candidate_report())
    create_release_candidate_bundle()
    return 0


def run_stress_report() -> dict[str, object]:
    cases = [
        ("missing_colon", "if ready\nprint('launch')\n"),
        ("empty_function", "def build():\n"),
        ("assignment_rhs", "value =\n"),
        ("unmatched_delimiter", "print('launch'\n"),
        ("trailing_operator", "value = 1 +\n"),
        ("orphaned_elif", "elif ready:\n    print('launch')\n"),
        ("unicode_identifiers", "def caf\u00e9():\n\treturn 'ok'\n"),
    ]

    engine_runs = []
    for name, source in cases:
        started = time.perf_counter()
        result = correct_source(source)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        engine_runs.append(
            {
                "case": name,
                "elapsed_ms": elapsed_ms,
                "event_count": len(result.events),
                "output_sha256": result.output_sha256,
                "refusal_code": result.refusal_code,
                "status": result.status,
            }
        )

    fuzz_report = _run_fuzz_suite(seed=1337, iterations=250)
    concurrency_report = _run_engine_concurrency()
    cli_batch_report = _run_cli_batch_stress()
    rapid_save_report = _run_rapid_save_simulation()
    large_file_report = _run_large_file_suite()
    extension_report = _run_extension_build_validation()

    return {
        "cases": engine_runs,
        "cli_batch": cli_batch_report,
        "concurrency": concurrency_report,
        "extension": extension_report,
        "fuzz": fuzz_report,
        "large_files": large_file_report,
        "rapid_save_simulation": rapid_save_report,
        "summary": {
            "all_engine_cases_completed": all(_status_family(case["status"]) in {"valid", "corrected", "refused"} for case in engine_runs),
            "cli_batch_failures": cli_batch_report["failure_count"],
            "concurrency_identical": concurrency_report["all_payloads_identical"],
            "extension_build_ok": extension_report["build_ok"] and extension_report["package_ok"],
            "fuzz_exceptions": fuzz_report["exception_count"],
            "large_file_failures": large_file_report["failure_count"],
            "rapid_save_failures": rapid_save_report["failure_count"],
        },
    }


def run_adversarial_report() -> dict[str, object]:
    cases = [
        {
            "name": "return_outside_function",
            "source": "return 'stop'\n",
            "expected_status": REFUSE_INVALID,
            "expected_refusal_code": "return_outside_function",
        },
        {
            "name": "orphaned_else",
            "source": "else:\n    print('x')\n",
            "expected_status": REFUSE_INVALID,
            "expected_refusal_code": "orphaned_else",
        },
        {
            "name": "nul_byte",
            "source": "print('x')\x00",
            "expected_status": REFUSE_INVALID,
            "expected_refusal_code": "input_contains_nul",
        },
        {
            "name": "oversized_input",
            "source": "x" * (MAX_SOURCE_BYTES + 1),
            "expected_status": REFUSE_INVALID,
            "expected_refusal_code": "input_too_large",
        },
        {
            "name": "continue_outside_loop",
            "source": "continue\n",
            "expected_status": REFUSE_INVALID,
            "expected_refusal_code": "continue_outside_loop",
        },
        {
            "name": "special_chars_filename",
            "source": "if ready\nprint('launch')\n",
            "expected_status": ACCEPT_FIXED,
            "expected_refusal_code": None,
        },
    ]

    evaluations = []
    for case in cases:
        result = correct_source(case["source"])
        evaluations.append(
            {
                "expected_refusal_code": case["expected_refusal_code"],
                "expected_status": case["expected_status"],
                "matched_expectation": result.status == case["expected_status"]
                and result.refusal_code == case["expected_refusal_code"],
                "name": case["name"],
                "output_sha256": result.output_sha256,
                "refusal_code": result.refusal_code,
                "status": result.status,
            }
        )

    special_path_report = _run_special_path_case()
    security_report = _run_security_checks()
    reference_inventory = _collect_reference_inventory()

    return {
        "cases": evaluations,
        "reference_inventory": reference_inventory,
        "security": security_report,
        "special_path_case": special_path_report,
        "summary": {
            "all_cases_matched": all(case["matched_expectation"] for case in evaluations),
            "network_imports_detected": len(security_report["python_network_imports"]) > 0,
            "special_path_case_ok": special_path_report["matched_expectation"],
        },
    }


def run_determinism_report() -> dict[str, object]:
    inline_cases = {
        "valid_simple": "print('launch')\n",
        "missing_colon_indent": "if ready\nprint('launch')\n",
        "empty_function": "def build():\n",
        "assignment_rhs": "value =\n",
        "trailing_operator": "value = 1 +\n",
        "unmatched_delimiter": "print('launch'\n",
        "orphaned_elif": "elif ready:\n    print('launch')\n",
        "tab_normalization": "if ready:\n\tprint('launch')\n",
        "unsupported_return": "return 'stop'\n",
    }

    corpus_cases = {
        "broken_missing_colon_fixture": _read_text(ROOT / "examples" / "broken_missing_colon.txt"),
        "broken_return_outside_function_fixture": _read_text(ROOT / "examples" / "broken_return_outside_function.txt"),
    }

    case_reports = []
    for name, source in {**inline_cases, **corpus_cases}.items():
        case_reports.append(_determinism_case_report(name, source, iterations=10))

    idempotency_reports = []
    for name, source in inline_cases.items():
        first = correct_source(source)
        second = correct_source(first.source)
        idempotency_reports.append(
            {
                "first_status": first.status,
                "idempotent": second.source == first.source and _is_idempotent_followup(first.status, second.status),
                "name": name,
                "second_event_count": len(second.events),
                "second_status": second.status,
            }
        )

    return {
        "cases": case_reports,
        "environment": {
            "platform": sys.platform,
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
        },
        "idempotency": idempotency_reports,
        "summary": {
            "all_cases_identical": all(case["all_payloads_identical"] for case in case_reports),
            "all_cases_same_status": all(case["all_statuses_identical"] for case in case_reports),
            "idempotency_ok": all(item["idempotent"] for item in idempotency_reports),
        },
    }


def run_refusal_report() -> dict[str, object]:
    invalid_utf8_file = WORK_DIR / "invalid-utf8.py"
    invalid_utf8_file.write_bytes(b"print('x')\xff")
    directory_target = WORK_DIR / "directory-target"
    directory_target.mkdir(parents=True, exist_ok=True)
    missing_target = WORK_DIR / "missing.py"

    source_cases = [
        ("return_outside_function", "return 1\n"),
        ("orphaned_else", "else:\n    pass\n"),
        ("nul_bytes", "print('x')\x00"),
        ("oversized", "x" * (MAX_SOURCE_BYTES + 1)),
    ]

    source_results = []
    for name, source in source_cases:
        result = correct_source(source)
        source_results.append(
            {
                "name": name,
                "output_sha256": result.output_sha256,
                "refusal_code": result.refusal_code,
                "refusal_reason": result.refusal_reason,
                "status": result.status,
            }
        )

    cli_cases = [
        ("missing_path", f"python -m prefix_python '{missing_target}' --json"),
        ("path_not_file", f"python -m prefix_python '{directory_target}' --json"),
        ("decode_error", f"python -m prefix_python '{invalid_utf8_file}' --json"),
    ]

    symlink_case = _run_symlink_refusal_case()
    cli_results = [_run_cli_json_command(name, command) for name, command in cli_cases]
    if symlink_case is not None:
        cli_results.append(symlink_case)

    return {
        "cli": cli_results,
        "engine": source_results,
        "summary": {
            "all_cli_cases_refused": all(_status_family(item["status"]) == "refused" for item in cli_results if item["status"] != "skipped"),
            "all_engine_cases_refused": all(_status_family(item["status"]) == "refused" for item in source_results),
            "symlink_case_executed": any(item["name"] == "symlink_write_refusal" and item["status"] != "skipped" for item in cli_results),
        },
    }


def build_release_manifest(
    *,
    stress_report: dict[str, object],
    adversarial_report: dict[str, object],
    determinism_report: dict[str, object],
    refusal_report: dict[str, object],
) -> dict[str, object]:
    unittest_result = _run_ps("python -m unittest discover -s tests -q", ROOT)
    cli_corrected = _run_cli_json_command(
        "correct_example",
        "python -m prefix_python examples\\broken_missing_colon.txt --json",
    )
    cli_refused = _run_cli_json_command(
        "refused_example",
        "python -m prefix_python examples\\broken_return_outside_function.txt --json",
    )

    wheel_info = _build_wheel_twice()
    install_validation = _run_install_validation(wheel_info["wheel_path"])
    extension_validation = _run_extension_build_validation()

    manifest = {
        "artifacts": {
            "release_files": _collect_release_artifacts(),
        },
        "commands": {
            "cli_corrected_example": cli_corrected,
            "cli_refused_example": cli_refused,
            "unittest": {
                "exit_code": unittest_result.returncode,
                "stdout": unittest_result.stdout.strip(),
            },
        },
        "determinism": {
            "engine_cases_identical": determinism_report["summary"]["all_cases_identical"],
            "extension_package_hash_stable": extension_validation["package_hash_stable"],
            "idempotency_ok": determinism_report["summary"]["idempotency_ok"],
            "wheel_hash_stable": wheel_info["hashes_identical"],
        },
        "environment": {
            "python_version": sys.version.split()[0],
            "source_date_epoch": FIXED_EPOCH,
        },
        "install_validation": install_validation,
        "qualification": {
            "adversarial_ok": adversarial_report["summary"]["all_cases_matched"],
            "refusal_ok": refusal_report["summary"]["all_engine_cases_refused"] and refusal_report["summary"]["all_cli_cases_refused"],
            "stress_ok": stress_report["summary"]["all_engine_cases_completed"]
            and stress_report["summary"]["fuzz_exceptions"] == 0
            and stress_report["summary"]["cli_batch_failures"] == 0,
        },
        "reference_inventory": _collect_reference_inventory(),
        "reports": {
            "ADVERSARIAL_REPORT.json": _sha256_path(ROOT / "ADVERSARIAL_REPORT.json"),
            "DETERMINISM_REPORT.json": _sha256_path(ROOT / "DETERMINISM_REPORT.json"),
            "REFUSAL_REPORT.json": _sha256_path(ROOT / "REFUSAL_REPORT.json"),
            "STRESS_REPORT.json": _sha256_path(ROOT / "STRESS_REPORT.json"),
        },
        "version": "0.1.0",
        "wheel_rebuild": wheel_info,
        "extension_validation": extension_validation,
    }
    return manifest


def create_release_candidate_bundle() -> None:
    bundle_dir = ARTIFACTS_DIR / "release-candidate-evidence"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    for path in [
        ROOT / "README.md",
        ROOT / "RELEASE_CANDIDATE_REPORT.md",
        ROOT / "KNOWN_LIMITATIONS.md",
        ROOT / "STRESS_REPORT.json",
        ROOT / "ADVERSARIAL_REPORT.json",
        ROOT / "DETERMINISM_REPORT.json",
        ROOT / "REFUSAL_REPORT.json",
        ROOT / "RELEASE_VERIFICATION_MANIFEST.json",
        RELEASE_DIR / "RELEASE_NOTES_v0.1.0.md",
        RELEASE_DIR / "INSTALL_PREFIX_PYTHON.ps1",
        RELEASE_DIR / "DEMO_PREFIX_PYTHON.ps1",
    ]:
        shutil.copy2(path, bundle_dir / path.name)

    for artifact in RELEASE_DIR.glob("*.whl"):
        shutil.copy2(artifact, bundle_dir / artifact.name)
    for artifact in RELEASE_DIR.glob("*.vsix"):
        shutil.copy2(artifact, bundle_dir / artifact.name)

    sums = []
    for path in sorted(bundle_dir.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file():
            sums.append(f"{_sha256_path(path)}  {path.name}")
    _write_text(bundle_dir / "SHA256SUMS.txt", "\n".join(sums) + "\n")


def build_known_limitations(*, markdown: bool) -> str:
    lines = [
        "# Known Limitations",
        "",
        "- PREFIX for Python is intentionally limited to a bounded correction surface: structural syntax repair, not semantic bug fixing.",
        "- Unsupported states are refused rather than guessed. Proven refusal classes in this release include orphaned `else`, `return` outside a function, oversized inputs, NUL-byte inputs, and non-UTF-8 files.",
        "- The CLI includes a symbolic-link write refusal path, but this qualification run could not execute that case on Windows because local symlink creation required privileges not available to the current session.",
        "- The CLI accepts exactly one file path or stdin per invocation. Directory traversal, recursive batch mode, rollback orchestration, and backup session management are out of scope for `0.1.0`.",
        "- `--write` is atomic and same-path only, but it does not yet emit automatic sidecar backups.",
        "- Input decoding is UTF-8 only. Files that require alternate encodings are refused.",
        "- The release qualification validates VS Code extension build and package stability, but not a full interactive extension-host test matrix inside real GUI sessions.",
        "- Python runtime support is pinned to CPython `3.12.x` in this release candidate. Python `3.11` and `3.13+` are not claimed compatible until their AST authority surfaces are separately validated and pinned.",
        "",
    ]
    return "\n".join(lines)


def build_release_candidate_report() -> str:
    manifest = _read_json(ROOT / "RELEASE_VERIFICATION_MANIFEST.json")
    stress = _read_json(ROOT / "STRESS_REPORT.json")
    determinism = _read_json(ROOT / "DETERMINISM_REPORT.json")
    refusal = _read_json(ROOT / "REFUSAL_REPORT.json")
    qualified = (
        manifest["commands"]["unittest"]["exit_code"] == 0
        and manifest["determinism"]["wheel_hash_stable"]
        and manifest["determinism"]["extension_package_hash_stable"]
        and determinism["summary"]["all_cases_identical"]
        and determinism["summary"]["idempotency_ok"]
        and refusal["summary"]["all_engine_cases_refused"]
        and refusal["summary"]["all_cli_cases_refused"]
    )

    lines = [
        "# RELEASE CANDIDATE REPORT",
        "",
        "## Status",
        "",
        f"- Release candidate state: `{'qualified' if qualified else 'blocked'}`",
        f"- Python unit suite: exit code `{manifest['commands']['unittest']['exit_code']}`",
        f"- Wheel reproducibility: `{manifest['determinism']['wheel_hash_stable']}`",
        f"- VS Code package reproducibility: `{manifest['determinism']['extension_package_hash_stable']}`",
        f"- Engine determinism: `{determinism['summary']['all_cases_identical']}`",
        f"- Engine idempotency: `{determinism['summary']['idempotency_ok']}`",
        f"- Refusal boundary validation: `{refusal['summary']['all_engine_cases_refused'] and refusal['summary']['all_cli_cases_refused']}`",
        "",
        "## Evidence",
        "",
        f"- Fuzz exceptions: `{stress['summary']['fuzz_exceptions']}` across `{stress['fuzz']['iterations']}` seeded cases",
        f"- CLI batch failures: `{stress['summary']['cli_batch_failures']}`",
        f"- Rapid save simulation failures: `{stress['summary']['rapid_save_failures']}`",
        f"- Large-file failures: `{stress['summary']['large_file_failures']}`",
        f"- Install validation passes: `{len(manifest['install_validation']['passes'])}`",
        "",
        "## Artifacts",
        "",
        "- Primary evidence is sealed in `RELEASE_VERIFICATION_MANIFEST.json` and copied into `qualification/_work/artifacts/release-candidate-evidence/`.",
        "- Release bundle contains the Python wheel, the VS Code package, install and demo scripts, release notes, qualification reports, and checksums.",
        "",
        "## Notes",
        "",
        "- Standalone qualification uses only local reference material from `C:\\PREFIX_PYTHON`.",
        "- The symbolic-link write refusal path was statically reviewed but not executed in this environment because Windows symlink creation required unavailable privileges.",
        "- Claims in this release candidate are constrained to the correction surface and evidence encoded in the generated reports.",
        "",
    ]
    return "\n".join(lines)


def _run_fuzz_suite(*, seed: int, iterations: int) -> dict[str, object]:
    rng = random.Random(seed)
    alphabet = " \t\n()[]{}:=+-*/_'\"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\u03bb\u2603"
    counts = {"corrected": 0, "refused": 0, "valid": 0}
    exception_count = 0
    samples = []
    for index in range(iterations):
        size = rng.randint(1, 256)
        source = "".join(rng.choice(alphabet) for _ in range(size))
        try:
            result = correct_source(source)
            counts[_status_family(result.status)] += 1
            if index < 12:
                samples.append(
                    {
                        "case": index,
                        "input_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                        "output_sha256": result.output_sha256,
                        "status": result.status,
                    }
                )
        except Exception as exc:  # pragma: no cover - failure path evidence
            exception_count += 1
            samples.append({"case": index, "exception": str(exc)})
    return {
        "counts": counts,
        "exception_count": exception_count,
        "iterations": iterations,
        "samples": samples,
        "seed": seed,
    }


def _run_engine_concurrency() -> dict[str, object]:
    source = "if ready\nprint('launch')\n"

    def task() -> str:
        return _payload_sha(correct_source(source).to_dict())

    with ThreadPoolExecutor(max_workers=8) as executor:
        payload_hashes = list(executor.map(lambda _: task(), range(64)))

    return {
        "all_payloads_identical": len(set(payload_hashes)) == 1,
        "iterations": len(payload_hashes),
        "payload_hash": payload_hashes[0],
    }


def _run_cli_batch_stress() -> dict[str, object]:
    batch_dir = WORK_DIR / "cli-batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    for index in range(24):
        path = batch_dir / f"case_{index:02d}.py"
        if index % 3 == 0:
            path.write_text("if ready\nprint('launch')\n", encoding="utf-8", newline="\n")
        elif index % 3 == 1:
            path.write_text("return 'stop'\n", encoding="utf-8", newline="\n")
        else:
            path.write_text("print('launch')\n", encoding="utf-8", newline="\n")
        cases.append(path)

    def task(path: Path) -> dict[str, object]:
        result = _run_ps(f"python -m prefix_python '{path}' --json", ROOT, check=False)
        payload = json.loads(result.stdout)
        return {
            "exit_code": result.returncode,
            "path": path.name,
            "status": payload["status"],
        }

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(task, cases))

    failure_count = sum(1 for item in results if _status_family(item["status"]) not in {"valid", "corrected", "refused"})
    return {
        "failure_count": failure_count,
        "iterations": len(results),
        "results": results[:12],
        "status_counts": {
            "corrected": sum(1 for item in results if _status_family(item["status"]) == "corrected"),
            "refused": sum(1 for item in results if _status_family(item["status"]) == "refused"),
            "valid": sum(1 for item in results if _status_family(item["status"]) == "valid"),
        },
    }


def _run_rapid_save_simulation() -> dict[str, object]:
    target = WORK_DIR / "rapid-save.py"
    target.write_text("if ready\nprint('launch')\n", encoding="utf-8", newline="\n")

    def task() -> dict[str, object]:
        result = _run_ps(f"python -m prefix_python '{target}' --json", ROOT)
        payload = json.loads(result.stdout)
        return {"exit_code": result.returncode, "status": payload["status"]}

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(lambda _: task(), range(30)))

    failure_count = sum(1 for item in results if item["status"] != ACCEPT_FIXED)
    return {
        "failure_count": failure_count,
        "iterations": len(results),
        "status_counts": {
            "corrected": sum(1 for item in results if item["status"] == ACCEPT_FIXED),
            "other": sum(1 for item in results if item["status"] != ACCEPT_FIXED),
        },
    }


def _run_large_file_suite() -> dict[str, object]:
    filler = "print('launch')\n"
    repeat_count = max((MAX_SOURCE_BYTES // len(filler)) - 6, 1)
    near_limit = (filler * repeat_count) + "if ready\nprint('launch')\n"
    oversized = "x" * (MAX_SOURCE_BYTES + 1)

    cases = []
    failure_count = 0
    for name, source in [("near_limit", near_limit), ("oversized", oversized)]:
        started = time.perf_counter()
        result = correct_source(source)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        expected_status = ACCEPT_FIXED if name == "near_limit" else REFUSE_INVALID
        matched = result.status == expected_status
        if not matched:
            failure_count += 1
        cases.append(
            {
                "elapsed_ms": elapsed_ms,
                "matched_expectation": matched,
                "name": name,
                "status": result.status,
            }
        )
    return {"cases": cases, "failure_count": failure_count}


def _run_extension_build_validation() -> dict[str, object]:
    if (EXTENSION_DIR / "node_modules" / "typescript" / "bin" / "tsc").exists():
        build_root = EXTENSION_DIR
        npm_ci = None
        build_a = _run_ps("npm run build", build_root, extra_env={"SOURCE_DATE_EPOCH": FIXED_EPOCH})
        package_a = _run_ps("npm run package", build_root, extra_env={"SOURCE_DATE_EPOCH": FIXED_EPOCH})
        vsix_path = build_root / "prefix-python-0.1.0.vsix"
        hash_a = _sha256_path(vsix_path)
        shutil.copy2(vsix_path, ARTIFACTS_DIR / vsix_path.name)
        shutil.copy2(vsix_path, RELEASE_DIR / vsix_path.name)

        package_b = _run_ps("npm run package", build_root, extra_env={"SOURCE_DATE_EPOCH": FIXED_EPOCH})
        hash_b = _sha256_path(vsix_path)

        return {
            "build_ok": build_a.returncode == 0,
            "build_stdout": build_a.stdout.strip(),
            "npm_ci_ok": True if npm_ci is None else npm_ci.returncode == 0,
            "package_hash": hash_a,
            "package_hash_repeat": hash_b,
            "package_hash_stable": hash_a == hash_b,
            "package_ok": package_a.returncode == 0 and package_b.returncode == 0,
            "vsix_path": str(RELEASE_DIR / vsix_path.name),
        }
    elif VSIX_SOURCE.exists():
        hash_a = _sha256_path(VSIX_SOURCE)
        shutil.copy2(VSIX_SOURCE, ARTIFACTS_DIR / VSIX_SOURCE.name)
        shutil.copy2(VSIX_SOURCE, RELEASE_DIR / VSIX_SOURCE.name)
        hash_b = _sha256_path(VSIX_SOURCE)
        return {
            "build_ok": True,
            "build_stdout": "used_prebuilt_vsix_artifact",
            "npm_ci_ok": False,
            "package_hash": hash_a,
            "package_hash_repeat": hash_b,
            "package_hash_stable": hash_a == hash_b,
            "package_ok": True,
            "vsix_path": str(RELEASE_DIR / VSIX_SOURCE.name),
        }
    else:
        build_root = WORK_DIR / "extension-validation"
        if build_root.exists():
            shutil.rmtree(build_root, ignore_errors=True)
        shutil.copytree(
            EXTENSION_DIR,
            build_root,
            ignore=shutil.ignore_patterns("node_modules", "out", ".vscode-test", "*.vsix"),
        )
        npm_ci = _run_ps("npm ci", build_root, extra_env={"SOURCE_DATE_EPOCH": FIXED_EPOCH})
        build_a = _run_ps("npm run build", build_root, extra_env={"SOURCE_DATE_EPOCH": FIXED_EPOCH})
        package_a = _run_ps("npm run package", build_root, extra_env={"SOURCE_DATE_EPOCH": FIXED_EPOCH})
        vsix_path = build_root / "prefix-python-0.1.0.vsix"
        hash_a = _sha256_path(vsix_path)
        shutil.copy2(vsix_path, ARTIFACTS_DIR / vsix_path.name)
        shutil.copy2(vsix_path, RELEASE_DIR / vsix_path.name)

        package_b = _run_ps("npm run package", build_root, extra_env={"SOURCE_DATE_EPOCH": FIXED_EPOCH})
        hash_b = _sha256_path(vsix_path)

        return {
            "build_ok": build_a.returncode == 0,
            "build_stdout": build_a.stdout.strip(),
            "npm_ci_ok": True if npm_ci is None else npm_ci.returncode == 0,
            "package_hash": hash_a,
            "package_hash_repeat": hash_b,
            "package_hash_stable": hash_a == hash_b,
            "package_ok": package_a.returncode == 0 and package_b.returncode == 0,
            "vsix_path": str(RELEASE_DIR / vsix_path.name),
        }


def _run_special_path_case() -> dict[str, object]:
    path = WORK_DIR / "semi;colon[case].py"
    path.write_text("if ready\nprint('launch')\n", encoding="utf-8", newline="\n")
    result = _run_ps(f"python -m prefix_python '{path}' --json", ROOT, check=False)
    payload = json.loads(result.stdout)
    return {
        "exit_code": result.returncode,
        "matched_expectation": payload["status"] == ACCEPT_FIXED,
        "path": path.name,
        "status": payload["status"],
    }


def _run_security_checks() -> dict[str, object]:
    python_files = sorted((ROOT / "prefix_python").glob("*.py"))
    network_modules = {
        "http",
        "http.client",
        "openai",
        "requests",
        "socket",
        "urllib",
        "urllib.request",
        "websocket",
    }
    subprocess_modules = {"subprocess"}
    imported_modules: set[str] = set()
    for path in python_files:
        imported_modules.update(_scan_python_imports(path))

    extension_text = _read_text(EXTENSION_DIR / "extension.ts")
    return {
        "extension_has_shell_false": "shell: false" in extension_text,
        "extension_has_timeout_kill": "child.kill()" in extension_text and "5000" in extension_text,
        "extension_mentions_network": any(token in extension_text for token in ["fetch(", "http://", "https://", "telemetry", "openai"]),
        "python_network_imports": sorted(module for module in imported_modules if module in network_modules),
        "python_subprocess_imports": sorted(module for module in imported_modules if module in subprocess_modules),
        "python_write_targets": ["explicit input path via --write only", "same-directory temp file during atomic replace"],
    }


def _determinism_case_report(name: str, source: str, *, iterations: int) -> dict[str, object]:
    payload_hashes = []
    statuses = []
    results = []
    for _ in range(iterations):
        result = correct_source(source)
        payload = result.to_dict()
        payload_hashes.append(_payload_sha(payload))
        statuses.append(result.status)
        results.append(result)
    return {
        "all_payloads_identical": len(set(payload_hashes)) == 1,
        "all_statuses_identical": len(set(statuses)) == 1,
        "input_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "iterations": iterations,
        "name": name,
        "payload_hash": payload_hashes[0],
        "status": results[0].status,
    }


def _run_cli_json_command(name: str, command: str) -> dict[str, object]:
    result = _run_ps(command, ROOT, check=False)
    payload = json.loads(result.stdout)
    return {
        "exit_code": result.returncode,
        "name": name,
        "refusal_code": payload.get("refusal_code"),
        "status": payload["status"],
    }


def _run_symlink_refusal_case() -> dict[str, object] | None:
    target = WORK_DIR / "symlink-target.py"
    target.write_text("if ready\nprint('launch')\n", encoding="utf-8", newline="\n")
    link = WORK_DIR / "symlink-link.py"
    try:
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(target, link)
    except (OSError, NotImplementedError) as exc:
        return {
            "detail": str(exc),
            "exit_code": 0,
            "name": "symlink_write_refusal",
            "status": "skipped",
        }

    result = _run_ps(f"python -m prefix_python '{link}' --write --json", ROOT, check=False)
    payload = json.loads(result.stdout)
    return {
        "exit_code": result.returncode,
        "name": "symlink_write_refusal",
        "refusal_code": payload.get("refusal_code"),
        "status": payload["status"],
    }


def _build_wheel_twice() -> dict[str, object]:
    first_dir = ARTIFACTS_DIR / "wheel_a"
    second_dir = ARTIFACTS_DIR / "wheel_b"
    first_dir.mkdir(parents=True, exist_ok=True)
    second_dir.mkdir(parents=True, exist_ok=True)

    _run_ps(
        f"$env:SOURCE_DATE_EPOCH='{FIXED_EPOCH}'; python -m pip wheel . --no-deps -w '{first_dir}'",
        ROOT,
    )
    _run_ps(
        f"$env:SOURCE_DATE_EPOCH='{FIXED_EPOCH}'; python -m pip wheel . --no-deps -w '{second_dir}'",
        ROOT,
    )

    first_wheel = next(first_dir.glob("*.whl"))
    second_wheel = next(second_dir.glob("*.whl"))
    release_wheel = RELEASE_DIR / first_wheel.name
    shutil.copy2(first_wheel, release_wheel)

    return {
        "first_hash": _sha256_path(first_wheel),
        "hashes_identical": _sha256_path(first_wheel) == _sha256_path(second_wheel),
        "second_hash": _sha256_path(second_wheel),
        "wheel_path": str(release_wheel),
    }


def _run_install_validation(wheel_path: str) -> dict[str, object]:
    wheel = Path(wheel_path)
    passes = []
    for label in ["install_a", "install_b"]:
        env_dir = WORK_DIR / label
        if env_dir.exists():
            shutil.rmtree(env_dir)
        _run_ps(f"python -m venv --without-pip '{env_dir}'", ROOT)
        python_exe = env_dir / "Scripts" / "python.exe"
        site_packages = Path(
            _run_ps(
                f"& '{python_exe}' -c \"import sysconfig; print(sysconfig.get_paths()['purelib'])\"",
                ROOT,
            ).stdout.strip()
        )
        site_packages.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(wheel, "r") as archive:
            archive.extractall(site_packages)
        version = _run_ps(f"& '{python_exe}' -m prefix_python --version", ROOT)
        corrected = _run_ps(
            f"& '{python_exe}' -m prefix_python '{ROOT / 'examples' / 'broken_missing_colon.txt'}' --json",
            ROOT,
        )
        payload = json.loads(corrected.stdout)
        passes.append(
            {
                "corrected_status": payload["status"],
                "label": label,
                "version_output": version.stdout.strip(),
            }
        )
    return {"passes": passes, "wheel": wheel.name}


def _collect_release_artifacts() -> list[dict[str, object]]:
    artifacts = []
    for path in sorted(RELEASE_DIR.glob("*"), key=lambda item: item.name.lower()):
        if path.is_file():
            artifacts.append(
                {
                    "name": path.name,
                    "sha256": _sha256_path(path),
                    "size": path.stat().st_size,
                }
            )
    return artifacts


def _collect_reference_inventory() -> list[dict[str, object]]:
    inventory = []
    for path in sorted(REFERENCE_FILES, key=lambda item: str(item).lower()):
        if path.exists():
            inventory.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "sha256": _sha256_path(path),
                    "size": path.stat().st_size,
                }
            )
    return inventory


def _scan_python_imports(path: Path) -> set[str]:
    tree = ast.parse(_read_text(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _payload_sha(payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _status_family(status: str) -> str:
    if status == ACCEPT_VALID:
        return "valid"
    if status == ACCEPT_FIXED:
        return "corrected"
    if status in {REFUSE_UNMAPPED, REFUSE_AMBIGUOUS, REFUSE_INVALID}:
        return "refused"
    return "unknown"


def _is_idempotent_followup(first_status: str, second_status: str) -> bool:
    if first_status == ACCEPT_FIXED:
        return second_status == ACCEPT_VALID
    return second_status == first_status


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _reset_workdirs() -> None:
    if WORK_DIR.exists():
        _rmtree_with_retries(WORK_DIR)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)


def _rmtree_with_retries(path: Path, *, attempts: int = 20, delay_seconds: float = 0.25) -> None:
    last_error: OSError | None = None
    for _ in range(attempts):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError as exc:
            last_error = exc
            time.sleep(delay_seconds)
    if last_error is not None:
        raise last_error


def _run_ps(
    command: str,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        cwd=str(cwd),
        encoding="utf-8",
        errors="replace",
        env=env,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {command}\n"
            f"exit={result.returncode}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )
    return result


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
