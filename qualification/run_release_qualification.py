from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "qualification" / "_work" / "platform-qualification"
EDITOR = ROOT / "editor" / "vscode"


def main() -> int:
    parser = argparse.ArgumentParser(description="Portable PREFIX for Python release qualification.")
    parser.add_argument("--python", default=sys.executable, help="CPython 3.12 executable to qualify.")
    parser.add_argument("--output", type=Path, help="JSON output path (defaults to the ignored qualification work root).")
    parser.add_argument("--editor-root", type=Path, default=EDITOR, help="Fresh VS Code extension build root to qualify.")
    parser.add_argument("--skip-extension", action="store_true", help="Skip only when the Node toolchain is unavailable.")
    args = parser.parse_args()

    python = str(Path(args.python).resolve()) if Path(args.python).exists() else args.python
    environment = _environment(python)
    if not environment["python_version"].startswith("3.12."):
        raise RuntimeError(f"Qualification requires CPython 3.12.x, got {environment['python_version']}")

    checks: list[dict[str, object]] = []
    checks.append(_command_check("unittest", [python, "-m", "unittest", "discover", "-s", "tests", "-q"], ROOT))
    checks.append(_command_check("version", [python, "-m", "prefix_python", "--version"], ROOT, contains="prefix-python 0.1.0"))
    checks.append(_json_cli_check(
        "corrected_example",
        [python, "-m", "prefix_python", str(ROOT / "examples" / "broken_missing_colon.txt"), "--json"],
        expected_exit=0,
        expected_status="ACCEPT_FIXED",
    ))
    checks.append(_json_cli_check(
        "refused_example",
        [python, "-m", "prefix_python", str(ROOT / "examples" / "broken_return_outside_function.txt"), "--json"],
        expected_exit=2,
        expected_status="REFUSE_INVALID",
    ))
    checks.extend(_receipt_workflow(python))
    checks.extend(_determinism_checks(python))
    checks.append(_symlink_refusal(python))

    if not args.skip_extension:
        editor = args.editor_root.resolve()
        npm = "npm.cmd" if os.name == "nt" else "npm"
        checks.append(_command_check("extension_build", [npm, "run", "build"], editor))
        checks.append(_command_check("extension_behavior", [npm, "run", "test:behavior"], editor, contains="behavior tests passed"))
        checks.append(_command_check("extension_package", [python, "package_vsix.py"], editor))
        checks.append(_vsix_check(editor / "prefix-python-0.1.0.vsix"))

    failures = [check for check in checks if not check["passed"] and not check.get("allowed_skip")]
    report = {
        "schema": "prefix-platform-qualification.v1",
        "product": "PREFIX for Python",
        "version": "0.1.0",
        "environment": environment,
        "checks": checks,
        "passed": not failures,
        "failure_count": len(failures),
    }
    WORK.mkdir(parents=True, exist_ok=True)
    output = args.output or WORK / f"{environment['platform']}-{environment['machine']}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "passed": report["passed"], "checks": len(checks)}, sort_keys=True))
    return 0 if report["passed"] else 1


def _environment(python: str) -> dict[str, str]:
    probe = _run([python, "-c", "import platform,sys; print(platform.python_version()); print(platform.machine()); print(sys.executable)"], ROOT)
    lines = probe.stdout.splitlines()
    return {
        "platform": platform.system().lower(),
        "machine": platform.machine().lower(),
        "python_version": lines[0].strip(),
        "python_executable": lines[2].strip(),
        "host": platform.platform(),
    }


def _receipt_workflow(python: str) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    base = WORK.parent
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prefix-receipt-", dir=base) as temp_name:
        temp = Path(temp_name)
        target = temp / "sample.py"
        receipt_dir = temp / "receipts"
        original = "if True:\n\tprint('ok')\n"
        target.write_text(original, encoding="utf-8", newline="\n")
        apply = _run_json([python, "-m", "prefix_python", str(target), "--apply", "--receipt-dir", str(receipt_dir), "--json"], ROOT)
        receipt = Path(str(apply["payload"].get("receipt_path", "")))
        checks.append(_payload_check("apply_receipt", apply, 0, "ACCEPT_FIXED", extra=bool(apply["payload"].get("wrote")) and receipt.is_file()))
        inspect = _run_json([python, "-m", "prefix_python", "--inspect-receipt", str(receipt), "--json"], ROOT)
        checks.append(_payload_check("inspect_receipt", inspect, 0, "ACCEPT_VALID", extra=inspect["payload"].get("receipt_kind") == "apply"))
        replay = _run_json([python, "-m", "prefix_python", "--replay-receipt", str(receipt), "--json"], ROOT)
        replay_verified = bool((replay["payload"].get("proof_trace") or {}).get("replay_verified"))
        checks.append(_payload_check("replay_receipt", replay, 0, "ACCEPT_VALID", extra=replay_verified))
        rollback = _run_json([python, "-m", "prefix_python", "--rollback", str(receipt), "--receipt-dir", str(receipt_dir), "--json"], ROOT)
        checks.append(_payload_check("rollback_receipt", rollback, 0, "ACCEPT_FIXED", extra=target.read_text(encoding="utf-8") == original))
    return checks


def _determinism_checks(python: str) -> list[dict[str, object]]:
    cases = [
        "print('valid')\n",
        "if ready\nprint('launch')\n",
        "value =\n",
        "return 1\n",
        "print('launch'\n",
    ]
    checks = []
    for index, source in enumerate(cases):
        hashes: list[str] = []
        statuses: list[str] = []
        for _ in range(12):
            result = _run([python, "-m", "prefix_python", "--stdin", "--json"], ROOT, input_text=source, expected={0, 2})
            payload = json.loads(result.stdout)
            hashes.append(hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
            statuses.append(str(payload["status"]))
        checks.append({
            "name": f"determinism_{index}",
            "passed": len(set(hashes)) == 1 and len(set(statuses)) == 1,
            "iterations": len(hashes),
            "status": statuses[0],
            "payload_sha256": hashes[0],
        })
    return checks


def _symlink_refusal(python: str) -> dict[str, object]:
    base = WORK.parent
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prefix-symlink-", dir=base) as temp_name:
        temp = Path(temp_name)
        target = temp / "target.py"
        link = temp / "link.py"
        target.write_text("if ready\nprint('launch')\n", encoding="utf-8")
        try:
            link.symlink_to(target)
        except OSError as exc:
            return {"name": "symlink_write_refusal", "passed": False, "allowed_skip": os.name == "nt", "detail": str(exc)}
        result = _run_json([python, "-m", "prefix_python", str(link), "--apply", "--json"], ROOT)
        return _payload_check("symlink_write_refusal", result, 2, "REFUSE_INVALID", extra=result["payload"].get("refusal_code") == "write_symlink_refused")


def _vsix_check(path: Path) -> dict[str, object]:
    required = {
        "extension.vsixmanifest",
        "extension/package.json",
        "extension/out/enter.js",
        "extension/out/extension.js",
        "extension/out/response.js",
        "extension/out/runtime.js",
    }
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        packaged = json.loads(archive.read("extension/package.json"))
    return {
        "name": "vsix_structure",
        "passed": required <= names and packaged["displayName"] == "PREFIX for Python" and packaged["version"] == "0.1.0",
        "sha256": _sha256(path),
        "size": path.stat().st_size,
    }


def _command_check(name: str, command: list[str], cwd: Path, *, contains: str | None = None) -> dict[str, object]:
    result = _run(command, cwd, expected=None)
    combined = result.stdout + result.stderr
    return {
        "name": name,
        "passed": result.returncode == 0 and (contains is None or contains.lower() in combined.lower()),
        "exit_code": result.returncode,
        "stdout_tail": result.stdout[-2000:].strip(),
        "stderr_tail": result.stderr[-2000:].strip(),
    }


def _json_cli_check(name: str, command: list[str], *, expected_exit: int, expected_status: str) -> dict[str, object]:
    return _payload_check(name, _run_json(command, ROOT), expected_exit, expected_status)


def _payload_check(name: str, result: dict[str, object], expected_exit: int, expected_status: str, *, extra: bool = True) -> dict[str, object]:
    payload = result["payload"]
    return {
        "name": name,
        "passed": result["exit_code"] == expected_exit and payload.get("status") == expected_status and extra,
        "exit_code": result["exit_code"],
        "status": payload.get("status"),
        "refusal_code": payload.get("refusal_code"),
    }


def _run_json(command: list[str], cwd: Path) -> dict[str, object]:
    result = _run(command, cwd, expected={0, 2})
    return {"exit_code": result.returncode, "payload": json.loads(result.stdout)}


def _run(command: list[str], cwd: Path, *, input_text: str | None = None, expected: set[int] | None = {0}) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, input=input_text, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=180)
    if expected is not None and result.returncode not in expected:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
